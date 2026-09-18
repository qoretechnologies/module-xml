/* Copyright (C) 2026 Qore Technologies, s.r.o. */
import javax.wsdl.Definition;
import javax.wsdl.Message;
import javax.wsdl.Part;
import javax.wsdl.factory.WSDLFactory;
import javax.wsdl.xml.WSDLReader;
import javax.xml.namespace.QName;

/** Observe independent part identities and schema references with WSDL4J. */
public final class WsdlMessagePartsOracle {
    private WsdlMessagePartsOracle() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            throw new IllegalArgumentException("local WSDL path, message namespace and local name are required");
        }
        System.setProperty("javax.xml.accessExternalDTD", "");
        System.setProperty("javax.xml.accessExternalSchema", "");
        WSDLReader reader = WSDLFactory.newInstance().newWSDLReader();
        reader.setFeature("javax.wsdl.verbose", false);
        Definition definition = reader.readWSDL(args[0]);
        Message message = definition.getMessage(new QName(args[1], args[2]));
        if (message == null) {
            throw new IllegalArgumentException("message not found");
        }
        for (Object value : message.getOrderedParts(null)) {
            Part part = (Part) value;
            System.out.println(part.getName() + "\t" + part.getElementName() + "\t" + part.getTypeName());
        }
    }
}
