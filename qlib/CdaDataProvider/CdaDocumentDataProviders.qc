# -*- mode: qore; indent-tabs-mode: nil -*-
#! Qore CDA document action data providers

/*  CdaDocumentDataProviders.qc Copyright 2026 Qore Technologies, s.r.o.

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
#! Data provider backing the parse-cda-document action
public class CdaParseDocumentDataProvider inherits AbstractDataProvider {
    public {
        #! Request type singleton
        const RequestType = CdaValidateDocumentRequestDataType;

        #! Response type singleton
        const ResponseType = CdaParseDocumentResponseDataType;

        #! Provider info
        const ProviderInfo = <DataProviderInfo>{
            "name": "parse-document",
            "type": "CdaParseDocumentDataProvider",
            "supports_request": True,
        };
    }

    private {
        CdaDataProvider parent;
    }

    constructor(CdaDataProvider parent) {
        self.parent = parent;
    }

    string getName() {
        return ProviderInfo.name;
    }

    *string getDesc() {
        return "Parse CDA XML, optionally validate with XSD, and extract metadata and sections";
    }

    private *AbstractDataProviderType getRequestTypeImpl() {
        return RequestType;
    }

    private *AbstractDataProviderType getResponseTypeImpl() {
        return ResponseType;
    }

    private auto doRequestImpl(auto req, *hash<auto> request_options) {
        return CdaDocumentParser::parse(req.xml, parent.getRequestOptions(req));
    }

    private hash<DataProviderInfo> getStaticInfoImpl() {
        return ProviderInfo;
    }
}

#! Data provider backing the validate-cda-document action
public class CdaValidateDocumentDataProvider inherits AbstractDataProvider {
    public {
        #! Request type singleton
        const RequestType = CdaParseDocumentRequestDataType;

        #! Response type singleton
        const ResponseType = CdaValidateDocumentResponseDataType;

        #! Provider info
        const ProviderInfo = <DataProviderInfo>{
            "name": "validate-document",
            "type": "CdaValidateDocumentDataProvider",
            "supports_request": True,
        };
    }

    private {
        CdaDataProvider parent;
    }

    constructor(CdaDataProvider parent) {
        self.parent = parent;
    }

    string getName() {
        return ProviderInfo.name;
    }

    *string getDesc() {
        return "Validate CDA XML with XSD and extract document metadata";
    }

    private *AbstractDataProviderType getRequestTypeImpl() {
        return RequestType;
    }

    private *AbstractDataProviderType getResponseTypeImpl() {
        return ResponseType;
    }

    private auto doRequestImpl(auto req, *hash<auto> request_options) {
        hash<auto> opts = parent.getRequestOptions(req);
        opts.validate = True;
        return CdaDocumentParser::validate(req.xml, opts);
    }

    private hash<DataProviderInfo> getStaticInfoImpl() {
        return ProviderInfo;
    }
}
}
