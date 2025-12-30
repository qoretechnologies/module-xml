# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavClientDataProvider.qm Copyright 2019 - 2025 Qore Technologies, s.r.o.
    MIT License - see LICENSE file
*/

public namespace WebDavClientDataProvider {

public class WebDavMoveDataProvider inherits WebDavClientDataProviderBase {
    public {
        const ProviderInfo = <DataProviderInfo>{
            "type": "WebDavMoveDataProvider",
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
        return "move";
    }

    *string getDesc() {
        return "WebDAV move data provider; moves or renames a file or directory. "
            "Request: {source: string, destination: string, overwrite: bool}. Response: {success: bool}";
    }

    private auto doRequestImpl(auto req, *hash<auto> request_options) {
        string src = req.source;
        string dest = req.destination;
        if (!src || !dest) {
            throw "WEBDAV-MOVE-ERROR", "source and destination are required";
        }

        bool overwrite = req.overwrite ?? True;
        client.moveResource(src, dest, overwrite);
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
