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

    private static void headers(String direction, List<?> extensions) {
        for (Object extension : extensions) {
            if (extension instanceof SOAPHeader) {
                SOAPHeader header = (SOAPHeader) extension;
                System.out.println(direction + "\t" + header.getMessage() + "\t" + header.getPart());
            } else if (extension instanceof SOAP12Header) {
                SOAP12Header header = (SOAP12Header) extension;
                System.out.println(direction + "\t" + header.getMessage() + "\t" + header.getPart());
            }
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("one local WSDL path is required");
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
                headers("input", operation.getBindingInput().getExtensibilityElements());
                headers("output", operation.getBindingOutput().getExtensibilityElements());
            }
        }
    }
}
