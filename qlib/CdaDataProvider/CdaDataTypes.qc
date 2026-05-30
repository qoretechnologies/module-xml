# -*- mode: qore; indent-tabs-mode: nil -*-
#! Qore CdaDataProvider data type metadata

/*  CdaDataTypes.qc Copyright 2026 Qore Technologies, s.r.o.

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
#! DataProvider metadata for CDA II-style identifiers
public class CdaIdentifierDataType inherits HashDataType {
    private {
        const Fields = {
            "root": {
                "display_name": "Root",
                "short_desc": "Identifier root",
                "desc": "The CDA identifier root value.",
                "type": StringOrNothingType,
            },
            "extension": {
                "display_name": "Extension",
                "short_desc": "Identifier extension",
                "desc": "The CDA identifier extension value, when present.",
                "type": StringOrNothingType,
            },
            "assigning_authority_name": {
                "display_name": "Assigning Authority",
                "short_desc": "Assigning authority name",
                "desc": "The assigning authority name, when present.",
                "type": StringOrNothingType,
            },
        };
    }

    constructor() : HashDataType("CdaIdentifier") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA identifier metadata type
public const CdaIdentifierDataType = new CdaIdentifierDataType();

#! DataProvider metadata for CDA coded values
public class CdaCodeDataType inherits HashDataType {
    private {
        const Fields = {
            "code": {
                "display_name": "Code",
                "short_desc": "Code value",
                "desc": "The coded value.",
                "type": StringOrNothingType,
            },
            "code_system": {
                "display_name": "Code System",
                "short_desc": "Code system identifier",
                "desc": "The code system identifier.",
                "type": StringOrNothingType,
            },
            "code_system_name": {
                "display_name": "Code System Name",
                "short_desc": "Code system name",
                "desc": "The human-readable code system name, when present.",
                "type": StringOrNothingType,
            },
            "display_name": {
                "display_name": "Display Name",
                "short_desc": "Code display name",
                "desc": "The human-readable code display name, when present.",
                "type": StringOrNothingType,
            },
        };
    }

    constructor() : HashDataType("CdaCode") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA code metadata type
public const CdaCodeDataType = new CdaCodeDataType();

#! DataProvider metadata for CDA patient summaries
public class CdaPatientDataType inherits HashDataType {
    private {
        const Fields = {
            "id": {
                "display_name": "Patient ID",
                "short_desc": "Patient identifier",
                "desc": "The patient identifier extracted from `recordTarget/patientRole/id`.",
                "type": CdaIdentifierDataType,
            },
            "name": {
                "display_name": "Patient Name",
                "short_desc": "Patient display name",
                "desc": "A compact patient name assembled from the CDA name elements.",
                "type": StringOrNothingType,
            },
            "birth_time": {
                "display_name": "Birth Time",
                "short_desc": "Patient birth time",
                "desc": "The CDA `birthTime/@value`, when present.",
                "type": StringOrNothingType,
            },
            "administrative_gender_code": {
                "display_name": "Administrative Gender",
                "short_desc": "Administrative gender code",
                "desc": "The CDA `administrativeGenderCode/@code`, when present.",
                "type": StringOrNothingType,
            },
        };
    }

    constructor() : HashDataType("CdaPatient") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA patient metadata type
public const CdaPatientDataType = new CdaPatientDataType();

#! DataProvider metadata for CDA organizations
public class CdaOrganizationDataType inherits HashDataType {
    private {
        const Fields = {
            "id": {
                "display_name": "Organization ID",
                "short_desc": "Organization identifier",
                "desc": "The CDA organization identifier.",
                "type": CdaIdentifierDataType,
            },
            "name": {
                "display_name": "Organization Name",
                "short_desc": "Organization name",
                "desc": "The CDA organization name, when present.",
                "type": StringOrNothingType,
            },
        };
    }

    constructor() : HashDataType("CdaOrganization") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA organization metadata type
public const CdaOrganizationDataType = new CdaOrganizationDataType();

#! DataProvider metadata for CDA authors
public class CdaAuthorDataType inherits HashDataType {
    private {
        const Fields = {
            "time": {
                "display_name": "Time",
                "short_desc": "Author time",
                "desc": "The CDA author `time/@value`, when present.",
                "type": StringOrNothingType,
            },
            "id": {
                "display_name": "Author ID",
                "short_desc": "Author identifier",
                "desc": "The CDA author identifier.",
                "type": CdaIdentifierDataType,
            },
            "name": {
                "display_name": "Author Name",
                "short_desc": "Author display name",
                "desc": "A compact author name assembled from CDA name elements.",
                "type": StringOrNothingType,
            },
            "represented_organization": {
                "display_name": "Represented Organization",
                "short_desc": "Represented organization",
                "desc": "The organization represented by the author, when present.",
                "type": CdaOrganizationDataType,
            },
        };
    }

    constructor() : HashDataType("CdaAuthor") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA author metadata type
public const CdaAuthorDataType = new CdaAuthorDataType();

#! DataProvider metadata for CDA document metadata
public class CdaDocumentMetadataDataType inherits HashDataType {
    private {
        const Fields = {
            "document_id": {
                "display_name": "Document ID",
                "short_desc": "CDA document identifier",
                "desc": "The CDA document identifier extracted from `ClinicalDocument/id`.",
                "type": CdaIdentifierDataType,
            },
            "template_ids": {
                "display_name": "Template IDs",
                "short_desc": "CDA template identifiers",
                "desc": "Template identifiers extracted from root-level `templateId` elements.",
                "type": new ListDataType(CdaIdentifierDataType),
            },
            "code": {
                "display_name": "Document Code",
                "short_desc": "CDA document code",
                "desc": "The CDA document code extracted from `ClinicalDocument/code`.",
                "type": CdaCodeDataType,
            },
            "title": {
                "display_name": "Title",
                "short_desc": "Document title",
                "desc": "The CDA document title.",
                "type": StringOrNothingType,
            },
            "effective_time": {
                "display_name": "Effective Time",
                "short_desc": "Document effective time",
                "desc": "The CDA `effectiveTime/@value`, when present.",
                "type": StringOrNothingType,
            },
            "confidentiality_code": {
                "display_name": "Confidentiality",
                "short_desc": "Confidentiality code",
                "desc": "The CDA confidentiality code.",
                "type": CdaCodeDataType,
            },
            "language_code": {
                "display_name": "Language",
                "short_desc": "Language code",
                "desc": "The CDA `languageCode/@code`, when present.",
                "type": StringOrNothingType,
            },
            "set_id": {
                "display_name": "Set ID",
                "short_desc": "CDA set identifier",
                "desc": "The CDA `setId`, when present.",
                "type": CdaIdentifierDataType,
            },
            "version_number": {
                "display_name": "Version",
                "short_desc": "Version number",
                "desc": "The CDA `versionNumber/@value`, when present.",
                "type": StringOrNothingType,
            },
            "patient": {
                "display_name": "Patient",
                "short_desc": "Patient metadata",
                "desc": "Synthetic patient metadata extracted from the CDA header.",
                "type": CdaPatientDataType,
            },
            "authors": {
                "display_name": "Authors",
                "short_desc": "CDA authors",
                "desc": "Authors extracted from the CDA header.",
                "type": new ListDataType(CdaAuthorDataType),
            },
            "custodian": {
                "display_name": "Custodian",
                "short_desc": "Custodian organization",
                "desc": "The CDA custodian organization.",
                "type": CdaOrganizationDataType,
            },
        };
    }

    constructor() : HashDataType("CdaDocumentMetadata") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA document metadata type
public const CdaDocumentMetadataDataType = new CdaDocumentMetadataDataType();

#! DataProvider metadata for CDA structured entry values
public class CdaEntryValueDataType inherits HashDataType {
    private {
        const Fields = {
            "type": {
                "display_name": "Type",
                "short_desc": "Value type",
                "desc": "The CDA value type, including namespaced `type` attributes such as `xsi:type`.",
                "type": StringOrNothingType,
            },
            "value": {
                "display_name": "Value",
                "short_desc": "Value",
                "desc": "The CDA value attribute, when present.",
                "type": StringOrNothingType,
            },
            "unit": {
                "display_name": "Unit",
                "short_desc": "Unit",
                "desc": "The CDA value unit, when present.",
                "type": StringOrNothingType,
            },
            "code": {
                "display_name": "Code",
                "short_desc": "Coded value",
                "desc": "Coded value attributes, when present.",
                "type": CdaCodeDataType,
            },
        };
    }

    constructor() : HashDataType("CdaEntryValue") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA structured entry value metadata type
public const CdaEntryValueDataType = new CdaEntryValueDataType();

#! DataProvider metadata for CDA structured entries
public class CdaEntryDataType inherits HashDataType {
    private {
        const Fields = {
            "section_index": {
                "display_name": "Section Index",
                "short_desc": "Parent section index",
                "desc": "The one-based index of the parent CDA section.",
                "type": IntType,
            },
            "type": {
                "display_name": "Type",
                "short_desc": "Clinical statement type",
                "desc": "The CDA clinical statement element name such as `observation` or `procedure`.",
                "type": StringType,
            },
            "template_ids": {
                "display_name": "Template IDs",
                "short_desc": "Entry template identifiers",
                "desc": "Template identifiers extracted from the clinical statement.",
                "type": new ListDataType(CdaIdentifierDataType),
            },
            "code": {
                "display_name": "Code",
                "short_desc": "Entry code",
                "desc": "The clinical statement code.",
                "type": CdaCodeDataType,
            },
            "status_code": {
                "display_name": "Status",
                "short_desc": "Status code",
                "desc": "The CDA clinical statement `statusCode/@code`, when present.",
                "type": StringOrNothingType,
            },
            "effective_time": {
                "display_name": "Effective Time",
                "short_desc": "Effective time",
                "desc": "The CDA clinical statement effective time value or low/high interval.",
                "type": StringOrNothingType,
            },
            "text": {
                "display_name": "Text",
                "short_desc": "Entry text",
                "desc": "Compact text extracted from the clinical statement text element.",
                "type": StringOrNothingType,
            },
            "value": {
                "display_name": "Value",
                "short_desc": "Entry value",
                "desc": "Structured CDA value metadata.",
                "type": CdaEntryValueDataType,
            },
        };
    }

    constructor() : HashDataType("CdaEntry") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA structured entry metadata type
public const CdaEntryDataType = new CdaEntryDataType();

#! DataProvider metadata for CDA section summaries
public class CdaSectionDataType inherits HashDataType {
    private {
        const Fields = {
            "index": {
                "display_name": "Index",
                "short_desc": "One-based section index",
                "desc": "The one-based section index in document order.",
                "type": IntType,
            },
            "template_ids": {
                "display_name": "Template IDs",
                "short_desc": "Section template identifiers",
                "desc": "Template identifiers extracted from the CDA section.",
                "type": new ListDataType(CdaIdentifierDataType),
            },
            "code": {
                "display_name": "Section Code",
                "short_desc": "Section code",
                "desc": "The CDA section code.",
                "type": CdaCodeDataType,
            },
            "title": {
                "display_name": "Title",
                "short_desc": "Section title",
                "desc": "The CDA section title.",
                "type": StringOrNothingType,
            },
            "text": {
                "display_name": "Text",
                "short_desc": "Section narrative text",
                "desc": "Compact narrative text extracted from the CDA section `text` element.",
                "type": StringOrNothingType,
            },
            "entries": {
                "display_name": "Entries",
                "short_desc": "Structured entries",
                "desc": "Structured clinical entries extracted from the CDA section.",
                "type": new ListDataType(CdaEntryDataType),
            },
        };
    }

    constructor() : HashDataType("CdaSection") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA section metadata type
public const CdaSectionDataType = new CdaSectionDataType();

#! Request metadata for parsing CDA XML
public class CdaParseDocumentRequestDataType inherits HashDataType {
    public {
        const Fields = {
            "xml": {
                "display_name": "CDA XML",
                "short_desc": "CDA XML document text",
                "desc": "The CDA XML document to parse.",
                "type": StringType,
                "example_value": "<?xml version=\"1.0\"?><ClinicalDocument xmlns=\"urn:hl7-org:v3\">...</ClinicalDocument>",
            },
            "validate": {
                "display_name": "Validate",
                "short_desc": "Validate with XSD",
                "desc": "If `True`, validate the XML using `xsd_path`, `xsd`, or the provider's configured schema.",
                "type": SoftBoolOrNothingType,
            },
            "xsd_path": {
                "display_name": "XSD Path",
                "short_desc": "Path to a CDA XSD",
                "desc": "Path to an XSD file. File-based validation resolves relative `xsd:include` and `xsd:import` references.",
                "type": StringOrNothingType,
                "example_value": "/opt/cda/schema/CDA.xsd",
            },
            "xsd": {
                "display_name": "XSD",
                "short_desc": "Inline CDA XSD",
                "desc": "Inline XSD text to validate against when file-based validation is not required.",
                "type": StringOrNothingType,
                "example_value": "<?xml version=\"1.0\"?><xsd:schema xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"/>",
            },
        };
    }

    constructor() : HashDataType("CdaParseDocumentRequest") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA parse request type
public const CdaParseDocumentRequestDataType = new CdaParseDocumentRequestDataType();

#! Request metadata for validating CDA XML
public class CdaValidateDocumentRequestDataType inherits HashDataType {
    public {
        const Fields = {
            "xml": {
                "display_name": "CDA XML",
                "short_desc": "CDA XML document text",
                "desc": "The CDA XML document to validate.",
                "type": StringType,
                "example_value": "<?xml version=\"1.0\"?><ClinicalDocument xmlns=\"urn:hl7-org:v3\">...</ClinicalDocument>",
            },
            "xsd_path": {
                "display_name": "XSD Path",
                "short_desc": "Path to a CDA XSD",
                "desc": "Path to an XSD file. File-based validation resolves relative `xsd:include` and `xsd:import` references.",
                "type": StringOrNothingType,
                "example_value": "/opt/cda/schema/CDA.xsd",
            },
            "xsd": {
                "display_name": "XSD",
                "short_desc": "Inline CDA XSD",
                "desc": "Inline XSD text to validate against when file-based validation is not required.",
                "type": StringOrNothingType,
                "example_value": "<?xml version=\"1.0\"?><xsd:schema xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"/>",
            },
        };
    }

    constructor() : HashDataType("CdaValidateDocumentRequest") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA validation request type
public const CdaValidateDocumentRequestDataType = new CdaValidateDocumentRequestDataType();

#! Response metadata for parsed CDA XML
public class CdaParseDocumentResponseDataType inherits HashDataType {
    private {
        const Fields = {
            "valid": {
                "display_name": "Valid",
                "short_desc": "Validation result",
                "desc": "`True` when XSD validation was performed and passed; `NOTHING` when validation was skipped.",
                "type": SoftBoolOrNothingType,
            },
            "metadata": {
                "display_name": "Metadata",
                "short_desc": "CDA document metadata",
                "desc": "Metadata extracted from the CDA header.",
                "type": CdaDocumentMetadataDataType,
            },
            "sections": {
                "display_name": "Sections",
                "short_desc": "CDA sections",
                "desc": "CDA section summaries extracted from the document body.",
                "type": new ListDataType(CdaSectionDataType),
            },
            "data": {
                "display_name": "Data",
                "short_desc": "Parsed XML hash",
                "desc": "The parsed XML document as a Qore hash.",
                "type": AutoHashType,
            },
        };
    }

    constructor() : HashDataType("CdaParseDocumentResponse") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA parse response type
public const CdaParseDocumentResponseDataType = new CdaParseDocumentResponseDataType();

#! Response metadata for CDA validation
public class CdaValidateDocumentResponseDataType inherits HashDataType {
    private {
        const Fields = {
            "valid": {
                "display_name": "Valid",
                "short_desc": "Validation result",
                "desc": "`True` when XSD validation passed.",
                "type": SoftBoolType,
            },
            "metadata": {
                "display_name": "Metadata",
                "short_desc": "CDA document metadata",
                "desc": "Metadata extracted after validation.",
                "type": CdaDocumentMetadataDataType,
            },
        };
    }

    constructor() : HashDataType("CdaValidateDocumentResponse") {
        addQoreFields(Fields);
    }
}

#! Singleton CDA validation response type
public const CdaValidateDocumentResponseDataType = new CdaValidateDocumentResponseDataType();
}
