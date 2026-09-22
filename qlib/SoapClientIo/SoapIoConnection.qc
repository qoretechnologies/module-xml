# -*- mode: qore; indent-tabs-mode: nil -*-
#! @file SoapIoConnection.qc @brief SOAP async I/O connection provider class

/*  SoapIoConnection.qc Copyright (C) 2026 Qore Technologies, s.r.o.

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

#! the %SoapClientIo namespace holds all public definitions in the %SoapClientIo module
public namespace SoapClientIo {

#! Class for SOAP async I/O client connections; returns @ref SoapClientIo objects
/** supports the following options:
    - \c "wsdl": overrides the WSDL URL provided by the connection URL
    - \c "service": the name of the SOAP service to use
    - \c "port": the SOAP port to use
    - \c "target_url": overrides the URL in the WSDL
    - \c "connect_timeout": connection timeout to use in milliseconds (default: 45000)
    - \c "timeout": transfer timeout to use in milliseconds (default: 45000)

    @see @ref SoapClientIo::SoapClientIo "SoapClientIo::constructor()" for more information on the
    above options
*/
public class SoapIoConnection inherits ConnectionProvider::HttpBasedConnection {
    public {
        #! real options for creating the SOAP client
        hash<auto> real_opts;

        #! Connection entry info
        const ConnectionScheme = <ConnectionSchemeInfo>{
            "display_name": "SOAP (Async I/O) Connection",
            "short_desc": "A connection to a SOAP server using async I/O",
            "desc": "A connection to a SOAP server using async I/O via HttpClientIo with automatic "
                "protocol negotiation (HTTP/3, HTTP/2, HTTP/1.1)",
            "cls": Class::forName("SoapClientIo::SoapIoConnection"),
            "schemes": {
                "soapios": True,
                "soapio": True,
            },
            "base_scheme_map": {
                "https": "soapios",
                "http": "soapio",
            },
            "options": HttpConnection::ConnectionScheme.options + {
                "service": <ConnectionOptionInfo>{
                    "display_name": "SOAP Service",
                    "short_desc": "The name of the SOAP service to use",
                    "type": "string",
                    "desc": "The name of the SOAP service to use; mandatory if more than one service is "
                        "defined in the WSDL",
                },
                "port": <ConnectionOptionInfo>{
                    "display_name": "SOAP Port",
                    "short_desc": "The SOAP port to use",
                    "type": "string",
                    "desc": "In case multiple port entries are found in the WSDL, give the one to be used here",
                },
                "target_url": <ConnectionOptionInfo>{
                    "display_name": "Override URL",
                    "short_desc": "Overrides the URL in the WSDL",
                    "type": "string",
                    "desc": "Overrides the URL in the WSDL",
                },
                "mtom": <ConnectionOptionInfo>{
                    "display_name": "MTOM Requests",
                    "short_desc": "Send requests as MTOM/XOP packages",
                    "type": "bool",
                    "default_value": False,
                    "desc": "Send SOAP requests as MTOM/XOP packages: `base64Binary` content of at least "
                        "`mtom_threshold` octets travels as binary MIME parts instead of base64 text, which "
                        "shortens large document and image uploads. MTOM responses are always accepted.",
                },
                "mtom_threshold": <ConnectionOptionInfo>{
                    "display_name": "MTOM Part Threshold",
                    "short_desc": "The smallest binary value sent as an MTOM part",
                    "type": "int",
                    "default_value": WSDL::MTOM_THRESHOLD,
                    "desc": "The minimum size in octets of `base64Binary` content sent as a binary MTOM part; "
                        "`0` sends every value as a part. Applies only when `mtom` is `True`.",
                },
                "wsdl": <ConnectionOptionInfo>{
                    "display_name": "WSDL URL",
                    "short_desc": "The URL for the WSDL",
                    "type": "file-as-string",
                    "desc": "Overrides the WSDL URL provided by the connection URL",
                    "freeform": True,
                },
            },
        };
    }

    #! creates the SoapIoConnection object
    /** @param name the name of the connection
        @param description connection description
        @param url connection URL (potentially with password info)
        @param attributes various attributes. See below
        @param options connection options

        See \c AbstractConnection::constructor() for \c attributes and \c options reference.
    */
    constructor(string name, string description, string url, hash<auto> attributes = {},
            hash<auto> options = {}) : HttpBasedConnection(name, description, url, attributes, options) {
        real_opts = {"url": real_url} + opts;
    }

    #! creates the object from the arguments
    /** @param config with the following keys:
        - name (required string): the connection name
        - display_name (optional string): the display name
        - short_desc (optional string): a short description in plain text
        - desc (optional string): a long description with markdown formatting
        - url (required string): the connection URL
        - opts (optional hash): connection options
        - logger (optional LoggerInterface object): logger for the connection
        @param attr optional connection attributes
        - monitor (optional bool): should the connection be monitored? Default: True
        - enabled (optional bool): is the connection enabled? Default: True
        - locked (optional bool): is the connection locked? Default: False
        - debug_data (optional bool): debug data? Default: False
        - tags (optional hash): tags for the connection; no default value

        @throw CONNECTION-OPTION-ERROR missing or invalid connection option or attribute
    */
    constructor(hash<auto> config, *hash<auto> attr) : HttpBasedConnection(config, attr) {
        real_opts = {"url": real_url} + opts;
    }

    #! returns \c "soapio"
    string getType() {
        return "soapio";
    }

    #! returns a @ref SoapClientIo object
    /** @param connect this parameter is accepted for compatibility; connections are established on demand
        @param rtopts this connection type does not accept any runtime options, so this parameter is ignored

        @return a @ref SoapClientIo object
    */
    private SoapClientIo getImpl(bool connect = True, *hash<auto> rtopts) {
        return new SoapClientIo(getClientOptions());
    }

    #! returns the connection scheme info for this connection type
    private hash<ConnectionSchemeInfo> getConnectionSchemeInfoImpl() {
        return ConnectionScheme;
    }

    #! @cond nodoc
    #! maps connection options onto SoapClientIo constructor options
    private hash<auto> getClientOptions() {
        string http_url = mapUrl(real_opts.url);
        hash<auto> client_opts = real_opts - ("url", "wsdl", "target_url");
        # The connection URL addresses the WSDL unless an explicit wsdl option overrides it; target_url
        # overrides the endpoint declared by the selected port.
        client_opts.wsdl = real_opts.wsdl ?? http_url;
        if (exists real_opts.target_url) {
            client_opts.url = real_opts.target_url;
        }
        return client_opts;
    }

    #! maps soapio/soapios URL schemes onto http/https
    private static string mapUrl(string input_url) {
        if (input_url =~ /^soapios:/) {
            return regex_subst(input_url, "^soapios:", "https:");
        }
        if (input_url =~ /^soapio:/) {
            return regex_subst(input_url, "^soapio:", "http:");
        }
        if (input_url =~ /^soaps:/) {
            return regex_subst(input_url, "^soaps:", "https:");
        }
        if (input_url =~ /^soap:/) {
            return regex_subst(input_url, "^soap:", "http:");
        }
        return input_url;
    }
    #! @endcond
}

} # namespace SoapClientIo
