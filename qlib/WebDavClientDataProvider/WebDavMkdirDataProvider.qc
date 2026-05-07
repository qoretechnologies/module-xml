# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavClientDataProvider.qm Copyright 2019 - 2026 Qore Technologies, s.r.o.
    MIT License - see LICENSE file
*/

public namespace WebDavClientDataProvider {

public class WebDavMkdirDataProvider inherits WebDavClientDataProviderBase {
    public {
        const ProviderInfo = <DataProviderInfo>{
            "type": "WebDavMkdirDataProvider",
            "supports_request": True,
        };

        const ProviderSummaryInfo = cast<hash<DataProviderSummaryInfo>>(ProviderInfo{
            AbstractDataProvider::DataProviderSummaryInfoKeys
        });

        static WebDavMkdirRequestDataType RequestType();
        static WebDavSuccessResponseDataType ResponseType();
    }

    constructor(object client) : WebDavClientDataProviderBase(client) {
    }

    string getName() {
        return "mkdir";
    }

    *string getDesc() {
        return "WebDAV mkdir data provider; creates a directory (collection). "
            "Request: `{path: string}`. Response: `{success: bool}`";
    }

    private auto doRequestImpl(auto req, *hash<auto> request_options) {
        string path = req.path;
        if (!path) {
            throw "WEBDAV-MKDIR-ERROR", "path is required";
        }

        client.mkcol(path);
        return {"success": True};
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
