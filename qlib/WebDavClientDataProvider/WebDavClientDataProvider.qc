# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavClientDataProvider.qm Copyright 2019 - 2025 Qore Technologies, s.r.o.

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

#! Contains all public definitions in the WebDavClientDataProvider module
public namespace WebDavClientDataProvider {

#! The WebDAV data provider class
public class WebDavClientDataProvider inherits WebDavClientDataProviderBase {
    public {
        #! Provider info
        const ProviderInfo = <DataProviderInfo>{
            "type": "WebDavClientDataProvider",
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
            "supports_schema": False,
            "children_can_support_apis": True,
            "children_can_support_records": False,
            "children_can_support_observers": False,
        };

        #! Constructor options
        const ConstructorOptions = {
            "webdavclient": <DataProviderOptionInfo>{
                "display_name": "WebDAV Client",
                "short_desc": "The WebDAV client for accessing the server",
                "type": AbstractDataProviderType::get(new Type("WebDavClient::WebDavClient")),
                "desc": "The WebDAV client for accessing the server",
            },
            "url": <DataProviderOptionInfo>{
                "display_name": "URL",
                "short_desc": "The URL to the WebDAV server",
                "type": AbstractDataProviderTypeMap."string",
                "desc": "The URL to the WebDAV server",
            },
        };
    }

    private {
        const ChildMap = {
            "list": Class::forName("WebDavClientDataProvider::WebDavListDataProvider"),
            "get": Class::forName("WebDavClientDataProvider::WebDavGetDataProvider"),
            "put": Class::forName("WebDavClientDataProvider::WebDavPutDataProvider"),
            "delete": Class::forName("WebDavClientDataProvider::WebDavDeleteDataProvider"),
            "mkdir": Class::forName("WebDavClientDataProvider::WebDavMkdirDataProvider"),
            "copy": Class::forName("WebDavClientDataProvider::WebDavCopyDataProvider"),
            "move": Class::forName("WebDavClientDataProvider::WebDavMoveDataProvider"),
        };
    }

    #! Creates the object from constructor options
    constructor(*hash<auto> options) : WebDavClientDataProviderBase(
            WebDavClientDataProvider::getClient(options)) {
    }

    #! Creates the object from an existing WebDavClient
    constructor(WebDavClient::WebDavClient client) : WebDavClientDataProviderBase(client) {
    }

    #! Returns a WebDAV client from options
    static WebDavClient::WebDavClient getClient(*hash<auto> options) {
        if (options.webdavclient) {
            return options.webdavclient;
        }
        if (!options.url) {
            throw "CONSTRUCTOR-ERROR", "no 'webdavclient' or 'url' option passed; "
                "cannot create WebDAV client without a URL";
        }
        return new WebDavClient::WebDavClient({"url": options.url});
    }

    #! Returns the data provider name
    string getName() {
        return "webdav";
    }

    #! Returns the data provider description
    *string getDesc() {
        return sprintf("WebDAV data provider for `%s`", client.getURL());
    }

    #! Return data provider summary info
    *list<hash<DataProvider::DataProviderSummaryInfo>> getChildProviderSummaryInfo() {
        return map $1.getConstant("ProviderSummaryInfo").getValue(), ChildMap.iterator();
    }

    #! Returns a list of child data provider names, if any
    private *list<string> getChildProviderNamesImpl() {
        return keys ChildMap;
    }

    #! Returns the given child provider or @ref nothing if the given child is unknown
    private *DataProvider::AbstractDataProvider getChildProviderImpl(string name) {
        *Class cls = ChildMap{name};
        if (!cls) {
            return;
        }
        return cls.newObject(client);
    }

    #! Returns data provider static info
    private hash<DataProvider::DataProviderInfo> getStaticInfoImpl() {
        return ProviderInfo;
    }
}

} # namespace WebDavClientDataProvider
