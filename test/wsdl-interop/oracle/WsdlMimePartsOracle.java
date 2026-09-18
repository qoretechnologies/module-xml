/* Copyright (C) 2026 Qore Technologies, s.r.o. */
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.List;
import javax.wsdl.Binding;
import javax.wsdl.BindingOperation;
import javax.wsdl.Definition;
import javax.wsdl.extensions.mime.MIMEMultipartRelated;
import javax.wsdl.extensions.mime.MIMEPart;
import javax.wsdl.extensions.mime.MIMEContent;
import javax.wsdl.extensions.soap.SOAPBody;
import javax.wsdl.extensions.soap.SOAPHeader;
import javax.wsdl.extensions.soap12.SOAP12Body;
import javax.wsdl.extensions.soap12.SOAP12Header;
import javax.wsdl.factory.WSDLFactory;
import javax.wsdl.xml.WSDLReader;

/** Observe nested SOAP metadata without native WSDL grouping or compilation. */
public final class WsdlMimePartsOracle {
    private WsdlMimePartsOracle() { }

    private static String encoded(String value) {
        return Base64.getEncoder().encodeToString((value == null ? "" : value).getBytes(StandardCharsets.UTF_8));
    }

    private static String joined(List<?> values) {
        StringBuilder result = new StringBuilder();
        if (values != null) {
            for (Object value : values) {
                if (result.length() > 0) {
                    result.append(' ');
                }
                result.append(value);
            }
        }
        return result.toString();
    }

    private static void formats(String direction, List<?> values) {
        for (Object value : values) {
            if (value instanceof MIMEMultipartRelated) {
                MIMEMultipartRelated multipart = (MIMEMultipartRelated) value;
                System.out.println(direction + "\tMULTIPART\t" + multipart.getMIMEParts().size());
                for (Object part : multipart.getMIMEParts()) {
                    formats(direction, ((MIMEPart) part).getExtensibilityElements());
                }
            } else if (value instanceof MIMEContent) {
                MIMEContent content = (MIMEContent) value;
                System.out.println(direction + "\tCONTENT\t" + content.getPart() + "\t" + content.getType());
            } else if (value instanceof SOAPBody) {
                SOAPBody body = (SOAPBody) value;
                System.out.println(direction + "\tBODY\t" + body.getElementType() + "\t" + body.getUse()
                    + "\t" + encoded(body.getNamespaceURI()) + "\t" + encoded(joined(body.getEncodingStyles()))
                    + "\t" + encoded(joined(body.getParts())));
            } else if (value instanceof SOAP12Body) {
                SOAP12Body body = (SOAP12Body) value;
                System.out.println(direction + "\tBODY\t" + body.getElementType() + "\t" + body.getUse()
                    + "\t" + encoded(body.getNamespaceURI()) + "\t" + encoded(body.getEncodingStyle())
                    + "\t" + encoded(joined(body.getParts())));
            } else if (value instanceof SOAPHeader) {
                SOAPHeader header = (SOAPHeader) value;
                System.out.println(direction + "\tHEADER\t" + header.getMessage() + "\t"
                    + encoded(header.getPart()) + "\t" + header.getSOAPHeaderFaults().size());
            } else if (value instanceof SOAP12Header) {
                SOAP12Header header = (SOAP12Header) value;
                System.out.println(direction + "\tHEADER\t" + header.getMessage() + "\t"
                    + encoded(header.getPart()) + "\t" + header.getSOAP12HeaderFaults().size());
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
            for (Object item : ((Binding) value).getBindingOperations()) {
                BindingOperation operation = (BindingOperation) item;
                formats("input", operation.getBindingInput().getExtensibilityElements());
                formats("output", operation.getBindingOutput().getExtensibilityElements());
            }
        }
    }
}
