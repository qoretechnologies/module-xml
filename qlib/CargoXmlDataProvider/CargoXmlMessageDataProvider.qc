# -*- mode: qore; indent-tabs-mode: nil -*-
#! Qore CargoXmlMessageDataProvider class definition

/** CargoXmlMessageDataProvider.qc Copyright 2026 Qore Technologies, s.r.o.

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
#! request type for @ref CargoXmlMessageDataProvider::doRequestImpl()
public hashdecl CargoXmlMessageRequest {
    #! \c "parse" to convert XML to a Qore hash, or \c "build" to convert a hash to XML
    string direction;

    #! the XML payload to parse (required when \c direction is \c "parse")
    *string xml;

    #! the hash payload to serialize (required when \c direction is \c "build")
    *hash<auto> data;

    #! when @ref True (default), validate the resulting XML against the message's XSD
    *bool validate;
}

#! response type for @ref CargoXmlMessageDataProvider::doRequestImpl()
public hashdecl CargoXmlMessageResponse {
    #! the parsed Qore hash (when direction was \c "parse")
    *hash<auto> data;

    #! the serialized XML string (when direction was \c "build")
    *string xml;

    #! @ref True if XSD validation succeeded; @ref False otherwise (or absent if not requested)
    *bool valid;
}

#! per-message data provider exposing parse and build operations for one XSD message
/** A single instance is bound to one top-level XSD message element. The \c doRequestImpl()
    API takes a @ref CargoXmlMessageRequest and returns a @ref CargoXmlMessageResponse.

    Validation uses libxml2 via @ref Qore::Xml::XmlDoc::validateSchemaFile() so multi-file
    XSD imports resolve relative to the message file. This is required for real-world
    packages like UN/CEFACT, where each message schema imports a tree of shared types.
*/
public class CargoXmlMessageDataProvider inherits AbstractDataProvider {
    public {
        #! information about the bound message
        hash<CargoXmlMessageInfo> message_info;

        #! provider info
        const ProviderInfo = <DataProviderInfo>{
            "type": "CargoXmlMessageDataProvider",
            "supports_request": True,
            "supports_read": False,
            "supports_create": False,
            "supports_update": False,
            "supports_upsert": False,
            "supports_delete": False,
            "supports_native_search": False,
            "supports_bulk_create": False,
            "supports_bulk_upsert": False,
            "supports_children": False,
            "transaction_management": False,
        };
    }

    #! creates the object bound to the given message
    constructor(hash<CargoXmlMessageInfo> mi) {
        message_info = mi;
    }

    #! returns the data provider name (the message's local element name)
    string getName() {
        return message_info.name;
    }

    #! returns a description that includes the namespace and source file
    *string getDesc() {
        return sprintf("CargoXML message %y in namespace %y (defined in %y)", message_info.name,
            message_info.namespace, message_info.xsd_file);
    }

    #! parses an XML string for this message and optionally validates it against the XSD
    /** @param xml the XML message text
        @param validate if @ref True, validate against the message's XSD file (multi-file
            imports resolved by libxml2)

        @return parsed payload as a Qore hash. Throws on parse failure or (if \a validate is
            @ref True) on schema validation failure.

        @throw XSD-ERROR the document is not valid against the schema
        @throw XSD-SYNTAX-ERROR the schema or its imports could not be loaded
    */
    hash<auto> parseMessage(string xml, bool validate = True) {
        if (validate) {
            XmlDoc d(xml);
            d.validateSchemaFile(message_info.xsd_file);
        }
        return parse_xml(xml);
    }

    #! serializes a Qore hash as XML and optionally validates it against the XSD
    string buildMessage(hash<auto> data, bool validate = True) {
        string xml = make_xml(data);
        if (validate) {
            XmlDoc d(xml);
            d.validateSchemaFile(message_info.xsd_file);
        }
        return xml;
    }

    #! request-reply API: dispatches to @ref parseMessage() or @ref buildMessage() based on \c direction
    private auto doRequestImpl(auto req, *hash<auto> request_options) {
        hash<CargoXmlMessageRequest> r = cast<hash<CargoXmlMessageRequest>>(req);
        bool validate = r.validate ?? True;
        switch (r.direction) {
            case "parse": {
                if (!exists r.xml) {
                    throw "CARGO-XML-REQUEST-ERROR", "direction \"parse\" requires xml";
                }
                return <CargoXmlMessageResponse>{
                    "data": parseMessage(r.xml, validate),
                    "valid": validate ? True : NOTHING,
                };
            }
            case "build": {
                if (!exists r.data) {
                    throw "CARGO-XML-REQUEST-ERROR", "direction \"build\" requires data";
                }
                return <CargoXmlMessageResponse>{
                    "xml": buildMessage(r.data, validate),
                    "valid": validate ? True : NOTHING,
                };
            }
            default:
                throw "CARGO-XML-REQUEST-ERROR", sprintf("unknown direction %y; expected \"parse\" or \"build\"",
                    r.direction);
        }
    }

    private *AbstractDataProviderType getRequestTypeImpl() {
        return AbstractDataProviderType::get(new Type("hash<CargoXmlMessageRequest>"));
    }

    private *AbstractDataProviderType getResponseTypeImpl() {
        return AbstractDataProviderType::get(new Type("hash<CargoXmlMessageResponse>"));
    }

    private hash<DataProviderInfo> getStaticInfoImpl() {
        return ProviderInfo;
    }
}
}
