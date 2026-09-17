/* Copyright (C) 2026 Qore Technologies, s.r.o. */
import java.util.List;
import javax.wsdl.Binding;
import javax.wsdl.BindingOperation;
import javax.wsdl.Definition;
import javax.wsdl.extensions.soap.SOAPHeader;
import javax.wsdl.extensions.soap12.SOAP12Header;
import javax.wsdl.factory.WSDLFactory;
import javax.wsdl.xml.WSDLReader;

/** Observe imported header message identities independently of native value projection. */
public final class WsdlHeadersOracle {
    private WsdlHeadersOracle() { }

    private static void headers(String direction, List<?> extensions, boolean metadata) {
        for (Object extension : extensions) {
            if (extension instanceof SOAPHeader) {
                SOAPHeader header = (SOAPHeader) extension;
                System.out.println(direction + "\t" + header.getMessage() + "\t" + header.getPart()
                    + (metadata ? "\t" + header.getUse() + "\t" + header.getNamespaceURI()
                        + "\t" + header.getEncodingStyles() : ""));
            } else if (extension instanceof SOAP12Header) {
                SOAP12Header header = (SOAP12Header) extension;
                System.out.println(direction + "\t" + header.getMessage() + "\t" + header.getPart()
                    + (metadata ? "\t" + header.getUse() + "\t" + header.getNamespaceURI()
                        + "\t[" + header.getEncodingStyle() + "]" : ""));
            }
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 1 || args.length > 2 || (args.length == 2 && !"--metadata".equals(args[1]))) {
            throw new IllegalArgumentException("one local WSDL path and optional --metadata are required");
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
                headers("input", operation.getBindingInput().getExtensibilityElements(), args.length == 2);
                headers("output", operation.getBindingOutput().getExtensibilityElements(), args.length == 2);
            }
        }
    }
}
