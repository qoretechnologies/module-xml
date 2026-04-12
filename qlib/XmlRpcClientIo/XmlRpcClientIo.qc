# -*- mode: qore; indent-tabs-mode: nil -*-
#! @file XmlRpcClientIo.qc @brief Pure-Qore XML-RPC client with async I/O

/*  XmlRpcClientIo.qc Copyright (C) 2026 Qore Technologies, s.r.o.

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

#! the %XmlRpcClientIo namespace holds all public definitions in the %XmlRpcClientIo module
public namespace XmlRpcClientIo {

#! Pure-Qore XML-RPC client with async I/O via HttpClientIo
/** This class provides an XML-RPC client implementation using
    \c HttpClientIo::HttpClientConnectionManager for async I/O with automatic protocol
    negotiation (HTTP/3 &rarr; HTTP/2 &rarr; HTTP/1.1) and connection pooling.

    It matches the API of the native \c XmlRpcClient class.

    @par Example:
    @code{.py}
XmlRpcClientIo client("http://localhost:8080/RPC2");
hash<auto> result = client.call("system.listMethods");
if (result.fault) {
    printf("error: %s\n", result.fault.faultString);
} else {
    printf("result: %N\n", result.params);
}
client.close();
    @endcode

    @since xml 2.3
*/
public class XmlRpcClientIo {
    public {
        #! Default connect timeout (45 seconds, matches native XmlRpcClient)
        const DefaultConnectTimeout = 45000;

        #! Default I/O timeout (45 seconds, matches native XmlRpcClient)
        const DefaultTimeout = 45000;

        #! Default Content-Type header value
        const DefaultContentType = "text/xml;charset=utf-8";

        #! Default Accept header value
        const DefaultAccept = "text/xml";

        #! Default User-Agent header value
        const DefaultUserAgent = "Qore-XML-RPC-Client-Io/1.0";
    }

    private {
        #! The server URL (with http/https scheme)
        string url;

        #! The request path extracted from the URL
        string url_path;

        #! Async I/O connection manager for all HTTP requests
        HttpClientIo::HttpClientConnectionManager mgr;

        #! Connect timeout in milliseconds
        int connect_timeout;

        #! Transfer timeout in milliseconds
        int io_timeout;

        #! Protocol for the connection manager ("h1", "h2", "h3", or "auto")
        *string http_protocol;

        #! Logger
        *LoggerInterface logger;

        #! Default headers for all requests
        hash<string, string> default_headers;
    }

    #! Creates the XmlRpcClientIo with the given URL and options
    /** @param url the URL of the XML-RPC server; supports \c http://, \c https://,
        \c xmlrpc://, \c xmlrpcs://, \c xmlrpcio://, and \c xmlrpcios:// schemes
        @param opts optional client options:
        - \c connect_timeout: connection timeout in milliseconds (default: 45000)
        - \c timeout: transfer timeout in milliseconds (default: 45000)
        - \c default_path: default URL path if none in URL (default: \c "RPC2")
        - \c http_protocol: HTTP protocol to use (\c "auto", \c "h1", \c "h2", \c "h3"; default: \c "auto")
        - \c logger: a \c LoggerInterface object for logging
        - \c headers: extra default headers as a hash

        @par Example:
        @code{.py}
XmlRpcClientIo client("http://localhost:8080/RPC2", {"timeout": 30000});
        @endcode
    */
    constructor(string url, *hash<auto> opts) {
        # Map custom schemes to http/https
        self.url = mapUrl(url);
        *string path = parse_url(self.url).path;
        string default_path = opts.default_path ?? DefaultXmlRpcPath;
        if (!path.val()) {
            # Append default path if none in URL
            url_path = "/" + default_path;
            self.url += url_path;
        } else {
            url_path = path;
        }

        connect_timeout = opts.connect_timeout ?? DefaultConnectTimeout;
        io_timeout = opts.timeout ?? DefaultTimeout;
        http_protocol = opts.http_protocol;
        logger = opts.logger;

        default_headers = {
            "Content-Type": DefaultContentType,
            "Accept": DefaultAccept,
            "User-Agent": DefaultUserAgent,
        };
        if (opts.headers.typeCode() == NT_HASH) {
            default_headers += cast<hash<string, string>>(opts.headers);
        }

        mgr = createConnectionManager();
    }

    #! Creates the XmlRpcClientIo from a hash of options (legacy-compatible form)
    /** @param opts options hash; supports the same keys as the primary constructor \c opts parameter,
        plus a required \c url key
        @param no_connect this parameter is accepted for compatibility but ignored; connections
        are established on demand

        @par Example:
        @code{.py}
XmlRpcClientIo client({"url": "http://localhost:8080/RPC2", "timeout": 30000});
        @endcode
    */
    constructor(hash<auto> opts, softbool no_connect = False) {
        string input_url = opts.url ?? "";
        if (!input_url.val()) {
            throw "XMLRPCCLIENTIO-ERROR", "missing required 'url' option";
        }

        self.url = mapUrl(input_url);
        *string path = parse_url(self.url).path;
        string default_path = opts.default_path ?? DefaultXmlRpcPath;
        if (!path.val()) {
            url_path = "/" + default_path;
            self.url += url_path;
        } else {
            url_path = path;
        }

        connect_timeout = opts.connect_timeout ?? DefaultConnectTimeout;
        io_timeout = opts.timeout ?? DefaultTimeout;
        http_protocol = opts.http_protocol;
        logger = opts.logger;

        default_headers = {
            "Content-Type": DefaultContentType,
            "Accept": DefaultAccept,
            "User-Agent": DefaultUserAgent,
        };
        if (opts.headers.typeCode() == NT_HASH) {
            default_headers += cast<hash<string, string>>(opts.headers);
        }

        mgr = createConnectionManager();
    }

    #! Destroys the client and cleans up resources
    destructor() {
        close();
    }

    #! Calls a remote method taking all arguments after the method name for the method arguments
    /** @param method the XML-RPC method name to call
        @param ... the arguments to the call

        @return a hash with one of the following keys:
        - \c params: will be present if the call completed normally
        - \c fault: will be present if the call is returning with error information; if this key is
          present then the value will be a hash with the following two keys:
          - \c faultCode: an integer fault code
          - \c faultString: a string error message

        @throw XMLRPC-SERIALIZATION-ERROR empty member name in hash or cannot serialize type to XML-RPC
        @throw PARSE-XMLRPC-RESPONSE-ERROR missing required element or other syntax error
        @throw PARSE-XMLRPC-ERROR syntax error parsing XML-RPC string
        @throw XMLRPCCLIENTIO-HTTP-ERROR HTTP error from server
        @throw XMLRPCCLIENTIO-RESPONSE-ERROR empty or invalid response

        @par Example:
        @code{.py}
hash<auto> result = client.call("method.name", arg1, arg2);
        @endcode
    */
    hash<auto> call(string method, ...) {
        string body = make_xmlrpc_call(method, argv);
        return doRequest(body);
    }

    #! Calls a remote method using a single value after the method name for the method arguments
    /** @param method the XML-RPC method name to call
        @param args an optional list of arguments (or single argument) for the method

        @return a hash with one of the following keys:
        - \c params: will be present if the call completed normally
        - \c fault: will be present if the call is returning with error information; if this key is
          present then the value will be a hash with the following two keys:
          - \c faultCode: an integer fault code
          - \c faultString: a string error message

        @throw XMLRPC-SERIALIZATION-ERROR empty member name in hash or cannot serialize type to XML-RPC
        @throw PARSE-XMLRPC-RESPONSE-ERROR missing required element or other syntax error
        @throw PARSE-XMLRPC-ERROR syntax error parsing XML-RPC string
        @throw XMLRPCCLIENTIO-HTTP-ERROR HTTP error from server
        @throw XMLRPCCLIENTIO-RESPONSE-ERROR empty or invalid response

        @par Example:
        @code{.py}
hash<auto> result = client.callArgs("method.name", arg_list);
        @endcode
    */
    hash<auto> callArgs(string method, auto args) {
        string body = make_xmlrpc_call(method, args);
        return doRequest(body);
    }

    #! Calls a remote method taking all arguments after the method name; populates a reference hash with debug info
    /** @param info a reference to a hash that provides the following keys on output:
        - \c request: the literal outgoing request body sent
        - \c request_headers: a hash of HTTP headers in the outgoing request
        - \c response_code: the HTTP response status code
        - \c response: the literal response body received from the server
        - \c response_headers: a hash of headers received in the response
        @param method the XML-RPC method name to call
        @param ... the arguments to the call

        @return a hash with one of the following keys:
        - \c params: will be present if the call completed normally
        - \c fault: will be present if the call is returning with error information

        @throw XMLRPC-SERIALIZATION-ERROR empty member name in hash or cannot serialize type to XML-RPC
        @throw PARSE-XMLRPC-RESPONSE-ERROR missing required element or other syntax error
        @throw PARSE-XMLRPC-ERROR syntax error parsing XML-RPC string
        @throw XMLRPCCLIENTIO-HTTP-ERROR HTTP error from server
        @throw XMLRPCCLIENTIO-RESPONSE-ERROR empty or invalid response

        @par Example:
        @code{.py}
hash<auto> info;
hash<auto> result = client.callWithInfo(\info, "method.name", arg1, arg2);
        @endcode
    */
    hash<auto> callWithInfo(reference<hash<auto>> info, string method, ...) {
        string body = make_xmlrpc_call(method, argv);
        return doRequestWithInfo(body, \info);
    }

    #! Calls a remote method using a single value for the arguments; populates a reference hash with debug info
    /** @param info a reference to a hash that provides the following keys on output:
        - \c request: the literal outgoing request body sent
        - \c request_headers: a hash of HTTP headers in the outgoing request
        - \c response_code: the HTTP response status code
        - \c response: the literal response body received from the server
        - \c response_headers: a hash of headers received in the response
        @param method the XML-RPC method name to call
        @param args an optional list of arguments (or single argument) for the method

        @return a hash with one of the following keys:
        - \c params: will be present if the call completed normally
        - \c fault: will be present if the call is returning with error information

        @throw XMLRPC-SERIALIZATION-ERROR empty member name in hash or cannot serialize type to XML-RPC
        @throw PARSE-XMLRPC-RESPONSE-ERROR missing required element or other syntax error
        @throw PARSE-XMLRPC-ERROR syntax error parsing XML-RPC string
        @throw XMLRPCCLIENTIO-HTTP-ERROR HTTP error from server
        @throw XMLRPCCLIENTIO-RESPONSE-ERROR empty or invalid response

        @par Example:
        @code{.py}
hash<auto> info;
hash<auto> result = client.callArgsWithInfo(\info, "method.name", arg_list);
        @endcode
    */
    hash<auto> callArgsWithInfo(reference<hash<auto>> info, string method, auto args) {
        string body = make_xmlrpc_call(method, args);
        return doRequestWithInfo(body, \info);
    }

    #! Returns the server URL
    /** @return the full URL including path
    */
    string getUrl() {
        return url;
    }

    #! Closes the client and releases resources
    /** The client can be reused after calling close(); a new connection will be established
        on the next request.
    */
    close() {
        mgr.closeAll();
        # Recreate the manager so the client can be reused after close
        mgr = createConnectionManager();
    }

    #! Internal: Sends an XML-RPC request via HTTP POST and returns the parsed response
    /** @param body the XML-RPC request body as a string

        @return the parsed XML-RPC response hash

        @throw XMLRPCCLIENTIO-HTTP-ERROR HTTP error from server
        @throw XMLRPCCLIENTIO-RESPONSE-ERROR empty response body
    */
    private hash<auto> doRequest(string body) {
        hash<auto> resp = mgr.request(url, "POST", url_path, default_headers, body, io_timeout);

        if (resp.status_code < 200 || resp.status_code >= 300) {
            throw "XMLRPCCLIENTIO-HTTP-ERROR",
                sprintf("HTTP error %d from %s", resp.status_code, url);
        }

        if (!resp.body) {
            throw "XMLRPCCLIENTIO-RESPONSE-ERROR", "empty response body from server";
        }

        return parse_xmlrpc_response(resp.body);
    }

    #! Internal: Sends an XML-RPC request via HTTP POST, populates debug info, and returns the parsed response
    /** @param body the XML-RPC request body as a string
        @param info a reference to a hash that will be populated with debug info

        @return the parsed XML-RPC response hash

        @throw XMLRPCCLIENTIO-HTTP-ERROR HTTP error from server
        @throw XMLRPCCLIENTIO-RESPONSE-ERROR empty response body
    */
    private hash<auto> doRequestWithInfo(string body, reference<hash<auto>> info) {
        info.request = body;
        info.request_headers = {} + default_headers;

        hash<auto> resp = mgr.request(url, "POST", url_path, default_headers, body, io_timeout);

        info.response_code = resp.status_code;
        info.response = resp.body;
        info.response_headers = resp.headers;

        if (resp.status_code < 200 || resp.status_code >= 300) {
            throw "XMLRPCCLIENTIO-HTTP-ERROR",
                sprintf("HTTP error %d from %s", resp.status_code, url);
        }

        if (!resp.body) {
            throw "XMLRPCCLIENTIO-RESPONSE-ERROR", "empty response body from server";
        }

        return parse_xmlrpc_response(resp.body);
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

    #! Internal: Maps custom URL schemes to http/https
    /** @param input_url the input URL potentially with xmlrpc[s]://, xmlrpcio[s]://, etc.
        @return the URL with http:// or https:// scheme
    */
    private static string mapUrl(string input_url) {
        if (input_url =~ /^xmlrpcios:/) {
            return regex_subst(input_url, "^xmlrpcios:", "https:");
        }
        if (input_url =~ /^xmlrpcio:/) {
            return regex_subst(input_url, "^xmlrpcio:", "http:");
        }
        if (input_url =~ /^xmlrpcs:/) {
            return regex_subst(input_url, "^xmlrpcs:", "https:");
        }
        if (input_url =~ /^xmlrpc:/) {
            return regex_subst(input_url, "^xmlrpc:", "http:");
        }
        return input_url;
    }
}

} # namespace XmlRpcClientIo
