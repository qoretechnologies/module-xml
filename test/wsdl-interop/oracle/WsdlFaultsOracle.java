/* Copyright (C) 2026 Qore Technologies, s.r.o. */
import javax.wsdl.Binding;
import javax.wsdl.BindingFault;
import javax.wsdl.BindingOperation;
import javax.wsdl.Definition;
import javax.wsdl.extensions.soap.SOAPFault;
import javax.wsdl.extensions.soap12.SOAP12Fault;
import javax.wsdl.factory.WSDLFactory;
import javax.wsdl.xml.WSDLReader;

/** Observe concrete SOAP fault metadata independently of the normal output body. */
public final class WsdlFaultsOracle {
    private WsdlFaultsOracle() { }

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
                for (Object faultValue : operation.getBindingFaults().values()) {
                    BindingFault fault = (BindingFault) faultValue;
                    for (Object extension : fault.getExtensibilityElements()) {
                        String name;
                        String use;
                        String namespace;
                        String encoding;
                        if (extension instanceof SOAPFault) {
                            SOAPFault soap = (SOAPFault) extension;
                            name = soap.getName();
                            use = soap.getUse();
                            namespace = soap.getNamespaceURI();
                            encoding = soap.getEncodingStyles() == null ? "null"
                                : soap.getEncodingStyles().toString();
                        } else if (extension instanceof SOAP12Fault) {
                            SOAP12Fault soap = (SOAP12Fault) extension;
                            name = soap.getName();
                            use = soap.getUse();
                            namespace = soap.getNamespaceURI();
                            encoding = soap.getEncodingStyle() == null ? "null"
                                : "[" + soap.getEncodingStyle() + "]";
                        } else {
                            continue;
                        }
                        System.out.println(fault.getName() + "\t" + name + "\t" + use + "\t"
                            + namespace + "\t" + encoding);
                        System.out.println("parts\t" + operation.getOperation().getFault(fault.getName())
                            .getMessage().getParts().size());
                    }
                }
            }
        }
    }
}
