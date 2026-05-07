# -*- mode: qore; indent-tabs-mode: nil -*-
#! Qore CargoXmlDataProvider class definition

/** CargoXmlDataProvider.qc Copyright 2026 Qore Technologies, s.r.o.

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
*/

#! contains all public definitions in the CargoXmlDataProvider module
public namespace CargoXmlDataProvider {
#! Information about a discovered top-level XSD message element
public hashdecl CargoXmlMessageInfo {
    #! the local name of the message element (e.g. \c "CrossIndustryDespatchAdvice")
    string name;
    #! the target namespace URI of the schema declaring the element
    string namespace;
    #! the absolute path to the XSD file declaring the element (used for libxml2 validation)
    string xsd_file;
}

#! the cargo XML data provider
/** Walks a directory of XSDs at construction time, indexes the top-level message elements
    declared in each schema, and exposes one child @ref CargoXmlMessageDataProvider per
    discovered message.

    The default schema directory points at the bundled UN/CEFACT D25A Cross-Industry
    message schemas; override the \c schema_dir option to point at the IATA Cargo-XML
    toolkit or any other XSD package.
*/
public class CargoXmlDataProvider inherits AbstractDataProvider {
    public {
        #! the schema directory in use
        string schema_dir;

        #! catalog of discovered messages keyed by \c "{namespace}name"
        hash<string, hash<CargoXmlMessageInfo>> messages;

        #! provider info
        const ProviderInfo = <DataProviderInfo>{
            "type": "CargoXmlDataProvider",
            "supports_read": False,
            "supports_create": False,
            "supports_update": False,
            "supports_upsert": False,
            "supports_delete": False,
            "supports_native_search": False,
            "supports_bulk_create": False,
            "supports_bulk_upsert": False,
            "supports_children": True,
            "constructor_options": ConstructorOptions,
            "search_options": NOTHING,
            "create_options": NOTHING,
            "upsert_options": NOTHING,
            "transaction_management": False,
            "children_can_support_apis": True,
        };

        #! constructor options
        const ConstructorOptions = {
            "schema_dir": <DataProviderOptionInfo>{
                "display_name": "Schema Directory",
                "short_desc": "The directory containing the XSD message schemas",
                "type": AbstractDataProviderType::get(StringType),
                "desc": "Absolute path to the directory containing the XSD message schemas. "
                    "When omitted, the bundled UN/CEFACT D25A `data/standard/` directory is used. "
                    "Override to point at the IATA Cargo-XML toolkit or any other XSD package; "
                    "the directory is walked recursively for `.xsd` files.",
            },
            "schema_subdir": <DataProviderOptionInfo>{
                "display_name": "Schema Subdirectory",
                "short_desc": "Subdirectory under schema_dir containing message-level XSDs",
                "type": AbstractDataProviderType::get(StringType),
                "desc": "Subdirectory under `schema_dir` to scan for top-level message XSDs. "
                    "For UN/CEFACT this is `data/standard`. Set to an empty string to scan "
                    "`schema_dir` itself.",
                "default_value": "data/standard",
            },
        };

        #! the bundled UN/CEFACT D25A schema directory
        const BundledSchemaDir = get_script_dir() + "/schemas/uncefact-D25A";
    }

    #! creates the object
    constructor(*hash<auto> options) {
        *hash<auto> copts = checkOptions("CONSTRUCTOR-ERROR", ConstructorOptions, options);
        schema_dir = copts.schema_dir ?? BundledSchemaDir;
        if (!is_dir(schema_dir)) {
            throw "CONSTRUCTOR-ERROR", sprintf("schema_dir %y is not a directory", schema_dir);
        }
        string subdir = copts.schema_subdir ?? "data/standard";
        string scan_dir = subdir ? schema_dir + DirSep + subdir : schema_dir;
        if (!is_dir(scan_dir)) {
            throw "CONSTRUCTOR-ERROR", sprintf("scan path %y (schema_dir %y + schema_subdir %y) is not a "
                "directory", scan_dir, schema_dir, subdir);
        }
        messages = discoverMessages(scan_dir);
    }

    #! returns the data provider name
    string getName() {
        return "cargo-xml";
    }

    #! returns the data provider description
    *string getDesc() {
        return sprintf("Cargo XML data provider with %d discovered messages from %y", messages.size(),
            schema_dir);
    }

    #! returns information about discovered messages keyed by \c "{namespace}name"
    hash<string, hash<CargoXmlMessageInfo>> getMessages() {
        return messages;
    }

    #! returns the names of child providers (one per discovered message)
    /** @return a list of message identifiers in James-Clark notation
        (\c "{namespace_uri}local_name") so that messages with the same local name in
        different namespaces (which occur in real-world packages) remain distinct
    */
    private *list<string> getChildProviderNamesImpl() {
        return keys messages;
    }

    #! returns the child provider for the named message, or @ref nothing if unknown
    private *AbstractDataProvider getChildProviderImpl(string name) {
        *hash<CargoXmlMessageInfo> mi = messages{name};
        if (!mi) {
            return;
        }
        return new CargoXmlMessageDataProvider(mi);
    }

    private hash<DataProviderInfo> getStaticInfoImpl() {
        return ProviderInfo;
    }

    #! Walks \a dir for \c .xsd files and indexes top-level <xsd:element> declarations.
    /** Lightweight (\c parse_xml only); does not load the full type tree. The full XSD,
        including all transitive imports, is parsed lazily by the per-message provider
        when the caller asks for record-type introspection.
    */
    private hash<string, hash<CargoXmlMessageInfo>> discoverMessages(string dir) {
        hash<string, hash<CargoXmlMessageInfo>> rv;
        Dir d();
        d.chdir(dir);
        list<string> files = sort(d.listFiles("\\.xsd$"));
        foreach string f in (files) {
            string path = dir + DirSep + f;
            try {
                File fh();
                fh.open2(path, O_RDONLY);
                hash<auto> doc = parse_xml(fh.read(-1));
                if (doc.size() != 1) {
                    continue;
                }
                hash<auto> root = doc{doc.firstKey()};
                *string tns = root."^attributes^".targetNamespace;
                if (!tns) {
                    continue;
                }
                # element children: under different prefixes ("xsd:element", "xs:element", "element")
                # parse_xml strips known XSD-namespace prefixes inconsistently across versions;
                # accept any of these forms for robustness
                auto el_nodes;
                foreach string k in (("xsd:element", "xs:element", "element")) {
                    if (exists root{k}) {
                        el_nodes = root{k};
                        break;
                    }
                }
                if (!exists el_nodes) {
                    continue;
                }
                foreach hash<auto> el in (el_nodes) {
                    *string local = el."^attributes^".name;
                    if (!local) {
                        continue;
                    }
                    string qname = make_qname(tns, local);
                    rv{qname} = <CargoXmlMessageInfo>{
                        "name": local,
                        "namespace": tns,
                        "xsd_file": path,
                    };
                }
            } catch (hash<ExceptionInfo> ex) {
                # skip unparseable files; the data provider stays usable for the rest
                continue;
            }
        }
        return rv;
    }
}
}
