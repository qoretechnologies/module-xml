# -*- mode: qore; indent-tabs-mode: nil -*-
#! Qore CargoXmlDataProvider action request and response data types

/** CargoXmlActionTypes.qc Copyright 2026 Qore Technologies, s.r.o.

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
#! request type for the parse-cargo-xml-message action
public class CargoXmlParseMessageRequestDataType inherits HashDataType {
    public {
        const Fields = {
            "message_qname": {
                "type": StringType,
                "display_name": "Message",
                "short_desc": "The cargo XML message type to parse",
                "desc": "Identifier of the cargo XML message type to parse, in James-Clark "
                    "notation `{namespace_uri}local_name`. Pick from the dropdown; the list is "
                    "discovered from the schema directory configured on the data provider.\n\n"
                    "**Example**: "
                    "`{urn:un:unece:uncefact:data:standard:CrossIndustryDespatchAdvice:27}"
                    "CrossIndustryDespatchAdvice`",
                "ref_data": "cargo-xml-message",
            },
            "xml": {
                "type": StringType,
                "display_name": "XML",
                "short_desc": "The XML message text to parse",
                "desc": "The XML message text to parse. When `validate` is `True` the document "
                    "is validated against the message's XSD (with all multi-file imports "
                    "resolved by libxml2) before being deserialized to a Qore hash.",
                "example_value": "<?xml version=\"1.0\"?><CrossIndustryDespatchAdvice xmlns=\"...\">...</CrossIndustryDespatchAdvice>",
            },
            "validate": {
                "type": SoftBoolType,
                "display_name": "Validate",
                "short_desc": "Validate the XML against the message XSD",
                "desc": "If `True` (default), validate the XML document against the message's "
                    "XSD before parsing. If validation fails, an `XSD-ERROR` exception is "
                    "thrown and no parse output is returned.",
                "default_value": True,
            },
        };
    }

    constructor() : HashDataType("CargoXmlParseMessageRequestDataType") {
        addQoreFields(Fields);
    }
}

#! response type for the parse-cargo-xml-message action
public class CargoXmlParseMessageResponseDataType inherits HashDataType {
    private {
        const Fields = {
            "data": {
                "type": AutoHashType,
                "display_name": "Data",
                "short_desc": "The parsed payload",
                "desc": "The parsed message payload as a Qore hash. The top-level key is the "
                    "message's element name and any nested elements appear as nested keys; "
                    "attributes appear under `^attributes^` and text content under `^value^`.",
            },
            "valid": {
                "type": SoftBoolOrNothingType,
                "display_name": "Valid",
                "short_desc": "Whether the input was XSD-validated",
                "desc": "`True` when the input passed XSD validation. `NOTHING` when validation "
                    "was skipped (i.e. the request had `validate` set to `False`).",
            },
        };
    }

    constructor() : HashDataType("CargoXmlParseMessageResponseDataType") {
        addQoreFields(Fields);
    }
}

#! request type for the build-cargo-xml-message action
public class CargoXmlBuildMessageRequestDataType inherits HashDataType {
    public {
        const Fields = {
            "message_qname": {
                "type": StringType,
                "display_name": "Message",
                "short_desc": "The cargo XML message type to build",
                "desc": "Identifier of the cargo XML message type to build, in James-Clark "
                    "notation `{namespace_uri}local_name`. Pick from the dropdown; the list is "
                    "discovered from the schema directory configured on the data provider.",
                "ref_data": "cargo-xml-message",
            },
            "data": {
                "type": AutoHashType,
                "display_name": "Data",
                "short_desc": "The hash payload to serialize as XML",
                "desc": "The message payload to serialize. The top-level key must be the "
                    "message's qualified element name with the appropriate `xmlns` declarations "
                    "on `^attributes^`. Nested elements are nested keys; attributes go under "
                    "`^attributes^`; text content goes under `^value^`.",
            },
            "validate": {
                "type": SoftBoolType,
                "display_name": "Validate",
                "short_desc": "Validate the generated XML against the message XSD",
                "desc": "If `True` (default), validate the generated XML against the message's "
                    "XSD before returning. If validation fails, an `XSD-ERROR` exception is "
                    "thrown and the XML is not returned.",
                "default_value": True,
            },
        };
    }

    constructor() : HashDataType("CargoXmlBuildMessageRequestDataType") {
        addQoreFields(Fields);
    }
}

#! response type for the build-cargo-xml-message action
public class CargoXmlBuildMessageResponseDataType inherits HashDataType {
    private {
        const Fields = {
            "xml": {
                "type": StringType,
                "display_name": "XML",
                "short_desc": "The serialized XML message",
                "desc": "The serialized XML message text. Includes the XML declaration and is "
                    "ready to send to a trading partner.",
            },
            "valid": {
                "type": SoftBoolOrNothingType,
                "display_name": "Valid",
                "short_desc": "Whether the output was XSD-validated",
                "desc": "`True` when the generated XML passed XSD validation. `NOTHING` when "
                    "validation was skipped (i.e. the request had `validate` set to `False`).",
            },
        };
    }

    constructor() : HashDataType("CargoXmlBuildMessageResponseDataType") {
        addQoreFields(Fields);
    }
}

#! singleton instance of the parse-cargo-xml-message request type, for action registration
public const CargoXmlParseMessageRequestDataType = new CargoXmlParseMessageRequestDataType();

#! singleton instance of the parse-cargo-xml-message response type, for action registration
public const CargoXmlParseMessageResponseDataType = new CargoXmlParseMessageResponseDataType();

#! singleton instance of the build-cargo-xml-message request type, for action registration
public const CargoXmlBuildMessageRequestDataType = new CargoXmlBuildMessageRequestDataType();

#! singleton instance of the build-cargo-xml-message response type, for action registration
public const CargoXmlBuildMessageResponseDataType = new CargoXmlBuildMessageResponseDataType();
}
