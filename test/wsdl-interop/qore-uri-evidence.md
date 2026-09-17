# Shared Qore URI resolution

Copyright (C) 2026 Qore Technologies, s.r.o.

This increment consumes Qore commit `53b8b3fff` (installed runtime
`ab4ff7b2737adb619bd19ac7775c98ea420c51b0`). No Qore files are modified.

## Implementation and contract

- WSDL document references use `resolve_url(base, reference, RESOLVE_URL_STRICT)`;
  only `RESOLVE-URL-ERROR` becomes the existing `WSDL-LOCATION-ERROR`.
  Malformed percent escapes now reject, alongside invalid characters and bases.
- Retained XML Base uses `RESOLVE_URL_RELATIVE_BASE`, preserving raw LEIRIs,
  empty delimiters, encoded octets and unresolved parents. An absent/empty inherited
  base leaves the authored reference untouched.
- File URI conversion uses FileLocationHandler 3.0 `getFileUri()` and
  `getPathFromFileUri()`. WSDL retains its literal-path/environment compatibility,
  strict character policy and error category.
- WebContentUtil HTML links and URL dot segments use the shared resolver. The
  crawler retains its separate case, port, trailing-slash and query-order policies.
  Query-only and network-path HTML links now resolve against the correct components.
- Native schema HTTP loading uses `qore_resolve_url()` for URI encoding and
  fragment removal, then uses the response `effective-url` as the dependency base.
  The old redirect replay with `xmlBuildURI()` is removed.
- CMake, Autoconf and requirements documentation require Qore 3.0. WSDL requires
  FileLocationHandler 3.0 explicitly. Durable design and module release notes are updated.

The remaining private WSDL component accessor serves directory extraction,
request-target construction and file compatibility; it does not implement
reference merging or dot-segment removal. libxml2's internal URI/schema fixes
remain in the independently built C library, and the Java oracle remains
independent of Qore. Neither is an alternative module-level resolution path.

## Regression checks

The validation inventory records the exact commands, source hashes and results.
Tests cover the RFC 3986 normal/abnormal vectors, escaped delimiters, empty
queries/fragments, double separators, relative XML Base, raw Unicode/space values,
malformed references followed by valid use, file aliases and saved graphs.
HTML extraction checks anchor, canonical and sitemap links against literal
expected URLs.

The native redirect regression checks all five redirect statuses with relative
Location, an empty query (`Location: ?`), fragments, nested schema references and
invalid integer content. The HTTP peer compares actual request targets. Fixtures
are batched in one worker so Valgrind tests the complete matrix without repeated
interpreter startup. Redirect and URI-encoding tests run under Valgrind with
`qore -b --enable-debug --exec-mode=ast`, leak checking and error exit codes.

The TLS test now supplies its own minimal OpenSSL configuration: the local
OpenSSL executable referenced a missing `/usr/local/ssl/openssl.cnf`. The fixture
no longer depends on a host-specific certificate configuration; verification
and rejection of an untrusted certificate are still tested.

The full documentation build exposed unresolved symbol references. Fixes qualify
symbols, render a removed historical method as code, add missing public class
briefs, and link the deprecated WebDAV client to the successor's module page
without creating a cyclic documentation dependency. They change documentation
only; provider metadata and runtime behavior are unchanged.

Two initial full-coverage test runs hit their 60-second outer deadline during
concurrent compilation. A profiled direct run completed in 56.869 seconds
(50.429 seconds in the Qore worker); the unchanged test then passed in the
complete 16-test coverage suite. No deadline, assertion or expected outcome was
relaxed. The initial broad Valgrind run was stopped in favor of focused batched
native tests; only completed focused results are acceptance evidence.

## Scope

This completes the shared-resolver migration, not all P6 work. WSDL/SoapClient
resource-result plumbing, redirect aliases and offline graph integration still
need to consume the new FileLocationHandler result API. The earlier prototype
is not applied by this increment. Remaining binding/operation work and P7–P9
also remain open. No push or CI image pipeline is triggered.
