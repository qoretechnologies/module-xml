# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavClientDataProvider.qm Copyright 2019 - 2026 Qore Technologies, s.r.o.
    MIT License - see LICENSE file
*/

public namespace WebDavClientDataProvider {

public class WebDavPutDataProvider inherits WebDavClientDataProviderBase {
    public {
        const ProviderInfo = <DataProviderInfo>{
            "type": "WebDavPutDataProvider",
            "supports_request": True,
        };

        const ProviderSummaryInfo = cast<hash<DataProviderSummaryInfo>>(ProviderInfo{
            AbstractDataProvider::DataProviderSummaryInfoKeys
        });

        static WebDavPutRequestDataType RequestType();
        static WebDavPutResponseDataType ResponseType();
    }

    constructor(WebDavClient::WebDavClient client) : WebDavClientDataProviderBase(client) {
    }

    string getName() {
        return "put";
    }

    *string getDesc() {
        return "WebDAV put file data provider; uploads a file to the server. "
            "Request: `{path: string, content: data, content_type: string}`. "
            "Response: `{created: bool}`";
    }

    private auto doRequestImpl(auto req, *hash<auto> request_options) {
        string path = req.path;
        if (!path) {
            throw "WEBDAV-PUT-ERROR", "path is required";
        }

        data content = req.content ?? "";
        bool created = client.put(path, content, req.content_type);

        return {"created": created};
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
