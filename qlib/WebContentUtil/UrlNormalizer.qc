# -*- mode: qore; indent-tabs-mode: nil -*-

/*  UrlNormalizer.qc Copyright 2026 Qore Technologies, s.r.o.

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

#! URL normalization utility class
/** Implements the full normalization rule set from \c design/web-crawler.md §5.2.

    All methods are static — no constructor needed, no state to manage.

    @par Example
    @code{.py}
string url = UrlNormalizer::normalize("HTTP://Example.COM:80/a/../b?z=1&a=2#section");
# returns "http://example.com/b?a=1&z=2"
    @endcode

    @since WebContentUtil 1.0
*/
public class UrlNormalizer {
    #! Default ports stripped during normalization
    /** Map of scheme (lowercase) -> default port that should be omitted from
        the normalized URL since it's redundant.
    */
    const DefaultPorts = {
        "http": 80,
        "https": 443,
        "ftp": 21,
        "ftps": 990,
        "ws": 80,
        "wss": 443,
    };

    #! Normalize a URL for deduplication
    /** Implements the full set of rules from design/web-crawler.md §5.2:
        1. Strip fragment (\c #section)
        2. Resolve \c /../ and \c /./ in path
        3. Lowercase scheme and host (path case is preserved)
        4. Strip default ports (\c :80 for http, \c :443 for https, etc.)
        5. Strip trailing slash on non-root paths (unless \c preserve_trailing_slash)
        6. Decode unreserved percent-encodings (\c %41 -> \c A)
        7. Sort query parameters (alphabetical)

        @param url the URL to normalize
        @param opts normalization options:
          - \c preserve_trailing_slash (bool, default \c False): keep trailing slash
            on non-root paths.  The default behavior strips them per the design spec;
            set this to True for callers that need directory-significant URL semantics.
        @return normalized URL string

        @par Example
        @code{.py}
string n = UrlNormalizer::normalize("https://example.com/docs/../api/?b=2&a=1#top");
# returns "https://example.com/api?a=1&b=2"
        @endcode
    */
    static string normalize(string url, *hash<auto> opts) {
        bool preserve_trailing_slash = opts.preserve_trailing_slash ?? False;

        # Step 1: Strip fragment
        url = regex_subst(url, "#.*$", "");

        # Parse components
        hash<auto> parts = parse_url(url);

        # Step 3: Lowercase scheme + host (path stays case-sensitive)
        if (parts.protocol.val()) {
            parts.protocol = parts.protocol.lwr();
        }
        if (parts.host.val()) {
            parts.host = parts.host.lwr();
        }

        # Step 2: Resolve /../ and /./ in path
        # Step 5: Trailing slash handling
        if (parts.path.val()) {
            # Separate path and query for path resolution
            *string query;
            string path_only = parts.path;
            int qpos = path_only.find("?");
            if (qpos >= 0) {
                query = path_only.substr(qpos + 1);
                path_only = path_only.substr(0, qpos);
            }

            # Detect trailing slash before resolution
            bool had_trailing = path_only.size() > 1 && path_only.endsWith("/");

            # Resolve segments
            list<string> segments = path_only.split("/");
            list<string> resolved = ();
            foreach string seg in (segments) {
                if (seg == "..") {
                    if (resolved.size() > 1) {
                        pop resolved;
                    }
                } else if (seg != ".") {
                    resolved += seg;
                }
            }
            path_only = resolved.join("/");
            if (!path_only.val()) {
                path_only = "/";
            }

            # Step 5: trailing slash policy
            if (path_only != "/" && path_only.endsWith("/") && !preserve_trailing_slash) {
                # Strip trailing slash on non-root paths (per design)
                path_only = path_only.substr(0, path_only.size() - 1);
            } else if (preserve_trailing_slash && had_trailing
                    && path_only != "/" && !path_only.endsWith("/")) {
                # Re-add the trailing slash if caller asked to preserve it
                path_only += "/";
            }

            # Step 6: Decode unreserved percent-encodings in the path
            path_only = UrlNormalizer::decodeUnreservedPercentEncodings(path_only);

            # Step 7: Sort query parameters
            if (query.val()) {
                list<string> qparts = query.split("&");
                qparts = sort(qparts);
                # Also percent-decode unreserved chars in each param's name and value
                qparts = map UrlNormalizer::decodeUnreservedPercentEncodings($1), qparts;
                parts.path = path_only + "?" + qparts.join("&");
            } else {
                parts.path = path_only;
            }
        }

        # Step 4: Strip default port
        *int port = parts.port;
        if (port) {
            *int default_port = DefaultPorts{parts.protocol ?? ""};
            if (default_port && port == default_port) {
                port = NOTHING;
            }
        }

        # Reconstruct
        return sprintf("%s://%s%s%s",
            parts.protocol ?? "https",
            parts.host,
            port ? sprintf(":%d", port) : "",
            parts.path ?? "/");
    }

    #! Decode percent-encoded sequences for unreserved characters
    /** RFC 3986 §2.3 unreserved characters are A-Z, a-z, 0-9, hyphen, period,
        underscore, tilde.  These should never be percent-encoded; if they are,
        decoding them produces an equivalent canonical form.

        Reserved characters and other bytes are left encoded so the URL semantics
        are preserved.

        @param s the string (URL path or query component) to decode
        @return string with %xx sequences for unreserved characters decoded
    */
    private static string decodeUnreservedPercentEncodings(string s) {
        # Match %XX where XX is two hex digits.
        # We use a callback-style replacement: scan and rebuild.
        string result = "";
        int i = 0;
        int sz = s.size();
        while (i < sz) {
            if (s[i] == "%" && i + 2 < sz) {
                string hex = s.substr(i + 1, 2);
                if (hex =~ /^[0-9a-fA-F]{2}$/) {
                    int byte = UrlNormalizer::hexToInt(hex);
                    # Unreserved set: A-Z (65-90), a-z (97-122), 0-9 (48-57),
                    # hyphen 45, period 46, underscore 95, tilde 126
                    if ((byte >= 65 && byte <= 90)
                            || (byte >= 97 && byte <= 122)
                            || (byte >= 48 && byte <= 57)
                            || byte == 45 || byte == 46 || byte == 95 || byte == 126) {
                        result += chr(byte);
                        i += 3;
                        continue;
                    }
                    # Keep the percent-encoded form, but uppercase the hex digits
                    # for canonical form (RFC 3986 §6.2.2.1)
                    result += "%" + hex.upr();
                    i += 3;
                    continue;
                }
            }
            result += s[i];
            ++i;
        }
        return result;
    }

    #! Parse a 2-character hex string to an int (0-255)
    /** @param hex 2-character hex string (case-insensitive)
        @return integer value 0-255
    */
    private static int hexToInt(string hex) {
        int result = 0;
        for (int i = 0; i < hex.size(); ++i) {
            int c = hex[i].lwr().toInt();  # toInt on a single-char string returns 0
            string ch = hex[i];
            int v;
            if (ch >= "0" && ch <= "9") {
                v = ord(ch) - ord("0");
            } else if (ch >= "a" && ch <= "f") {
                v = ord(ch) - ord("a") + 10;
            } else if (ch >= "A" && ch <= "F") {
                v = ord(ch) - ord("A") + 10;
            } else {
                v = 0;
            }
            result = (result * 16) + v;
        }
        return result;
    }
}

} # namespace WebContentUtil
