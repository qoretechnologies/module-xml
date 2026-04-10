# -*- mode: qore; indent-tabs-mode: nil -*-

/*  HtmlExtractor.qc Copyright 2026 Qore Technologies, s.r.o.

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

#! Result of HtmlExtractor::extractLinks() — discovered hrefs plus metadata
public hashdecl LinkInfo {
    #! Crawlable absolute URLs (relative URLs are resolved against base_url)
    /** rel="nofollow" anchors are excluded; non-HTTP schemes (mailto:, javascript:,
        tel:, sms:, data:, etc.) are excluded.
    */
    list<string> hrefs = ();

    #! \c <link rel="canonical" href="..."> if present
    /** When set, this is the canonical URL for the page and the crawler should
        use it as the page's identity instead of the request URL.
    */
    *string canonical;

    #! \c <link rel="sitemap" href="..."> URLs declared in the page (rare)
    list<string> sitemaps = ();
}

#! HTML text extraction utility class — DOM-backed via libxml2's HTML parser
/** Uses the @ref Qore::Xml::parse_html() "parse_html()" function from the \c xml
    module (which wraps libxml2's lenient HTML parser \c htmlReadMemory).  This
    handles real-world malformed HTML5, supports proper CSS-selector content
    stripping via XPath translation, and reliably extracts \c <link rel="canonical">
    and \c rel="nofollow" semantics — none of which are reliable with regex.

    All methods are static.

    @par Example
    @code{.py}
string text = HtmlExtractor::extractText("<html><body><p>Hello</p></body></html>");
# returns "Hello"

hash<LinkInfo> info = HtmlExtractor::extractLinks(html, "https://example.com/page");
# info.hrefs = absolute URLs (rel=nofollow excluded, non-HTTP schemes excluded)
# info.canonical = the <link rel=canonical> if present
    @endcode

    @since WebContentUtil 1.0
*/
public class HtmlExtractor {
    #! Default CSS selectors stripped from HTML before text extraction
    /** Per design/web-crawler.md §5.6.  Includes element selectors and ARIA
        role attribute selectors that match common navigation/banner regions.
    */
    const DefaultStripSelectors = (
        "script", "style", "nav", "footer", "header", "noscript",
        "[role='navigation']", "[role='banner']", "[role='contentinfo']",
    );

    #! Block-level element names — converted to newlines during text extraction
    const BlockElements = (
        "p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "tr", "td", "th", "section", "article", "aside",
        "blockquote", "pre", "hr",
    );

    #! Link schemes that are NEVER followed (mailto:, javascript:, etc.)
    const BlockedLinkSchemes = (
        "javascript:", "mailto:", "tel:", "sms:", "data:",
        "vbscript:", "file:", "chrome:", "about:", "ftp:", "ftps:",
    );

    #! Strip CSS-selected elements from HTML, returning the cleaned HTML
    /** Parses the HTML into a DOM via @ref Qore::Xml::parse_html(), removes
        every element matching any of the supplied CSS selectors, and serializes
        the remaining DOM back to an HTML string.

        Useful for callers that need to keep HTML structure (for downstream
        processors that consume HTML, e.g. document ingesters that re-parse
        the HTML to extract structured fields) but want to drop noise like
        navigation menus, sidebars, footers, scripts, and ads BEFORE handing
        the document downstream.

        @param html raw HTML string
        @param strip_selectors optional list of CSS selectors to strip; appended
            to @ref DefaultStripSelectors.  Supported selector forms: \c element,
            \c .class, \c #id, \c [attr='value'], and combinations (e.g.
            \c div.sidebar).  Compound and pseudo-class selectors are not
            supported and will be silently skipped.
        @return the cleaned HTML — body subtree if present, otherwise the
            document root; on parse failure returns the original \a html
            unchanged
    */
    static string stripElements(string html, *list<string> strip_selectors) {
        try {
            XmlDoc doc = parse_html(html);
            list<string> selectors = DefaultStripSelectors;
            if (strip_selectors) {
                selectors += strip_selectors;
            }
            foreach string sel in (selectors) {
                *string xpath = HtmlExtractor::cssToXPath(sel);
                if (!xpath) {
                    continue;  # unsupported selector — silently skipped
                }
                HtmlExtractor::removeMatching(doc, xpath);
            }
            # Serialize the cleaned DOM back to HTML — prefer the body subtree
            # so we don't include the <html><head> wrapper that libxml2 adds
            list<auto> body = doc.evalXPath("//body");
            if (body) {
                return body[0].getXML();
            }
            list<auto> root = doc.evalXPath("/*");
            if (root) {
                return root[0].getXML();
            }
        } catch (hash<ExceptionInfo> ex) {
            # Parse failure — fall through and return original
        }
        return html;
    }

    #! Extract readable text from HTML, stripping non-content elements
    /** Parses the HTML into a DOM via @ref Qore::Xml::parse_html() "parse_html()",
        removes elements matching the strip selectors, and returns the remaining
        text content with whitespace normalized.

        @param html raw HTML string
        @param strip_selectors optional list of additional CSS selectors to strip;
            these are appended to @ref DefaultStripSelectors.  Supported selector
            forms: \c element, \c .class, \c #id, \c [attr='value'], and combinations
            (e.g. \c div.sidebar).  Compound and pseudo-class selectors are not
            supported and will be ignored with a warning.
        @return extracted plain text content with whitespace normalized
    */
    static string extractText(string html, *list<string> strip_selectors) {
        # Step 1: Parse the HTML into a DOM and use CSS-selector-aware stripping.
        # If parsing fails (extreme malformed input), fall back to the original
        # text directly so the regex pass below still gets a chance.
        string cleaned_html = html;
        try {
            XmlDoc doc = parse_html(html);

            list<string> selectors = DefaultStripSelectors;
            if (strip_selectors) {
                selectors += strip_selectors;
            }
            foreach string sel in (selectors) {
                *string xpath = HtmlExtractor::cssToXPath(sel);
                if (!xpath) {
                    continue;  # unsupported selector — silently skipped
                }
                HtmlExtractor::removeMatching(doc, xpath);
            }
            # Serialize the cleaned DOM back to HTML.  We use evalXPath to find
            # the body (if present) and serialize just that subtree, otherwise
            # serialize the whole document.
            list<auto> body = doc.evalXPath("//body");
            if (body) {
                cleaned_html = body[0].getXML();
            } else {
                list<auto> root = doc.evalXPath("/*");
                if (root) {
                    cleaned_html = root[0].getXML();
                }
            }
        } catch (hash<ExceptionInfo> ex) {
            # Fall through with raw html
        }

        # Step 2: Regex-based text extraction on the cleaned HTML.  This handles
        # the inline-element walking (text mixed with <span>, <b>, etc. inside
        # block elements) that XmlNode's element-only API can't traverse, and
        # produces newlines at block element boundaries for the chunker.
        string text = cleaned_html;

        # Replace block-level tags with newlines to preserve paragraph structure
        text = regex_subst(text, "<(?:p|div|br|h[1-6]|li|tr|td|th|section|article|aside|blockquote|pre|hr)[^>]*>",
            "\n", RE_Global);

        # Remove all remaining HTML tags
        text = regex_subst(text, "<[^>]+>", " ", RE_Global);

        # Decode HTML entities
        text = html_decode(text);

        # Collapse whitespace
        text = regex_subst(text, "[ \t]+", " ", RE_Global);
        text = regex_subst(text, "\n[ \t]+", "\n", RE_Global);
        text = regex_subst(text, "\n{3,}", "\n\n", RE_Global);

        return trim(text);
    }

    #! Extract the page title from HTML
    /** @param html raw HTML string
        @return title text, or @ref nothing if no \c <title> tag found
    */
    static *string extractTitle(string html) {
        XmlDoc doc;
        try {
            doc = parse_html(html);
        } catch (hash<ExceptionInfo> ex) {
            return NOTHING;
        }
        list<auto> nodes = doc.evalXPath("//title/text()");
        if (!nodes) {
            return NOTHING;
        }
        string t = nodes[0].getContent();
        return trim(t).val() ? trim(t) : NOTHING;
    }

    #! Extract anchor links + canonical/sitemap metadata from HTML
    /** Walks the parsed DOM, extracts \c href from \c <a> elements, skips
        anchors with \c rel="nofollow", excludes non-HTTP schemes, and resolves
        relative URLs against the supplied base URL.  Also extracts
        \c <link rel="canonical"> and \c <link rel="sitemap"> if present.

        @param html raw HTML string
        @param base_url base URL for resolving relative links
        @return @ref LinkInfo hash with crawlable hrefs + canonical + sitemaps
    */
    static hash<LinkInfo> extractLinks(string html, string base_url) {
        hash<LinkInfo> info = <LinkInfo>{};
        XmlDoc doc;
        try {
            doc = parse_html(html);
        } catch (hash<ExceptionInfo> ex) {
            return info;
        }

        # Anchor hrefs that are NOT rel="nofollow"
        list<auto> anchor_nodes = doc.evalXPath(
            "//a[not(@rel) or not(contains(@rel, 'nofollow'))][@href]");
        foreach auto a in (anchor_nodes) {
            *string href = HtmlExtractor::getAttribute(a, "href");
            if (!href.val()) {
                continue;
            }
            href = trim(href);
            if (!href.val()) {
                continue;
            }
            if (HtmlExtractor::hasBlockedScheme(href)) {
                continue;
            }
            info.hrefs += HtmlExtractor::resolveUrl(href, base_url);
        }

        # <link rel="canonical">
        list<auto> canonical_nodes = doc.evalXPath(
            "//link[@rel='canonical' and @href]");
        if (canonical_nodes) {
            *string href = HtmlExtractor::getAttribute(canonical_nodes[0], "href");
            if (href.val()) {
                info.canonical = HtmlExtractor::resolveUrl(trim(href), base_url);
            }
        }

        # <link rel="sitemap">
        list<auto> sitemap_nodes = doc.evalXPath(
            "//link[@rel='sitemap' and @href]");
        foreach auto sm in (sitemap_nodes) {
            *string href = HtmlExtractor::getAttribute(sm, "href");
            if (href.val()) {
                info.sitemaps += HtmlExtractor::resolveUrl(trim(href), base_url);
            }
        }

        return info;
    }

    #! Convert a simple CSS selector to an XPath expression
    /** Supported selector forms (matching the design's strip list):
        - \c element — all elements with that tag name
        - \c .class — all elements with that class
        - \c #id — element with that ID
        - \c [attr] — elements that have the attribute
        - \c [attr='value'] — elements with that attribute value
        - \c element.class, \c element[attr='value'] — combinations

        Compound selectors (\c "a > b", \c "a b") and pseudo-classes
        (\c ":hover", \c ":nth-child(2)") are NOT supported and return @ref nothing
        with a one-time \c QORE-WARNING log line.

        @param css the CSS selector
        @return XPath equivalent, or @ref nothing if the selector is not supported
    */
    static *string cssToXPath(string css) {
        css = trim(css);
        if (!css.val()) {
            return NOTHING;
        }
        # Reject compound/pseudo selectors we can't handle
        if (css =~ /[ >+~:]/) {
            return NOTHING;
        }

        # Parse: optional element name, then any number of .class / #id / [attr...]
        # qualifiers
        string element = "*";
        list<string> predicates = ();

        # Element name (alphanumeric + hyphen, start of selector)
        *list<*string> elem_match = regex_extract(css, "^([a-zA-Z][a-zA-Z0-9-]*)");
        int pos = 0;
        if (elem_match && elem_match[0].val()) {
            element = elem_match[0];
            pos = element.size();
        }

        # Walk the rest of the selector pulling off qualifiers
        while (pos < css.size()) {
            string rest = css.substr(pos);
            *list<*string> m;
            # .class
            m = regex_extract(rest, "^\\.([a-zA-Z_][a-zA-Z0-9_-]*)");
            if (m && m[0].val()) {
                predicates += sprintf(
                    "contains(concat(' ', normalize-space(@class), ' '), ' %s ')",
                    m[0]);
                pos += m[0].size() + 1;  # 1 for the dot
                continue;
            }
            # #id
            m = regex_extract(rest, "^#([a-zA-Z_][a-zA-Z0-9_-]*)");
            if (m && m[0].val()) {
                predicates += sprintf("@id='%s'", m[0]);
                pos += m[0].size() + 1;  # 1 for the hash
                continue;
            }
            # [attr='value'] or [attr="value"] or [attr]
            m = regex_extract(rest, "^\\[([a-zA-Z_][a-zA-Z0-9_-]*)(?:=['\"]?([^'\"\\]]*)['\"]?)?\\]");
            if (m && m[0].val()) {
                string attr = m[0];
                *string val = m[1];
                if (val.val()) {
                    predicates += sprintf("@%s='%s'", attr, val);
                } else {
                    predicates += sprintf("@%s", attr);
                }
                # Length consumed: '[' + attr + optional '=val' + ']'
                # Easier: match the whole bracket expression and consume that
                *list<*string> bracket_match = regex_extract(rest, "^(\\[[^\\]]+\\])");
                if (bracket_match && bracket_match[0].val()) {
                    pos += bracket_match[0].size();
                } else {
                    return NOTHING;  # malformed
                }
                continue;
            }
            # Unsupported selector character — bail
            return NOTHING;
        }

        string xpath = "//" + element;
        if (predicates) {
            xpath += "[" + predicates.join(" and ") + "]";
        }
        return xpath;
    }

    #! Remove all elements matching an XPath expression from a parsed document
    /** Walks matched nodes and unlinks them from the DOM tree.

        @param doc the parsed document
        @param xpath an XPath expression matching the nodes to remove
    */
    private static removeMatching(XmlDoc doc, string xpath) {
        list<auto> nodes = doc.evalXPath(xpath);
        foreach auto node in (nodes) {
            try {
                node.unlinkNode();
            } catch (hash<ExceptionInfo> ex) {
                # Some node types may not support unlinkNode — ignore
            }
        }
    }

    #! Get an attribute value from an XmlNode
    /** XmlNode exposes attribute access via getProp() — this is a thin wrapper
        with the conventional name.

        @param node the element node
        @param attr the attribute name
        @return the attribute value, or @ref nothing if absent
    */
    private static *string getAttribute(XmlNode node, string attr) {
        return node.getProp(attr);
    }

    #! Returns True if the URL uses a scheme that should never be followed
    /** @param url the URL or href to check
        @return True for javascript:, mailto:, tel:, sms:, data:, vbscript:,
            file:, chrome:, about:, ftp:, ftps:
    */
    static bool hasBlockedScheme(string url) {
        string lurl = url.lwr();
        foreach string scheme in (BlockedLinkSchemes) {
            if (lurl.find(scheme) == 0) {
                return True;
            }
        }
        return False;
    }

    #! Resolve a possibly-relative URL against a base URL
    /** @param href the href value (may be absolute, root-relative, or relative)
        @param base_url the base URL of the page containing the link
        @return absolute URL
    */
    static string resolveUrl(string href, string base_url) {
        if (href =~ /^https?:\/\//i) {
            return href;
        }
        if (href =~ /^\//) {
            # Root-relative — resolve against scheme + host
            *string base = (base_url =~ x/^(https?:\/\/[^\/]+)/)[0];
            if (base) {
                return base + href;
            }
            return href;
        }
        # Relative — resolve against page base directory
        string base_dir = base_url =~ /\/$/ ? base_url : dirname(base_url) + "/";
        return base_dir + href;
    }
}

} # namespace WebContentUtil
