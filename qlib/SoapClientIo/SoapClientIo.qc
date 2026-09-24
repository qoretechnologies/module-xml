# -*- mode: qore; indent-tabs-mode: nil -*-
#! @file SoapClientIo.qc @brief SOAP client class with async I/O

/*  SoapClientIo.qc Copyright (C) 2026 Qore Technologies, s.r.o.

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

#! SOAP client with async I/O via HttpClientIo
/** This class provides a SOAP client implementation using
    \c HttpClientIo::HttpClientConnectionManager for async I/O with automatic protocol
    negotiation (HTTP/3 &rarr; HTTP/2 &rarr; HTTP/1.1) and connection pooling.

    Message serialization, envelope validation, mandatory-header processing, fault grammar and
    response decoding are the same as in the \c SoapClient module; both clients drive the same
    @ref WSDL::WebService "WebService" model, so a service that works with one works with the
    other. Only the transport differs.

    @par Example:
    @code{.py}
SoapClientIo client({"wsdl": "http://example.com/service?wsdl"});
auto result = client.callOperation("echo", {"body": "invoice-71"});
client.close();
    @endcode

    @since xml 2.3
*/
public class SoapClientIo {
    public {
        #! version of the implementation of this class
        const Version = "1.0";

        #! default connect timeout in milliseconds
        const DefaultConnectTimeout = 45000;

        #! default I/O timeout in milliseconds
        const DefaultTimeout = 45000;

        #! default HTTP headers
        const Headers = {"User-Agent": "Qore-Soap-Client-Io/" + SoapClientIo::Version};
    }

    #! @cond nodoc
    private {
        #! the web service definition driving serialization and decoding
        WSDL::WebService wsdl;

        #! the selected service name
        string svc;

        #! the selected port name
        string port;

        #! the selected binding component key
        string binding;

        #! the target endpoint URL
        string url;

        #! the path component of the target endpoint URL
        *string url_path;

        #! response header capabilities for this client
        WSDL::SoapProcessingNode soap_node;

        #! whether requests are sent as MTOM/XOP packages
        bool mtom = False;

        #! the minimum size in octets of base64Binary content sent as an MTOM part
        int mtom_threshold = WSDL::MTOM_THRESHOLD;

        #! the limits for the responses this client decodes; NOTHING for the thread's or the WSDL's limits
        *hash<WSDL::SoapMessageLimits> message_limits;

        #! WS-Addressing: True or False to always or never send it, NOTHING to follow the WSDL policy
        *bool addressing;

        #! whether the WS-Addressing request headers are marked mustUnderstand
        bool addressing_must_understand = False;

        #! the receiver of replies sent to a non-anonymous address
        *WSDL::WsaReplyReceiver reply_receiver;

        #! async I/O connection manager used for every request; replaced atomically by close()
        HttpClientIo::HttpClientConnectionManager mgr;

        #! guards replacement of @ref mgr so a concurrent close() cannot be observed half-applied
        Mutex mgr_lock();

        #! connect timeout in milliseconds
        int connect_timeout;

        #! transfer timeout in milliseconds
        int io_timeout;

        #! HTTP protocol selector for the connection manager
        string http_protocol;

        #! the maximum response body size in bytes, as received and decoded; 0 for no limit
        int max_response_body_size = 0;

        #! default headers sent with every request
        hash<auto> headers = Headers;

        #! optional logger
        *LoggerInterface logger;
    }
    #! @endcond

    #! creates the object from a %WSDL which provides the basis for all communication with the service
    /** @param h valid option keys:
        - \c wsdl: the URL of the web service or a @ref WSDL::WebService "WebService" object itself
        - \c wsdl_file: a path to use to load the %WSDL and create the @ref WSDL::WebService "WebService" object
        - \c url: override the target URL given in the %WSDL
        - \c service: in case multiple service entries are found in the WSDL, give the one to be used here
        - \c port: in case multiple port entries are found in the WSDL, give the one to be used here
        - \c soap_node: optional ultimate-receiver @ref WSDL::SoapProcessingNode "SoapProcessingNode" for
          response headers; the default has no application header capabilities and rejects unknown targeted
          mandatory headers
        - \c mtom: @ref Qore::True "True" to send SOAP requests as MTOM/XOP packages, with base64Binary content of
          at least \c mtom_threshold octets in binary parts; see @ref WSDL::SoapMtomScope "SoapMtomScope"
        - \c mtom_threshold: the minimum MTOM part size in octets (default:
          @ref WSDL::MTOM_THRESHOLD "MTOM_THRESHOLD"); 0 sends every base64Binary value as a part
        - \c message_limits: a @ref WSDL::SoapMessageLimits "SoapMessageLimits" hash for the responses this
          client decodes; see setMessageLimits()
        - \c addressing: @ref Qore::True "True" to send WS-Addressing headers with every request,
          @ref Qore::False "False" to send none; by default they are sent when the effective policy of the
          WSDL supports WS-Addressing; see <a href="../../WSDL/html/index.html#wsdl_addressing">WS-Addressing</a> in the WSDL module
        - \c addressing_must_understand: @ref Qore::True "True" to mark the WS-Addressing request headers
          \c mustUnderstand
        - \c reply_receiver: a @ref WSDL::WsaReplyReceiver "WsaReplyReceiver" whose address request-response
          calls use as \c wsa:ReplyTo and \c wsa:FaultTo; the reply then arrives as a separate HTTP request at a
          handler such as \c SoapHandler::SoapReplyHandler, which delivers it to the receiver
        - \c connect_timeout: connection timeout in milliseconds (default: 45000)
        - \c timeout: transfer timeout in milliseconds (default: 45000)
        - \c http_protocol: HTTP protocol to use (\c "auto", \c "h1", \c "h2", \c "h3"; default: \c "auto")
        - \c max_response_body_size: the maximum size in bytes of a response body, as received and after its
          content encoding is decoded; a larger body, such as a small compressed body that expands to a huge size,
          fails the call with \c HTTP-CLIENT-RESPONSE-BODY-TOO-LARGE as soon as the limit is exceeded (default: 0,
          no limit)
        - \c headers: extra default headers as a hash
        - \c logger: a \c LoggerInterface object for logging

        @throw SOAP-CLIENT-IO-ERROR missing or conflicting options, an unknown service or port, or a port
        that cannot be selected

        @note A remote %WSDL is retrieved with an ordinary HTTP client owned by the @ref WSDL "WSDL" module;
        only SOAP operation traffic uses the async connection manager.

        @par Example
        @code{.py}
SoapClientIo client({"wsdl": service, "url": "https://example.org/services/v1"});
        @endcode
    */
    constructor(hash<auto> h) {
        soap_node = getProcessingNode(h.soap_node);
        if (exists h.mtom) {
            if (h.mtom.typeCode() != NT_BOOLEAN) {
                throw "SOAP-CLIENT-IO-ERROR", sprintf("the mtom option must be a bool; got %y", h.mtom.type());
            }
            mtom = h.mtom;
        }
        if (exists h.mtom_threshold) {
            if (h.mtom_threshold.typeCode() != NT_INT || h.mtom_threshold < 0) {
                throw "SOAP-CLIENT-IO-ERROR", sprintf("the mtom_threshold option must be a non-negative int; "
                    "got %y", h.mtom_threshold);
            }
            mtom_threshold = h.mtom_threshold;
        }
        if (exists h.message_limits) {
            setMessageLimits(h.message_limits);
        }
        foreach string option in (("addressing", "addressing_must_understand")) {
            if (exists h{option} && h{option}.typeCode() != NT_BOOLEAN) {
                throw "SOAP-CLIENT-IO-ERROR", sprintf("the %s option must be a bool; got %y", option,
                    h{option}.type());
            }
        }
        addressing = h.addressing;
        addressing_must_understand = h.addressing_must_understand ?? False;
        if (exists h.reply_receiver) {
            if (!(h.reply_receiver instanceof WSDL::WsaReplyReceiver)) {
                throw "SOAP-CLIENT-IO-ERROR", "the reply_receiver option must be a WsaReplyReceiver";
            }
            reply_receiver = h.reply_receiver;
        }
        if (exists h.wsdl_file && exists h.wsdl) {
            throw "SOAP-CLIENT-IO-ERROR", "only one of 'wsdl' or 'wsdl_file' keys can be given; both were "
                "passed";
        }
        if (h.wsdl instanceof WSDL::WebService) {
            wsdl = h.wsdl;
        } else {
            auto source = h.wsdl_file ?? h.wsdl;
            if (!exists source) {
                throw "SOAP-CLIENT-IO-ERROR", "neither one of required 'wsdl' or 'wsdl_file' keys is present "
                    "in the hash argument to SoapClientIo::constructor()";
            }
            *string def_path;
            *string document_location;
            hash<string, string> aliases();
            auto parsed = WSDL::WSDLLib::getWSDL(source, NOTHING, h.headers, \def_path, \document_location,
                \aliases);
            if (!exists parsed) {
                throw "SOAP-CLIENT-IO-ERROR", "missing wsdl in SoapClientIo::constructor()";
            }
            *string requested_location = WSDL::WSDLLib::getUriDocumentLocation(source);
            if (requested_location && document_location && requested_location != document_location) {
                aliases{requested_location} = document_location;
            }
            wsdl = parsed instanceof WSDL::WebService ? parsed : new WSDL::WebService(parsed, {
                "http_headers": h.headers, "def_path": def_path,
                "document_location": document_location ?? requested_location, "resource_locations": aliases,
            } + h.wsdl_opt);
        }

        list<auto> services = wsdl.listServices();
        if (services.size() > 1 && !h.service) {
            throw "SOAP-CLIENT-IO-ERROR", sprintf("no 'service' key passed in the option hash argument to "
                "SoapClientIo::constructor() (WSDL defines the following services: %y)",
                (map $1.name, services));
        }
        svc = h.service ?? services[0].name;
        hash<auto> service_info = wsdl.getService(svc);

        port = h.port ?? service_info.port.firstKey();
        if (!service_info.port.hasKey(port)) {
            throw "SOAP-CLIENT-IO-ERROR", sprintf("service %y has no port %y", svc, port);
        }
        *string unsupported = service_info.port{port}.unsupported_reason
            ?? service_info.port{port}.binding.getUnsupportedReason();
        if (unsupported) {
            throw "SOAP-CLIENT-IO-ERROR", sprintf("service %y port %y cannot be selected: %s", svc, port,
                unsupported);
        }
        binding = service_info.port{port}.binding.getComponentKey();

        url = h.url ?? service_info.port{port}.address;
        url_path = parse_url(url).path;

        connect_timeout = h.connect_timeout ?? DefaultConnectTimeout;
        io_timeout = h.timeout ?? DefaultTimeout;
        http_protocol = h.http_protocol ?? "auto";
        if (exists h.max_response_body_size) {
            if (h.max_response_body_size.typeCode() != NT_INT || h.max_response_body_size < 0) {
                throw "SOAP-CLIENT-IO-ERROR", sprintf("the max_response_body_size option must be a non-negative int; "
                    "got %y", h.max_response_body_size);
            }
            max_response_body_size = h.max_response_body_size;
        }
        logger = h.logger;
        if (h.headers.typeCode() == NT_HASH) {
            headers += h.headers;
        }
        # Credentials supplied as options or in the endpoint URL become a Basic authorization default;
        # silently dropping them would send unauthenticated requests to a protected service.
        *string username = h.username ?? parse_url(url).username;
        *string password = h.password ?? parse_url(url).password;
        if (exists username || exists password) {
            headers.Authorization = "Basic " + make_base64_string(sprintf("%s:%s", username ?? "",
                password ?? ""));
        }

        mgr = createConnectionManager();
    }

    #! makes a server call with the given operation and arguments and returns the deserialized result
    /** @param operation the SOAP operation to use to serialize the request
        @param args the arguments to the SOAP operation

        @return the deserialized result of the SOAP call

        @throw WSDL-OPERATION-ERROR the operation is not defined in the WSDL
        @throw SOAP-SERVER-FAULT-RESPONSE the server returned a SOAP fault

        @par Example
        @code{.py}
auto result = client.call("echo", {"body": "invoice-71"});
        @endcode
    */
    auto call(string operation, auto args) {
        return callOperation(operation, args);
    }

    #! makes a server call with the given operation, arguments, options and optional info hash reference
    /** @param operation the SOAP operation to use to serialize the request
        @param args the arguments to the SOAP operation
        @param opts an optional hash of options for the call as follows:
        - \c soap_header: a hash giving SOAP header information, if required by the message
        - \c http_header: a hash giving HTTP header information to include in the message
        - \c xml_opts: an integer XML generation option code
        - \c soapaction: an optional string overriding the SOAPAction for the request; an empty string
          prevents the SOAPAction from being sent
        - \c soap_node: optional ultimate-receiver @ref WSDL::SoapProcessingNode "SoapProcessingNode"
          overriding the constructor's response header capabilities for this call only
        - \c xml_values: True to return @ref WSDL::SoapXmlMessageInfo "SoapXmlMessageInfo" with retained
          XML body parts and headers, and the response's MIME parts in \c parts; the default returns native
          values
        - \c preserve_types: True to retain selected native types as portable \c ^type^ / \c ^val^ wrappers;
          cannot be combined with \c xml_values
        - \c addressing: a hash of @ref WSDL::WsaMessageAddressing "WsaMessageAddressing" properties replacing
          the computed WS-Addressing properties of this request; it sends WS-Addressing headers with the request
        @param info an optional reference returning technical information about the call; the following keys
        are present: \c "request-uri", \c "request-body", \c "request-soap-headers", \c "response-code",
        \c "response-headers", \c "response-body", \c "effective-url" and, for SOAP responses,
        \c "soap-processing"; when the request uses WS-Addressing, \c "addressing" holds the \c request and,
        if the response has any, the \c response message addressing properties

        @return the deserialized result of the SOAP call; one-way operations return @ref nothing

        @throw SOAP-CLIENT-IO-ERROR invalid option combination
        @throw SOAP-SERVER-FAULT-RESPONSE the server returned a SOAP fault

        @par Example
        @code{.py}
hash<auto> info;
auto result = client.callOperation("echo", {"body": "invoice-71"}, {"xml_values": True}, \info);
        @endcode
    */
    auto callOperation(string operation, auto args, *hash<auto> opts, *reference<hash<auto>> info) {
        if (opts.xml_values && opts.preserve_types) {
            throw "SOAP-CLIENT-IO-ERROR", "xml_values and preserve_types cannot be combined";
        }
        if (exists opts.addressing && opts.addressing.typeCode() != NT_HASH) {
            throw "SOAP-CLIENT-IO-ERROR", "the addressing call option must be a hash of WS-Addressing properties";
        }
        WSDL::WSOperation op = wsdl.getBindingOperation(binding, operation);
        # the WS-Addressing properties of the request (P9a-04)
        *hash<WSDL::WsaMessageAddressing> request_maps;
        if (op.getBinding(binding) instanceof WSDL::SoapBinding) {
            request_maps = WSDL::WsAddressingHelper::clientRequest(wsdl, op, binding, svc, port, url, addressing,
                opts.addressing, reply_receiver);
        } else if (exists opts.addressing) {
            throw "SOAP-CLIENT-IO-ERROR", "WS-Addressing requires a SOAP binding";
        }
        hash<auto> msg;
        {
            WSDL::WsaOutputScope addressing_scope(request_maps, addressing_must_understand);
            WSDL::SoapMtomScope mtom_scope(mtom, mtom_threshold);
            msg = op.serializeRequest(args, opts.soap_header, "utf-8", NOTHING, opts.xml_opts,
                opts.soapaction, binding, opts.http_header);
        }

        string path = msg.path ?? "";
        if (path && path !~ /^[\/\?]/) {
            path = "/" + path;
        }
        if (url_path) {
            path = rtrim(url_path, "/") + path;
        }
        if (!path.val()) {
            path = "/";
        }
        return doRequest(op, msg.method ?? "POST", path, headers + (msg.hdr ?? {}), msg.body,
            opts, \info, {"request-soap-headers": opts.soap_header}, request_maps);
    }

    #! retrieves a SOAP 1.2 response with an envelope-free GET request
    /** Implements the SOAP 1.2 SOAP-response message exchange pattern: the request carries no envelope and
        the response is an ordinary SOAP 1.2 message decoded with the selected operation's output and fault
        declarations.

        @param operation the SOAP operation supplying the output and fault declarations
        @param resource_url the resource to retrieve, resolved against the client endpoint
        @param opts an optional hash of options; \c xml_values, \c preserve_types, \c soap_node and
        \c http_header are honored; request-only options are rejected
        @param info an optional reference returning technical information about the call

        @return the deserialized response

        @throw SOAP-CLIENT-IO-ERROR the binding is not SOAP 1.2, has no output message, or a request-only
        option was given

        @par Example
        @code{.py}
auto result = client.getSoapResponse("echo", "/resource");
        @endcode
    */
    auto getSoapResponse(string operation, string resource_url, *hash<auto> opts,
            *reference<hash<auto>> info) {
        foreach string key in (("soap_header", "soapaction", "xml_opts", "addressing")) {
            if (exists opts{key}) {
                throw "SOAP-CLIENT-IO-ERROR", sprintf("%y is a request-only option and cannot be used with "
                    "SOAP response retrieval", key);
            }
        }
        WSDL::WSOperation op = wsdl.getBindingOperation(binding, operation);
        WSDL::OperationalBinding selected = op.getBinding(binding);
        if (!(selected instanceof WSDL::SoapBinding) || !selected.isSoap12() || !selected.output) {
            throw "SOAP-CLIENT-IO-ERROR", "SOAP response retrieval requires a SOAP 1.2 binding with an "
                "output message";
        }
        string request_url = resolve_url(url, resource_url, RESOLVE_URL_ENCODE | RESOLVE_URL_NO_FRAGMENT);
        return doRequest(op, "GET", parse_url(request_url).path ?? "/",
            headers + {"Accept": "application/soap+xml"} + (opts.http_header ?? {}), NOTHING, opts, \info);
    }

    #! transparently serializes the arguments and makes a call to the given operation
    /** @param op the operation name, which is the method name passed to methodGate()
        @param ... zero or more arguments for the operation

        @return the deserialized result of the SOAP call
    */
    auto methodGate(string op) {
        return call(op, argv.typeCode() == NT_LIST && argv.size() == 1 ? argv[0] : argv);
    }

    #! returns the @ref WSDL::WebService "WebService" object associated with this object
    WSDL::WebService getWebService() {
        return wsdl;
    }

    #! returns the target endpoint URL
    string getUrl() {
        return url;
    }

    #! returns the selected service name
    string getService() {
        return svc;
    }

    #! returns the selected port name
    string getPort() {
        return port;
    }

    #! returns the selected binding component key
    string getBinding() {
        return binding;
    }

    #! closes all pooled connections and releases transport resources
    /** The client can be reused after calling this method; a new connection is established on the next
        request.
    */
    close() {
        HttpClientIo::HttpClientConnectionManager old;
        {
            AutoLock al(mgr_lock);
            old = mgr;
            mgr = createConnectionManager();
        }
        # Close the retired manager outside the lock so an in-flight request is never blocked by it.
        old.closeAll();
    }

    #! returns the limits for the SOAP responses that this client decodes
    /** @return the limits set with the \c message_limits option or setMessageLimits(), or NOTHING when the
        limits selected by the calling thread or configured for the WSDL apply
    */
    *hash<WSDL::SoapMessageLimits> getMessageLimits() {
        return message_limits;
    }

    #! sets the limits for the SOAP responses that this client decodes
    /** @param limits the limits (see @ref WSDL::SoapMessageLimits "SoapMessageLimits"), which take precedence over
        those selected by the calling thread and those configured for the WSDL; NOTHING removes them
        @throw SOAP-LIMIT-ERROR a limit is not positive
    */
    setMessageLimits(*hash<auto> limits) {
        if (limits) {
            hash<WSDL::SoapMessageLimits> checked = cast<hash<WSDL::SoapMessageLimits>>(limits);
            WSDL::SoapMessageLimitsScope check(checked);
            message_limits = checked;
        } else {
            remove message_limits;
        }
    }

    #! @cond nodoc
    #! performs one SOAP exchange and decodes the response with the operation's declarations
    private auto doRequest(WSDL::WSOperation op, string method, string path, hash<auto> hdr, *data body,
            *hash<auto> opts, *reference<hash<auto>> info, *hash<auto> extra_info,
            *hash<WSDL::WsaMessageAddressing> request_maps) {
        WSDL::OperationalBinding selected = op.getBinding(binding);
        # the response is parsed and decoded within the limits of this client, the thread or the WSDL (P8-06)
        WSDL::SoapMessageLimitsScope limits_scope(message_limits ?? WSDL::SoapMessageLimitsScope::getSelected()
            ?? op.getMessageLimits());
        WSDL::SoapProcessingNode response_node = exists opts.soap_node
            ? getProcessingNode(opts.soap_node) : soap_node;
        if (request_maps && !response_node.getOptions().addressing) {
            # the response's WS-Addressing headers are honored, including mandatory ones (WS-I R1143)
            hash<WSDL::SoapNodeOptions> node_options = response_node.getOptions();
            node_options.addressing = True;
            response_node = new WSDL::SoapProcessingNode(node_options);
        }
        hash<auto> addressing_info = {};
        if (request_maps) {
            addressing_info.request = request_maps;
        }
        info = (info ?? {}) + (extra_info ?? {}) + (addressing_info ? {"addressing": addressing_info} : {}) + {
            "request-uri": sprintf("%s %s", method, path),
            "request-body": body,
            "headers": hdr,
        };
        if (logger) {
            logger.info("SoapClientIo: %s %s%s", method, url, path);
        }
        # WS-Addressing SOAP Binding section 5.2: a response endpoint at the reply receiver receives the response as
        # a separate HTTP request
        bool decoupled = request_maps && reply_receiver && exists op.output
            && inlist(reply_receiver.getEndpointReference().address, (request_maps.reply_to.address,
                request_maps.fault_to.address));
        if (decoupled) {
            reply_receiver.expect(request_maps.message_id);
        }
        on_exit if (decoupled) {
            reply_receiver.cancel(request_maps.message_id);
        }
        hash<auto> resp = getManager().request(url, method, path, hdr, body, io_timeout);
        if (decoupled && resp.status_code == 202 && !resp.body) {
            # the back channel acknowledges the request; the response arrives at the reply receiver
            hash<WSDL::WsaReceivedMessage> received = reply_receiver.wait(request_maps.message_id, io_timeout);
            info."reply-headers" = received.headers;
            resp = {"status_code": resp.status_code, "headers": received.headers, "body": received.body,
                "content_type": received.headers."content-type"};
        }
        # Present the async response in the shape the shared WSDL message decoders expect.
        hash<auto> rh = (resp.headers ?? {}) + {
            "body": resp.body,
            "status_code": resp.status_code,
            # content_type is the bare media type; multipart framing needs the parameters of the full header
            "content-type": resp.headers."content-type" ?? resp.content_type,
        };
        info += {
            "response-code": resp.status_code,
            "response-headers": resp.headers,
            "response-body": resp.body,
            "effective-url": resp.effective_url ?? (url + path),
        };

        bool is_soap = selected instanceof WSDL::SoapBinding;
        *hash<auto> rmsg;
        *hash<auto> pdata;
        bool fault = False;
        if (resp.status_code == 400 || (resp.status_code >= 500 && resp.status_code < 600)) {
            # A protocol Fault is recognized by expanded name before any HTTP error is reported.
            if (is_soap && resp.body) {
                try {
                    rmsg = WSDL::WSDLLib::parseMultiPartSOAPMessage(rh, False, True);
                } catch (hash<ExceptionInfo> ex) {
                    if (ex.err != "SOAP-MEDIA-TYPE-ERROR") {
                        rethrow;
                    }
                }
                if (rmsg && rmsg.body) {
                    pdata = WSDL::WSDLLib::parseSOAPMessage(rmsg, False, True);
                    fault = hasSoapFault(pdata);
                }
            }
            if (!fault) {
                throw "SOAP-CLIENT-IO-HTTP-ERROR", sprintf("HTTP status %d returned from %s%s",
                    resp.status_code, url, path), rh;
            }
        } else if (resp.status_code < 200 || resp.status_code >= 300) {
            throw "SOAP-CLIENT-IO-HTTP-ERROR", sprintf("HTTP status %d returned from %s%s",
                resp.status_code, url, path), rh;
        }

        if (!op.output && !fault) {
            # A one-way operation has no response message to decode, but a fault returned for one is
            # still reported: skipping it here would discard the server's error.
            return;
        }
        rmsg = rmsg ?? WSDL::WSDLLib::parseMultiPartSOAPMessage(rh, False, is_soap && !!rh.body);
        pdata = pdata ?? WSDL::WSDLLib::parseSOAPMessage(rmsg, False, is_soap);

        *string response_xml;
        if (is_soap && pdata && rmsg.body) {
            bool response_soap12 = WSDL::WSDLLib::validateSOAPEnvelope(pdata, selected.isSoap12(), True,
                True);
            WSDL::WSDLLib::validateSOAPMediaType(rmsg, response_soap12);
            hash<WSDL::SoapNodeResult> processed = response_node.processMessage(
                WSDL::WSDLLib::getXmlMessageText(rmsg), {"operation": op, "http_info": info},
                info."effective-url", selected.isSoap12(), True);
            hash<auto> typed_info();
            typed_info += info;
            typed_info."soap-processing" = processed;
            if (request_maps) {
                bool response_fault = hasSoapFault(pdata);
                try {
                    typed_info.addressing.response = WSDL::WsAddressingHelper::clientResponse(request_maps, processed,
                        op, wsdl.getAddressingPolicy(op, binding, svc, port).required, response_fault);
                } catch (hash<ExceptionInfo> ex) {
                    # a SOAP fault is reported to the caller even when its WS-Addressing headers are wrong
                    if (!response_fault || ex.err != "WSA-RESPONSE-ERROR") {
                        rethrow;
                    }
                    typed_info.addressing.error = ex.desc;
                }
            }
            info = typed_info;
            response_xml = processed.application_message.getXml();
            pdata = WSDL::WSDLLib::parseSOAPMessage(rmsg + {
                "body": response_xml,
                "content-type": "application/xml;charset=UTF-8",
            }, False, True);
        }
        if (opts.xml_values) {
            return op.deserializeXmlResponse(response_xml ?? WSDL::WSDLLib::getXmlMessageText(rmsg),
                binding, rmsg.parts);
        }
        return op.deserializeResponse(pdata, binding, opts.preserve_types ?? False);
    }

    #! recognizes a protocol Fault by expanded name without interpreting application content
    private static bool hasSoapFault(hash<auto> document) {
        hash<auto> expanded = WSDL::XsdBase::expandElementNamespaces(document);
        foreach string uri in ((WSDL::SOAP_11_ENV, WSDL::SOAP_12_ENV)) {
            string prefix = "{" + uri + "}";
            auto root = expanded{prefix + "Envelope"};
            list<auto> envelopes = root.typeCode() == NT_LIST ? root : (root,);
            foreach auto envelope in (envelopes) {
                foreach string key in (keys envelope) {
                    if (key != prefix + "Body" && !key.startsWith(prefix + "Body^")) {
                        continue;
                    }
                    auto value = envelope{key};
                    list<auto> bodies = value.typeCode() == NT_LIST ? value : (value,);
                    foreach auto candidate in (bodies) {
                        if (candidate.typeCode() == NT_HASH && candidate.hasKey(prefix + "Fault")) {
                            return True;
                        }
                    }
                }
            }
        }
        return False;
    }

    #! validates and returns the ultimate-receiver processing node to use
    private static WSDL::SoapProcessingNode getProcessingNode(auto supplied) {
        if (!exists supplied) {
            return new WSDL::SoapProcessingNode();
        }
        if (!(supplied instanceof WSDL::SoapProcessingNode) || !supplied.isUltimateReceiver()) {
            throw "SOAP-CLIENT-IO-ERROR", "soap_node requires an ultimate-receiver SoapProcessingNode";
        }
        return supplied;
    }

    #! returns the current connection manager; a concurrent close() swaps it under the lock
    private HttpClientIo::HttpClientConnectionManager getManager() {
        AutoLock al(mgr_lock);
        return mgr;
    }

    #! creates the async connection manager used for every request
    private HttpClientIo::HttpClientConnectionManager createConnectionManager() {
        return new HttpClientIo::HttpClientConnectionManager(
            <HttpClientIo::HttpClientConnectionManagerOptions>{
                "connect_timeout": connect_timeout,
                "request_timeout": io_timeout,
                "protocol": http_protocol,
                "max_response_body_size": max_response_body_size,
            });
    }
    #! @endcond
}

} # namespace SoapClientIo
