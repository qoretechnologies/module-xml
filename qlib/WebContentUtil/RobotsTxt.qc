# -*- mode: qore; indent-tabs-mode: nil -*-

/*  RobotsTxt.qc Copyright 2026 Qore Technologies, s.r.o.

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

#! Per-User-agent rule group accumulated during robots.txt parsing
hashdecl RobotsGroup {
    list<string> allow = ();
    list<string> disallow = ();
    *int crawl_delay;
}

#! robots.txt fetcher and parser (RFC 9309)
/** Used by @ref WebContentUtil::WebCrawler "WebCrawler" when \c respect_robots is True.

    Implements the subset of RFC 9309 needed for crawl politeness:
    - \c User-agent groups (most-specific match wins; falls back to \c "*")
    - \c Disallow rules (path prefix match)
    - \c Allow rules (override Disallow per Google's interpretation)
    - \c Crawl-delay extension (non-standard but widely honored)
    - \c Sitemap directives

    Per RFC 9309 §2.3.1.3, an unreachable robots.txt is treated as fully permissive.

    @par Example
    @code{.py}
*RobotsTxt robots = RobotsTxt::fetch("https://example.com/", "MyBot/1.0");
if (robots && !robots.isAllowed("/admin/")) {
    # skip /admin/
}
*int delay = robots ? robots.getCrawlDelay() : NOTHING;
    @endcode

    @since WebContentUtil 1.0
*/
public class RobotsTxt {
    #! Default request timeout for fetching robots.txt
    const DefaultRequestTimeout = 10s;

    private {
        #! Allow rules for the matching User-agent group (path prefixes)
        list<string> allow_rules;
        #! Disallow rules for the matching User-agent group (path prefixes)
        list<string> disallow_rules;
        #! Crawl-delay in seconds (NOTHING if not set)
        *int crawl_delay;
        #! Sitemap URLs declared anywhere in the file
        list<string> sitemap_urls;
        #! The User-agent that this instance was matched against
        string matched_ua;
    }

    #! Fetch and parse robots.txt for a base URL
    /** Builds the robots.txt URL from the base URL's scheme, host, and port.
        On any HTTP error (404, 5xx, network failure), returns @ref nothing — per
        RFC 9309 §2.3.1.3 the caller should treat this as "everything allowed".

        @param base_url the base URL of the site (only scheme/host/port are used)
        @param user_agent the User-Agent string (used both as the request header
            and as the matching key against User-agent: directives in the file)
        @param request_timeout per-request HTTP timeout
        @return parsed RobotsTxt instance, or NOTHING if unreachable / not present
    */
    static *RobotsTxt fetch(string base_url, *string user_agent,
            *timeout request_timeout) {
        timeout effective_timeout = request_timeout ?? DefaultRequestTimeout;
        string ua = user_agent ?? "*";

        # Build the robots.txt URL: scheme://host[:port]/robots.txt
        hash<auto> parts;
        try {
            parts = parse_url(base_url);
        } catch (hash<ExceptionInfo> ex) {
            return NOTHING;
        }
        if (!parts.host.val()) {
            return NOTHING;
        }
        string robots_url = sprintf("%s://%s%s/robots.txt",
            parts.protocol ?? "https",
            parts.host,
            parts.port ? sprintf(":%d", parts.port) : "");

        # Fetch with a short timeout — robots.txt should be fast or skipped
        HttpClientIo::HttpClientConnectionManager mgr(
            <HttpClientIo::HttpClientConnectionManagerOptions>{
                "connect_timeout": 5s,
                "request_timeout": effective_timeout,
            });

        string base_only = sprintf("%s://%s%s",
            parts.protocol ?? "https",
            parts.host,
            parts.port ? sprintf(":%d", parts.port) : "");
        hash<auto> resp;
        try {
            resp = mgr.request(base_only, "GET", "/robots.txt", {
                "User-Agent": ua,
                "Accept": "text/plain, */*",
            });
        } catch (hash<ExceptionInfo> ex) {
            # Network failure — treat as permissive (RFC 9309 §2.3.1.3)
            return NOTHING;
        }

        if (resp.status_code != 200) {
            # 404, 5xx, etc. — treat as permissive
            return NOTHING;
        }

        string body = resp.body.typeCode() == NT_BINARY
            ? resp.body.toString("UTF-8") : resp.body;
        return new RobotsTxt(body, ua);
    }

    #! Construct from raw robots.txt content
    /** Parses the file and extracts the rule set for the given user agent.
        Most-specific User-agent group wins; falls back to \c "*" group if no
        explicit match.  Hostname-style matching is case-insensitive.

        @param content raw robots.txt body
        @param user_agent the User-Agent to match against (default: \c "*")
    */
    constructor(string content, *string user_agent) {
        matched_ua = user_agent ?? "*";
        allow_rules = ();
        disallow_rules = ();
        sitemap_urls = ();

        # Parse the file into User-agent groups
        # A "group" starts with one or more User-agent: lines and contains
        # Allow/Disallow/Crawl-delay rules until the next User-agent group.
        string ua_lower = matched_ua.lwr();

        # State machine
        list<string> current_uas = ();
        # Per-UA accumulators
        hash<string, hash<RobotsGroup>> groups;
        bool in_group_header = False;  # True while we're in a run of User-agent lines

        list<string> lines = content.split("\n");
        foreach string raw_line in (lines) {
            # Strip comments and trim
            string line = regex_subst(raw_line, "#.*$", "");
            line = trim(line);
            if (!line.val()) {
                continue;
            }

            int colon = line.find(":");
            if (colon < 0) {
                continue;
            }
            string field = trim(line.substr(0, colon)).lwr();
            string value = trim(line.substr(colon + 1));

            switch (field) {
                case "user-agent":
                    if (!in_group_header) {
                        # Starting a new group
                        current_uas = ();
                        in_group_header = True;
                    }
                    current_uas += value.lwr();
                    if (!groups{value.lwr()}) {
                        groups{value.lwr()} = <RobotsGroup>{};
                    }
                    break;

                case "allow":
                    in_group_header = False;
                    foreach string ua in (current_uas) {
                        groups{ua}.allow += value;
                    }
                    break;

                case "disallow":
                    in_group_header = False;
                    foreach string ua in (current_uas) {
                        groups{ua}.disallow += value;
                    }
                    break;

                case "crawl-delay":
                    in_group_header = False;
                    foreach string ua in (current_uas) {
                        groups{ua}.crawl_delay = value.toInt();
                    }
                    break;

                case "sitemap":
                    # Sitemap is global, not per-UA
                    sitemap_urls += value;
                    break;
            }
        }

        # Pick the most specific matching group.
        # Per RFC 9309 §2.2.1, the longest matching User-agent prefix wins.
        # For simplicity we do exact-match-or-star, with case-insensitive comparison.
        *hash<RobotsGroup> matched_group;
        if (groups{ua_lower}) {
            matched_group = groups{ua_lower};
        } else {
            # Try substring matches: a group "MyBot" matches a UA "MyBot/1.0"
            int best_len = 0;
            foreach string g in (keys groups) {
                if (g != "*" && ua_lower.find(g) == 0 && g.size() > best_len) {
                    matched_group = groups{g};
                    best_len = g.size();
                }
            }
            if (!matched_group && groups{"*"}) {
                matched_group = groups{"*"};
            }
        }

        if (matched_group) {
            allow_rules = matched_group.allow;
            disallow_rules = matched_group.disallow;
            crawl_delay = matched_group.crawl_delay;
        }
    }

    #! Returns True if the path is allowed for the configured User-agent
    /** Per Google's interpretation, the longest matching rule wins, with Allow
        beating Disallow on a tie.  An empty Disallow rule means "allow everything".

        @param path the URL path (no scheme/host) to check
        @return True if the path is allowed
    */
    bool isAllowed(string path) {
        # Find the longest matching Allow and Disallow rules
        int best_allow_len = -1;
        int best_disallow_len = -1;

        foreach string rule in (allow_rules) {
            if (rule.val() && path.find(rule) == 0 && rule.size() > best_allow_len) {
                best_allow_len = rule.size();
            }
        }
        foreach string rule in (disallow_rules) {
            if (rule == "") {
                # Empty Disallow means "allow everything" — skip
                continue;
            }
            if (path.find(rule) == 0 && rule.size() > best_disallow_len) {
                best_disallow_len = rule.size();
            }
        }

        if (best_disallow_len < 0) {
            return True;  # no matching disallow
        }
        if (best_allow_len >= best_disallow_len) {
            return True;  # allow wins on length tie or longer
        }
        return False;
    }

    #! Returns the Crawl-delay directive in seconds
    /** @return crawl delay in seconds, or @ref nothing if not specified
    */
    *int getCrawlDelay() {
        return crawl_delay;
    }

    #! Returns the list of Sitemap URLs declared in robots.txt
    /** @return list of sitemap URLs (may be empty)
    */
    list<string> getSitemaps() {
        return sitemap_urls;
    }
}

} # namespace WebContentUtil
