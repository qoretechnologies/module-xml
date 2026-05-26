# -*- mode: qore; indent-tabs-mode: nil -*-
#! Qore CDA document parsing and validation support

/*  CdaDocumentParser.qc Copyright 2026 Qore Technologies, s.r.o.

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

#! contains all public definitions in the CdaDataProvider module
public namespace CdaDataProvider {
#! CDA document identifier metadata
public hashdecl CdaIdentifierInfo {
    *string root;
    *string extension;
    *string assigning_authority_name;
}

#! CDA coded value metadata
public hashdecl CdaCodeInfo {
    *string code;
    *string code_system;
    *string code_system_name;
    *string display_name;
}

#! CDA patient metadata
public hashdecl CdaPatientInfo {
    hash<CdaIdentifierInfo> id;
    *string name;
    *string birth_time;
    *string administrative_gender_code;
}

#! CDA document metadata
public hashdecl CdaDocumentMetadata {
    hash<CdaIdentifierInfo> document_id;
    list<hash<CdaIdentifierInfo>> template_ids;
    hash<CdaCodeInfo> code;
    *string title;
    *string effective_time;
    hash<CdaCodeInfo> confidentiality_code;
    *string language_code;
    hash<CdaIdentifierInfo> set_id;
    *string version_number;
    hash<CdaPatientInfo> patient;
}

#! CDA document section summary
public hashdecl CdaSectionInfo {
    int index;
    hash<CdaCodeInfo> code;
    *string title;
    *string text;
}

#! CDA parse response hash
public hashdecl CdaParseDocumentResponse {
    *bool valid;
    hash<CdaDocumentMetadata> metadata;
    list<hash<CdaSectionInfo>> sections;
    hash<auto> data;
}

#! CDA validation response hash
public hashdecl CdaValidateDocumentResponse {
    bool valid;
    hash<CdaDocumentMetadata> metadata;
}

#! CDA XML parser, metadata extractor, and XSD validator
public class CdaDocumentParser {
    #! Parses a CDA XML document and optionally validates it with an XSD
    public static hash<CdaParseDocumentResponse> parse(string xml, *hash<auto> opts = NOTHING) {
        bool validate = opts.validate ?? False;
        if (validate) {
            validateXml(xml, opts);
        }

        hash<auto> data = parse_xml(xml, XPF_PRESERVE_ORDER);
        hash<auto> root = getClinicalDocumentRoot(data);
        return <CdaParseDocumentResponse>{
            "valid": validate ? True : NOTHING,
            "metadata": extractMetadata(root),
            "sections": extractSections(root),
            "data": data,
        };
    }

    #! Validates a CDA XML document and returns metadata when validation succeeds
    public static hash<CdaValidateDocumentResponse> validate(string xml, hash<auto> opts) {
        validateXml(xml, opts + {"validate": True});
        hash<auto> data = parse_xml(xml, XPF_PRESERVE_ORDER);
        return <CdaValidateDocumentResponse>{
            "valid": True,
            "metadata": extractMetadata(getClinicalDocumentRoot(data)),
        };
    }

    #! Validates the given XML with either file-based or inline XSD configuration
    public static validateXml(string xml, *hash<auto> opts = NOTHING) {
        *string xsd_path = opts.xsd_path;
        *string xsd = opts.xsd;
        if (xsd_path && xsd) {
            throw "CDA-VALIDATION-ERROR", "provide only one of `xsd_path` or `xsd`";
        }
        if (!xsd_path && !xsd) {
            throw "CDA-VALIDATION-ERROR", "`xsd_path` or `xsd` is required when CDA validation is enabled";
        }

        XmlDoc doc(xml);
        if (xsd_path) {
            doc.validateSchemaFile(xsd_path);
        } else {
            doc.validateSchema(xsd);
        }
    }

    private static hash<auto> getClinicalDocumentRoot(hash<auto> data) {
        if (data.size() != 1) {
            throw "CDA-PARSE-ERROR", "CDA XML must have exactly one document element";
        }
        string key = data.firstKey();
        if (localName(key) != "ClinicalDocument") {
            throw "CDA-PARSE-ERROR", sprintf("expected CDA ClinicalDocument root element, got %y", key);
        }
        return cast<hash<auto>>(data{key});
    }

    private static hash<CdaDocumentMetadata> extractMetadata(hash<auto> root) {
        hash<auto> id = firstChild(root, "id") ?? {};
        hash<auto> code = firstChild(root, "code") ?? {};
        hash<auto> effective_time = firstChild(root, "effectiveTime") ?? {};
        hash<auto> confidentiality = firstChild(root, "confidentialityCode") ?? {};
        hash<auto> language = firstChild(root, "languageCode") ?? {};
        hash<auto> set_id = firstChild(root, "setId") ?? {};
        hash<auto> version = firstChild(root, "versionNumber") ?? {};

        return <CdaDocumentMetadata>{
            "document_id": identifierInfo(id),
            "template_ids": (map identifierInfo($1), childList(root, "templateId")),
            "code": codeInfo(code),
            "title": nodeText(firstChildValue(root, "title")),
            "effective_time": attr(effective_time, "value"),
            "confidentiality_code": codeInfo(confidentiality),
            "language_code": attr(language, "code"),
            "set_id": identifierInfo(set_id),
            "version_number": attr(version, "value"),
            "patient": patientInfo(root),
        };
    }

    private static hash<CdaPatientInfo> patientInfo(hash<auto> root) {
        hash<auto> patient_role = firstChild(firstChild(root, "recordTarget") ?? {}, "patientRole") ?? {};
        hash<auto> patient = firstChild(patient_role, "patient") ?? {};
        hash<auto> gender = firstChild(patient, "administrativeGenderCode") ?? {};
        hash<auto> birth = firstChild(patient, "birthTime") ?? {};
        return <CdaPatientInfo>{
            "id": identifierInfo(firstChild(patient_role, "id") ?? {}),
            "name": compactText(firstChild(patient, "name")),
            "birth_time": attr(birth, "value"),
            "administrative_gender_code": attr(gender, "code"),
        };
    }

    private static list<hash<CdaSectionInfo>> extractSections(hash<auto> root) {
        list<hash<auto>> raw_sections = collectSections(root);
        list<hash<CdaSectionInfo>> rv = ();
        int index = 0;
        foreach hash<auto> section in (raw_sections) {
            ++index;
            push rv, <CdaSectionInfo>{
                "index": index,
                "code": codeInfo(firstChild(section, "code") ?? {}),
                "title": nodeText(firstChildValue(section, "title")),
                "text": compactText(firstChildValue(section, "text")),
            };
        }
        return rv;
    }

    private static list<hash<auto>> collectSections(hash<auto> node) {
        list<hash<auto>> sections = ();
        foreach string key in (keys node) {
            if (key =~ /^\^/) {
                continue;
            }
            auto val = node{key};
            foreach hash<auto> child in (asHashList(val)) {
                if (localName(key) == "section") {
                    push sections, child;
                }
                sections += collectSections(child);
            }
        }
        return sections;
    }

    private static hash<CdaIdentifierInfo> identifierInfo(hash<auto> node) {
        return <CdaIdentifierInfo>{
            "root": attr(node, "root"),
            "extension": attr(node, "extension"),
            "assigning_authority_name": attr(node, "assigningAuthorityName"),
        };
    }

    private static hash<CdaCodeInfo> codeInfo(hash<auto> node) {
        return <CdaCodeInfo>{
            "code": attr(node, "code"),
            "code_system": attr(node, "codeSystem"),
            "code_system_name": attr(node, "codeSystemName"),
            "display_name": attr(node, "displayName"),
        };
    }

    private static *hash<auto> firstChild(hash<auto> node, string child_name) {
        foreach string key in (keys node) {
            if (localName(key) == child_name) {
                list<hash<auto>> children = asHashList(node{key});
                return children ? children[0] : NOTHING;
            }
        }
        return NOTHING;
    }

    private static auto firstChildValue(hash<auto> node, string child_name) {
        foreach string key in (keys node) {
            if (localName(key) == child_name) {
                return node{key};
            }
        }
        return NOTHING;
    }

    private static list<hash<auto>> childList(hash<auto> node, string child_name) {
        list<hash<auto>> rv = ();
        foreach string key in (keys node) {
            if (localName(key) == child_name) {
                rv += asHashList(node{key});
            }
        }
        return rv;
    }

    private static list<hash<auto>> asHashList(auto val) {
        list<hash<auto>> rv = ();
        if (val === NOTHING) {
            return rv;
        }
        if (val.typeCode() == NT_HASH) {
            push rv, cast<hash<auto>>(val);
        } else if (val.typeCode() == NT_LIST) {
            foreach auto item in (val) {
                if (item.typeCode() == NT_HASH) {
                    push rv, cast<hash<auto>>(item);
                }
            }
        }
        return rv;
    }

    private static *string attr(hash<auto> node, string name) {
        if (!exists node."^attributes^") {
            return NOTHING;
        }
        return node."^attributes^"{name};
    }

    private static *string nodeText(auto val) {
        if (val === NOTHING) {
            return NOTHING;
        }
        string text = compactText(val);
        return text ? text : NOTHING;
    }

    private static string compactText(auto val) {
        string text = trim(textValue(val));
        return regex_subst(text, "\\s+", " ", RE_Global);
    }

    private static string textValue(auto val) {
        if (val === NOTHING) {
            return "";
        }
        switch (val.typeCode()) {
            case NT_STRING:
                return val;
            case NT_INT:
            case NT_FLOAT:
            case NT_BOOLEAN:
                return string(val);
            case NT_LIST:
                return joinTextList(val);
            case NT_HASH:
                return textValueFromHash(cast<hash<auto>>(val));
        }
        return "";
    }

    private static string joinTextList(list val) {
        list<string> parts = ();
        foreach auto item in (val) {
            string text = textValue(item);
            if (text) {
                push parts, text;
            }
        }
        return parts.join(" ");
    }

    private static string textValueFromHash(hash<auto> val) {
        list<string> parts = ();
        if (val."^value^") {
            push parts, string(val."^value^");
        }
        foreach string key in (keys val) {
            if (key =~ /^\^/) {
                continue;
            }
            string text = textValue(val{key});
            if (text) {
                push parts, text;
            }
        }
        return parts.join(" ");
    }

    private static string localName(string key) {
        string k = regex_subst(key, "\\^.*$", "");
        if (!k) {
            return "";
        }
        list<string> parts = k.split(":");
        return parts[parts.size() - 1];
    }
}
}
