// Copyright (C) 2026 Qore Technologies, s.r.o.
// Internal offline XSD 1.0 worker; invoked by independent.py with a pinned Xerces JAR.

import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.sax.SAXSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;
import org.apache.xerces.dom.DOMInputImpl;
import org.apache.xerces.parsers.SAXParser;
import org.w3c.dom.ls.LSResourceResolver;
import org.xml.sax.ErrorHandler;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;

public final class XsdOracle {
    private static String normalizeAnyURI(String value) {
        StringBuilder normalized = new StringBuilder(value.length());
        boolean space = false;
        for (int index = 0; index < value.length(); ++index) {
            char c = value.charAt(index);
            if (c == ' ' || c == '\t' || c == '\r' || c == '\n') {
                space = normalized.length() != 0;
            } else {
                if (space) {
                    normalized.append(' ');
                    space = false;
                }
                normalized.append(c);
            }
        }
        return normalized.toString();
    }

    // XSD 1.0 anyURI uses the XLink 1.0 UTF-8 escaping procedure. Existing
    // percent escapes and URI delimiters retain their meaning.
    private static URI uri(String value) {
        StringBuilder escaped = new StringBuilder(value.length());
        final String hex = "0123456789ABCDEF";
        for (byte octet : value.getBytes(StandardCharsets.UTF_8)) {
            int c = octet & 255;
            if (c <= 32 || c >= 127 || "\"<>\\^`{|}".indexOf(c) >= 0) {
                escaped.append('%').append(hex.charAt(c >>> 4)).append(hex.charAt(c & 15));
            } else {
                escaped.append((char) c);
            }
        }
        return URI.create(escaped.toString());
    }

    // RFC 3986 section 5.2.4. URI.normalize() collapses empty path segments;
    // those segments can identify a different resource and must be preserved.
    private static String removeDotSegments(String path) {
        StringBuilder result = new StringBuilder(path.length());
        int read = 0;
        while (read < path.length()) {
            if (path.startsWith("../", read)) {
                read += 3;
            } else if (path.startsWith("./", read)) {
                read += 2;
            } else if (path.startsWith("/./", read)) {
                read += 2;
            } else if (path.startsWith("/.", read) && read + 2 == path.length()) {
                result.append('/');
                break;
            } else if (path.startsWith("/../", read)
                       || (path.startsWith("/..", read) && read + 3 == path.length())) {
                read += 3;
                int slash = result.lastIndexOf("/");
                result.setLength(Math.max(slash, 0));
                if (read == path.length()) {
                    result.append('/');
                    break;
                }
            } else if ((path.startsWith(".", read) && read + 1 == path.length())
                       || (path.startsWith("..", read) && read + 2 == path.length())) {
                break;
            } else {
                int next = path.indexOf('/', read + (path.charAt(read) == '/' ? 1 : 0));
                if (next < 0) {
                    next = path.length();
                }
                result.append(path, read, next);
                read = next;
            }
        }
        return result.toString();
    }

    private static boolean hasAuthority(URI value) {
        return value.getRawSchemeSpecificPart().startsWith("//");
    }

    // Resolve raw components per RFC 3986 section 5.2. java.net.URI.resolve()
    // uses older rules for empty/query references, excess parents and slashes.
    private static URI resolve(String reference, String base) {
        URI ref = uri(reference);
        if (ref.isOpaque()) {
            return ref;
        }
        URI parent = base == null ? null : uri(base);
        String scheme = ref.getScheme();
        String authority = ref.getRawAuthority();
        boolean authorityPresent = hasAuthority(ref);
        String path = ref.getRawPath();
        String query = ref.getRawQuery();
        if (scheme == null && parent != null) {
            scheme = parent.getScheme();
            if (!authorityPresent) {
                authority = parent.getRawAuthority();
                authorityPresent = hasAuthority(parent);
                String parentPath = parent.getRawPath() == null ? "" : parent.getRawPath();
                if (path.isEmpty()) {
                    path = parentPath;
                    if (query == null) {
                        query = parent.getRawQuery();
                    }
                } else if (!path.startsWith("/")) {
                    path = (authorityPresent && parentPath.isEmpty() ? "/"
                            : parentPath.substring(0, parentPath.lastIndexOf('/') + 1)) + path;
                }
            }
        }
        StringBuilder result = new StringBuilder();
        if (scheme != null) {
            result.append(scheme).append(':');
        }
        if (authorityPresent) {
            result.append("//");
            if (authority != null) {
                result.append(authority);
            }
        }
        result.append(removeDotSegments(path));
        if (query != null) {
            result.append('?').append(query);
        }
        if (ref.getRawFragment() != null) {
            result.append('#').append(ref.getRawFragment());
        }
        return URI.create(result.toString());
    }

    private static final class Diagnostics implements ErrorHandler {
        private final List<String> warnings = new ArrayList<>();

        public void warning(SAXParseException error) {
            warnings.add(encoded(error.toString()));
        }
        public void error(SAXParseException error) throws SAXException {
            throw error;
        }
        public void fatalError(SAXParseException error) throws SAXException {
            throw error;
        }
    }

    private static SAXSource source(byte[] data, String uri, Diagnostics diagnostics) throws SAXException {
        SAXParser parser = new SAXParser();
        parser.setFeature("http://xml.org/sax/features/namespaces", true);
        parser.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        parser.setFeature("http://xml.org/sax/features/external-general-entities", false);
        parser.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
        parser.setEntityResolver((publicId, systemId) -> {
            throw new SAXException("external entity unavailable offline: " + systemId);
        });
        parser.setErrorHandler(diagnostics);
        InputSource input = new InputSource(new ByteArrayInputStream(data));
        input.setSystemId(uri);
        return new SAXSource(parser, input);
    }

    private static String encoded(String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    // Standalone ENTITY tests need the containing document's unparsed entities.
    // DOM preserves first declarations, including parsed declarations absent
    // from the JAXP ValidatorHandler's unparsedEntityDecl-only view.
    private static DOMSource entitySource(byte[] data, Diagnostics diagnostics) throws Exception {
        DocumentBuilderFactory factory = new org.apache.xerces.jaxp.DocumentBuilderFactoryImpl();
        factory.setNamespaceAware(true);
        factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
        factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
        factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
        DocumentBuilder builder = factory.newDocumentBuilder();
        builder.setErrorHandler(diagnostics);
        builder.setEntityResolver((publicId, systemId) -> {
            throw new SAXException("external entity unavailable offline: " + systemId);
        });
        return new DOMSource(builder.parse(new ByteArrayInputStream(data), "urn:wsdl-interop:entity-payload"));
    }

    private static void result(String stage, String id, String status, String error, Diagnostics diagnostics) {
        System.out.println(stage + "\t" + id + "\t" + status + "\t" + encoded(error)
                           + "\t" + String.join(",", diagnostics.warnings));
    }

    public static void main(String[] args) throws Exception {
        run(args, false);
    }

    static void run(String[] args, boolean entityDocuments) throws Exception {
        boolean typed = !entityDocuments && args.length == 2 && args[0].equals("--typed");
        if (args.length != 1 && !typed) {
            throw new IllegalArgumentException("XsdOracle [--typed] MANIFEST.tsv");
        }
        Path manifest = Path.of(args[typed ? 1 : 0]);
        if (Files.size(manifest) > 128L * 1024 * 1024) {
            throw new IllegalArgumentException("oracle manifest exceeds 128 MiB");
        }
        Map<URI, byte[]> resources = new HashMap<>();
        Map<String, Schema> schemas = new HashMap<>();
        Map<String, TypedXmlObserver> observers = new HashMap<>();
        Set<String> documents = new HashSet<>();
        LSResourceResolver resolver = (type, namespace, publicId, systemId, baseURI) -> {
            if (systemId == null) {
                // schemaLocation is optional. No location means no resource to fetch;
                // let the schema processor resolve known components or report unresolved refs.
                return null;
            }
            URI location = resolve(normalizeAnyURI(systemId), baseURI);
            byte[] data = resources.get(location);
            if (data == null) {
                throw new IllegalArgumentException("resource unavailable offline: " + location);
            }
            DOMInputImpl input = new DOMInputImpl();
            input.setSystemId(location.toASCIIString());
            input.setBaseURI(location.toASCIIString());
            input.setByteStream(new ByteArrayInputStream(data));
            return input;
        };
        System.out.println("version\t" + encoded(org.apache.xerces.impl.Version.getVersion())
                           + "\t" + encoded(System.getProperty("java.runtime.version")));
        try (BufferedReader reader = Files.newBufferedReader(manifest, StandardCharsets.UTF_8)) {
            String line;
            boolean started = false;
            while ((line = reader.readLine()) != null) {
                String[] fields = line.split("\t", -1);
                if (fields.length == 3 && fields[0].equals("R") && !started) {
                    if (resources.putIfAbsent(resolve(fields[1], null), Base64.getDecoder().decode(fields[2])) != null) {
                        throw new IllegalArgumentException("duplicate resource: " + fields[1]);
                    }
                    continue;
                }
                started = true;
                if (fields.length != 4) {
                    throw new IllegalArgumentException("malformed oracle manifest row");
                }
                byte[] data = Base64.getDecoder().decode(fields[3]);
                Diagnostics diagnostics = new Diagnostics();
                if (fields[0].equals("S")) {
                    if (schemas.containsKey(fields[1])) {
                        throw new IllegalArgumentException("duplicate schema: " + fields[1]);
                    }
                    schemas.put(fields[1], null);
                    SchemaFactory factory = new org.apache.xerces.jaxp.validation.XMLSchemaFactory();
                    factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
                    factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
                    factory.setResourceResolver(resolver);
                    factory.setErrorHandler(diagnostics);
                    try {
                        schemas.put(fields[1], factory.newSchema(source(data, resolve(fields[2], null).toASCIIString(),
                                                                        diagnostics)));
                        if (typed) { observers.put(fields[1], new TypedXmlObserver(schemas.get(fields[1]))); }
                        result("S", fields[1], "valid", "", diagnostics);
                    } catch (SAXException | IllegalArgumentException error) {
                        result("S", fields[1], "invalid", error.toString(), diagnostics);
                    }
                } else if (fields[0].equals("V")) {
                    if (!schemas.containsKey(fields[1]) || !documents.add(fields[2])) {
                        throw new IllegalArgumentException("unknown schema or duplicate document: " + fields[2]);
                    }
                    Schema schema = schemas.get(fields[1]);
                    if (schema == null) {
                        result("V", fields[2], "unreachable", "schema compilation failed: " + fields[1], diagnostics);
                        continue;
                    }
                    Validator validator = schema.newValidator();
                    validator.setResourceResolver(resolver);
                    validator.setErrorHandler(diagnostics);
                    try {
                        if (entityDocuments) {
                            validator.validate(entitySource(data, diagnostics));
                        } else if (typed) {
                            String observation = observers.get(fields[1]).observe(
                                source(data, "urn:wsdl-interop:payload", diagnostics), diagnostics, resolver);
                            System.out.println("T\t" + fields[2] + "\t" + encoded(observation));
                        } else {
                            validator.validate(source(data, "urn:wsdl-interop:payload", diagnostics));
                        }
                        result("V", fields[2], "valid", "", diagnostics);
                    } catch (SAXException | IllegalArgumentException error) {
                        result("V", fields[2], "invalid", error.toString(), diagnostics);
                    }
                } else {
                    throw new IllegalArgumentException("unknown oracle operation: " + fields[0]);
                }
            }
        }
    }
}
