// Copyright (C) 2026 Qore Technologies, s.r.o.
// Independent Apache CXF header-understanding and role oracle.
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import javax.xml.namespace.QName;
import jakarta.jws.WebMethod;
import jakarta.jws.WebParam;
import jakarta.jws.WebResult;
import jakarta.jws.WebService;
import jakarta.jws.soap.SOAPBinding;
import org.apache.cxf.Bus;
import org.apache.cxf.BusFactory;
import org.apache.cxf.binding.soap.SoapMessage;
import org.apache.cxf.binding.soap.interceptor.AbstractSoapInterceptor;
import org.apache.cxf.endpoint.Server;
import org.apache.cxf.jaxws.JaxWsServerFactoryBean;
import org.apache.cxf.phase.Phase;
import org.apache.cxf.transport.http_jetty.JettyHTTPDestination;
import org.apache.cxf.transport.http_jetty.JettyHTTPServerEngine;
import org.eclipse.jetty.server.NetworkConnector;
import org.w3c.dom.Element;

public final class NodePeer {
    private NodePeer() { }
    @WebService(targetNamespace="urn:soap-node-test")
    @SOAPBinding(parameterStyle=SOAPBinding.ParameterStyle.BARE)
    public interface Echo {
        @WebMethod(action="urn:echo")
        @WebResult(name="value", targetNamespace="urn:soap-node-test")
        String echo(@WebParam(name="value", targetNamespace="urn:soap-node-test") String value);
    }
    public static final class EchoImpl implements Echo {
        public String echo(String value) {
            if (!"invoice-71".equals(value)) { throw new IllegalArgumentException("incorrect invoice"); }
            return value;
        }
    }
    private static final class Tracking extends AbstractSoapInterceptor {
        private static final QName NAME = new QName("urn:tracking", "Tracking");
        private final boolean known;
        Tracking(boolean known) { super(Phase.PRE_PROTOCOL); this.known = known; }
        @Override public Set<URI> getRoles() { return Set.of(URI.create("urn:billing")); }
        @Override public Set<QName> getUnderstoodHeaders() { return known ? Set.of(NAME) : Set.of(); }
        @Override public void handleMessage(SoapMessage message) {
            if (known && message.hasHeader(NAME)
                    && !"invoice-71".equals(((Element) message.getHeader(NAME).getObject()).getTextContent())) {
                throw new IllegalArgumentException("invalid tracking header");
            }
        }
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 2) { throw new IllegalArgumentException("VERSION KNOWN"); }
        Bus bus = BusFactory.newInstance().createBus();
        try {
            JaxWsServerFactoryBean factory = new JaxWsServerFactoryBean();
            factory.setBus(bus);
            factory.setServiceClass(Echo.class);
            factory.setServiceBean(new EchoImpl());
            factory.setBindingId(args[0].equals("12") ? jakarta.xml.ws.soap.SOAPBinding.SOAP12HTTP_BINDING
                : jakarta.xml.ws.soap.SOAPBinding.SOAP11HTTP_BINDING);
            factory.getInInterceptors().add(new Tracking(Boolean.parseBoolean(args[1])));
            factory.setAddress("http://127.0.0.1:0/service");
            Server server = factory.create();
            try {
                JettyHTTPDestination destination = (JettyHTTPDestination) server.getDestination();
                JettyHTTPServerEngine engine = (JettyHTTPServerEngine) destination.getEngine();
                int port = ((NetworkConnector) engine.getConnector()).getLocalPort();
                System.out.println("READY\t" + port);
                System.out.flush();
                BufferedReader input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
                if (!"STOP".equals(input.readLine())) { throw new IllegalArgumentException("expected STOP"); }
            } finally { server.destroy(); }
        } finally { bus.shutdown(true); }
    }
}
