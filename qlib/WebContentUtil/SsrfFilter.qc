# -*- mode: qore; indent-tabs-mode: nil -*-

/*  SsrfFilter.qc Copyright 2026 Qore Technologies, s.r.o.

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

#! Main namespace
public namespace WebContentUtil {

#! SSRF (Server-Side Request Forgery) protection
/** Default-deny URL filter that rejects requests targeting private, internal, or
    sensitive addresses.  Used by @ref WebContentUtil::WebCrawler "WebCrawler" to
    prevent a hostile or misconfigured site from being used to probe internal
    networks via crawled links.

    Blocked categories:
    - **IPv4 private ranges** (RFC 1918): 10/8, 172.16/12, 192.168/16
    - **IPv4 loopback**: 127/8
    - **IPv4 link-local**: 169.254/16 (includes cloud metadata endpoint 169.254.169.254)
    - **IPv4 CGNAT**: 100.64/10
    - **IPv4 "this network"**: 0/8
    - **IPv6 loopback**: ::1
    - **IPv6 unique local**: fc00::/7
    - **IPv6 link-local**: fe80::/10
    - **IPv6 IPv4-mapped**: ::ffff:0:0/96 (so a mapped IPv4 still goes through IPv4 checks)
    - **Hostnames**: localhost, *.local, *.svc.cluster.local, *.cluster.local,
      kubernetes.default*, metadata.google.internal, metadata.azure.com

    Hostname-based URLs are resolved to IPs via DNS and **all** returned addresses
    are checked — a hostname can resolve to multiple addresses, including a public
    address that redirects to a private one.

    @par Example
    @code{.py}
# Throws SSRF-BLOCKED unless allow_private is True
SsrfFilter::checkUrl("http://10.0.0.1/admin");

# OK — public address
SsrfFilter::checkUrl("https://example.com/");

# OK — explicit opt-in for trusted internal use
SsrfFilter::checkUrl("http://localhost:8080/", {"allow_private": True});
    @endcode

    @since WebContentUtil 1.0
*/
public class SsrfFilter {
    #! Hostname patterns that match well-known internal services
    /** These are checked as case-insensitive suffix or full matches before any DNS
        resolution, so even a public DNS entry that resolves to a private host won't
        slip through.
    */
    const InternalHostnamePatterns = (
        "localhost",
        "ip6-localhost",
        "ip6-loopback",
        ".local",                    # mDNS / Bonjour
        ".localdomain",
        ".svc.cluster.local",        # k8s service DNS
        ".cluster.local",            # k8s cluster DNS
        ".internal",                 # GCP / generic internal TLD
        "metadata.google.internal",  # GCP metadata
        "metadata.azure.com",        # Azure metadata (one of several)
    );

    #! Returns True if the URL targets a private/internal address
    /** Performs both hostname pattern matching and DNS resolution.  Use this for
        a soft check; use @ref checkUrl() for an exception-throwing variant.

        @param url the URL to check
        @return True if the URL is private/internal (or unresolvable, conservatively)
    */
    static bool isPrivateUrl(string url) {
        try {
            hash<auto> parts = parse_url(url);
            *string host = parts.host;
            if (!host.val()) {
                # No host means we can't validate — treat as private (conservative)
                return True;
            }
            return SsrfFilter::isHostPrivate(host);
        } catch (hash<ExceptionInfo> ex) {
            # Unparseable URL — treat as private (conservative)
            return True;
        }
    }

    #! Resolve a URL's hostname and return a validated public IP for DNS pinning
    /** Performs the same SSRF check as @ref checkUrl() but ALSO returns the
        validated public IP address that the caller should use to fetch the
        resource.  Use this when you need to close the TOCTOU window between
        the SSRF check and the HTTP fetch — by pinning the resolved IP, you
        prevent DNS rebinding attacks where the attacker's DNS server flips
        the record between validation and fetch.

        Typical usage in a crawler:
        @code{.py}
*string pinned_ip = SsrfFilter::resolveAndValidate(url, {"allow_private": False});
if (pinned_ip) {
    # Replace the host in the URL with the IP, set Host header to the
    # original hostname, and fetch.  The HTTP client will connect to the
    # validated IP regardless of any DNS changes that happen later.
    string fetch_url = url with hostname replaced by pinned_ip;
    headers.Host = original_hostname;
    http.request(fetch_url, ..., headers);
}
        @endcode

        For HTTPS targets, the caller is responsible for SNI handling — the
        substituted IP would normally fail TLS hostname verification.  When
        using this for HTTPS, either:
        - Configure the HTTP client to use the original hostname for SNI/cert
          validation while connecting to the pinned IP, or
        - Accept the (small) TOCTOU window and use \c checkUrl() instead

        @param url the URL to validate
        @param opts validation options:
          - \c allow_private (bool, default \c False): allow private/internal targets
          - \c blocked_hostnames (\c *list<string>): additional hostnames to reject
        @return the first validated public IP from DNS resolution, suitable for
            DNS pinning; or @ref nothing if the host is already an IP literal
            (no pinning needed) or DNS resolution failed
        @throw SSRF-BLOCKED if the URL targets a blocked address and allow_private is not True
        @throw SSRF-BLOCKED-HOSTNAME if the URL targets an explicitly blocked hostname
    */
    static *string resolveAndValidate(string url, *hash<auto> opts) {
        bool allow_private = opts.allow_private ?? False;
        *list<string> blocked_hostnames = opts.blocked_hostnames;

        hash<auto> parts;
        try {
            parts = parse_url(url);
        } catch (hash<ExceptionInfo> ex) {
            throw "SSRF-BLOCKED", sprintf("URL %y could not be parsed: %s: %s",
                url, ex.err, ex.desc);
        }
        *string host = parts.host;
        if (!host.val()) {
            throw "SSRF-BLOCKED", sprintf("URL %y has no host", url);
        }

        # Caller-supplied blocklist (case-insensitive exact match)
        if (blocked_hostnames) {
            string lhost = host.lwr();
            foreach string blocked in (blocked_hostnames) {
                if (lhost == blocked.lwr()) {
                    throw "SSRF-BLOCKED-HOSTNAME",
                        sprintf("URL %y targets explicitly-blocked hostname %y", url, host);
                }
            }
        }

        # Hostname pattern check (loopback, k8s DNS, etc.)
        if (!allow_private && SsrfFilter::isPrivateHostname(host)) {
            throw "SSRF-BLOCKED",
                sprintf("URL %y targets a private/internal address (host: %y)", url, host);
        }

        # Already an IP literal — no pinning needed (caller can use the URL as-is)
        if (ip_address_type(host) != "invalid") {
            if (!allow_private && SsrfFilter::isPrivateIp(host)) {
                throw "SSRF-BLOCKED",
                    sprintf("URL %y targets a private/internal address (host: %y)", url, host);
            }
            return NOTHING;
        }

        # Resolve via DNS, validate every returned address, and pin the first
        # public one for the caller to use.
        list<hash<auto>> addrs;
        try {
            addrs = getaddrinfo(host, NOTHING, AF_UNSPEC, AI_ADDRCONFIG);
        } catch (hash<ExceptionInfo> ex) {
            # DNS failure — let the HTTP client handle it (return NOTHING so
            # the caller falls back to the unpinned URL)
            return NOTHING;
        }
        if (!addrs) {
            return NOTHING;
        }
        # Validate all addresses and collect by type.  Prefer IPv4 for
        # the pinned result because IPv6 literal addresses in URLs require
        # bracket notation and many TLS clients set SNI to the IP literal
        # instead of the original hostname, causing handshake failures with
        # CDNs like Cloudflare that require hostname-based SNI.
        *string first_ipv4;
        *string first_ipv6;
        foreach hash<auto> a in (addrs) {
            *string addr = a.address;
            if (!addr.val()) {
                continue;
            }
            if (!allow_private && SsrfFilter::isPrivateIp(addr)) {
                throw "SSRF-BLOCKED",
                    sprintf("URL %y resolves to private/reserved IP address %y",
                        url, addr);
            }
            string addr_type = ip_address_type(addr);
            if (!first_ipv4 && addr_type == "IPv4") {
                first_ipv4 = addr;
            } else if (!first_ipv6 && addr_type == "IPv6") {
                first_ipv6 = addr;
            }
        }
        return first_ipv4 ?? first_ipv6;
    }

    #! Throws SSRF-BLOCKED if the URL targets a private/internal address
    /** @param url the URL to validate
        @param opts validation options:
          - \c allow_private (bool, default \c False): allow private/internal targets
          - \c blocked_hostnames (\c *list<string>): additional hostnames to reject
            (e.g., the host's own hostname/IP, the Qorus instance hostname)

        @throw SSRF-BLOCKED if the URL targets a blocked address and allow_private is not True
        @throw SSRF-BLOCKED-HOSTNAME if the URL targets an explicitly blocked hostname
    */
    static checkUrl(string url, *hash<auto> opts) {
        bool allow_private = opts.allow_private ?? False;
        *list<string> blocked_hostnames = opts.blocked_hostnames;

        hash<auto> parts;
        try {
            parts = parse_url(url);
        } catch (hash<ExceptionInfo> ex) {
            throw "SSRF-BLOCKED", sprintf("URL %y could not be parsed: %s: %s",
                url, ex.err, ex.desc);
        }

        *string host = parts.host;
        if (!host.val()) {
            throw "SSRF-BLOCKED", sprintf("URL %y has no host", url);
        }

        # Caller-supplied blocklist (case-insensitive exact match)
        if (blocked_hostnames) {
            string lhost = host.lwr();
            foreach string blocked in (blocked_hostnames) {
                if (lhost == blocked.lwr()) {
                    throw "SSRF-BLOCKED-HOSTNAME",
                        sprintf("URL %y targets explicitly-blocked hostname %y", url, host);
                }
            }
        }

        if (allow_private) {
            return;
        }

        if (SsrfFilter::isHostPrivate(host)) {
            throw "SSRF-BLOCKED",
                sprintf("URL %y targets a private/internal address (host: %y)", url, host);
        }
    }

    #! Returns True if a hostname or IP address is private/internal
    /** Combines hostname pattern matching with DNS resolution + IP range checking.

        @param host hostname or IP address string
        @return True if the host is private/internal
    */
    static bool isHostPrivate(string host) {
        # Pattern check first (catches localhost, k8s DNS, etc. without DNS lookup)
        if (SsrfFilter::isPrivateHostname(host)) {
            return True;
        }

        # If it parses as an IP literal, just check it directly
        if (ip_address_type(host) != "invalid") {
            return SsrfFilter::isPrivateIp(host);
        }

        # Otherwise resolve via DNS and check ALL returned addresses.
        # getaddrinfo() is a top-level function (in ql_lib.qpp).
        list<hash<auto>> addrs;
        try {
            addrs = getaddrinfo(host, NOTHING, AF_UNSPEC, AI_ADDRCONFIG);
        } catch (hash<ExceptionInfo> ex) {
            # DNS failure — treat as private (conservative; can't verify it's safe)
            return True;
        }
        if (!addrs) {
            return True;
        }
        foreach hash<auto> a in (addrs) {
            *string addr = a.address;
            if (addr.val() && SsrfFilter::isPrivateIp(addr)) {
                return True;
            }
        }
        return False;
    }

    #! Returns True if a hostname matches a known internal pattern
    /** Pattern matching only — does not perform DNS resolution.

        @param hostname the hostname to check (without scheme/port)
        @return True if the hostname matches an internal pattern
    */
    static bool isPrivateHostname(string hostname) {
        string h = hostname.lwr();
        foreach string pat in (InternalHostnamePatterns) {
            if (pat[0] == ".") {
                # Suffix match for patterns starting with .
                if (h.endsWith(pat)) {
                    return True;
                }
            } else if (h == pat) {
                return True;
            } else if (pat.endsWith("*") && h.find(pat.substr(0, pat.size() - 1)) == 0) {
                # Trailing-wildcard match (e.g., kubernetes.default*)
                return True;
            }
        }
        return False;
    }

    #! Returns True if an IP address string is in a blocked SSRF range
    /** @param ip the IP address (IPv4 or IPv6 textual form)
        @return True if the address is in a blocked range
    */
    static bool isPrivateIp(string ip) {
        string type = ip_address_type(ip);
        if (type == "IPv4") {
            return SsrfFilter::isPrivateIpv4(ip);
        }
        if (type == "IPv6") {
            return SsrfFilter::isPrivateIpv6(ip);
        }
        # Unparseable — treat as private
        return True;
    }

    #! IPv4-specific blocked range check
    /** Blocked: 10/8, 172.16/12, 192.168/16, 127/8, 169.254/16, 100.64/10, 0/8

        @param ip valid IPv4 textual address
        @return True if blocked
    */
    private static bool isPrivateIpv4(string ip) {
        list<string> octets = ip.split(".");
        if (octets.size() != 4) {
            return True;
        }
        int o0 = octets[0].toInt();
        int o1 = octets[1].toInt();

        # 0.0.0.0/8 — "this network"
        if (o0 == 0) {
            return True;
        }
        # 10.0.0.0/8 — RFC 1918
        if (o0 == 10) {
            return True;
        }
        # 100.64.0.0/10 — CGNAT (RFC 6598)
        if (o0 == 100 && o1 >= 64 && o1 <= 127) {
            return True;
        }
        # 127.0.0.0/8 — loopback
        if (o0 == 127) {
            return True;
        }
        # 169.254.0.0/16 — link-local (includes 169.254.169.254 cloud metadata)
        if (o0 == 169 && o1 == 254) {
            return True;
        }
        # 172.16.0.0/12 — RFC 1918
        if (o0 == 172 && o1 >= 16 && o1 <= 31) {
            return True;
        }
        # 192.168.0.0/16 — RFC 1918
        if (o0 == 192 && o1 == 168) {
            return True;
        }
        # 192.0.0.0/24, 192.0.2.0/24, 198.18.0.0/15, 198.51.100.0/24, 203.0.113.0/24,
        # 224.0.0.0/4 (multicast), 240.0.0.0/4 (reserved) — also unsafe but less common
        if (o0 == 192 && o1 == 0) {
            return True;
        }
        if (o0 == 198 && (o1 == 18 || o1 == 19 || o1 == 51)) {
            return True;
        }
        if (o0 == 203 && o1 == 0) {
            return True;
        }
        if (o0 >= 224) {
            return True;
        }
        return False;
    }

    #! IPv6-specific blocked range check
    /** Blocked: ::1 (loopback), fc00::/7 (ULA), fe80::/10 (link-local),
        ::ffff:0:0/96 (IPv4-mapped — recursively check the embedded IPv4).

        @param ip valid IPv6 textual address
        @return True if blocked
    */
    private static bool isPrivateIpv6(string ip) {
        string l = ip.lwr();

        # Loopback ::1 (also "0:0:0:0:0:0:0:1" expanded)
        if (l == "::1" || l == "0:0:0:0:0:0:0:1") {
            return True;
        }
        # Unspecified ::
        if (l == "::" || l == "0:0:0:0:0:0:0:0") {
            return True;
        }
        # IPv4-mapped IPv6 — recursively check the embedded IPv4
        # Format: ::ffff:a.b.c.d  or  ::ffff:hex:hex
        if (l =~ /^::ffff:/i) {
            *list<*string> m = regex_extract(l, "^::ffff:(.+)$");
            if (m && m[0].val()) {
                string suffix = m[0];
                # Try as IPv4 dotted-quad
                if (ip_address_type(suffix) == "IPv4") {
                    return SsrfFilter::isPrivateIpv4(suffix);
                }
                # Otherwise it's hex form — fall through to ULA/LL checks
            }
        }
        # Unique Local fc00::/7 — first byte is 0xfc or 0xfd
        if (l =~ /^f[cd][0-9a-f]{0,2}:/) {
            return True;
        }
        # Link-local fe80::/10
        if (l =~ /^fe[89ab][0-9a-f]{0,2}:/) {
            return True;
        }
        # Multicast ff00::/8
        if (l =~ /^ff[0-9a-f]{0,2}:/) {
            return True;
        }
        return False;
    }
}

} # namespace WebContentUtil
