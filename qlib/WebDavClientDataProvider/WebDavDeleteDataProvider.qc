# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavClientDataProvider.qm Copyright 2019 - 2026 Qore Technologies, s.r.o.
    MIT License - see LICENSE file
*/

public namespace WebDavClientDataProvider {

public class WebDavDeleteDataProvider inherits WebDavClientDataProviderBase {
    public {
        const ProviderInfo = <DataProviderInfo>{
            "type": "WebDavDeleteDataProvider",
            "supports_request": True,
        };

        const ProviderSummaryInfo = cast<hash<DataProviderSummaryInfo>>(ProviderInfo{
            AbstractDataProvider::DataProviderSummaryInfoKeys
        });

        static WebDavDeleteRequestDataType RequestType();
        static WebDavSuccessResponseDataType ResponseType();
    }

    constructor(object client) : WebDavClientDataProviderBase(client) {
    }

    string getName() {
        return "delete";
    }

    *string getDesc() {
        return "WebDAV delete data provider; deletes a file or directory. "
            "Request: `{path: string}`. Response: `{success: bool}`";
    }

    private auto doRequestImpl(auto req, *hash<auto> request_options) {
        string path = req.path;
        if (!path) {
            throw "WEBDAV-DELETE-ERROR", "path is required";
        }

        client.del(path);
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
