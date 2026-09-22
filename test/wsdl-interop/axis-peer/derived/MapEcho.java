// Copyright (C) 2026 Qore Technologies, s.r.o.
package probe;

/** The minimal interface from which Apache Axis 1.4's Java2WSDL emits its xml-soap Map schema. */
public interface MapEcho {
    java.util.HashMap<Object, Object> echoMap(java.util.HashMap<Object, Object> value);
}
