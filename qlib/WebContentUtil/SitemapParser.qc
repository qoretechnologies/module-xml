# -*- mode: qore; indent-tabs-mode: nil -*-

/*  SitemapParser.qc Copyright 2026 Qore Technologies, s.r.o.

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

#! Parses sitemap.xml and sitemap-index.xml files per the sitemaps.org protocol
/** Implements the [sitemaps.org protocol](https://www.sitemaps.org/protocol.html)
    for both regular sitemap files (containing \c <urlset><url><loc>) and sitemap
    index files (containing \c <sitemapindex><sitemap><loc>).  Uses libxml2 (via
    @ref Qore::Xml::parse_xml() and the underlying @ref Qore::Xml::XmlDoc) for
    namespace-aware parsing — robust to whitespace, attribute ordering, and
    encoding declarations that the regex approach in older crawlers would miss.

    All methods are static.

    @par Example: parse a sitemap file
    @code{.py}
list<string> urls = SitemapParser::parseUrls(sitemap_xml);
    @endcode

    @par Example: fetch and recursively parse with index support
    @code{.py}
list<string> urls = SitemapParser::fetchAndParse("https://example.com/", {
    "user_agent": "MyBot/1.0",
    "headers": {"Authorization": "Bearer token"},
    "max_depth": 3,
});
    @endcode

    @since WebContentUtil 1.0
*/
public class SitemapParser {
    #! Default per-request HTTP timeout when fetching sitemap files
    const DefaultRequestTimeout = 30s;

    #! Maximum recursion depth for sitemap-index files referencing sub-sitemaps
    /** Spec doesn't impose a hard limit but real-world index trees are
        usually 1-2 deep.  Capping at 3 prevents infinite recursion from
        misconfigured or malicious sitemaps that loop back to themselves.
    */
    const DefaultMaxIndexDepth = 3;

    #! Maximum total URLs to extract from a single sitemap fetch
    /** Sitemaps can legally contain 50,000 URLs each, and an index can chain
        unboundedly.  We cap the total at 100k by default to bound memory and
        keep the crawler from getting wedged on a single sitemap.
    */
    const DefaultMaxUrls = 100000;

    #! Parse a sitemap or sitemap-index XML document and return all discovered URLs
    /** Detects whether the document is a regular sitemap (\c <urlset>) or an
        index (\c <sitemapindex>) by inspecting the root element.  For regular
        sitemaps the returned list contains the page URLs.  For index files
        the returned list contains the sub-sitemap URLs (the caller must fetch
        and recursively parse each one — use @ref fetchAndParse() for that).

        Both standard sitemap namespace declarations are accepted:
        \c http://www.sitemaps.org/schemas/sitemap/0.9 and the rare
        \c https:// variant; namespace prefix is also accepted (e.g.
        \c <sm:urlset xmlns:sm="...">).

        @param xml the sitemap XML body
        @return list of URLs (page URLs for sitemap files, sub-sitemap URLs
            for index files); empty if the document is malformed
    */
    static list<string> parseUrls(string xml) {
        list<string> urls = ();
        XmlDoc doc;
        try {
            doc = new XmlDoc(xml);
        } catch (hash<ExceptionInfo> ex) {
            return urls;
        }

        # Use a namespace-agnostic XPath that matches both <loc> in
        # <urlset><url> and in <sitemapindex><sitemap>.  local-name()
        # ignores any namespace prefix the document might use.
        list<auto> loc_nodes = doc.evalXPath(
            "//*[local-name()='loc']");
        foreach auto node in (loc_nodes) {
            string text = trim(node.getContent());
            if (text.val() && text =~ /^https?:\/\//i) {
                urls += text;
            }
        }
        return urls;
    }

    #! Returns True if the parsed sitemap document is a sitemap-index
    /** A sitemap-index has \c <sitemapindex> as its root element and contains
        \c <sitemap><loc> entries pointing to sub-sitemaps.  A regular sitemap
        has \c <urlset> as its root and contains \c <url><loc> entries.

        @param xml the sitemap XML body
        @return True if the root element is \c <sitemapindex>, False otherwise
            (including parse failures)
    */
    static bool isIndex(string xml) {
        XmlDoc doc;
        try {
            doc = new XmlDoc(xml);
        } catch (hash<ExceptionInfo> ex) {
            return False;
        }
        list<auto> idx = doc.evalXPath("//*[local-name()='sitemapindex']");
        return idx ? True : False;
    }

    #! Fetch a sitemap from a URL and recursively parse sitemap-index entries
    /** Issues an HTTP GET against \a sitemap_url, parses the response with
        @ref parseUrls(), and if the document is a sitemap-index recursively
        fetches each referenced sub-sitemap up to \c max_index_depth levels.

        Total returned URLs are capped at \c max_urls to bound memory.

        @param sitemap_url the URL of the sitemap or sitemap-index to fetch
        @param opts options hash:
          - \c user_agent (\c *string): User-Agent header
          - \c headers (\c *hash<string, string>): extra HTTP headers (auth, etc.)
          - \c request_timeout (\c *timeout): per-request HTTP timeout
          - \c max_index_depth (int, default 3): maximum sitemap-index recursion depth
          - \c max_urls (int, default 100000): hard cap on returned URL count
        @return list of page URLs discovered (empty on any failure)
    */
    static list<string> fetchAndParse(string sitemap_url, *hash<auto> opts) {
        int max_depth = opts.max_index_depth ?? DefaultMaxIndexDepth;
        int max_urls = opts.max_urls ?? DefaultMaxUrls;
        timeout request_timeout = opts.request_timeout ?? DefaultRequestTimeout;
        string user_agent = opts.user_agent ?? "Qore-WebContentUtil-Sitemap/1.0";
        *hash<string, string> extra_headers = opts.headers;

        HttpClientIo::HttpClientConnectionManager mgr(
            <HttpClientIo::HttpClientConnectionManagerOptions>{
                "connect_timeout": 5s,
                "request_timeout": request_timeout,
            });

        # Avoid revisits when an index file points back at itself or
        # cross-references already-seen sub-sitemaps
        hash<string, bool> visited_sitemaps = {};
        return SitemapParser::fetchRecursive(mgr, sitemap_url, user_agent,
            extra_headers, 0, max_depth, max_urls, \visited_sitemaps);
    }

    #! Internal recursive helper for fetchAndParse
    private static list<string> fetchRecursive(
            HttpClientIo::HttpClientConnectionManager mgr,
            string sitemap_url, string user_agent, *hash<string, string> extra_headers,
            int depth, int max_depth, int max_urls,
            reference<hash<string, bool>> visited_sitemaps) {
        list<string> result = ();
        if (depth > max_depth) {
            return result;
        }
        if (visited_sitemaps{sitemap_url}) {
            return result;
        }
        visited_sitemaps{sitemap_url} = True;

        # Parse the URL into origin + path for HttpClientConnectionManager
        hash<auto> parts;
        try {
            parts = parse_url(sitemap_url);
        } catch (hash<ExceptionInfo> ex) {
            return result;
        }
        if (!parts.host.val()) {
            return result;
        }
        string origin = sprintf("%s://%s%s",
            parts.protocol ?? "https",
            parts.host,
            parts.port ? sprintf(":%d", parts.port) : "");
        string req_path = parts.path ?? "/";
        if (parts.query.val()) {
            req_path += "?" + parts.query;
        }

        hash<auto> req_headers = {
            "User-Agent": user_agent,
            "Accept": "application/xml, text/xml, */*",
        };
        if (extra_headers) {
            req_headers += extra_headers;
        }

        hash<auto> resp;
        try {
            resp = mgr.request(origin, "GET", req_path, req_headers);
        } catch (hash<ExceptionInfo> ex) {
            return result;
        }
        if (resp.status_code != 200) {
            return result;
        }

        string body;
        if (resp.body.typeCode() == NT_BINARY) {
            body = resp.body.toString("UTF-8");
        } else {
            body = string(resp.body ?? "");
        }
        if (!body.val()) {
            return result;
        }

        # Index file: recurse into sub-sitemaps; regular file: collect URLs
        if (SitemapParser::isIndex(body)) {
            list<string> sub_sitemaps = SitemapParser::parseUrls(body);
            foreach string sub_url in (sub_sitemaps) {
                if (result.size() >= max_urls) {
                    break;
                }
                list<string> sub_urls = SitemapParser::fetchRecursive(mgr,
                    sub_url, user_agent, extra_headers, depth + 1, max_depth,
                    max_urls - result.size(), \visited_sitemaps);
                result += sub_urls;
            }
        } else {
            list<string> page_urls = SitemapParser::parseUrls(body);
            foreach string url in (page_urls) {
                if (result.size() >= max_urls) {
                    break;
                }
                result += url;
            }
        }
        return result;
    }
}

} # namespace WebContentUtil
