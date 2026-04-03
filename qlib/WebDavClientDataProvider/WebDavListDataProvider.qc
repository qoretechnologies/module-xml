# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavClientDataProvider.qm Copyright 2019 - 2026 Qore Technologies, s.r.o.
    MIT License - see LICENSE file
*/

public namespace WebDavClientDataProvider {

public class WebDavListDataProvider inherits WebDavClientDataProviderBase {
    public {
        const ProviderInfo = <DataProviderInfo>{
            "type": "WebDavListDataProvider",
            "supports_request": True,
        };

        const ProviderSummaryInfo = cast<hash<DataProviderSummaryInfo>>(ProviderInfo{
            AbstractDataProvider::DataProviderSummaryInfoKeys
        });

        static WebDavListRequestDataType RequestType();
        static WebDavListResponseDataType ResponseType();
    }

    constructor(WebDavClient::WebDavClient client) : WebDavClientDataProviderBase(client) {
    }

    string getName() {
        return "list";
    }

    *string getDesc() {
        return "WebDAV list directory data provider; lists files and directories using `PROPFIND`. "
            "Request: `{path: string, depth: string}`. Response: `{resources: list<hash>}`";
    }

    private auto doRequestImpl(auto req, *hash<auto> request_options) {
        string path = req.path ?? "/";
        string depth = req.depth ?? "1";

        list<hash<WebDavClient::WebDavResourceInfo>> resources = client.list(path, depth);

        return {"resources": resources};
    }

    private *AbstractDataProviderType getRequestTypeImpl() {
        return RequestType;
    }

    private *AbstractDataProviderType getResponseTypeImpl() {
        return ResponseType;
    }

    private hash<DataProviderInfo> getStaticInfoImpl() {
        return ProviderInfo;
    }
}

}
