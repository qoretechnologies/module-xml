# -*- mode: qore; indent-tabs-mode: nil -*-
#! Qore CdaDataProvider class definition

/*  CdaDataProvider.qc Copyright 2026 Qore Technologies, s.r.o.

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
#! Root data provider for CDA document parsing and validation actions
public class CdaDataProvider inherits AbstractDataProvider {
    public {
        #! DataProvider factory name
        const FactoryName = "cda";

        #! Provider child action classes
        const ChildMap = {
            "parse-document": Class::forName("CdaDataProvider::CdaParseDocumentDataProvider"),
            "validate-document": Class::forName("CdaDataProvider::CdaValidateDocumentDataProvider"),
        };

        #! Constructor options
        const ConstructorOptions = {
            "validate": <DataProviderOptionInfo>{
                "display_name": "Validate",
                "short_desc": "Validate CDA input by default",
                "desc": "If `True`, parse and validate child actions validate XML by default unless the request overrides it.",
                "type": AbstractDataProviderType::get(SoftBoolType),
                "default_value": False,
            },
            "xsd_path": <DataProviderOptionInfo>{
                "display_name": "XSD Path",
                "short_desc": "Default CDA XSD path",
                "desc": "Default XSD path for validation. File-based validation resolves relative `xsd:include` and `xsd:import` references.",
                "type": AbstractDataProviderType::get(StringOrNothingType),
            },
            "xsd": <DataProviderOptionInfo>{
                "display_name": "XSD",
                "short_desc": "Default inline CDA XSD",
                "desc": "Default inline XSD text for validation when file-based schema resolution is not required.",
                "type": AbstractDataProviderType::get(StringOrNothingType),
            },
        };

        #! Provider info
        const ProviderInfo = <DataProviderInfo>{
            "name": FactoryName,
            "type": "CdaDataProvider",
            "supports_read": False,
            "supports_create": False,
            "supports_update": False,
            "supports_upsert": False,
            "supports_delete": False,
            "supports_native_search": False,
            "supports_bulk_create": False,
            "supports_bulk_upsert": False,
            "supports_children": True,
            "children_can_support_apis": True,
            "constructor_options": ConstructorOptions,
            "transaction_management": False,
        };
    }

    private {
        bool validate_default = False;
        *string xsd_path;
        *string xsd;
    }

    #! Creates the CDA data provider
    constructor(*hash<auto> options) {
        *hash<auto> copts = checkOptions("CONSTRUCTOR-ERROR", ConstructorOptions, options);
        validate_default = copts.validate ?? False;
        xsd_path = copts.xsd_path;
        xsd = copts.xsd;
        if (xsd_path && xsd) {
            throw "CONSTRUCTOR-ERROR", "provide only one of `xsd_path` or `xsd`";
        }
    }

    #! Returns the provider name
    string getName() {
        return FactoryName;
    }

    #! Returns the child provider names
    private *list<string> getChildProviderNamesImpl() {
        return keys ChildMap;
    }

    #! Returns a child action provider
    private *AbstractDataProvider getChildProviderImpl(string name) {
        *Class cls = ChildMap{name};
        return cls ? cls.newObject(self) : NOTHING;
    }

    #! Returns effective parse/validation options for a request
    hash<auto> getRequestOptions(auto req) {
        hash<auto> rv = {
            "validate": exists req{"validate"} ? req.validate : validate_default,
            "xsd_path": req.xsd_path ?? xsd_path,
            "xsd": req.xsd ?? xsd,
        };
        if (rv.xsd_path && rv.xsd) {
            throw "CDA-VALIDATION-ERROR", "provide only one of `xsd_path` or `xsd`";
        }
        return rv;
    }

    private hash<DataProviderInfo> getStaticInfoImpl() {
        return ProviderInfo;
    }
}
}
