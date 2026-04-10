# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebCrawler.qc Copyright 2026 Qore Technologies, s.r.o.

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

#! Parallel BFS web crawler
/** Crawls a website starting from a seed URL using breadth-first traversal with
    parallel HTTP requests via @ref HttpClientIo::HttpClientConnectionManager. Features:

    - HTTP/2 and HTTP/3 multiplexing for high throughput (both protocols supported on a single
      connection); automatic protocol auto-selection via Alt-Svc discovery upgrades from HTTP/2
      to HTTP/3 when available
    - HTTP/1.1 fallback with multiple connections per host
    - Redirect following (via \c request() method)
    - Automatic rate limiting detection and throttling on 429/503 responses
    - URL normalization and deduplication
    - Configurable depth, page cap, concurrency, and delay
    - Progress reporting via callback

    All methods are static.

    @par Example
    @code{.py}
list<hash<auto>> pages = WebCrawler::crawl("https://docs.example.com/", {
    "max_depth": 3,
    "max_pages": 500,
    "concurrency": 10,
    "delay_ms": 50,
    "progress": sub (int pages, int queued) {
        stderr.printf("  crawled %d pages, %d queued\n", pages, queued);
    },
});
    @endcode

    @since WebContentUtil 1.0
*/
public class WebCrawler {
    #! Default maximum crawl depth
    const DefaultMaxDepth = 3;

    #! Default maximum pages to crawl
    const DefaultMaxPages = 500;

    #! Default number of concurrent requests per batch
    const DefaultConcurrency = 10;

    #! Default connect timeout
    const DefaultConnectTimeout = 10s;

    #! Default request timeout
    const DefaultRequestTimeout = 30s;

    #! Minimum text length to keep a page (characters)
    const MinTextLength = 50;

    #! Default User-Agent header sent for crawl requests
    /** Generic Qore-library identifier.  Higher-level callers (\c qctl, \c saasctl,
        \c QorusAiWebCrawler) should override this with their own User-Agent.
    */
    const DefaultUserAgent = "Qore-WebContentUtil/1.0 (+https://qore.org)";

    #! Default maximum response body size in bytes (10 MiB)
    /** Pages larger than this are skipped — likely binary content the
        \c text/html content-type filter missed, or a DoS attempt.
    */
    const DefaultMaxResponseBytes = 10485760;

    #! Default URL extensions to skip pre-fetch (binary/non-HTML content)
    /** Applied as a suffix-on-path filter during link extraction so we don't
        waste a HTTP round trip on links that are clearly not crawlable HTML.
    */
    const DefaultSkipExtensions = (
        "pdf", "zip", "tar", "gz", "tgz", "bz2", "rar", "7z",
        "png", "jpg", "jpeg", "gif", "ico", "svg", "webp", "bmp",
        "mp3", "mp4", "mov", "avi", "wmv", "ogg", "wav", "webm",
        "css", "js", "json", "xml", "rss", "atom",
        "woff", "woff2", "ttf", "eot", "otf",
        "exe", "dmg", "msi", "deb", "rpm", "iso",
    );

    #! URL schemes that are NEVER followed during link extraction
    /** These are link-extraction artifacts (mail/phone/javascript) or local-resource
        schemes that should never be crawled.
    */
    const BlockedLinkSchemes = (
        "javascript:", "mailto:", "tel:", "sms:", "data:",
        "vbscript:", "file:", "chrome:", "about:", "ftp:", "ftps:",
    );

    #! Crawl a website starting from seed_url
    /** Performs a breadth-first crawl starting from the seed URL. Only follows links
        within the same URL prefix (same host and path prefix as the seed URL). Extracts
        HTML text content and page titles from each page.

        @param seed_url the starting URL
        @param opts crawl options hash:
          - \c max_depth (int, default 3): maximum link-follow depth
          - \c max_pages (int, default 500): hard page cap
          - \c concurrency (int, default 10): parallel requests per batch
          - \c delay_ms (int, default 0): delay between batches in milliseconds
          - \c progress (code<nothing(int pages, int queued)>, optional): progress callback
            invoked after each batch
          - \c url_filter (code<bool(string url)>, optional): return True to accept a discovered
            URL for crawling; called after normalization but before dedup check
        @return list of page hashes, each containing:
          - \c url (string): the page URL
          - \c title (string): the page title (from HTML &lt;title&gt; tag, or URL if none)
          - \c content (string): extracted plain text content
    */
    static list<hash<auto>> crawl(string seed_url, *hash<auto> opts) {
        int max_depth = opts.max_depth ?? DefaultMaxDepth;
        int max_pages = opts.max_pages ?? DefaultMaxPages;
        int concurrency = opts.concurrency ?? DefaultConcurrency;
        int delay_ms = opts.delay_ms ?? 0;
        *code<nothing(int, int)> progress = opts.progress;
        *code<bool(string)> url_filter = opts.url_filter;

        # Phase A options
        bool allow_private_ips = opts.allow_private_ips ?? False;
        *list<string> blocked_hostnames = opts.blocked_hostnames;
        list<string> skip_extensions = opts.skip_extensions ?? DefaultSkipExtensions;
        # Build a set for O(1) extension lookup
        hash<string, bool> skip_ext_set;
        foreach string ext in (skip_extensions) {
            skip_ext_set{ext.lwr()} = True;
        }

        # Phase C options
        string user_agent = opts.user_agent ?? DefaultUserAgent;
        int max_response_bytes = opts.max_response_bytes ?? DefaultMaxResponseBytes;
        bool respect_robots = opts.respect_robots ?? True;

        # Validate seed URL with SsrfFilter (default-deny private IPs).
        # Throws SSRF-BLOCKED if the seed targets a private/internal address.
        SsrfFilter::checkUrl(seed_url, {
            "allow_private": allow_private_ips,
            "blocked_hostnames": blocked_hostnames,
        });

        # Phase C: fetch robots.txt for the seed origin (per RFC 9309 — unreachable
        # robots.txt is treated as fully permissive).
        *RobotsTxt robots;
        if (respect_robots) {
            robots = RobotsTxt::fetch(seed_url, user_agent);
            if (robots) {
                # If the file specifies a Crawl-delay larger than our configured
                # delay, honor it (politeness)
                *int rdelay = robots.getCrawlDelay();
                if (rdelay && rdelay * 1000 > delay_ms) {
                    delay_ms = rdelay * 1000;
                }
            }
        }

        # Determine the URL prefix for same-site filtering
        *string url_prefix = (seed_url =~ x/^(https?:\/\/[^\/]+\/[^?#]*)/)[0];
        if (!url_prefix) {
            url_prefix = seed_url;
        }
        if (url_prefix =~ /\.[a-z]+$/i) {
            url_prefix = dirname(url_prefix) + "/";
        }

        # Shared crawl state — guarded by state_mutex for atomic access from concurrent
        # background fetcher threads. The visited index and queue must always be updated
        # together under the lock to prevent duplicate enqueueing or lost claims.
        Mutex state_mutex();
        hash<string, bool> visited = {};
        list<hash<auto>> queue = ();
        list<hash<auto>> pages = ();

        # Seed the crawl atomically
        string seed_norm = UrlNormalizer::normalize(seed_url);
        visited{seed_norm} = True;
        queue += {"url": seed_norm, "depth": 0};

        HttpClientIo::HttpClientConnectionManager mgr(
            <HttpClientIo::HttpClientConnectionManagerOptions>{
                "connect_timeout": DefaultConnectTimeout,
                "request_timeout": DefaultRequestTimeout,
            });

        # Default request headers — passed per-request because
        # HttpClientConnectionManagerOptions has no default_headers field
        hash<auto> req_headers = {
            "User-Agent": user_agent,
        };

        while (True) {
            # Drain a batch from the queue atomically
            list<hash<auto>> batch;
            {
                state_mutex.lock();
                on_exit state_mutex.unlock();
                if (pages.size() >= max_pages) {
                    break;
                }
                while (queue && batch.size() < concurrency) {
                    batch += shift queue;
                }
            }
            if (!batch) {
                break;
            }

            # Fetch all batch URLs in parallel
            int rate_limited = 0;
            Counter cnt(batch.size());

            foreach hash<auto> item in (batch) {
                # Pass 'item' as a closure parameter to avoid capture-by-reference
                # issues with the foreach iteration variable
                background sub (hash<auto> citem) {
                    on_exit cnt.dec();
                    try {
                        hash<auto> url_parts = parse_url(citem.url);
                        string base_url = sprintf("%s://%s%s",
                            url_parts.protocol ?? "https",
                            url_parts.host,
                            url_parts.port ? sprintf(":%d", url_parts.port) : "");
                        string req_path = url_parts.path ?? "/";
                        hash<auto> resp = mgr.request(base_url, "GET", req_path, req_headers);

                        if (resp.status_code == 429 || resp.status_code == 503) {
                            # Atomic re-queue for retry: re-clear visited so the URL
                            # can be re-queued and re-processed
                            state_mutex.lock();
                            on_exit state_mutex.unlock();
                            ++rate_limited;
                            remove visited{citem.url};
                            queue += {"url": citem.url, "depth": citem.depth};
                            return;
                        }

                        if (resp.status_code != 200
                                || resp.headers."content-type" !~ /text\/html/i) {
                            return;
                        }
                        # Phase C: enforce max response size
                        int body_size = resp.body.typeCode() == NT_BINARY
                            ? resp.body.size() : resp.body.size();
                        if (body_size > max_response_bytes) {
                            return;
                        }
                        *string html = resp.body.typeCode() == NT_BINARY
                            ? resp.body.toString("UTF-8") : resp.body;
                        if (!html) {
                            return;
                        }

                        *string title = HtmlExtractor::extractTitle(html);
                        if (!title) {
                            title = citem.url;
                        }

                        string text = HtmlExtractor::extractText(html);
                        if (text.size() < MinTextLength) {
                            return;
                        }

                        # Extract links into a local list (no lock held during regex work)
                        list<hash<auto>> new_links = ();
                        if (citem.depth < max_depth) {
                            new_links = WebCrawler::extractLinks(html, citem.url, citem.depth,
                                url_prefix);
                        }

                        # Atomically commit the page result and any new link claims
                        state_mutex.lock();
                        on_exit state_mutex.unlock();
                        if (pages.size() >= max_pages) {
                            return;
                        }
                        pages += {
                            "url": citem.url,
                            "title": title,
                            "content": text,
                        };
                        # Atomic check-and-claim for each discovered link.
                        # Filters in order:
                        #   1. dedup against visited
                        #   2. URL extension blacklist (Phase A)
                        #   3. caller-supplied url_filter
                        #   4. robots.txt Disallow (Phase C)
                        #   5. SSRF check (Phase A) — DNS-resolved
                        # Cheap filters first; SSRF is last because it's a DNS lookup.
                        foreach hash<auto> link in (new_links) {
                            if (visited{link.url}) {
                                continue;
                            }
                            if (WebCrawler::hasBlockedExtension(link.url, skip_ext_set)) {
                                continue;
                            }
                            if (url_filter && !url_filter(link.url)) {
                                continue;
                            }
                            if (robots) {
                                hash<auto> link_parts = parse_url(link.url);
                                string link_path = link_parts.path ?? "/";
                                if (!robots.isAllowed(link_path)) {
                                    continue;
                                }
                            }
                            try {
                                SsrfFilter::checkUrl(link.url, {
                                    "allow_private": allow_private_ips,
                                    "blocked_hostnames": blocked_hostnames,
                                });
                            } catch (hash<ExceptionInfo> ex) {
                                # SSRF rejected — skip this link silently
                                continue;
                            }
                            visited{link.url} = True;
                            queue += link;
                        }
                    } catch () {
                        # Request failed — drop this URL (already claimed in visited
                        # so we won't retry it; this matches the previous behavior)
                    }
                }(item);
            }
            cnt.waitForZero();

            # Auto-throttle on rate limiting
            if (rate_limited > 0) {
                if (concurrency > 3) {
                    concurrency = concurrency / 2;
                }
                usleep(2s);
            }

            if (progress) {
                int pcount;
                int qcount;
                {
                    state_mutex.lock();
                    on_exit state_mutex.unlock();
                    pcount = pages.size();
                    qcount = queue.size();
                }
                progress(pcount, qcount);
            }

            if (delay_ms > 0) {
                usleep(delay_ms * 1ms);
            }
        }

        return pages;
    }

    #! Extract links from HTML and resolve them against the page URL
    /** Pure function — does not touch the visited index or queue. Returns a list of
        candidate links that the caller can atomically claim under the state mutex.

        @param html the HTML content to parse for links
        @param page_url the URL of the page containing the links
        @param depth the current crawl depth
        @param url_prefix the URL prefix for same-site filtering
        @return list of \c {"url", "depth"} hashes for links matching the prefix
    */
    private static list<hash<auto>> extractLinks(string html, string page_url, int depth,
            string url_prefix) {
        list<hash<auto>> links = ();

        # Delegate the HTML parsing and link extraction to HtmlExtractor, which
        # uses parse_html() (libxml2's lenient parser) for proper DOM handling.
        # HtmlExtractor::extractLinks already filters rel="nofollow", excludes
        # non-HTTP schemes (mailto:, javascript:, etc.), resolves relative URLs
        # against page_url, and finds <link rel="canonical">.
        hash<LinkInfo> info;
        try {
            info = HtmlExtractor::extractLinks(html, page_url);
        } catch (hash<ExceptionInfo> ex) {
            return links;
        }

        foreach string href in (info.hrefs) {
            string normalized = UrlNormalizer::normalize(href);
            if (normalized =~ /^https?:\/\//i && normalized.find(url_prefix) == 0) {
                links += {"url": normalized, "depth": depth + 1};
            }
        }
        return links;
    }

    #! Returns True if the URL uses a scheme that should never be crawled
    /** @param url the URL or href to check
        @return True for javascript:, mailto:, tel:, sms:, data:, vbscript:, file:,
            chrome:, about:, ftp:, ftps:
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

    #! Returns True if the URL's path ends with a blocked extension
    /** Used as a pre-fetch filter to avoid HTTP round trips on links that are
        clearly not crawlable HTML (PDFs, images, archives, etc.).

        @param url the URL to check
        @param skip_ext_set hash of blocked extensions (lowercase, no dot)
        @return True if the URL's last path segment ends with a blocked extension
    */
    static bool hasBlockedExtension(string url, hash<string, bool> skip_ext_set) {
        # Extract the path portion (strip query/fragment first)
        string path = regex_subst(url, "[?#].*$", "");
        # Last path segment
        int last_slash = path.rfind("/");
        string last = last_slash >= 0 ? path.substr(last_slash + 1) : path;
        # Extension
        int last_dot = last.rfind(".");
        if (last_dot < 0) {
            return False;
        }
        string ext = last.substr(last_dot + 1).lwr();
        return skip_ext_set{ext} ?? False;
    }
}

} # namespace WebContentUtil
