// Copyright (C) 2026 Qore Technologies, s.r.o.
import java.io.*;
import java.net.ServerSocket;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import javax.xml.namespace.QName;
import jakarta.xml.ws.BindingProvider;
import jakarta.xml.ws.WebServiceException;
import org.apache.cxf.Bus;
import org.apache.cxf.BusFactory;
import org.apache.cxf.endpoint.Server;
import org.apache.cxf.frontend.ClientProxy;
import org.apache.cxf.interceptor.Fault;
import org.apache.cxf.jaxws.JaxWsProxyFactoryBean;
import org.apache.cxf.jaxws.JaxWsServerFactoryBean;
import org.apache.cxf.message.Message;
import org.apache.cxf.phase.AbstractPhaseInterceptor;
import org.apache.cxf.phase.Phase;
import org.apache.cxf.transport.http.HTTPConduit;
import org.apache.cxf.transport.http_jetty.JettyHTTPDestination;
import org.apache.cxf.transport.http_jetty.JettyHTTPServerEngine;
import org.apache.cxf.ws.addressing.AddressingProperties;
import org.apache.cxf.ws.addressing.JAXWSAConstants;
import org.apache.cxf.ws.addressing.WSAddressingFeature;
import org.eclipse.jetty.server.NetworkConnector;
import org.apache.cxf.systest.ws.addr_feature.AddNumbersFault;
import org.apache.cxf.systest.ws.addr_feature.AddNumbersFault_Exception;
import org.apache.cxf.systest.ws.addr_feature.AddNumbersPortType;

// A WS-Addressing peer for CXF's pinned add_numbers.wsdl (SOAP 1.1) and add_numbers_soap12.wsdl contracts. The
// server checks the message addressing properties of each request; the client checks those of each response.
public final class AddressingPeer implements AddNumbersPortType {
    private static final String NS = "http://apache.org/cxf/systest/ws/addr_feature/";
    private static final String PORT_TYPE = NS + "AddNumbersPortType/";

    // the inbound message addressing properties of the request being processed
    private static final ThreadLocal<AddressingProperties> inbound = new ThreadLocal<>();

    private static final class Recorder extends AbstractPhaseInterceptor<Message> {
        Recorder() { super(Phase.PRE_INVOKE); }
        public void handleMessage(Message message) throws Fault {
            inbound.set((AddressingProperties)message.get(JAXWSAConstants.ADDRESSING_PROPERTIES_INBOUND));
        }
    }

    private static void check(boolean condition, String what) {
        if (!condition) { throw new AssertionError(what); }
    }

    // the request must use WS-Addressing with the operation's input action and a message ID
    private static void expectRequest(String action) {
        AddressingProperties maps = inbound.get();
        check(maps != null && maps.getAction() != null, "request without WS-Addressing properties");
        check(action.equals(maps.getAction().getValue()), "request action " + maps.getAction().getValue());
        check(maps.getMessageID() != null, "request without a message ID");
    }

    public int addNumbers(int number1, int number2) throws AddNumbersFault_Exception {
        expectRequest(PORT_TYPE + "addNumbersRequest");
        if (number1 < 0) {
            AddNumbersFault fault = new AddNumbersFault();
            fault.setDetail("negative number " + number1);
            fault.setMessage("negative numbers cannot be added");
            throw new AddNumbersFault_Exception("negative number", fault);
        }
        return number1 + number2;
    }
    public int addNumbers2(int number1, int number2) {
        expectRequest(PORT_TYPE + "add2In");
        return number1 + number2;
    }
    public int addNumbers3(int number1, int number2) {
        expectRequest("3in");
        return number1 + number2;
    }

    // the message addressing properties of the last request that the client sent
    private static volatile AddressingProperties outbound;

    private static final class OutboundRecorder extends AbstractPhaseInterceptor<Message> {
        OutboundRecorder() { super(Phase.PRE_STREAM); }
        public void handleMessage(Message message) throws Fault {
            outbound = (AddressingProperties)message.get(JAXWSAConstants.ADDRESSING_PROPERTIES_OUTBOUND);
        }
    }

    // the message ID of the last request that the client sent
    private static String sentMessageId() {
        check(outbound != null && outbound.getMessageID() != null, "request without a message ID");
        return outbound.getMessageID().getValue();
    }

    // the response relates to the request and carries the expected action
    private static void expectResponse(AddNumbersPortType client, String action) {
        String message_id = sentMessageId();
        Map<String, Object> response = ((BindingProvider)client).getResponseContext();
        AddressingProperties received =
            (AddressingProperties)response.get(JAXWSAConstants.ADDRESSING_PROPERTIES_INBOUND);
        check(received != null && received.getAction() != null, "response without WS-Addressing properties");
        check(action.equals(received.getAction().getValue()), "response action " + received.getAction().getValue());
        check(received.getRelatesTo() != null && message_id.equals(received.getRelatesTo().getValue()),
            "response relationship "
                + (received.getRelatesTo() == null ? "missing" : received.getRelatesTo().getValue()));
    }

    // a free local port for the decoupled endpoint, whose address the requests carry as wsa:ReplyTo
    private static int freePort() throws IOException {
        try (ServerSocket socket = new ServerSocket(0)) { return socket.getLocalPort(); }
    }

    public static void main(String[] args) throws Exception {
        Bus bus = BusFactory.newInstance().createBus();
        QName service = new QName(NS, "AddNumbersService");
        try {
            if (args[0].equals("server")) {
                // server <wsdl> <port>
                JaxWsServerFactoryBean factory = new JaxWsServerFactoryBean();
                factory.setBus(bus); factory.setServiceClass(AddNumbersPortType.class);
                factory.setServiceBean(new AddressingPeer()); factory.setWsdlURL(args[1]);
                factory.setServiceName(service); factory.setEndpointName(new QName(NS, args[2]));
                factory.setAddress("http://127.0.0.1:0/add");
                factory.getFeatures().add(new WSAddressingFeature());
                factory.getInInterceptors().add(new Recorder());
                Server server = factory.create();
                try {
                    JettyHTTPDestination destination = (JettyHTTPDestination)server.getDestination();
                    JettyHTTPServerEngine engine = (JettyHTTPServerEngine)destination.getEngine();
                    System.out.println("READY\t" + ((NetworkConnector)engine.getConnector()).getLocalPort());
                    System.out.flush();
                    BufferedReader input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
                    check("STOP".equals(input.readLine()), "STOP");
                } finally { server.destroy(); }
            } else {
                // client <wsdl> <url> <port> [decoupled]
                JaxWsProxyFactoryBean factory = new JaxWsProxyFactoryBean();
                factory.setBus(bus); factory.setServiceClass(AddNumbersPortType.class); factory.setWsdlURL(args[1]);
                factory.setServiceName(service); factory.setEndpointName(new QName(NS, args[3]));
                factory.setAddress(args[2]);
                factory.getFeatures().add(new WSAddressingFeature());
                factory.getOutInterceptors().add(new OutboundRecorder());
                AddNumbersPortType client = (AddNumbersPortType)factory.create();
                try {
                    HTTPConduit conduit = (HTTPConduit)ClientProxy.getClient(client).getConduit();
                    conduit.getClient().setConnectionTimeout(10000); conduit.getClient().setReceiveTimeout(30000);
                    if (args.length > 4 && args[4].equals("decoupled")) {
                        // WS-Addressing SOAP Binding section 5.2: replies and faults arrive at a separate endpoint
                        conduit.getClient().setDecoupledEndpoint("http://127.0.0.1:" + freePort() + "/decoupled");
                    }
                    // the SOAP 1.2 HTTP binding sends Sender faults with HTTP 400, which CXF otherwise reports as a
                    // transport error without reading the fault
                    ((BindingProvider)client).getRequestContext().put(
                        "org.apache.cxf.transport.process_fault_on_http_400", Boolean.TRUE);
                    check(client.addNumbers(1, 2) == 3, "addNumbers");
                    expectResponse(client, PORT_TYPE + "addNumbersResponse");
                    check(client.addNumbers2(3, 4) == 7, "addNumbers2");
                    expectResponse(client, PORT_TYPE + "add2Out");
                    try {
                        client.addNumbers(-1, 2);
                        check(false, "addNumbers fault");
                    } catch (AddNumbersFault_Exception fault) {
                        check(fault.getFaultInfo().getDetail().equals("negative number -1"), "fault detail");
                        expectResponse(client, PORT_TYPE + "addNumbers/Fault/addNumbersFault");
                    }
                    // addNumbers3's relative action is not an [action] (WS-Addressing Core section 3.1), and with
                    // SOAP 1.2 not an action parameter either, which must be an absolute URI
                    try {
                        client.addNumbers3(1, 2);
                        check(false, "addNumbers3 with a relative action");
                    } catch (WebServiceException fault) {
                        String text = String.valueOf(fault.getMessage());
                        check(text.contains("Message Addressing Property is not valid")
                            || text.contains("invalid SOAP 1.2 action URI"), "addNumbers3 fault " + text);
                    }
                    System.out.println("PASS");
                } finally { ClientProxy.getClient(client).destroy(); }
            }
        } finally { bus.shutdown(true); }
    }
}
