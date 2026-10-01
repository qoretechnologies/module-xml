# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavHandler module Copyright 2019 - 2026 Qore Technologies, s.r.o.

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

public namespace WebDavHandler {

#! Routes WebDAV requests to child handlers and provides a virtual root collection
/** Uses DummyWebDavHandler's concrete defaults for operations not handled by the proxy.

    Each child must use its complete public mount path as its virtual base,
    including this proxy's base path. Requests and Destination headers retain
    their public URLs so child listings and COPY/MOVE destinations agree.

    @par Example:
    @code{.py}
    FsWebDavHandler files("/srv/documents", NOTHING, "/dav/files");
    WebDavHandlerProxy proxy({"files": files}, "/dav");
    @endcode
*/
public class WebDavHandlerProxy inherits DummyWebDavHandler {
    private {
        hash<string, AbstractWebDavHandler> m_ifaces;
    }

    #! Creates the object with an empty logger and an in-memory property handler
    /** @param interfaces the WebDAV handlers to proxy
    */
    constructor(hash<string, AbstractWebDavHandler> interfaces) {
        m_ifaces = interfaces;
    }

    #! Creates the object with the given argument and an in-memory property handler
    /** @param interfaces the WebDAV handlers to proxy
        @param virtual_relative_path_base the virtual base path for WebDavHandler requests; this path will be
        stripped from requests internally when serving WebDavHandler resources
    */
    constructor(hash<string, AbstractWebDavHandler> interfaces, string virtual_relative_path_base)
            : DummyWebDavHandler(virtual_relative_path_base) {
        m_ifaces = interfaces;
    }

    #! Creates the object with the given arguments
    /** @param interfaces the WebDAV handlers to proxy
        @param logger the logger
        @param virtual_relative_path_base the virtual base path for WebDavHandler requests; this path will be
        stripped from requests internally when serving WebDavHandler resources
    */
    constructor(hash<string, AbstractWebDavHandler> interfaces, Logger logger,
            string virtual_relative_path_base = "/")
                : DummyWebDavHandler(logger, new InMemoryWebDavPropertyHandler(), virtual_relative_path_base) {
        m_ifaces = interfaces;
    }

    private *hash<HttpResponseInfo> handleChildRaw(hash<auto> cx, hash<auto> hdr, *data body) {
        string path = getRelativePath(cx.raw_path);
        path =~ s/^\/+//;
        list<string> parts = path.split("/");
        if (parts.size() && m_ifaces.hasKey(parts[0])) {
            # Child dispatch must derive its filesystem path and enforce its own
            # authentication and lock preconditions before invoking a method.
            return m_ifaces{parts[0]}.handleRequest(cx, hdr, body);
        }
    }

    private hash<HttpResponseInfo> handleChild(hash<auto> cx, hash<auto> hdr, *data body) {
        return handleChildRaw(cx, hdr, body) ?? response(501, "Not Implemented");
    }

    /**
        GET

        Get a resource.
    */
    hash<HttpResponseInfo> handleGet(hash<auto> cx, hash<auto> hdr, *data body) {
        return handleChild(cx, hdr, body);
    }

    /**
        HEAD

        Same like GET but without sending a body.
    */
    hash<HttpResponseInfo> handleHead(hash<auto> cx, hash<auto> hdr, *data body) {
        return handleChild(cx, hdr, body);
    }

    /**
        POST

        Create new resource.
    */
    hash<HttpResponseInfo> handlePost(hash<auto> cx, hash<auto> hdr, *data body) {
        return handleChild(cx, hdr, body);
    }

    /**
        PUT

        Modify resource.
    */
    hash<HttpResponseInfo> handlePut(hash<auto> cx, hash<auto> hdr, *data body) {
        return handleChild(cx, hdr, body);
    }

    /**
        DELETE

        Delete a resource.
    */
    hash<HttpResponseInfo> handleDelete(hash<auto> cx, hash<auto> hdr, *data body) {
        return handleChild(cx, hdr, body);
    }

    /**
        COPY

        Copy a resource from one URI to another.
    */
    hash<HttpResponseInfo> handleCopy(hash<auto> cx, hash<auto> hdr, *data body) {
        return handleChild(cx, hdr, body);
    }

    /**
        MOVE

        Move a resource from one URI to another.
    */
    hash<HttpResponseInfo> handleMove(hash<auto> cx, hash<auto> hdr, *data body) {
        return handleChild(cx, hdr, body);
    }

    /**
        LOCK

        Put a lock on a resource. WebDavHandler supports both shared and exclusive locks.
    */
    hash<HttpResponseInfo> handleLock(hash<auto> cx, hash<auto> hdr, *data body) {
        return response(501, "Not Implemented");
    }

    /**
        UNLOCK

        Remove a lock from a resource.
    */
    hash<HttpResponseInfo> handleUnlock(hash<auto> cx, hash<auto> hdr, *data body) {
        return handleChild(cx, hdr, body);
    }

    /**
        MKCOL

        Create collections (aka a directory).
    */
    hash<HttpResponseInfo> handleMkcol(hash<auto> cx, hash<auto> hdr, *data body) {
        return handleChild(cx, hdr, body);
    }

    /**
        PROPFIND

        Retrieve properties, stored as XML, from a web resource. It is also
        overloaded to allow one to retrieve the collection structure (also
        known as directory hierarchy) of a remote system.
    */
    hash<HttpResponseInfo> handlePropfind(hash<auto> cx, hash<auto> hdr, *data body) {
        # handle children first
        *hash<HttpResponseInfo> ret = handleChildRaw(cx, hdr, body);
        if (ret) {
            return cast<hash<HttpResponseInfo>>(ret);
        }

        # then top level impl
        hash<auto> resp = {
            "DAV:multistatus" : {
                "^attributes^" : {"xmlns:DAV": "DAV:"},
                "DAV:response" : list(),
            },
        };

        HashIterator it(m_ifaces);
        while (it.next()) {
            hash<auto> props = {
                "displayname": it.getKey(),
                "size": 0,
            };
            string path = cx.raw_path;
            path =~ s/\/+$//;
            path += "/" + it.getKey();
            resp."DAV:multistatus"."DAV:response" += preparePropFindXmlResponse(path, path, True, props);
        }

        return <HttpResponseInfo>{
            "code": 207,
            "hdr": {"Content-Type": MimeTypeXml + "; charset=UTF-8"},
            "body": make_xml(resp),
        };
    }

    /**
        PROPPATCH

        Change and delete multiple properties on a resource in a single atomic act.
    */
    hash<HttpResponseInfo> handleProppatch(hash<auto> cx, hash<auto> hdr, *data body) {
        return handleChild(cx, hdr, body);
    }
} # class WebDavHandlerProxy
} # namespace WebDavHandler
