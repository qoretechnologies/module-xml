// Copyright (C) 2026 Qore Technologies, s.r.o.
// Post-schema-validation observations for the pinned offline oracle.
import java.util.ArrayList;
import java.util.ArrayDeque;
import java.util.Base64;
import java.util.Deque;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import javax.xml.transform.sax.SAXSource;
import javax.xml.validation.Schema;
import javax.xml.validation.ValidatorHandler;
import org.apache.xerces.xs.ItemPSVI;
import org.apache.xerces.xs.ElementPSVI;
import org.apache.xerces.xs.PSVIProvider;
import org.apache.xerces.xs.ShortList;
import org.apache.xerces.xs.XSObjectList;
import org.apache.xerces.xs.XSValue;
import org.apache.xerces.xs.XSTypeDefinition;
import org.apache.xerces.xs.XSComplexTypeDefinition;
import org.apache.xerces.xs.datatypes.XSQName;
import org.apache.xerces.xs.datatypes.XSDecimal;
import org.apache.xerces.xs.datatypes.XSFloat;
import org.apache.xerces.xs.datatypes.XSDouble;
import org.apache.xerces.xs.datatypes.XSDateTime;
import org.apache.xerces.xs.datatypes.ByteList;
import org.w3c.dom.ls.LSResourceResolver;
import org.xml.sax.ErrorHandler;
import org.xml.sax.Attributes;
import org.xml.sax.helpers.DefaultHandler;

final class TypedXmlObserver {
    private final Schema schema;

    TypedXmlObserver(Schema schema) { this.schema = schema; }
    private final IdentityHashMap<XSTypeDefinition, Integer> typeIds = new IdentityHashMap<>();
    private String typeName(XSTypeDefinition type) {
        if (type == null) { return null; }
        if (type.getName() == null) {
            return "anonymous:" + typeIds.computeIfAbsent(type, key -> typeIds.size());
        }
        return "{" + (type.getNamespace() == null ? "" : type.getNamespace()) + "}" + type.getName();
    }
    private static Object actual(Object value) {
        if (value == null || value instanceof String || value instanceof Boolean) { return value; }
        if (value instanceof XSQName) {
            javax.xml.namespace.QName name = ((XSQName) value).getJAXPQName();
            return Map.of("kind", "QName", "expanded", "{" + name.getNamespaceURI() + "}" + name.getLocalPart());
        }
        if (value instanceof XSDecimal) {
            return Map.of("kind", "decimal", "value", ((XSDecimal) value).getBigDecimal().stripTrailingZeros().toPlainString());
        }
        if (value instanceof XSFloat) {
            return Map.of("kind", "float", "bits", Integer.toUnsignedString(Float.floatToIntBits(((XSFloat) value).getValue())));
        }
        if (value instanceof XSDouble) {
            return Map.of("kind", "double", "bits", Long.toUnsignedString(Double.doubleToLongBits(((XSDouble) value).getValue())));
        }
        if (value instanceof ByteList) {
            return Map.of("kind", "binary", "base64", Base64.getEncoder().encodeToString(((ByteList) value).toByteArray()));
        }
        if (value instanceof XSDateTime) {
            // Exact Python calendar/duration predicates consume the assessed
            // lexical value; converting fractional seconds to double loses digits.
            return Map.of("kind", "calendar", "lexical", ((XSDateTime) value).getLexicalValue());
        }
        if (value instanceof List<?>) {
            List<Object> values = new ArrayList<>();
            for (Object item : (List<?>) value) { values.add(actual(item)); }
            return values;
        }
        throw new IllegalStateException("unsupported assessed value class: " + value.getClass().getName());
    }
    private Map<String, Object> psvi(ItemPSVI info) {
        Map<String, Object> row = new LinkedHashMap<>();
        if (info == null) { row.put("assessment", "absent"); return row; }
        row.put("attempted", info.getValidationAttempted());
        row.put("validity", info.getValidity());
        row.put("type", typeName(info.getTypeDefinition()));
        row.put("member", typeName(info.getMemberTypeDefinition()));
        XSValue value = info.getSchemaValue();
        row.put("value", value == null ? null : actual(value.getActualValue()));
        row.put("value_type", value == null ? null : value.getActualValueType());
        row.put("schema_specified", info.getIsSchemaSpecified());
        List<Object> members = new ArrayList<>();
        List<Object> itemTypes = new ArrayList<>();
        if (value != null) {
            XSObjectList definitions = value.getMemberTypeDefinitions();
            if (definitions != null) {
                for (int i = 0; i < definitions.getLength(); ++i) {
                    members.add(typeName((XSTypeDefinition) definitions.item(i)));
                }
            }
            ShortList kinds = value.getListValueTypes();
            if (kinds != null) {
                for (int i = 0; i < kinds.getLength(); ++i) { itemTypes.add(kinds.item(i)); }
            }
        }
        row.put("list_members", members);
        row.put("list_types", itemTypes);
        if (info instanceof ElementPSVI) { row.put("nil", ((ElementPSVI) info).getNil()); }
        XSTypeDefinition type = info.getTypeDefinition();
        if (type instanceof XSComplexTypeDefinition) {
            row.put("content_type", ((XSComplexTypeDefinition) type).getContentType());
        }
        return row;
    }
    private enum Marker { NULL, OBJECT_END, ARRAY_END, COMMA, COLON }

    private static void push(Deque<Object> pending, Object value) {
        pending.push(value == null ? Marker.NULL : value);
    }

    private static String json(Object value) {
        StringBuilder text = new StringBuilder();
        Deque<Object> pending = new ArrayDeque<>();
        push(pending, value);
        final String hex = "0123456789abcdef";
        while (!pending.isEmpty()) {
            Object item = pending.pop();
            if (item instanceof Marker) {
                switch ((Marker) item) {
                    case NULL: text.append("null"); break;
                    case OBJECT_END: text.append('}'); break;
                    case ARRAY_END: text.append(']'); break;
                    case COMMA: text.append(','); break;
                    case COLON: text.append(':'); break;
                    default: throw new IllegalStateException("unknown JSON marker");
                }
            } else if (item instanceof Number || item instanceof Boolean) {
                text.append(item);
            } else if (item instanceof CharSequence) {
                text.append('"');
                CharSequence characters = (CharSequence) item;
                for (int index = 0; index < characters.length(); ++index) {
                    char c = characters.charAt(index);
                    if (c == '"' || c == '\\') { text.append('\\').append(c); }
                    else if (c < 32) {
                        text.append("\\u00").append(hex.charAt(c >>> 4)).append(hex.charAt(c & 15));
                    } else { text.append(c); }
                }
                text.append('"');
            } else if (item instanceof Map<?, ?>) {
                text.append('{');
                pending.push(Marker.OBJECT_END);
                List<Map.Entry<?, ?>> entries = new ArrayList<>(((Map<?, ?>) item).entrySet());
                for (int i = entries.size() - 1; i >= 0; --i) {
                    Map.Entry<?, ?> entry = entries.get(i);
                    if (i < entries.size() - 1) { pending.push(Marker.COMMA); }
                    push(pending, entry.getValue());
                    pending.push(Marker.COLON);
                    push(pending, entry.getKey());
                }
            } else if (item instanceof List<?>) {
                text.append('[');
                pending.push(Marker.ARRAY_END);
                List<?> entries = (List<?>) item;
                for (int i = entries.size() - 1; i >= 0; --i) {
                    if (i < entries.size() - 1) { pending.push(Marker.COMMA); }
                    push(pending, entries.get(i));
                }
            } else { throw new IllegalStateException("unsupported observation JSON value: " + item.getClass()); }
        }
        return text.toString();
    }
    private static final class Node {
        final Map<String, Object> data = new LinkedHashMap<>();
        final List<Object> content = new ArrayList<>();
        final Map<String, Object> attributes = new LinkedHashMap<>();
        final Map<String, String> namespaces = new TreeMap<>();
        Node(String name) {
            data.put("name", name); data.put("attributes", attributes); data.put("content", content);
            data.put("namespace_declarations", namespaces);
        }
        void text(char[] data, int start, int length) {
            if (length == 0) { return; }
            int last = content.size() - 1;
            if (last >= 0 && content.get(last) instanceof StringBuilder) {
                ((StringBuilder) content.get(last)).append(data, start, length);
            } else { content.add(new StringBuilder().append(data, start, length)); }
        }
    }
    String observe(SAXSource input, ErrorHandler diagnostics, LSResourceResolver resolver) throws Exception {
        ValidatorHandler handler = schema.newValidatorHandler();
        handler.setErrorHandler(diagnostics);
        handler.setResourceResolver(resolver);
        PSVIProvider provider = (PSVIProvider) handler;
        List<Object> roots = new ArrayList<>();
        Deque<Node> stack = new ArrayDeque<>();
        handler.setContentHandler(new DefaultHandler() {
            final Map<String, String> pendingNamespaces = new TreeMap<>();
            public void startPrefixMapping(String prefix, String uri) { pendingNamespaces.put(prefix, uri); }
            public void startElement(String uri, String local, String qname, Attributes attributes) {
                Node node = new Node("{" + uri + "}" + local);
                node.namespaces.putAll(pendingNamespaces);
                pendingNamespaces.clear();
                for (int i = 0; i < attributes.getLength(); ++i) {
                    Map<String, Object> attr = psvi(provider.getAttributePSVI(i));
                    attr.put("lexical", attributes.getValue(i));
                    node.attributes.put("{" + attributes.getURI(i) + "}" + attributes.getLocalName(i), attr);
                }
                if (stack.isEmpty()) { roots.add(node.data); } else { stack.peek().content.add(node.data); }
                stack.push(node);
            }
            public void characters(char[] text, int start, int length) { stack.peek().text(text, start, length); }
            public void ignorableWhitespace(char[] text, int start, int length) { characters(text, start, length); }
            public void endElement(String uri, String local, String qname) { stack.pop().data.put("psvi", psvi(provider.getElementPSVI())); }
        });
        input.getXMLReader().setContentHandler(handler);
        input.getXMLReader().parse(input.getInputSource());
        if (!stack.isEmpty() || roots.size() != 1) {
            throw new IllegalStateException("incomplete typed XML observation");
        }
        return json(Map.of("format", 1, "root", roots.get(0)));
    }

}
