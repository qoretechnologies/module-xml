# -*- mode: qore; indent-tabs-mode: nil -*-
#! Qore CargoXmlBuildMessageDataProvider class definition

/** CargoXmlBuildMessageDataProvider.qc Copyright 2026 Qore Technologies, s.r.o.

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
#! data provider backing the build-cargo-xml-message action
/** Serializes a Qore hash to a Cargo XML message and optionally validates it against
    the message's XSD (with multi-file imports resolved by libxml2). The message type
    is selected by \c message_qname; see @ref CargoXmlParseMessageDataProvider for the
    inverse direction.
*/
public class CargoXmlBuildMessageDataProvider inherits AbstractDataProvider {
    public {
        #! request type singleton (referenced from action registration)
        const RequestType = CargoXmlDataProvider::CargoXmlBuildMessageRequestDataType;

        #! response type singleton (referenced from action registration)
        const ResponseType = CargoXmlDataProvider::CargoXmlBuildMessageResponseDataType;

        #! provider info
        const ProviderInfo = <DataProviderInfo>{
            "name": "build-message",
            "type": "CargoXmlBuildMessageDataProvider",
            "supports_request": True,
        };
    }

    private {
        #! the parent provider that owns the message catalog
        CargoXmlDataProvider parent;
    }

    constructor(CargoXmlDataProvider parent) {
        self.parent = parent;
    }

    string getName() {
        return ProviderInfo.name;
    }

    *string getDesc() {
        return "Serialize a hash to a Cargo XML message; optionally validate against its XSD";
    }

    private *AbstractDataProviderType getRequestTypeImpl() {
        return RequestType;
    }

    private *AbstractDataProviderType getResponseTypeImpl() {
        return ResponseType;
    }

    private auto doRequestImpl(auto req, *hash<auto> request_options) {
        string qname = req.message_qname;
        *hash<CargoXmlMessageInfo> mi = parent.getMessages(){qname};
        if (!mi) {
            throw "CARGO-XML-MESSAGE-ERROR", sprintf("unknown cargo XML message %y; the message must "
                "be one of the qualified names discovered from %y", qname, parent.schema_dir);
        }
        bool validate = exists req.validate ? req.validate : True;
        string xml = make_xml(req.data);
        if (validate) {
            XmlDoc d(xml);
            d.validateSchemaFile(mi.xsd_file);
        }
        return {
            "xml": xml,
            "valid": validate ? True : NOTHING,
        };
    }

    private hash<DataProviderInfo> getStaticInfoImpl() {
        return ProviderInfo;
    }
}
}
