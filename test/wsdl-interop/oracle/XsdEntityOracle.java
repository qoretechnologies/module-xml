// Copyright (C) 2026 Qore Technologies, s.r.o.
// Separate entry point for standalone XML with internal entity declarations.
// The SOAP oracle keeps its unconditional DOCTYPE prohibition.
public final class XsdEntityOracle {
    private XsdEntityOracle() { }

    public static void main(String[] args) throws Exception {
        XsdOracle.run(args, true);
    }
}
