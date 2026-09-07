// Copyright (C) 2026 Qore Technologies, s.r.o.
// Internal offline XSD 1.0 worker; invoked by independent.py with a pinned Xerces JAR.

import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import javax.xml.XMLConstants;
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
    private static final ErrorHandler ERRORS = new ErrorHandler() {
        public void warning(SAXParseException error) throws SAXException {
            throw error;
        }
        public void error(SAXParseException error) throws SAXException {
            throw error;
        }
        public void fatalError(SAXParseException error) throws SAXException {
            throw error;
        }
    };

    private static SAXSource source(byte[] data, String uri) throws SAXException {
        SAXParser parser = new SAXParser();
        parser.setFeature("http://xml.org/sax/features/namespaces", true);
        parser.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        parser.setFeature("http://xml.org/sax/features/external-general-entities", false);
        parser.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
        parser.setEntityResolver((publicId, systemId) -> {
            throw new SAXException("external entity unavailable offline: " + systemId);
        });
        parser.setErrorHandler(ERRORS);
        InputSource input = new InputSource(new ByteArrayInputStream(data));
        input.setSystemId(uri);
        return new SAXSource(parser, input);
    }

    private static String encoded(String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    private static void result(String stage, String id, String status, String error) {
        System.out.println(stage + "\t" + id + "\t" + status + "\t" + encoded(error));
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("XsdOracle MANIFEST.tsv");
        }
        Path manifest = Path.of(args[0]);
        if (Files.size(manifest) > 128L * 1024 * 1024) {
            throw new IllegalArgumentException("oracle manifest exceeds 128 MiB");
        }
        Map<String, byte[]> resources = new HashMap<>();
        Map<String, Schema> schemas = new HashMap<>();
        Set<String> documents = new HashSet<>();
        LSResourceResolver resolver = (type, namespace, publicId, systemId, baseURI) -> {
            if (systemId == null) {
                // schemaLocation is optional. No location means no resource to fetch;
                // let the schema processor resolve known components or report unresolved refs.
                return null;
            }
            URI location = URI.create(systemId);
            String uri = (baseURI == null ? location : URI.create(baseURI).resolve(location)).toString();
            byte[] data = resources.get(uri);
            if (data == null) {
                throw new IllegalArgumentException("resource unavailable offline: " + uri);
            }
            DOMInputImpl input = new DOMInputImpl();
            input.setSystemId(uri);
            input.setBaseURI(uri);
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
                    if (resources.putIfAbsent(fields[1], Base64.getDecoder().decode(fields[2])) != null) {
                        throw new IllegalArgumentException("duplicate resource: " + fields[1]);
                    }
                    continue;
                }
                started = true;
                if (fields.length != 4) {
                    throw new IllegalArgumentException("malformed oracle manifest row");
                }
                byte[] data = Base64.getDecoder().decode(fields[3]);
                if (fields[0].equals("S")) {
                    if (schemas.containsKey(fields[1])) {
                        throw new IllegalArgumentException("duplicate schema: " + fields[1]);
                    }
                    schemas.put(fields[1], null);
                    SchemaFactory factory = new org.apache.xerces.jaxp.validation.XMLSchemaFactory();
                    factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
                    factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
                    factory.setResourceResolver(resolver);
                    factory.setErrorHandler(ERRORS);
                    try {
                        schemas.put(fields[1], factory.newSchema(source(data, fields[2])));
                        result("S", fields[1], "valid", "");
                    } catch (SAXException | IllegalArgumentException error) {
                        result("S", fields[1], "invalid", error.toString());
                    }
                } else if (fields[0].equals("V")) {
                    if (!schemas.containsKey(fields[1]) || !documents.add(fields[2])) {
                        throw new IllegalArgumentException("unknown schema or duplicate document: " + fields[2]);
                    }
                    Schema schema = schemas.get(fields[1]);
                    if (schema == null) {
                        result("V", fields[2], "unreachable", "schema compilation failed: " + fields[1]);
                        continue;
                    }
                    Validator validator = schema.newValidator();
                    validator.setResourceResolver(resolver);
                    validator.setErrorHandler(ERRORS);
                    try {
                        validator.validate(source(data, "urn:wsdl-interop:payload"));
                        result("V", fields[2], "valid", "");
                    } catch (SAXException | IllegalArgumentException error) {
                        result("V", fields[2], "invalid", error.toString());
                    }
                } else {
                    throw new IllegalArgumentException("unknown oracle operation: " + fields[0]);
                }
            }
        }
    }
}
