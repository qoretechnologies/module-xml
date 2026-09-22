// Copyright (C) 2026 Qore Technologies, s.r.o.

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.apache.axis.AxisFault;
import org.apache.axis.Message;
import org.apache.axis.MessageContext;
import org.apache.axis.WSDDEngineConfiguration;
import org.apache.axis.configuration.XMLStringProvider;
import org.apache.axis.deployment.wsdd.WSDDDocument;
import org.apache.axis.handlers.BasicHandler;
import org.apache.axis.server.AxisServer;
import org.apache.axis.transport.http.SimpleAxisServer;
import org.apache.axis.utils.XMLUtils;
import samples.echo.TestClient;

/** Runs the pinned Axis 1.4 SOAPBuilders interop service and client without modifying their sources. */
public final class AxisPeer {
    private AxisPeer() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 2 && args[0].equals("server")) {
            server(args[1]);
        } else if (args.length == 2 && args[0].equals("client")) {
            System.exit(client(args[1]));
        } else {
            throw new IllegalArgumentException("usage: AxisPeer server DEPLOY.wsdd | AxisPeer client URL");
        }
    }

    // Deploys the pinned descriptor into Axis's default server configuration held in memory, so no
    // administration state is written to disk. Prints READY<TAB>port; STOP or end of input ends the server.
    private static void server(String deploy) throws Exception {
        String defaults;
        try (InputStream in = AxisServer.class.getResourceAsStream("/org/apache/axis/server/server-config.wsdd")) {
            if (in == null) {
                throw new IllegalStateException("Axis default server configuration is missing");
            }
            defaults = new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
        SimpleAxisServer server = new SimpleAxisServer();
        server.setMyConfig(new XMLStringProvider(defaults));
        try (ServerSocket socket = new ServerSocket(0, 50, InetAddress.getLoopbackAddress())) {
            // SimpleAxisServer reads the listening port while it creates its engine.
            server.setServerSocket(socket);
            AxisServer engine = server.getAxisServer();
            try (InputStream in = new FileInputStream(deploy)) {
                new WSDDDocument(XMLUtils.newDocument(in)).deploy(
                    ((WSDDEngineConfiguration) engine.getConfig()).getDeployment());
            }
            engine.refreshGlobalOptions();
            server.start(true);
            System.out.println("READY\t" + socket.getLocalPort());
            System.out.flush();
            BufferedReader input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
            String line;
            while ((line = input.readLine()) != null && !line.equals("STOP")) {
                // commands other than STOP are ignored
            }
        } finally {
            server.stop();
        }
    }

    // Runs Axis's own interop client, values and comparisons; only the verification outcome is collected.
    private static int client(String url) throws Exception {
        List<String> failures = new ArrayList<>();
        int[] verified = new int[1];
        TestClient client = new TestClient(false) {
            @Override
            protected void verify(String method, Object sent, Object gotBack) {
                ++verified[0];
                if (!equals(sent, gotBack)) {
                    failures.add(method + ": " + gotBack);
                }
            }
        };
        client.setURL(url);
        client.executeAll();
        System.out.println("VERIFIED " + verified[0] + " FAILURES " + failures.size());
        for (String failure : failures) {
            System.out.println("FAIL " + failure);
        }
        return failures.isEmpty() ? 0 : 1;
    }

    /** Appends each completed exchange's request and response SOAP parts to a JSON-lines capture file. */
    public static final class RecordingHandler extends BasicHandler {
        private static final long serialVersionUID = 1L;

        @Override
        public void invoke(MessageContext context) throws AxisFault {
            Message response = context.getResponseMessage();
            String capture = System.getProperty("qore.axis.capture");
            if (response == null || capture == null) {
                return;
            }
            String operation = context.getOperation() == null ? "" : context.getOperation().getName();
            String line = "{\"operation\":" + json(operation)
                + ",\"request\":" + json(context.getRequestMessage().getSOAPPartAsString())
                + ",\"response\":" + json(response.getSOAPPartAsString()) + "}\n";
            synchronized (RecordingHandler.class) {
                try (Writer out = new OutputStreamWriter(new FileOutputStream(capture, true), StandardCharsets.UTF_8)) {
                    out.write(line);
                } catch (IOException e) {
                    throw AxisFault.makeFault(e);
                }
            }
        }
    }

    private static String json(String value) {
        StringBuilder out = new StringBuilder("\"");
        for (int i = 0; i < value.length(); ++i) {
            char c = value.charAt(i);
            if (c == '"' || c == '\\') {
                out.append('\\').append(c);
            } else if (c < 0x20) {
                out.append(String.format("\\u%04x", (int) c));
            } else {
                out.append(c);
            }
        }
        return out.append('"').toString();
    }
}
