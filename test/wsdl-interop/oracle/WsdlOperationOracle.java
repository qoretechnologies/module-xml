/* Copyright (C) 2026 Qore Technologies, s.r.o. */
import java.util.TreeSet;
import javax.wsdl.Binding;
import javax.wsdl.BindingOperation;
import javax.wsdl.Definition;
import javax.wsdl.Operation;
import javax.wsdl.OperationType;
import javax.wsdl.PortType;
import javax.wsdl.factory.WSDLFactory;
import javax.wsdl.xml.WSDLReader;

/** Resolve abstract labels and concrete overload selectors with pinned WSDL4J. */
public final class WsdlOperationOracle {
    private WsdlOperationOracle() { }

    private static String inputName(Operation operation) {
        if (operation.getInput() == null) {
            return null;
        }
        if (operation.getInput().getName() != null) {
            return operation.getInput().getName();
        }
        return operation.getName() + (operation.getStyle() == OperationType.REQUEST_RESPONSE ? "Request"
            : operation.getStyle() == OperationType.SOLICIT_RESPONSE ? "Solicit" : "");
    }

    private static String outputName(Operation operation) {
        if (operation.getOutput() == null) {
            return null;
        }
        if (operation.getOutput().getName() != null) {
            return operation.getOutput().getName();
        }
        return operation.getName() + (operation.getStyle() == OperationType.NOTIFICATION ? "" : "Response");
    }

    private static String label(String value) {
        return value == null ? "-" : value;
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("one fixture path is required");
        }
        System.setProperty("javax.xml.accessExternalDTD", "");
        System.setProperty("javax.xml.accessExternalSchema", "");
        WSDLReader reader = WSDLFactory.newInstance().newWSDLReader();
        reader.setFeature("javax.wsdl.verbose", false);
        Definition definition = reader.readWSDL(args[0]);
        TreeSet<String> observations = new TreeSet<>();
        for (Object value : definition.getAllPortTypes().values()) {
            PortType port = (PortType) value;
            if (port.isUndefined()) {
                throw new IllegalArgumentException("undefined port type " + port.getQName());
            }
            for (Object entry : port.getOperations()) {
                Operation operation = (Operation) entry;
                if (operation.isUndefined()) {
                    throw new IllegalArgumentException("undefined operation " + operation.getName());
                }
                String input = inputName(operation);
                String output = outputName(operation);
                // WSDL4J independently applies the defaults in its operation lookup.
                if (port.getOperation(operation.getName(), input, output) != operation) {
                    throw new IllegalArgumentException("effective labels select a different operation");
                }
                observations.add("operation\t" + port.getQName() + "\t" + operation.getName()
                    + "\t" + operation.getStyle() + "\t" + label(input) + "\t" + label(output));
            }
        }
        for (Object value : definition.getAllBindings().values()) {
            Binding binding = (Binding) value;
            for (Object entry : binding.getBindingOperations()) {
                BindingOperation selected = (BindingOperation) entry;
                Operation operation = selected.getOperation();
                if (operation == null || operation.isUndefined()) {
                    throw new IllegalArgumentException("undefined binding operation " + selected.getName());
                }
                observations.add("binding\t" + binding.getQName() + "\t" + operation.getName()
                    + "\t" + label(inputName(operation)) + "\t" + label(outputName(operation)));
            }
        }
        for (String observation : observations) {
            System.out.println(observation);
        }
    }
}
