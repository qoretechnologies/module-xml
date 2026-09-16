/* Copyright (C) 2026 Qore Technologies, s.r.o. */
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;
import java.util.TreeSet;
import javax.wsdl.Binding;
import javax.wsdl.BindingOperation;
import javax.wsdl.Definition;
import javax.wsdl.Import;
import javax.wsdl.Message;
import javax.wsdl.Operation;
import javax.wsdl.Port;
import javax.wsdl.Part;
import javax.wsdl.extensions.ExtensibilityElement;
import javax.wsdl.extensions.soap.SOAPBody;
import javax.wsdl.extensions.soap12.SOAP12Body;
import javax.wsdl.PortType;
import javax.wsdl.Service;
import javax.wsdl.factory.WSDLFactory;
import javax.wsdl.xml.WSDLLocator;
import javax.wsdl.xml.WSDLReader;
import org.xml.sax.InputSource;

/** Observe resolved WSDL4J component edges without relying on Qore's compiler. */
public final class WsdlImportOracle {
    private WsdlImportOracle() { }

    private static final class Locator implements WSDLLocator {
        private final Path root;
        private final Path directory;
        private String latest;

        Locator(Path root) throws IOException {
            this.root = root.toRealPath();
            directory = this.root.getParent();
        }

        private InputSource source(Path path) {
            try {
                Path actual = path.toRealPath();
                if (!actual.startsWith(directory)) {
                    throw new IllegalArgumentException("resource outside fixture directory");
                }
                byte[] bytes = Files.readAllBytes(actual);
                InputSource result = new InputSource(new ByteArrayInputStream(bytes));
                result.setSystemId(actual.toUri().toString());
                return result;
            } catch (IOException error) {
                throw new IllegalArgumentException("missing fixture resource", error);
            }
        }

        @Override public InputSource getBaseInputSource() { return source(root); }
        @Override public String getBaseURI() { return root.toUri().toString(); }
        @Override public InputSource getImportInputSource(String parent, String location) {
            URI resolved = URI.create(parent).resolve(location);
            if (!"file".equals(resolved.getScheme())) {
                throw new IllegalArgumentException("unexpected non-file fixture import");
            }
            InputSource result = source(Path.of(resolved));
            latest = result.getSystemId();
            return result;
        }
        @Override public String getLatestImportURI() { return latest; }
        @Override public void close() { /* InputSources contain only byte arrays. */ }
    }

    private static void bodies(Set<String> observations, Binding binding, BindingOperation operation,
            String direction, java.util.List<?> extensions) {
        for (Object extension : extensions) {
            String namespace;
            if (extension instanceof SOAPBody) {
                namespace = ((SOAPBody) extension).getNamespaceURI();
            } else if (extension instanceof SOAP12Body) {
                namespace = ((SOAP12Body) extension).getNamespaceURI();
            } else {
                continue;
            }
            observations.add("body\t" + binding.getQName() + "/" + operation.getName() + "/" + direction
                + "\t" + namespace);
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("one root WSDL path is required");
        }
        System.setProperty("javax.xml.accessExternalDTD", "");
        System.setProperty("javax.xml.accessExternalSchema", "");
        WSDLReader reader = WSDLFactory.newInstance().newWSDLReader();
        reader.setFeature("javax.wsdl.verbose", false);
        reader.setFeature("javax.wsdl.importDocuments", true);
        Definition root = reader.readWSDL(new Locator(Path.of(args[0])));
        Set<Definition> seen = Collections.newSetFromMap(new IdentityHashMap<Definition, Boolean>());
        ArrayDeque<Definition> pending = new ArrayDeque<>();
        pending.add(root);
        TreeSet<String> observations = new TreeSet<>();
        while (!pending.isEmpty()) {
            Definition document = pending.removeFirst();
            if (!seen.add(document)) {
                continue;
            }
            for (Object value : document.getMessages().values()) {
                Message message = (Message) value;
                if (message.isUndefined()) {
                    throw new IllegalArgumentException("undefined message " + message.getQName());
                }
                observations.add("message\t" + message.getQName());
                for (Object entry : message.getParts().values()) {
                    Part part = (Part) entry;
                    observations.add("part\t" + message.getQName() + "/" + part.getName() + "\t"
                        + (part.getTypeName() == null ? "element:" + part.getElementName()
                            : "type:" + part.getTypeName()));
                }
            }
            for (Object value : document.getPortTypes().values()) {
                PortType portType = (PortType) value;
                if (portType.isUndefined()) {
                    throw new IllegalArgumentException("undefined port type " + portType.getQName());
                }
                for (Object entry : portType.getOperations()) {
                    Operation operation = (Operation) entry;
                    observations.add("operation\t" + portType.getQName() + "/" + operation.getName()
                        + "\t" + (operation.getInput() == null ? "-" : operation.getInput().getMessage().getQName())
                        + "\t" + (operation.getOutput() == null ? "-" : operation.getOutput().getMessage().getQName()));
                }
            }
            for (Object value : document.getBindings().values()) {
                Binding binding = (Binding) value;
                if (binding.isUndefined() || binding.getPortType() == null) {
                    throw new IllegalArgumentException("undefined binding " + binding.getQName());
                }
                observations.add("binding\t" + binding.getQName() + "\t" + binding.getPortType().getQName());
                for (Object extension : binding.getExtensibilityElements()) {
                    observations.add("protocol\t" + binding.getQName() + "\t"
                        + ((ExtensibilityElement) extension).getElementType().getNamespaceURI());
                }
                for (Object entry : binding.getBindingOperations()) {
                    BindingOperation operation = (BindingOperation) entry;
                    if (operation.getBindingInput() != null) {
                        bodies(observations, binding, operation, "input", operation.getBindingInput().getExtensibilityElements());
                    }
                    if (operation.getBindingOutput() != null) {
                        bodies(observations, binding, operation, "output", operation.getBindingOutput().getExtensibilityElements());
                    }
                    if (operation.getOperation() == null) {
                        throw new IllegalArgumentException("undefined binding operation " + operation.getName());
                    }
                }
            }
            for (Object value : document.getServices().values()) {
                Service service = (Service) value;
                for (Object entry : service.getPorts().values()) {
                    Port port = (Port) entry;
                    if (port.getBinding() == null || port.getBinding().isUndefined()) {
                        throw new IllegalArgumentException("undefined service binding " + port.getName());
                    }
                    observations.add("port\t" + service.getQName() + "/" + port.getName()
                        + "\t" + port.getBinding().getQName());
                }
            }
            for (Object value : document.getImports().values()) {
                for (Object entry : (java.util.List<?>) value) {
                    Import imported = (Import) entry;
                    if (imported.getDefinition() != null) {
                        pending.add(imported.getDefinition());
                    }
                }
            }
        }
        System.out.println("documents\t" + seen.size());
        for (String observation : observations) {
            System.out.println(observation);
        }
    }
}
