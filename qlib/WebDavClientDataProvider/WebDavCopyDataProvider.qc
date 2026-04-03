# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavClientDataProvider.qm Copyright 2019 - 2026 Qore Technologies, s.r.o.
    MIT License - see LICENSE file
*/

public namespace WebDavClientDataProvider {

public class WebDavCopyDataProvider inherits WebDavClientDataProviderBase {
    public {
        const ProviderInfo = <DataProviderInfo>{
            "type": "WebDavCopyDataProvider",
            "supports_request": True,
        };

        const ProviderSummaryInfo = cast<hash<DataProviderSummaryInfo>>(ProviderInfo{
            AbstractDataProvider::DataProviderSummaryInfoKeys
        });

        static WebDavCopyRequestDataType RequestType();
        static WebDavSuccessResponseDataType ResponseType();
    }

    constructor(WebDavClient::WebDavClient client) : WebDavClientDataProviderBase(client) {
    }

    string getName() {
        return "copy";
    }

    *string getDesc() {
        return "WebDAV copy data provider; copies a file or directory. "
            "Request: `{source: string, destination: string, overwrite: bool}`. "
            "Response: `{success: bool}`";
    }

    private auto doRequestImpl(auto req, *hash<auto> request_options) {
        string src = req.source;
        string dest = req.destination;
        if (!src || !dest) {
            throw "WEBDAV-COPY-ERROR", "source and destination are required";
        }

        bool overwrite = req.overwrite ?? True;
        client.copyResource(src, dest, overwrite);
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
