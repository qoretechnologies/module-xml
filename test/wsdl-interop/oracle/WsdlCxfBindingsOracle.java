/* Copyright (C) 2026 Qore Technologies, s.r.o. */
import javax.wsdl.Binding;
import javax.wsdl.BindingOperation;
import javax.wsdl.Message;
import javax.wsdl.Definition;
import javax.wsdl.extensions.soap.SOAPBody;
import javax.wsdl.factory.WSDLFactory;
import javax.wsdl.xml.WSDLReader;
import javax.xml.namespace.QName;

/** Observe body-part references without changing pinned CXF source declarations. */
public final class WsdlCxfBindingsOracle {
    private WsdlCxfBindingsOracle() { }
    public static void main(String[] args) throws Exception {
        System.setProperty("javax.xml.accessExternalDTD", "");
        System.setProperty("javax.xml.accessExternalSchema", "");
        WSDLReader reader = WSDLFactory.newInstance().newWSDLReader();
        reader.setFeature("javax.wsdl.verbose", false);
        Definition d = reader.readWSDL(args[0]);
        Binding b = d.getBinding(new QName(args[1], "headerTesterSOAPBinding"));
        for (Object item : b.getBindingOperations()) {
            BindingOperation op = (BindingOperation)item;
            for (boolean input : new boolean[]{true, false}) {
                Message message = input ? op.getOperation().getInput().getMessage()
                    : op.getOperation().getOutput().getMessage();
                for (Object extension : input ? op.getBindingInput().getExtensibilityElements()
                        : op.getBindingOutput().getExtensibilityElements()) {
                    if (extension instanceof SOAPBody) {
                        SOAPBody body = (SOAPBody)extension;
                        if (body.getParts() != null) {
                            for (Object part : body.getParts()) {
                                String name = (String)part;
                                System.out.println(op.getName() + "\t" + (input ? "input" : "output")
                                    + "\t" + message.getQName() + "\t" + name + "\t"
                                    + (message.getPart(name) == null ? "undefined" : "defined"));
                            }
                        }
                    }
                }
            }
        }
    }
}
