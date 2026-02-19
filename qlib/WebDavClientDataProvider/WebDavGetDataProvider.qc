# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavClientDataProvider.qm Copyright 2019 - 2025 Qore Technologies, s.r.o.
    MIT License - see LICENSE file
*/

public namespace WebDavClientDataProvider {

public class WebDavGetDataProvider inherits WebDavClientDataProviderBase {
    public {
        const ProviderInfo = <DataProviderInfo>{
            "type": "WebDavGetDataProvider",
            "supports_request": True,
        };

        const ProviderSummaryInfo = cast<hash<DataProviderSummaryInfo>>(ProviderInfo{
            AbstractDataProvider::DataProviderSummaryInfoKeys
        });

        const RequestType = AbstractDataProviderTypeMap."hash";
        const ResponseType = AbstractDataProviderTypeMap."hash";
    }

    constructor(WebDavClient::WebDavClient client) : WebDavClientDataProviderBase(client) {
    }

    string getName() {
        return "get";
    }

    *string getDesc() {
        return "WebDAV get file data provider; downloads a file from the server. "
            "Request: `{path: string}`. Response: `{content: binary, found: bool}`";
    }

    private auto doRequestImpl(auto req, *hash<auto> request_options) {
        string path = req.path;
        if (!path) {
            throw "WEBDAV-GET-ERROR", "path is required";
        }

        *data content = client.get(path);

        return {
            "content": content,
            "found": exists content,
        };
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
