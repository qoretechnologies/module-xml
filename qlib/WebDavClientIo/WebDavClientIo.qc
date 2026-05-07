# -*- mode: qore; indent-tabs-mode: nil -*-
#! @file WebDavClientIo.qc @brief Pure-Qore WebDAV client class with async I/O

/*  WebDavClientIo.qc Copyright (C) 2026 Qore Technologies, s.r.o.

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

#! the %WebDavClientIo namespace holds all public definitions in the %WebDavClientIo module
public namespace WebDavClientIo {

#! Pure-Qore WebDAV client with async I/O via HttpClientIo
/** This class provides a WebDAV client implementation using
    \c HttpClientIo::HttpClientConnectionManager for async socket I/O with automatic protocol
    negotiation (HTTP/3 &rarr; HTTP/2 &rarr; HTTP/1.1) and connection pooling.

    Method names match @ref WebDavClient::WebDavClient so callers can switch with minimal changes.
    The @ref WebDavClient::WebDavResourceInfo and @ref WebDavClient::WebDavLockInfo result
    hashdecls are reused.

    @par Example:
    @code{.py}
WebDavClientIo client({"url": "https://webdav.example.com/files"});
list<hash<WebDavResourceInfo>> resources = client.list("/");
client.put("/test.txt", "Hello, World!");
*data content = client.get("/test.txt");
    @endcode

    @since WebDavClientIo 1.0
*/
public class WebDavClientIo {
    public {
        #! Default connect timeout (30 seconds, matches WebDavClient)
        const DefaultConnectTimeout = 30000;

        #! Default I/O timeout (30 seconds, matches WebDavClient)
        const DefaultTimeout = 30000;
    }

    private {
        #! The base server URL with http/https scheme (no path)
        string base_url;

        #! Base path for all operations (always ends with a '/')
        string base_path = "/";

        #! Async I/O connection manager for all HTTP requests
        HttpClientIo::HttpClientConnectionManager mgr;

        #! Connect timeout in milliseconds
        int connect_timeout;

        #! Transfer timeout in milliseconds
        int io_timeout;

        #! HTTP protocol selector ("auto", "h1", "h2", "h3")
        *string http_protocol;

        #! Logger
        *LoggerInterface logger;

        #! Default headers for all requests
        hash<string, string> default_headers;

        #! Debug flag
        bool debug = False;
    }

    #! Creates the WebDavClientIo from a hash of options
    /** @param opts a hash of options:
        - \c url: (required) the WebDAV server URL; supports \c http://, \c https://,
          \c webdav://, \c webdavs://, \c webdavio://, and \c webdavios:// schemes
        - \c timeout: (optional) transfer timeout in milliseconds (default: 30000)
        - \c connect_timeout: (optional) connection timeout in milliseconds (default: 30000)
        - \c http_protocol: (optional) HTTP protocol to use (\c "auto", \c "h1", \c "h2",
          \c "h3"; default: \c "auto")
        - \c logger: (optional) a \c LoggerInterface object for logging
        - \c headers: (optional) extra default headers as a hash
    */
    constructor(hash<auto> opts) {
        string input_url = opts.url ?? "";
        if (!input_url.val()) {
            throw "WEBDAVCLIENTIO-ERROR", "missing required 'url' option";
        }

        string mapped = WebDavClientIo::mapUrl(input_url);
        hash<UrlInfo> uinfo = parse_url(mapped);
        # Reconstruct host base URL without the path so the connection manager pools by host:port
        base_url = sprintf("%s://%s", uinfo.protocol, uinfo.host);
        if (uinfo.port) {
            base_url += sprintf(":%d", uinfo.port);
        }
        if (uinfo.path) {
            base_path = uinfo.path;
            if (base_path !~ /\/$/) {
                base_path += "/";
            }
        }

        connect_timeout = opts.connect_timeout ?? DefaultConnectTimeout;
        io_timeout = opts.timeout ?? DefaultTimeout;
        http_protocol = opts.http_protocol;
        logger = opts.logger;

        default_headers = {};
        if (opts.headers.typeCode() == NT_HASH) {
            default_headers += cast<hash<string, string>>(opts.headers);
        }

        mgr = createConnectionManager();
    }

    #! Destroys the client and cleans up resources
    destructor() {
        close();
    }

    #! Enables or disables debug output
    setDebug(bool val = True) {
        debug = val;
    }

    #! Returns the server's base URL (no path)
    string getURL() {
        return base_url;
    }

    #! Closes the client and releases resources
    /** The client can be reused after calling close(); a new connection will be established
        on the next request.
    */
    close() {
        mgr.closeAll();
        mgr = createConnectionManager();
    }

    #! Gets the supported DAV capabilities
    /** @return a list of DAV compliance classes (e.g., \c "1", \c "2", \c "3")
    */
    list<string> options(string path = "/") {
        hash<auto> resp = mgr.request(base_url, "OPTIONS", resolvePath(path), default_headers,
            NOTHING, io_timeout);
        *string dav_header = resp.headers.dav ?? resp.headers.DAV;
        if (!dav_header) {
            return ();
        }
        return map trim($1), dav_header.split(",");
    }

    #! Lists resources in a directory using PROPFIND
    /** @param path the path to list
        @param depth \c "0" for just the resource, \c "1" for immediate children,
        \c "infinity" for all descendants

        @return a list of resource information
    */
    list<hash<WebDavClient::WebDavResourceInfo>> list(string path = "/", string depth = "1") {
        return propfind(path, depth);
    }

    #! Performs a PROPFIND request
    /** @param path the resource path
        @param depth \c "0", \c "1", or \c "infinity"
        @param properties optional list of specific properties to request

        @return a list of resource information
    */
    list<hash<WebDavClient::WebDavResourceInfo>> propfind(string path = "/", string depth = "1",
            *list<string> properties) {
        hash<auto> body;
        if (properties) {
            hash<auto> props;
            foreach string prop in (properties) {
                props{"DAV:" + prop} = NOTHING;
            }
            body = {
                "DAV:propfind": {
                    "^attributes^": {"xmlns:DAV": WebDavClient::DavNs},
                    "DAV:prop": props,
                },
            };
        } else {
            body = {
                "DAV:propfind": {
                    "^attributes^": {"xmlns:DAV": WebDavClient::DavNs},
                    "DAV:allprop": NOTHING,
                },
            };
        }

        string xml_body = make_xml(body);
        hash<auto> hdrs = default_headers + {
            "Depth": depth,
            "Content-Type": MimeTypeXml,
        };

        on_error if (debug) printf("PROPFIND error: %s\n", $1.desc);

        hash<auto> resp = mgr.request(base_url, "PROPFIND", resolvePath(path), hdrs, xml_body,
            io_timeout);

        if (resp.status_code != 207) {
            throw "WEBDAV-ERROR", sprintf("PROPFIND failed with status %d: %s",
                resp.status_code, resp.body);
        }

        return parsePropfindResponse(resp.body);
    }

    #! Downloads a file
    /** @param path the file path

        @return the file contents as binary data, or @ref NOTHING if not found

        @throw WEBDAV-ERROR if the request returns a non-2xx, non-404 status
    */
    *data get(string path) {
        hash<auto> resp = mgr.request(base_url, "GET", resolvePath(path), default_headers,
            NOTHING, io_timeout);
        if (resp.status_code == 404) {
            return NOTHING;
        }
        if (resp.status_code < 200 || resp.status_code >= 300) {
            throw "WEBDAV-ERROR", sprintf("GET failed with status %d", resp.status_code);
        }
        return resp.body;
    }

    #! Uploads a file
    /** @param path the file path
        @param content the file contents
        @param content_type optional content type (default: \c application/octet-stream)

        @return @ref True if a new resource was created, @ref False if an existing resource was
        updated

        @throw WEBDAV-ERROR if the server returns a non-2xx status
    */
    bool put(string path, data content, *string content_type) {
        hash<auto> hdrs = default_headers + {
            "Content-Type": content_type ?? MimeTypeOctetStream,
        };
        hash<auto> resp = mgr.request(base_url, "PUT", resolvePath(path), hdrs, content, io_timeout);
        if (resp.status_code < 200 || resp.status_code >= 300) {
            throw "WEBDAV-ERROR", sprintf("PUT failed with status %d", resp.status_code);
        }
        return resp.status_code == 201;
    }

    #! Deletes a resource
    /** @param path the resource path

        @throw WEBDAV-ERROR if the server returns a non-2xx status
    */
    del(string path) {
        hash<auto> resp = mgr.request(base_url, "DELETE", resolvePath(path), default_headers,
            NOTHING, io_timeout);
        if (resp.status_code < 200 || resp.status_code >= 300) {
            throw "WEBDAV-ERROR", sprintf("DELETE failed with status %d", resp.status_code);
        }
    }

    #! Creates a collection (directory)
    /** @param path the collection path

        @throw WEBDAV-ERROR if the server returns a non-2xx status
    */
    mkcol(string path) {
        hash<auto> resp = mgr.request(base_url, "MKCOL", resolvePath(path), default_headers,
            NOTHING, io_timeout);
        if (resp.status_code < 200 || resp.status_code >= 300) {
            throw "WEBDAV-ERROR", sprintf("MKCOL failed with status %d", resp.status_code);
        }
    }

    #! Copies a resource
    /** @param src source path
        @param dest destination path
        @param overwrite whether to overwrite existing resources (default: @ref True)

        @throw WEBDAV-ERROR if the server returns a non-2xx status
    */
    copyResource(string src, string dest, bool overwrite = True) {
        string abs_dest = base_url + resolvePath(dest);
        hash<auto> hdrs = default_headers + {
            "Destination": abs_dest,
            "Overwrite": overwrite ? "T" : "F",
        };
        hash<auto> resp = mgr.request(base_url, "COPY", resolvePath(src), hdrs, NOTHING, io_timeout);
        if (resp.status_code < 200 || resp.status_code >= 300) {
            throw "WEBDAV-ERROR", sprintf("COPY failed with status %d", resp.status_code);
        }
    }

    #! Moves a resource
    /** @param src source path
        @param dest destination path
        @param overwrite whether to overwrite existing resources (default: @ref True)

        @throw WEBDAV-ERROR if the server returns a non-2xx status
    */
    moveResource(string src, string dest, bool overwrite = True) {
        string abs_dest = base_url + resolvePath(dest);
        hash<auto> hdrs = default_headers + {
            "Destination": abs_dest,
            "Overwrite": overwrite ? "T" : "F",
        };
        hash<auto> resp = mgr.request(base_url, "MOVE", resolvePath(src), hdrs, NOTHING, io_timeout);
        if (resp.status_code < 200 || resp.status_code >= 300) {
            throw "WEBDAV-ERROR", sprintf("MOVE failed with status %d", resp.status_code);
        }
    }

    #! Locks a resource
    /** @param path the resource path
        @param scope \c "exclusive" or \c "shared"
        @param owner optional owner information
        @param timeout timeout in seconds (\c 0 for infinite)
        @param depth \c "0" or \c "infinity"

        @return lock information including the lock token
    */
    hash<WebDavClient::WebDavLockInfo> lock(string path, string scope = "exclusive", *string owner,
            int timeout = 0, string depth = "infinity") {
        hash<auto> body = {
            "DAV:lockinfo": {
                "^attributes^": {"xmlns:DAV": WebDavClient::DavNs},
                "DAV:lockscope": scope == "exclusive"
                    ? {"DAV:exclusive": NOTHING}
                    : {"DAV:shared": NOTHING},
                "DAV:locktype": {"DAV:write": NOTHING},
            },
        };
        if (owner) {
            body."DAV:lockinfo"."DAV:owner" = {"DAV:href": owner};
        }
        string xml_body = make_xml(body);

        hash<auto> hdrs = default_headers + {
            "Depth": depth,
            "Content-Type": MimeTypeXml,
        };
        if (timeout > 0) {
            hdrs.Timeout = sprintf("Second-%d", timeout);
        } else {
            hdrs.Timeout = "Infinite";
        }

        hash<auto> resp = mgr.request(base_url, "LOCK", resolvePath(path), hdrs, xml_body,
            io_timeout);

        if (resp.status_code != 200 && resp.status_code != 201) {
            throw "WEBDAV-LOCK-ERROR", sprintf("LOCK failed with status %d", resp.status_code);
        }

        # Parse lock token from response
        *string lock_token = resp.headers."lock-token" ?? resp.headers."Lock-Token";
        if (lock_token) {
            lock_token =~ s/^<//;
            lock_token =~ s/>$//;
        }

        return <WebDavClient::WebDavLockInfo>{
            "token": lock_token,
            "scope": scope,
            "type": "write",
            "depth": depth,
            "owner": owner,
            "timeout": timeout,
        };
    }

    #! Unlocks a resource
    /** @param path the resource path
        @param token the lock token

        @throw WEBDAV-ERROR if the server returns a non-2xx status
    */
    unlock(string path, string token) {
        hash<auto> hdrs = default_headers + {
            "Lock-Token": sprintf("<%s>", token),
        };
        hash<auto> resp = mgr.request(base_url, "UNLOCK", resolvePath(path), hdrs, NOTHING,
            io_timeout);
        if (resp.status_code < 200 || resp.status_code >= 300) {
            throw "WEBDAV-ERROR", sprintf("UNLOCK failed with status %d", resp.status_code);
        }
    }

    #! Checks if a resource exists
    /** @param path the resource path

        @return @ref True if the resource exists, @ref False otherwise
    */
    bool exists(string path) {
        hash<auto> resp = mgr.request(base_url, "HEAD", resolvePath(path), default_headers,
            NOTHING, io_timeout);
        if (resp.status_code == 404) {
            return False;
        }
        if (resp.status_code < 200 || resp.status_code >= 300) {
            throw "WEBDAV-ERROR", sprintf("HEAD failed with status %d", resp.status_code);
        }
        return True;
    }

    #! Resolves a path relative to the base path
    private string resolvePath(string path) {
        if (path =~ /^\//) {
            return path;
        }
        return base_path + path;
    }

    #! Parses a PROPFIND response into a list of resource records
    private list<hash<WebDavClient::WebDavResourceInfo>> parsePropfindResponse(auto body) {
        if (!body) {
            return ();
        }
        hash<auto> xml;
        if (body.typeCode() == NT_STRING || body.typeCode() == NT_BINARY) {
            xml = parse_xml(body, XPF_PRESERVE_ORDER);
        } else {
            xml = body;
        }
        list<hash<WebDavClient::WebDavResourceInfo>> result = ();
        *auto responses = xml."DAV:multistatus"."DAV:response";
        if (!responses) {
            return result;
        }
        if (responses.typeCode() != NT_LIST) {
            responses = (responses,);
        }
        foreach hash<auto> resp in (responses) {
            result += parseResourceResponse(resp);
        }
        return result;
    }

    #! Parses a single PROPFIND response element into a resource info hash
    private hash<WebDavClient::WebDavResourceInfo> parseResourceResponse(hash<auto> resp) {
        string href = resp."DAV:href" ?? "";
        hash<auto> props;
        auto propstats = resp."DAV:propstat";
        if (propstats.typeCode() != NT_LIST) {
            propstats = (propstats,);
        }
        foreach auto propstat in (propstats) {
            if (propstat.typeCode() != NT_HASH) {
                continue;
            }
            *string status = propstat."DAV:status";
            if (status && status =~ /200/) {
                props = propstat."DAV:prop";
                break;
            }
        }
        bool is_collection = props."DAV:resourcetype".hasKey("DAV:collection");
        return <WebDavClient::WebDavResourceInfo>{
            "href": href,
            "displayname": props."DAV:displayname",
            "type": is_collection ? "collection" : "file",
            "contenttype": props."DAV:getcontenttype",
            "contentlength": props."DAV:getcontentlength" ? int(props."DAV:getcontentlength") : NOTHING,
            "lastmodified": parseDate(props."DAV:getlastmodified"),
            "creationdate": parseDate(props."DAV:creationdate"),
            "etag": props."DAV:getetag",
        };
    }

    #! Parses an HTTP-format date string into a Qore date, or @ref NOTHING if unparseable
    private *date parseDate(*string str) {
        if (!str) {
            return NOTHING;
        }
        try {
            return date(str);
        } catch (hash<ExceptionInfo> ex) {
            return NOTHING;
        }
    }

    #! Internal: Creates a new HttpClientConnectionManager
    private HttpClientIo::HttpClientConnectionManager createConnectionManager() {
        return new HttpClientIo::HttpClientConnectionManager(
            <HttpClientIo::HttpClientConnectionManagerOptions>{
                "connect_timeout": connect_timeout,
                "request_timeout": io_timeout,
                "protocol": http_protocol ?? "auto",
            });
    }

    #! Internal: Maps webdav-style URL schemes to http/https
    private static string mapUrl(string input_url) {
        if (input_url =~ /^webdavios:/) {
            return regex_subst(input_url, "^webdavios:", "https:");
        }
        if (input_url =~ /^webdavio:/) {
            return regex_subst(input_url, "^webdavio:", "http:");
        }
        if (input_url =~ /^webdavs:/) {
            return regex_subst(input_url, "^webdavs:", "https:");
        }
        if (input_url =~ /^webdav:/) {
            return regex_subst(input_url, "^webdav:", "http:");
        }
        return input_url;
    }
}

} # namespace WebDavClientIo
