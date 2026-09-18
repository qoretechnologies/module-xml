// Copyright (C) 2026 Qore Technologies, s.r.o.
// Independent CXF endpoints for the pinned WSDL contracts; no Qore codec is used here.
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import javax.xml.namespace.QName;
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
import org.apache.headers.coloc.types.*;
import org.apache.hello_world_doc_lit_bare.PutLastTradedPricePortType;
import org.apache.hello_world_doc_lit_bare.types.TradePriceData;
import org.apache.hello_world_rpclit.GreeterRPCLit;
import org.apache.hello_world_rpclit.types.MyComplexStruct;
import org.apache.hello_world_soap12_http.Greeter;

public final class CxfPeer {
    private CxfPeer() { }

    private record Contract(Class<?> type, Object implementation, String namespace, String service, String port) { }

    private static Contract contract(String name) {
        return switch (name) {
            case "bare" -> new Contract(PutLastTradedPricePortType.class, new Bare(),
                "http://apache.org/hello_world_doc_lit_bare", "SOAPService", "SoapPort");
            case "rpc" -> new Contract(GreeterRPCLit.class, new Rpc(),
                "http://apache.org/hello_world_rpclit", "SOAPServiceRPCLit", "SoapPortRPCLit");
            case "soap12" -> new Contract(Greeter.class, new Soap12(),
                "http://apache.org/hello_world_soap12_http", "SOAPService", "SoapPort");
            case "header-rpc" -> new Contract(org.apache.headers.rpc_lit.HeaderTester.class, new RpcHeaders(),
                "http://apache.org/headers/rpc_lit", "SOAPHeaderService", "SoapPort");
            case "header-doc" -> new Contract(org.apache.headers.doc_lit.HeaderTester.class, new DocHeaders(),
                "http://apache.org/headers/doc_lit", "SOAPHeaderService", "SoapPort9000");
            default -> throw new IllegalArgumentException("unknown contract: " + name);
        };
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 3 || (!args[0].equals("server") && !args[0].equals("client"))
                || (args[0].equals("client") ? args.length != 4 : args.length != 3)) {
            throw new IllegalArgumentException("server|client CONTRACT WSDL [URL]");
        }
        Contract c = contract(args[1]);
        Bus bus = BusFactory.newInstance().createBus();
        try {
            if (args[0].equals("server")) {
                serve(bus, c, args[2]);
            } else {
                call(bus, c, args[1], args[2], args[3]);
            }
        } finally {
            bus.shutdown(true);
        }
    }

    private static void serve(Bus bus, Contract c, String wsdl) throws Exception {
        JaxWsServerFactoryBean factory = new JaxWsServerFactoryBean();
        factory.setBus(bus);
        factory.setServiceClass(c.type());
        factory.setServiceBean(c.implementation());
        factory.setWsdlURL(wsdl);
        factory.setServiceName(new QName(c.namespace(), c.service()));
        factory.setEndpointName(new QName(c.namespace(), c.port()));
        factory.setAddress("http://127.0.0.1:0/service");
        Server server = factory.create();
        try {
            JettyHTTPDestination destination = (JettyHTTPDestination) server.getDestination();
            JettyHTTPServerEngine engine = (JettyHTTPServerEngine) destination.getEngine();
            int port = ((NetworkConnector) engine.getConnector()).getLocalPort();
            System.out.println("READY\t" + port);
            System.out.flush();
            BufferedReader input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
            String command = input.readLine();
            if (!"STOP".equals(command)) {
                throw new IllegalArgumentException("expected STOP, received " + command);
            }
        } finally {
            server.destroy();
        }
    }

    private static void call(Bus bus, Contract c, String name, String wsdl, String url) throws Exception {
        JaxWsProxyFactoryBean factory = new JaxWsProxyFactoryBean();
        factory.setBus(bus);
        factory.setServiceClass(c.type());
        factory.setWsdlURL(wsdl);
        factory.setServiceName(new QName(c.namespace(), c.service()));
        factory.setEndpointName(new QName(c.namespace(), c.port()));
        factory.setAddress(url);
        Object proxy = factory.create();
        try {
            HTTPConduit conduit = (HTTPConduit) ClientProxy.getClient(proxy).getConduit();
            conduit.getClient().setConnectionTimeout(10000);
            conduit.getClient().setReceiveTimeout(30000);
            switch (name) {
                case "bare" -> testBare((PutLastTradedPricePortType) proxy);
                case "rpc" -> testRpc((GreeterRPCLit) proxy);
                case "soap12" -> {
                    Greeter client = (Greeter) proxy;
                    equal("hello SOAP 1.2", client.sayHi());
                    client.pingMe();
                }
                case "header-rpc" -> testRpcHeaders((org.apache.headers.rpc_lit.HeaderTester) proxy);
                case "header-doc" -> testDocHeaders((org.apache.headers.doc_lit.HeaderTester) proxy);
                default -> throw new IllegalArgumentException(name);
            }
            System.out.println("PASS\t" + name);
        } finally {
            ClientProxy.getClient(proxy).destroy();
        }
    }

    private static void equal(Object expected, Object actual) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError("expected " + expected + ", received " + actual);
        }
    }

    private static TradePriceData trade(String ticker, float price) {
        TradePriceData value = new TradePriceData();
        value.setTickerSymbol(ticker);
        value.setTickerPrice(price);
        return value;
    }

    public static final class Bare implements PutLastTradedPricePortType {
        public void putLastTradedPrice(TradePriceData value) {
            equal("QORE & CXF", value.getTickerSymbol());
            equal(12.5f, value.getTickerPrice());
        }
        public String bareNoParam() { return "bare response"; }
        public void sayHi(Holder<TradePriceData> value) {
            equal("QORE & CXF", value.value.getTickerSymbol());
            equal(12.5f, value.value.getTickerPrice());
            value.value = trade("accepted", 25.0f);
        }
        public String nillableParameter(BigDecimal value) {
            return value == null ? "nil" : value.toPlainString();
        }
    }

    private static void testBare(PutLastTradedPricePortType client) {
        client.putLastTradedPrice(trade("QORE & CXF", 12.5f));
        equal("bare response", client.bareNoParam());
        Holder<TradePriceData> value = new Holder<>(trade("QORE & CXF", 12.5f));
        client.sayHi(value);
        equal("accepted", value.value.getTickerSymbol());
        equal(25.0f, value.value.getTickerPrice());
        equal("123.45", client.nillableParameter(new BigDecimal("123.45")));
        equal("nil", client.nillableParameter(null));
    }

    public static final class Rpc implements GreeterRPCLit {
        public String greetMe(String value) { return "hello " + value; }
        public String greetUs(String you, String me) { return you + " & " + me; }
        public String sayHi() { return "hello RPC"; }
        public MyComplexStruct sendReceiveData(MyComplexStruct value) {
            equal("first", value.getElem1());
            equal("second", value.getElem2());
            equal(42, value.getElem3());
            MyComplexStruct result = new MyComplexStruct();
            result.setElem1(value.getElem2());
            result.setElem2(value.getElem1());
            result.setElem3(value.getElem3() + 1);
            return result;
        }
    }

    private static void testRpc(GreeterRPCLit client) {
        equal("hello RPC", client.sayHi());
        equal("hello Qore <CXF>", client.greetMe("Qore <CXF>"));
        equal("you & me", client.greetUs("you", "me"));
        MyComplexStruct value = new MyComplexStruct();
        value.setElem1("first");
        value.setElem2("second");
        value.setElem3(42);
        MyComplexStruct result = client.sendReceiveData(value);
        equal("second", result.getElem1());
        equal("first", result.getElem2());
        equal(43, result.getElem3());
    }

    public static final class Soap12 implements Greeter {
        public String sayHi() { return "hello SOAP 1.2"; }
        public void pingMe() { }
    }

    private static HeaderInfo header(String originator, String message) {
        HeaderInfo value = new HeaderInfo();
        value.setOriginator(originator);
        value.setMessage(message);
        return value;
    }

    private static InHeaderResponseT inHeaderResult(InHeaderT body, HeaderInfo header) {
        equal("client", header.getOriginator());
        equal("input header", header.getMessage());
        InHeaderResponseT result = new InHeaderResponseT();
        result.setResponseType("accepted " + body.getRequestType());
        return result;
    }

    private static InoutHeaderResponseT inoutHeaderResult(InoutHeaderT body, Holder<HeaderInfo> header) {
        equal("client", header.value.getOriginator());
        equal("input header", header.value.getMessage());
        header.value = header("server", "output header");
        InoutHeaderResponseT result = new InoutHeaderResponseT();
        result.setResponseType("accepted " + body.getRequestType());
        return result;
    }

    private static void outHeaderResult(OutHeaderT body, Holder<OutHeaderResponseT> result,
            Holder<HeaderInfo> header) {
        result.value = new OutHeaderResponseT();
        result.value.setResponseType("accepted " + body.getRequestType());
        header.value = header("server", "output header");
    }

    public static final class RpcHeaders implements org.apache.headers.rpc_lit.HeaderTester {
        public InHeaderResponseT inHeader(InHeaderT body, HeaderInfo header) {
            return inHeaderResult(body, header);
        }
        public InoutHeaderResponseT inoutHeader(InoutHeaderT body, Holder<HeaderInfo> header) {
            return inoutHeaderResult(body, header);
        }
        public void outHeader(OutHeaderT body, Holder<OutHeaderResponseT> result, Holder<HeaderInfo> header) {
            outHeaderResult(body, result, header);
        }
        public PingMeResponseT pingMe(PingMeT body) {
            equal("none", body.getFaultType());
            return new PingMeResponseT();
        }
    }

    public static final class DocHeaders implements org.apache.headers.doc_lit.HeaderTester {
        public InHeaderResponseT inHeader(InHeaderT body, HeaderInfo header) {
            return inHeaderResult(body, header);
        }
        public InoutHeaderResponseT inoutHeader(InoutHeaderT body, Holder<HeaderInfo> header) {
            return inoutHeaderResult(body, header);
        }
        public void outHeader(OutHeaderT body, Holder<OutHeaderResponseT> result, Holder<HeaderInfo> header) {
            outHeaderResult(body, result, header);
        }
        public void pingMe(String faultType) { equal("none", faultType); }
    }

    private static InHeaderT inBody() {
        InHeaderT value = new InHeaderT();
        value.setRequestType("input body");
        return value;
    }

    private static InoutHeaderT inoutBody() {
        InoutHeaderT value = new InoutHeaderT();
        value.setRequestType("inout body");
        return value;
    }

    private static OutHeaderT outBody() {
        OutHeaderT value = new OutHeaderT();
        value.setRequestType("output body");
        return value;
    }

    private static void checkHeader(HeaderInfo value) {
        equal("server", value.getOriginator());
        equal("output header", value.getMessage());
    }

    private static void testRpcHeaders(org.apache.headers.rpc_lit.HeaderTester client) throws Exception {
        equal("accepted input body", client.inHeader(inBody(), header("client", "input header")).getResponseType());
        Holder<HeaderInfo> header = new Holder<>(header("client", "input header"));
        equal("accepted inout body", client.inoutHeader(inoutBody(), header).getResponseType());
        checkHeader(header.value);
        Holder<OutHeaderResponseT> result = new Holder<>();
        client.outHeader(outBody(), result, header);
        equal("accepted output body", result.value.getResponseType());
        checkHeader(header.value);
        PingMeT body = new PingMeT();
        body.setFaultType("none");
        Objects.requireNonNull(client.pingMe(body));
    }

    private static void testDocHeaders(org.apache.headers.doc_lit.HeaderTester client) throws Exception {
        equal("accepted input body", client.inHeader(inBody(), header("client", "input header")).getResponseType());
        Holder<HeaderInfo> header = new Holder<>(header("client", "input header"));
        equal("accepted inout body", client.inoutHeader(inoutBody(), header).getResponseType());
        checkHeader(header.value);
        Holder<OutHeaderResponseT> result = new Holder<>();
        client.outHeader(outBody(), result, header);
        equal("accepted output body", result.value.getResponseType());
        checkHeader(header.value);
        client.pingMe("none");
    }
}
