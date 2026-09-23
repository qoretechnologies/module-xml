// Copyright (C) 2026 Qore Technologies, s.r.o.
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.awt.Image;
import java.awt.image.BufferedImage;
import javax.xml.transform.Source;
import javax.xml.transform.stream.StreamSource;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.TransformerFactory;
import javax.xml.namespace.QName;
import jakarta.activation.DataHandler;
import jakarta.activation.DataSource;
import jakarta.xml.ws.Holder;
import org.apache.cxf.Bus;
import org.apache.cxf.BusFactory;
import org.apache.cxf.endpoint.Server;
import org.apache.cxf.frontend.ClientProxy;
import org.apache.cxf.jaxws.JaxWsProxyFactoryBean;
import org.apache.cxf.jaxws.JaxWsServerFactoryBean;
import org.apache.cxf.transport.http.HTTPConduit;
import org.apache.cxf.transport.http_jetty.JettyHTTPDestination;
import org.apache.cxf.transport.http_jetty.JettyHTTPServerEngine;
import org.eclipse.jetty.server.NetworkConnector;
import org.apache.cxf.swa.SwAServiceInterface;
import org.apache.cxf.swa.types.*;

public final class SwAPeer implements SwAServiceInterface {
    private static final byte[] BYTES = {0, (byte)255, 65, 13, 10};
    // echoDataRef: the swaRef request content and the text of the reply (WS-I Attachments Profile 1.0 R2928)
    private static final byte[] REFERENCE = {1, 2, (byte)255, 13, 10, 0};
    private static final String REFERENCE_REPLY = "reference reply é";
    private static DataHandler data(byte[] bytes) { return data(bytes, "application/octet-stream"); }
    private static DataHandler data(byte[] bytes, String media) {
        return new DataHandler(new DataSource() {
            public InputStream getInputStream() { return new ByteArrayInputStream(bytes); }
            public OutputStream getOutputStream() throws IOException { throw new IOException("read only"); }
            public String getContentType() { return media; }
            public String getName() { return "attachment"; }
        });
    }
    private static byte[] bytes(DataHandler value) {
        try (InputStream input = value.getInputStream()) {
            return input.readAllBytes();
        } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    private static void check(boolean condition) {
        if (!condition) { throw new AssertionError("unexpected attachment or SOAP value"); }
    }
    public void echoData(Holder<String> text, Holder<DataHandler> data) {
        check(text.value.equals("hello é") && Arrays.equals(BYTES, bytes(data.value)));
        text.value = "response é";
        data.value = data(BYTES);
    }
    public void echoDataWithHeader(Holder<String> text, Holder<DataHandler> data, Holder<String> header) {
        check(header.value.equals("header request"));
        echoData(text, data);
        header.value = "header response";
    }
    public void echoDataRef(Holder<DataStruct> data) {
        check(Arrays.equals(REFERENCE, bytes(data.value.getDataRef())));
        DataStruct reply = new DataStruct();
        reply.setDataRef(data(REFERENCE_REPLY.getBytes(StandardCharsets.UTF_8), "text/plain;charset=UTF-8"));
        data.value = reply;
    }
    public OutputResponseAll echoAllAttachmentTypes(VoidRequest request, Holder<DataHandler> a,
            Holder<DataHandler> b, Holder<javax.xml.transform.Source> c, Holder<java.awt.Image> d,
            Holder<java.awt.Image> e) {
        check(request != null);
        check(new String(bytes(a.value), StandardCharsets.UTF_8).equals("plain é"));
        check(new String(bytes(b.value), StandardCharsets.UTF_8).equals("<p>html é</p>"));
        check(xml(c.value).contains("payload"));
        c.value = new StreamSource(new StringReader("<payload>XML é</payload>"));
        check(d.value.getWidth(null) == 2 && d.value.getHeight(null) == 2);
        check(e.value.getWidth(null) == 2 && e.value.getHeight(null) == 2);
        OutputResponseAll response = new OutputResponseAll();
        response.setResult("ok"); response.setReason("all attachment types");
        return response;
    }
    private static String xml(Source source) {
        try {
            StringWriter text = new StringWriter();
            TransformerFactory.newInstance().newTransformer().transform(source, new StreamResult(text));
            return text.toString();
        } catch (Exception error) { throw new IllegalStateException(error); }
    }
    private static Image image() {
        BufferedImage image = new BufferedImage(2, 2, BufferedImage.TYPE_INT_RGB);
        for (int x = 0; x < 2; ++x) { for (int y = 0; y < 2; ++y) { image.setRGB(x, y, 0x112233); } }
        return image;
    }
    public static void main(String[] args) throws Exception {
        Bus bus = BusFactory.newInstance().createBus();
        QName service = new QName("http://cxf.apache.org/swa", "SwAService");
        QName port = new QName("http://cxf.apache.org/swa", "SwAServiceHttpPort");
        try {
            if (args[0].equals("server")) {
                JaxWsServerFactoryBean factory = new JaxWsServerFactoryBean();
                factory.setBus(bus); factory.setServiceClass(SwAServiceInterface.class);
                factory.setServiceBean(new SwAPeer()); factory.setWsdlURL(args[1]);
                factory.setServiceName(service); factory.setEndpointName(port);
                factory.setAddress("http://127.0.0.1:0/service");
                Server server = factory.create();
                try {
                    JettyHTTPDestination destination = (JettyHTTPDestination)server.getDestination();
                    JettyHTTPServerEngine engine = (JettyHTTPServerEngine)destination.getEngine();
                    System.out.println("READY\t" + ((NetworkConnector)engine.getConnector()).getLocalPort());
                    System.out.flush();
                    check("STOP".equals(new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8)).readLine()));
                } finally { server.destroy(); }
            } else {
                JaxWsProxyFactoryBean factory = new JaxWsProxyFactoryBean();
                factory.setBus(bus); factory.setServiceClass(SwAServiceInterface.class); factory.setWsdlURL(args[1]);
                factory.setServiceName(service); factory.setEndpointName(port); factory.setAddress(args[2]);
                SwAServiceInterface client = (SwAServiceInterface)factory.create();
                try {
                    HTTPConduit conduit = (HTTPConduit)ClientProxy.getClient(client).getConduit();
                    conduit.getClient().setConnectionTimeout(10000); conduit.getClient().setReceiveTimeout(30000);
                    for (boolean headers : new boolean[]{false, true}) {
                        Holder<String> text = new Holder<>("hello é");
                        Holder<DataHandler> attachment = new Holder<>(data(BYTES));
                        Holder<String> header = new Holder<>("header request");
                        if (headers) { client.echoDataWithHeader(text, attachment, header); }
                        else { client.echoData(text, attachment); }
                        check(text.value.equals("response é") && Arrays.equals(BYTES, bytes(attachment.value)));
                        if (headers) { check(header.value.equals("header response")); }
                    }
                    Holder<DataHandler> a = new Holder<>(data("plain é".getBytes(StandardCharsets.UTF_8), "text/plain;charset=UTF-8"));
                    Holder<DataHandler> b = new Holder<>(data("<p>html é</p>".getBytes(StandardCharsets.UTF_8), "text/html;charset=UTF-8"));
                    Holder<Source> c = new Holder<>(new StreamSource(new StringReader("<payload>XML é</payload>")));
                    Holder<Image> d = new Holder<>(image());
                    Holder<Image> e = new Holder<>(image());
                    OutputResponseAll result = client.echoAllAttachmentTypes(new VoidRequest(), a, b, c, d, e);
                    check(result.getResult().equals("ok") && result.getReason().equals("all attachment types"));
                    check(new String(bytes(a.value), StandardCharsets.UTF_8).equals("plain é"));
                    check(new String(bytes(b.value), StandardCharsets.UTF_8).equals("<p>html é</p>"));
                    check(xml(c.value).contains("payload"));
                    check(d.value.getWidth(null) == 2 && d.value.getHeight(null) == 2);
                    check(e.value.getWidth(null) == 2 && e.value.getHeight(null) == 2);
                    // the reference operation is called when the runner asks for it (argument "reference")
                    if (args.length > 3 && args[3].equals("reference")) {
                        DataStruct reference = new DataStruct();
                        reference.setDataRef(data(REFERENCE));
                        Holder<DataStruct> echoed = new Holder<>(reference);
                        client.echoDataRef(echoed);
                        check(new String(bytes(echoed.value.getDataRef()), StandardCharsets.UTF_8)
                            .equals(REFERENCE_REPLY));
                    }
                    System.out.println("PASS");
                } finally { ClientProxy.getClient(client).destroy(); }
            }
        } finally { bus.shutdown(true); }
    }
}
