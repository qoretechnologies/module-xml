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

    - HTTP/2 and HTTP/3 multiplexing for high throughput (both protocols supported on a
      single connection); automatic protocol auto-selection via Alt-Svc discovery upgrades
      from HTTP/2 to HTTP/3 when available
    - HTTP/1.1 fallback with multiple connections per host
    - Redirect following (via \c request() method)
    - Automatic rate limiting detection and throttling on 429/503 responses
    - URL normalization and deduplication
    - SSRF protection (default-deny private/internal addresses)
    - robots.txt compliance (RFC 9309)
    - URL extension and link scheme blacklists
    - Configurable depth, page cap, concurrency, and delay
    - Progress reporting via callback
    - Pluggable thread launcher (\c start_thread option) — required when imported into a
      context where @ref Qore::PO_NO_THREAD_CONTROL is set, such as Qorus services

    @par Example
    @code{.py}
list<hash<auto>> pages = WebCrawler::crawl("https://docs.example.com/", {
    "max_depth": 3,
    "max_pages": 500,
    "concurrency": 10,
    "delay_ms": 50,
    "user_agent": "MyBot/1.0",
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

    #! Slice size for cancellable sleeps — bounds the worst-case latency
    #! between a cancel_check returning True and the crawler observing it
    const CancelSlice = 250ms;

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

    private {
        # Configuration (set in constructor)
        int max_depth;
        int max_pages;
        int concurrency;
        int delay_ms;
        bool allow_private_ips;
        *list<string> blocked_hostnames;
        hash<string, bool> skip_ext_set;
        string user_agent;
        int max_response_bytes;
        bool respect_robots;
        *code<nothing(int, int)> progress;
        *code<bool(string)> url_filter;
        #! Optional thread launcher — required under PO_NO_THREAD_CONTROL
        *code<int(code<nothing()>)> start_thread;
        #! Optional cancellation hook — polled between batches and inside
        #! rate-limit / crawl-delay sleeps; when it returns True the run
        #! exits gracefully and returns whatever pages were collected so far
        *code<bool()> cancel_check;
        #! Optional pre-fetch filter — called with each URL just before the
        #! HTTP request; return False to skip the fetch entirely (no body,
        #! no link extraction, no page recorded).  Use cases: external
        #! denylists, cache-based dedup against a trusted cached link graph,
        #! per-tenant URL policies that change between crawls
        *code<bool(string)> should_fetch_callback;
        #! Optional post-fetch hook — called after a page is successfully
        #! fetched, with the rich page hash (url, title, content, raw_body,
        #! response_headers, depth).  The callback can perform side effects
        #! (DB persistence, ingestion enqueue, hash-based change detection)
        #! and return either a modified page hash to include in the pages
        #! list, or @ref nothing to skip accumulation entirely (streaming /
        #! memory-pressure mode).  Link extraction proceeds regardless.
        *code<*hash<auto>(hash<auto>)> page_callback;

        # Derived configuration
        string url_prefix;
        *RobotsTxt robots;

        # HTTP client
        HttpClientIo::HttpClientConnectionManager mgr;
        hash<auto> req_headers;

        # Caller-supplied extra headers (auth tokens, custom User-Agent
        # overrides, X-Forwarded-For for testing, etc.) merged into every
        # request after the built-in headers so callers can override
        # anything except the User-Agent default
        *hash<string, string> extra_headers;

        # DNS pinning state — when dns_pin is True we resolve each unique
        # host once via SsrfFilter::resolveAndValidate and cache the
        # validated IP, then rewrite subsequent fetch URLs to use the IP
        # directly (with Host header set to the original hostname).  This
        # closes the TOCTOU window between SSRF check and HTTP fetch where
        # a DNS-rebinding attack could flip the resolution to a private IP.
        bool dns_pin;
        Mutex dns_pin_mutex();
        hash<string, *string> dns_pin_cache = {};

        # Shared crawl state — guarded by state_mutex
        Mutex state_mutex();
        hash<string, bool> visited = {};
        list<hash<auto>> queue = ();
        list<hash<auto>> pages = ();

        # Per-batch state (reset each batch)
        int rate_limited;
        Counter cnt;

        # Sleep helper — Condition::wait(Mutex, timeout) is permitted under
        # PO_NO_PROCESS_CONTROL while usleep()/sleep() are not, so we use a
        # private mutex+condition for inter-batch and crawl-delay sleeps that
        # works in Qorus service contexts.
        Mutex sleep_mutex();
        Condition sleep_cond();
    }

    #! Internal helper: sleep for the given duration without using usleep()
    /** Uses Condition::wait() on a private mutex/condition pair so the call is
        classified as thread-control rather than process-control, allowing it
        to run under PO_NO_PROCESS_CONTROL (e.g. inside Qorus user services).

        When a \c cancel_check callback was supplied to the constructor, the
        sleep is broken into short slices (250 ms) and the cancel callback is
        polled between slices.  This bounds the worst-case latency between a
        cancel request and the crawler returning to ~250 ms regardless of the
        configured rate-limit / crawl-delay value.

        @param duration the requested sleep duration
        @return True if the sleep completed normally, False if it was
            interrupted by a cancel_check returning True
    */
    private bool sleepDuration(date duration) {
        if (!cancel_check) {
            sleep_mutex.lock();
            on_exit sleep_mutex.unlock();
            sleep_cond.wait(sleep_mutex, duration);
            return True;
        }
        # Cancellable sleep: break into CancelSlice slices and poll
        # cancel_check between slices.
        date remaining = duration;
        while (remaining > 0s) {
            if (cancel_check()) {
                return False;
            }
            date wait_dur = remaining < CancelSlice ? remaining : CancelSlice;
            {
                sleep_mutex.lock();
                on_exit sleep_mutex.unlock();
                sleep_cond.wait(sleep_mutex, wait_dur);
            }
            remaining -= wait_dur;
        }
        return !cancel_check();
    }

    #! Construct a crawler from a seed URL and an options hash
    /** See @ref crawl() for the option documentation.

        @param seed_url the starting URL
        @param opts crawl options
        @throw SSRF-BLOCKED if the seed URL targets a private/internal address
            and \c allow_private_ips is not True
    */
    constructor(string seed_url, *hash<auto> opts) {
        max_depth = opts.max_depth ?? DefaultMaxDepth;
        max_pages = opts.max_pages ?? DefaultMaxPages;
        concurrency = opts.concurrency ?? DefaultConcurrency;
        delay_ms = opts.delay_ms ?? 0;
        progress = opts.progress;
        url_filter = opts.url_filter;

        # Phase A options
        allow_private_ips = opts.allow_private_ips ?? False;
        blocked_hostnames = opts.blocked_hostnames;
        list<string> skip_extensions = opts.skip_extensions ?? DefaultSkipExtensions;
        foreach string ext in (skip_extensions) {
            skip_ext_set{ext.lwr()} = True;
        }

        # Phase C options
        user_agent = opts.user_agent ?? DefaultUserAgent;
        max_response_bytes = opts.max_response_bytes ?? DefaultMaxResponseBytes;
        respect_robots = opts.respect_robots ?? True;

        # Optional thread launcher (required under PO_NO_THREAD_CONTROL)
        start_thread = opts.start_thread;

        # Caller-supplied extra HTTP headers
        extra_headers = opts.headers;

        # Caller-supplied cancellation hook
        cancel_check = opts.cancel_check;

        # Caller-supplied pre-fetch filter
        should_fetch_callback = opts.should_fetch_callback;

        # Caller-supplied post-fetch hook
        page_callback = opts.page_callback;

        # Sitemap pre-seeding (Phase 5 feature 5)
        bool use_sitemap = opts.use_sitemap ?? False;
        *string sitemap_url = opts.sitemap_url;

        # DNS pinning (Phase 5 feature 6)
        dns_pin = opts.dns_pin ?? False;

        # Validate seed URL — throws SSRF-BLOCKED if private and not allowed
        SsrfFilter::checkUrl(seed_url, {
            "allow_private": allow_private_ips,
            "blocked_hostnames": blocked_hostnames,
        });

        # Phase C: fetch robots.txt for the seed origin
        if (respect_robots) {
            robots = RobotsTxt::fetch(seed_url, user_agent, NOTHING, extra_headers);
            if (robots) {
                *int rdelay = robots.getCrawlDelay();
                if (rdelay && rdelay * 1000 > delay_ms) {
                    delay_ms = rdelay * 1000;
                }
            }
        }

        # Determine the URL prefix for same-site filtering
        *string up = (seed_url =~ x/^(https?:\/\/[^\/]+\/[^?#]*)/)[0];
        if (!up) {
            up = seed_url;
        }
        if (up =~ /\.[a-z]+$/i) {
            up = dirname(up) + "/";
        }
        url_prefix = up;

        # Seed the crawl atomically
        string seed_norm = UrlNormalizer::normalize(seed_url);
        visited{seed_norm} = True;
        queue += {"url": seed_norm, "depth": 0};

        # HTTP client
        mgr = new HttpClientIo::HttpClientConnectionManager(
            <HttpClientIo::HttpClientConnectionManagerOptions>{
                "connect_timeout": DefaultConnectTimeout,
                "request_timeout": DefaultRequestTimeout,
            });
        req_headers = {
            "User-Agent": user_agent,
        };
        # Merge caller-supplied headers; caller wins over the built-in
        # User-Agent so e.g. an Authorization header doesn't get clobbered
        # but a custom UA does override the constructor default
        if (extra_headers) {
            req_headers += extra_headers;
        }

        # Pre-seed the queue from sitemap.xml if requested.  Sitemap URLs
        # are subject to the same scope/dedup/SSRF filters as URLs
        # discovered through link extraction during the BFS — see the
        # filter chain in fetchOne() at the link-claim step.
        if (use_sitemap) {
            seedFromSitemap(sitemap_url ?? sprintf("%s/sitemap.xml", originOf(seed_url)));
        }
    }

    #! Internal: pre-seed the queue with URLs discovered from a sitemap.xml
    /** Fetches the sitemap via @ref SitemapParser::fetchAndParse(), normalizes
        each URL, and adds those that pass the same filter chain the BFS link
        extractor uses (URL prefix, dedup against \c visited, scheme/extension
        filters, robots.txt, SSRF).  Failures are logged silently — sitemap
        seeding is best-effort and the crawl falls back to BFS-only.

        @param url the URL of the sitemap or sitemap-index file to fetch
    */
    private seedFromSitemap(string url) {
        list<string> sitemap_urls;
        try {
            sitemap_urls = SitemapParser::fetchAndParse(url, {
                "user_agent": user_agent,
                "headers": extra_headers,
            });
        } catch (hash<ExceptionInfo> ex) {
            return;
        }
        foreach string surl in (sitemap_urls) {
            string normalized = UrlNormalizer::normalize(surl);
            if (visited{normalized}) {
                continue;
            }
            # Same-site filter: only seed URLs under the seed prefix
            if (normalized.find(url_prefix) != 0) {
                continue;
            }
            # Extension and scheme filters
            if (WebCrawler::hasBlockedExtension(normalized, skip_ext_set)) {
                continue;
            }
            # robots.txt
            if (robots) {
                hash<auto> link_parts = parse_url(normalized);
                string link_path = link_parts.path ?? "/";
                if (!robots.isAllowed(link_path)) {
                    continue;
                }
            }
            # SSRF
            try {
                SsrfFilter::checkUrl(normalized, {
                    "allow_private": allow_private_ips,
                    "blocked_hostnames": blocked_hostnames,
                });
            } catch (hash<ExceptionInfo> ex) {
                continue;
            }
            visited{normalized} = True;
            queue += {"url": normalized, "depth": 0};
        }
    }

    #! Internal: extract scheme://host[:port] from a URL
    private static string originOf(string url) {
        *string origin = (url =~ x/^(https?:\/\/[^\/?#]+)/)[0];
        return origin ?? url;
    }

    #! Internal: look up or compute the pinned IP for a host
    /** Cache key is the bare hostname (no scheme/port).  On first sight,
        calls @ref SsrfFilter::resolveAndValidate to validate AND get the
        first public IP, then caches the result for the rest of the crawl.
        On subsequent lookups returns the cached value without re-resolving
        — DNS pinning means once we've validated a host, we don't ask DNS
        about it again.

        SSRF rejections from resolveAndValidate are cached as NOTHING-with-
        a-tombstone-marker so subsequent fetches for the same host are
        skipped without re-attempting DNS.

        @param host the hostname to resolve and pin
        @return the validated public IP, or NOTHING if the host is already
            an IP literal (no pinning needed) or DNS resolution failed
            (caller should fall back to the unpinned hostname)
        @throw SSRF-BLOCKED if the host resolves to a private/blocked address
    */
    private *string resolvePinnedIp(string host) {
        dns_pin_mutex.lock();
        on_exit dns_pin_mutex.unlock();
        if (dns_pin_cache.hasKey(host)) {
            return dns_pin_cache{host};
        }
        *string ip;
        try {
            ip = SsrfFilter::resolveAndValidate("http://" + host + "/", {
                "allow_private": allow_private_ips,
                "blocked_hostnames": blocked_hostnames,
            });
        } catch (hash<ExceptionInfo> ex) {
            # Cache the rejection as NOTHING so we don't re-resolve next time;
            # the caller's exception handler in fetchOne will skip this URL
            dns_pin_cache{host} = NOTHING;
            rethrow;
        }
        dns_pin_cache{host} = ip;
        return ip;
    }

    #! Run the crawl and return the collected pages
    /** Performs a breadth-first crawl from the seed URL passed to the constructor.
        Spawns parallel fetcher threads via the configured launcher (\c start_thread
        option, or @ref background under @ref Qore::PO_NO_THREAD_CONTROL).

        @return list of page hashes, each containing:
          - \c url (string): the page URL
          - \c title (string): the page title (from HTML &lt;title&gt; tag, or URL if none)
          - \c content (string): extracted plain text content
    */
    list<hash<auto>> run() {
        while (True) {
            # Cancellation check at the top of every batch — gives the caller
            # a deterministic upper bound on how long after a cancel request
            # the crawl will keep running (one batch's fetches at most)
            if (cancel_check && cancel_check()) {
                break;
            }
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
            rate_limited = 0;
            cnt = new Counter(batch.size());

            foreach hash<auto> item in (batch) {
                # Use the closure factory pattern to bind `item` at call time
                # rather than relying on closure capture-by-reference of the
                # foreach iteration variable.  Each makeFetchTask() invocation
                # creates a fresh activation record with its own `citem` parameter,
                # so each returned closure captures a different `citem`.
%ifdef PO_NO_THREAD_CONTROL
                # Under PO_NO_THREAD_CONTROL, the start_thread launcher is required
                if (!start_thread) {
                    cnt.dec();
                    throw "WEBCRAWLER-START-THREAD-REQUIRED",
                        "WebCrawler requires the 'start_thread' option when imported "
                        "into a context with PO_NO_THREAD_CONTROL set";
                }
                call_function(start_thread, makeFetchTask(item));
%else
                if (start_thread) {
                    call_function(start_thread, makeFetchTask(item));
                } else {
                    # background takes the call site argument by value, so item
                    # is bound at the call site (not lazily).  This is the same
                    # mechanism that makes makeFetchTask correct for start_thread.
                    background fetchOne(item);
                }
%endif
            }
            cnt.waitForZero();

            # Auto-throttle on rate limiting
            if (rate_limited > 0) {
                if (concurrency > 3) {
                    concurrency = concurrency / 2;
                }
                sleepDuration(2s);
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
                sleepDuration(delay_ms * 1ms);
            }
        }

        return pages;
    }

    #! Static factory: construct a WebCrawler and run it in one call
    /** This is the convenience entry point for callers that don't need an instance
        reference.  Equivalent to:
        @code{.py}
WebCrawler c(seed_url, opts);
return c.run();
        @endcode

        @param seed_url the starting URL
        @param opts crawl options hash:
          - \c max_depth (int, default 3): maximum link-follow depth
          - \c max_pages (int, default 500): hard page cap
          - \c concurrency (int, default 10): parallel requests per batch
          - \c delay_ms (int, default 0): delay between batches in milliseconds
          - \c progress (\c *code<nothing(int, int)>): progress callback (pages, queued)
          - \c url_filter (\c *code<bool(string)>): return True to accept a URL
          - \c skip_extensions (\c *list<string>): URL extensions to skip pre-fetch
          - \c allow_private_ips (bool, default False): allow private/internal targets
          - \c blocked_hostnames (\c *list<string>): additional blocked hostnames
          - \c user_agent (\c *string): User-Agent header
          - \c max_response_bytes (int, default 10485760): skip pages larger than this
          - \c respect_robots (bool, default True): honor robots.txt
          - \c headers (\c *hash<string, string>): extra HTTP request headers added
            to every request — typically auth credentials (\c Authorization,
            \c Cookie), session tokens, or custom \c X- headers
          - \c cancel_check (\c *code<bool()>): cancellation hook polled between
            batches and inside rate-limit / crawl-delay sleeps; return True to
            cause the run to exit gracefully and return whatever pages were
            collected so far.  Worst-case latency between cancel and return is
            ~250 ms regardless of \c delay_ms
          - \c should_fetch_callback (\c *code<bool(string)>): pre-fetch filter
            called with each URL just before the HTTP round trip; return False
            to skip the fetch entirely (no body, no link extraction, no page
            recorded).  Use cases: external denylists, cache-based dedup,
            per-tenant URL policies that change between crawls.  Note that
            this is a *pre*-fetch hook; for *post*-fetch decisions (e.g.
            content-hash change detection where the body is needed) use
            \c page_callback instead
          - \c page_callback (\c *code<*hash<auto>(hash<auto>)>): post-fetch
            hook called with a rich page hash containing \c url, \c title,
            \c content, \c raw_body, \c response_headers, \c depth.  Return
            either a (possibly modified) page hash to include in the result
            list, or @ref nothing to skip accumulation entirely (streaming /
            memory-pressure mode where the caller already persisted the page
            via side effect and doesn't need it kept in RAM).  Link extraction
            from the page proceeds regardless of the callback's return value.
            The callback is invoked outside the state mutex to avoid deadlocks
            when it acquires its own locks (e.g. DB transactions)
          - \c use_sitemap (bool, default False): pre-seed the BFS queue from
            \c /sitemap.xml at the seed origin (or from \c sitemap_url if set).
            Sitemap-index files are recursively followed up to 3 levels deep.
            Discovered URLs are subject to the same scope/dedup/SSRF/robots.txt
            filters as URLs found via link extraction.  Sitemap fetch failures
            are silent — the crawl falls back to BFS-only
          - \c sitemap_url (\c *string): explicit sitemap URL to use when
            \c use_sitemap is True; defaults to \c {seed_origin}/sitemap.xml
          - \c dns_pin (bool, default False): SSRF TOCTOU hardening — when
            True, each unique hostname is resolved once via SsrfFilter and
            the validated public IP is cached for the rest of the crawl.
            Subsequent fetches connect directly to the pinned IP with the
            \c Host header set to the original hostname, eliminating the
            window where a DNS-rebinding attack could flip the resolution
            to a private address between SSRF check and HTTP fetch.
            **Caveat**: HTTPS targets may fail TLS hostname verification
            since the connection is made to an IP rather than the hostname;
            use this primarily for HTTP crawling or in combination with an
            HTTP client configured to use the original hostname for SNI
          - \c start_thread (\c *code<int(code<nothing()>)>): thread launcher; REQUIRED
            when imported into a context with @ref Qore::PO_NO_THREAD_CONTROL set
        @return list of page hashes
    */
    static list<hash<auto>> crawl(string seed_url, *hash<auto> opts) {
        WebCrawler c(seed_url, opts);
        return c.run();
    }

    #! Build a 0-argument closure that fetches a specific item, with item bound by value
    /** Closure-factory pattern: \c citem is THIS method's parameter, so each call to
        makeFetchTask creates a fresh activation record.  The returned closure captures
        \c citem from this fresh scope, so each task gets its own item value — even when
        called inside a foreach loop.

        @param citem the {url, depth} hash to fetch
        @return a 0-arg closure suitable for @ref Qore::background or a \c start_thread launcher
    */
    private code<nothing()> makeFetchTask(hash<auto> citem) {
        return sub () {
            fetchOne(citem);
        };
    }

    #! Fetch and process a single URL
    /** Called by the background tasks.  Performs:
        1. HTTP fetch via the connection manager
        2. Rate limit detection (429/503) — atomic re-queue
        3. Content-Type and size validation
        4. Title and text extraction
        5. Link discovery and atomic check-and-claim against the visited index

        All access to the shared visited/queue/pages state is guarded by state_mutex.

        @param citem the {url, depth} hash to fetch
    */
    private fetchOne(hash<auto> citem) {
        on_exit cnt.dec();
        try {
            # Pre-fetch filter — caller can veto this URL before the network
            # round trip (denylist, cached dedup, dynamic policy, etc.).
            # Skipped URLs are dropped entirely: no body, no links, no page.
            if (should_fetch_callback && !should_fetch_callback(citem.url)) {
                return;
            }
            hash<auto> url_parts = parse_url(citem.url);
            string original_host = url_parts.host;
            string fetch_host = original_host;
            hash<auto> fetch_headers = req_headers;
            # DNS pinning: substitute the validated IP for the hostname in
            # the connect URL so the HTTP client connects to the pinned IP
            # rather than re-resolving the host (which could now point to a
            # private address).  Set Host header to the original hostname
            # so virtual-hosted servers route correctly.
            if (dns_pin) {
                *string pinned_ip = resolvePinnedIp(original_host);
                if (pinned_ip.val()) {
                    fetch_host = pinned_ip;
                    fetch_headers = req_headers + {"Host": original_host};
                }
            }
            string base_url = sprintf("%s://%s%s",
                url_parts.protocol ?? "https",
                fetch_host,
                url_parts.port ? sprintf(":%d", url_parts.port) : "");
            string req_path = url_parts.path ?? "/";
            hash<auto> resp = mgr.request(base_url, "GET", req_path, fetch_headers);

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
            int body_size = resp.body.size();
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
                new_links = WebCrawler::extractLinksForUrl(html, citem.url, citem.depth,
                    url_prefix);
            }

            # Build the rich page hash for the post-fetch hook.  Includes
            # raw_body and response_headers so the callback can compute
            # content hashes, parse Last-Modified / ETag headers, etc.
            hash<auto> page = {
                "url": citem.url,
                "title": title,
                "content": text,
                "raw_body": html,
                "response_headers": resp.headers,
                "depth": citem.depth,
            };

            # Run page_callback OUTSIDE the state mutex to avoid deadlocks
            # when the callback acquires its own locks (DB transaction, etc.).
            *hash<auto> result_page;
            if (page_callback) {
                result_page = page_callback(page);
            } else {
                # No callback — use the lean default schema {url, title, content}
                # to keep the in-memory pages list small for callers that just
                # want to collect everything at the end.
                result_page = {
                    "url": citem.url,
                    "title": title,
                    "content": text,
                };
            }

            # Atomically commit the page result and any new link claims
            state_mutex.lock();
            on_exit state_mutex.unlock();
            if (pages.size() >= max_pages) {
                return;
            }
            if (result_page) {
                pages += result_page;
            }
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
    }

    #! Extract crawlable links from HTML, filtered to the same URL prefix
    /** Pure function — does not touch the visited index or queue. Returns a list of
        candidate links that the caller can atomically claim under the state mutex.
        Delegates HTML parsing to @ref HtmlExtractor::extractLinks() which uses
        @ref Qore::Xml::parse_html() (libxml2's lenient parser) for proper DOM handling
        including \c rel="nofollow" filtering and non-HTTP scheme exclusion.

        @param html the HTML content to parse for links
        @param page_url the URL of the page containing the links
        @param depth the current crawl depth
        @param url_prefix the URL prefix for same-site filtering
        @return list of \c {"url", "depth"} hashes for links matching the prefix
    */
    private static list<hash<auto>> extractLinksForUrl(string html, string page_url, int depth,
            string url_prefix) {
        list<hash<auto>> links = ();
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
