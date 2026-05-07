# -*- mode: qore; indent-tabs-mode: nil -*-
#! @file WebDavIoConnection.qc @brief WebDAV connection class for the async I/O WebDavClientIo

/*  WebDavIoConnection.qc Copyright (C) 2026 Qore Technologies, s.r.o.

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

public namespace WebDavClientIo {

#! WebDAV connection class for ConnectionProvider integration; instantiates @ref WebDavClientIo
public class WebDavIoConnection inherits ConnectionProvider::HttpBasedConnection {
    public {
        const ConnectionScheme = <ConnectionSchemeInfo>{
            "display_name": "WebDAV (Async I/O)",
            "short_desc": "WebDAV server connection using async socket I/O",
            "desc": "WebDAV server connection supporting RFC 4918 operations using async I/O via "
                "`HttpClientIo::HttpClientConnectionManager`. This is the preferred connection "
                "type for new code; the legacy `webdav`/`webdavs` schemes built on the synchronous "
                "`HTTPClient` remain available for backward compatibility.",
            "cls": Class::forName("WebDavClientIo::WebDavIoConnection"),
            "schemes": {
                "webdavio": True,
                "webdavios": True,
            },
            "options": HttpConnection::ConnectionScheme.options + {
                "root_path": <ConnectionOptionInfo>{
                    "display_name": "Root Path",
                    "short_desc": "Root path for WebDAV operations",
                    "type": "string",
                    "desc": "Root path that will be prepended to all WebDAV operations",
                    "default_value": "/",
                },
                "http_protocol": <ConnectionOptionInfo>{
                    "display_name": "HTTP Protocol",
                    "short_desc": "HTTP protocol selector for the async connection manager",
                    "type": "string",
                    "desc": "Selects the HTTP protocol used by the async connection manager: "
                        "`auto` (default; HTTP/3 preferred, falls back to HTTP/2 then HTTP/1.1), "
                        "`h1`, `h2`, or `h3`.",
                    "default_value": "auto",
                    "allowed_values": (
                        <AllowedValueInfo>{"value": "auto", "display_name": "Auto-Negotiate"},
                        <AllowedValueInfo>{"value": "h1", "display_name": "HTTP/1.1"},
                        <AllowedValueInfo>{"value": "h2", "display_name": "HTTP/2"},
                        <AllowedValueInfo>{"value": "h3", "display_name": "HTTP/3"},
                    ),
                },
                "ping_method": <ConnectionOptionInfo>{
                    "display_name": "Ping Method",
                    "short_desc": "HTTP method for advanced ping",
                    "type": "string",
                    "desc": "HTTP method for an advanced ping; must be set together with `ping_path`",
                },
                "ping_path": <ConnectionOptionInfo>{
                    "display_name": "Ping Path",
                    "short_desc": "URI path for advanced ping",
                    "type": "string",
                    "desc": "URI path for an advanced ping; must be set together with `ping_method`. "
                        "Leading `/` replaces the connection path; otherwise it is appended.",
                },
                "ping_headers": <ConnectionOptionInfo>{
                    "display_name": "Ping Headers",
                    "short_desc": "Headers sent with the advanced ping",
                    "type": "hash",
                    "desc": "Headers sent with the advanced ping; ignored when `ping_method` and `ping_path` are not both set",
                },
                "ping_body": <ConnectionOptionInfo>{
                    "display_name": "Ping Body",
                    "short_desc": "Body sent with the advanced ping",
                    "type": "auto",
                    "desc": "Body sent with the advanced ping; ignored when `ping_method` is `GET` "
                        "or when `ping_path`/`ping_method` are not both set",
                },
            },
        };
    }

    #! Creates the connection object
    constructor(string name, string description, string url, hash<auto> attributes = {},
            hash<auto> options = {})
            : HttpBasedConnection(name, description, url, attributes, options) {
    }

    #! Returns the connection scheme info
    hash<ConnectionSchemeInfo> getConnectionSchemeInfo() {
        return ConnectionScheme;
    }

    #! Returns \c "webdavio"
    string getType() {
        return "webdavio";
    }

    #! Creates the underlying @ref WebDavClientIo object
    private WebDavClientIo getImpl(bool connect = True, *hash<auto> rtopts) {
        return new WebDavClientIo(getRealOpts() + rtopts);
    }

    #! Returns connection options with the URL scheme normalized to http/https
    private hash<auto> getRealOpts() {
        string real_url = url;
        if (real_url =~ /^webdavios:/) {
            real_url =~ s/^webdavios:/https:/;
        } else if (real_url =~ /^webdavio:/) {
            real_url =~ s/^webdavio:/http:/;
        }
        return {"url": real_url} + opts;
    }

    #! Starts a non-blocking polling ping operation against the remote WebDAV server
    Qore::AbstractPollOperation startPollConnect(*Logger::LoggerInterface logger) {
        if (!(opts.ping_method && opts.ping_path)) {
            return HttpBasedConnection::startPollConnect(logger);
        }
        hash<auto> headers;
        headers += opts.headers;
        headers += opts.ping_headers;
        hash<auto> http_opts = opts{keys HttpConnection::ConnectionScheme.options} + {"url": real_url};
        return new ConnectionProvider::HttpPingPollOperation(real_url, opts.ping_method,
            opts.ping_path, http_opts, headers,
            (opts.ping_method == "GET" ? NOTHING : opts.ping_body),
            logger, "WEBDAV-PING-ERROR", "WebDavIoConnection");
    }

    #! Returns the ConnectionSchemeInfo hash
    private hash<ConnectionSchemeInfo> getConnectionSchemeInfoImpl() {
        return ConnectionScheme;
    }
}

} # namespace WebDavClientIo
