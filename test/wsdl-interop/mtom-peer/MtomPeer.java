// Copyright (C) 2026 Qore Technologies, s.r.o.
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Base64;
import java.util.Collection;
import java.util.Map;
import javax.xml.namespace.QName;
import jakarta.activation.DataHandler;
import jakarta.activation.DataSource;
import jakarta.xml.ws.Holder;
import org.apache.cxf.Bus;
import org.apache.cxf.BusFactory;
import org.apache.cxf.endpoint.Server;
import org.apache.cxf.frontend.ClientProxy;
import org.apache.cxf.interceptor.Fault;
import org.apache.cxf.jaxws.JaxWsProxyFactoryBean;
import org.apache.cxf.jaxws.JaxWsServerFactoryBean;
import org.apache.cxf.message.Attachment;
import org.apache.cxf.message.Message;
import org.apache.cxf.phase.AbstractPhaseInterceptor;
import org.apache.cxf.phase.Phase;
import org.apache.cxf.transport.http.HTTPConduit;
import org.apache.cxf.transport.http_jetty.JettyHTTPDestination;
import org.apache.cxf.transport.http_jetty.JettyHTTPServerEngine;
import org.eclipse.jetty.server.NetworkConnector;
import org.apache.cxf.mime.TestMtom;
import org.apache.cxf.mime.types.XopStringType;

// An MTOM peer for the pinned mtom_xop.wsdl contract. Each side verifies the other's wire form: whether a
// message is a XOP package and how many binary parts its xop:Include elements referenced.
public final class MtomPeer implements TestMtom {
    private static final String TEXT = "text é ";

    // the last received message's Content-Type and extracted parts, recorded after unmarshalling
    private static volatile String received_type;
    private static volatile int received_parts;

    private static final class Recorder extends AbstractPhaseInterceptor<Message> {
        Recorder() { super(Phase.POST_UNMARSHAL); }
        public void handleMessage(Message message) throws Fault {
            received_type = String.valueOf(message.get(Message.CONTENT_TYPE));
            Collection<Attachment> attachments = message.getAttachments();
            received_parts = attachments == null ? 0 : attachments.size();
        }
    }

    private static byte[] pattern(int size) {
        byte[] result = new byte[size];
        for (int i = 0; i < size; ++i) { result[i] = (byte)(i * 7 + 3); }
        return result;
    }
    private static byte[] reversed(byte[] bytes) {
        byte[] result = new byte[bytes.length];
        for (int i = 0; i < bytes.length; ++i) { result[i] = bytes[bytes.length - 1 - i]; }
        return result;
    }
    private static String text(int repeat) { return TEXT.repeat(repeat); }
    // JAXB maps this base64Binary element to a String holding its lexical form: the base64 characters of inline
    // content or of an xop:Include's octets. It is never optimized on output.
    private static String lexical(String text) {
        return Base64.getEncoder().encodeToString(text.getBytes(StandardCharsets.UTF_8));
    }
    private static DataHandler data(byte[] bytes) {
        return new DataHandler(new DataSource() {
            public InputStream getInputStream() { return new ByteArrayInputStream(bytes); }
            public OutputStream getOutputStream() throws IOException { throw new IOException("read only"); }
            public String getContentType() { return "application/octet-stream"; }
            public String getName() { return "attachinfo"; }
        });
    }
    private static byte[] bytes(DataHandler value) {
        try (InputStream input = value.getInputStream()) {
            return input.readAllBytes();
        } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    private static void check(boolean condition, String what) {
        if (!condition) { throw new AssertionError(what + " (received " + received_type + " with " + received_parts
            + " parts)"); }
    }
    private static boolean xop(String type) {
        return type.startsWith("multipart/related") && type.contains("application/xop+xml");
    }
    // a request name is "<xop|inline>:<size>": the form the sender must use and the payload size
    private static int expect(String name) {
        String[] fields = name.split(":");
        check(fields.length == 2, "request name " + name);
        check(fields[0].equals("xop") ? received_parts == 1 : received_parts == 0, name + " optimization");
        check(!fields[0].equals("xop") || xop(received_type), name + " package");
        return Integer.parseInt(fields[1]);
    }

    public void testXop(Holder<String> name, Holder<DataHandler> attachinfo) {
        int size = expect(name.value);
        check(Arrays.equals(pattern(size), bytes(attachinfo.value)), "testXop octets");
        name.value = "reply:" + name.value;
        attachinfo.value = data(reversed(pattern(size)));
    }
    public XopStringType testXopString(XopStringType data) {
        int repeat = expect(data.getName());
        check(lexical(text(repeat)).equals(data.getAttachinfo()), "testXopString text " + data.getAttachinfo());
        XopStringType response = new XopStringType();
        response.setName("reply:" + data.getName());
        response.setAttachinfo(lexical(text(repeat).toUpperCase()));
        return response;
    }

    private static void call(TestMtom client, String form, int size, boolean mtom_reply) {
        Holder<String> name = new Holder<>(form + ":" + size);
        Holder<DataHandler> attachinfo = new Holder<>(data(pattern(size)));
        client.testXop(name, attachinfo);
        check(name.value.equals("reply:" + form + ":" + size), "testXop reply name");
        check(Arrays.equals(reversed(pattern(size)), bytes(attachinfo.value)), "testXop reply octets");
        check(xop(received_type) == mtom_reply, "testXop reply package");
        check(received_parts == (mtom_reply && size >= 1024 ? 1 : 0), "testXop reply optimization");
    }
    private static void callString(TestMtom client, int repeat, boolean mtom_reply) {
        XopStringType request = new XopStringType();
        request.setName("inline:" + repeat);
        request.setAttachinfo(lexical(text(repeat)));
        XopStringType response = client.testXopString(request);
        check(response.getName().equals("reply:inline:" + repeat), "testXopString reply name");
        check(response.getAttachinfo().equals(lexical(text(repeat).toUpperCase())), "testXopString reply text");
        check(xop(received_type) == mtom_reply, "testXopString reply package");
        check(received_parts == (mtom_reply && lexical(text(repeat)).length() * 3 / 4 >= 1024 ? 1 : 0),
            "testXopString reply optimization");
    }

    public static void main(String[] args) throws Exception {
        Bus bus = BusFactory.newInstance().createBus();
        QName service = new QName("http://cxf.apache.org/mime", "TestMtomService");
        QName port = new QName("http://cxf.apache.org/mime", "TestMtomPort");
        try {
            if (args[0].equals("server")) {
                JaxWsServerFactoryBean factory = new JaxWsServerFactoryBean();
                factory.setBus(bus); factory.setServiceClass(TestMtom.class);
                factory.setServiceBean(new MtomPeer()); factory.setWsdlURL(args[1]);
                factory.setServiceName(service); factory.setEndpointName(port);
                factory.setAddress("http://127.0.0.1:0/service");
                factory.setProperties(Map.of("mtom-enabled", Boolean.TRUE));
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
                // client <wsdl> <url> <mtom|plain>: the Qore server mirrors the request's form
                boolean mtom = args[3].equals("mtom");
                JaxWsProxyFactoryBean factory = new JaxWsProxyFactoryBean();
                factory.setBus(bus); factory.setServiceClass(TestMtom.class); factory.setWsdlURL(args[1]);
                factory.setServiceName(service); factory.setEndpointName(port); factory.setAddress(args[2]);
                factory.setProperties(Map.of("mtom-enabled", mtom));
                factory.getInInterceptors().add(new Recorder());
                TestMtom client = (TestMtom)factory.create();
                try {
                    HTTPConduit conduit = (HTTPConduit)ClientProxy.getClient(client).getConduit();
                    conduit.getClient().setConnectionTimeout(10000); conduit.getClient().setReceiveTimeout(30000);
                    String form = mtom ? "xop" : "inline";
                    for (int size : new int[]{0, 1, 1023, 1024, 70000}) { call(client, form, size, mtom); }
                    for (int repeat : new int[]{1, 300}) { callString(client, repeat, mtom); }
                    System.out.println("PASS");
                } finally { ClientProxy.getClient(client).destroy(); }
            }
        } finally { bus.shutdown(true); }
    }
}
