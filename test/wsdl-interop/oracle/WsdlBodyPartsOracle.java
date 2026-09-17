/* Copyright (C) 2026 Qore Technologies, s.r.o. */
import java.util.List;
import javax.wsdl.Binding;
import javax.wsdl.BindingOperation;
import javax.wsdl.Definition;
import javax.wsdl.Message;
import javax.wsdl.Part;
import javax.wsdl.extensions.soap.SOAPBody;
import javax.wsdl.extensions.soap12.SOAP12Body;
import javax.wsdl.factory.WSDLFactory;
import javax.wsdl.xml.WSDLReader;

/** Observe selected body parts and resolve their message declarations with WSDL4J. */
public final class WsdlBodyPartsOracle {
    private WsdlBodyPartsOracle() { }

    private static void observe(String direction, List<?> extensions, Message message) {
        for (Object extension : extensions) {
            List<?> parts;
            if (extension instanceof SOAPBody) {
                parts = ((SOAPBody) extension).getParts();
            } else if (extension instanceof SOAP12Body) {
                parts = ((SOAP12Body) extension).getParts();
            } else {
                continue;
            }
            System.out.println(direction + "\t" + (parts == null ? "omitted" : parts.toString().replace("\t", "\\t")
                .replace("\r", "\\r").replace("\n", "\\n")));
            for (Object value : message.getOrderedParts(parts)) {
                Part part = (Part) value;
                System.out.println("part\t" + part.getName());
            }
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("one WSDL path is required");
        }
        System.setProperty("javax.xml.accessExternalDTD", "");
        System.setProperty("javax.xml.accessExternalSchema", "");
        WSDLReader reader = WSDLFactory.newInstance().newWSDLReader();
        reader.setFeature("javax.wsdl.verbose", false);
        Definition definition = reader.readWSDL(args[0]);
        for (Object value : definition.getAllBindings().values()) {
            Binding binding = (Binding) value;
            for (Object entry : binding.getBindingOperations()) {
                BindingOperation operation = (BindingOperation) entry;
                observe("input", operation.getBindingInput().getExtensibilityElements(),
                    operation.getOperation().getInput().getMessage());
                observe("output", operation.getBindingOutput().getExtensibilityElements(),
                    operation.getOperation().getOutput().getMessage());
            }
        }
    }
}
