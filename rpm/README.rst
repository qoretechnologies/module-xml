RPM packaging
=============

Copyright 2026 Qore Technologies, s.r.o.

The recipe packages the native XML module, seventeen compiled and source Qore
modules, metadata, schemas, provider translations, soaputil and webdav-server.
A separate documentation package contains native and user API references.
The private libxml2 2.15.4 and fast_float 8.3.0 implementations retain their
licenses and existing fixes. No system XML library is replaced. Updating a
system XML package does not update this private implementation; security fixes
require a module rebuild.

Source bundles use the pinned RPM vendor manifest, with libxml2 test/result
fixtures excluded as in the Debian source package. The main archive must also
exclude these paths, matching debian/copyright::

    test/wsdl-interop/oracle/*.jar
    test/wsdl-interop/axis-peer/jars/*.jar
    test/wsdl-interop/cxf-peer/jars/*.jar
    test/enterprise.wsdl
    test/partner.wsdl
    test/wsdl-interop/normative/rfc2392.txt

Pass each path as --exclude to qore-packaging/tools/packaging.py prepare,
along with --vendor-manifest rpm/vendor-sources.json --cache CACHE. Verify the
recorded exclusions and source hashes before uploading. Credentials and external
Java peer libraries are never included in package qualification.

Builds use the installed Qore SDK, offline pinned parser sources, strict public
documentation, four native probes, real ELF metadata tests and every Qore test
suite. The Process module and Litmus are test-only dependencies. Litmus compliance
is mandatory and runs against a private local WebDAV server; Salesforce account
and separately provisioned Java interoperability checks remain explicit external
gates. Complete provider translations and WebDAV CLI startup/shutdown are tested.

For installed runtime checks, install the module, qore-process-module, litmus and
Python 3 in an image without the SDK or compiler. Run unprivileged with networking
disabled (loopback remains available)::

    python3 -B -W error rpm/run-tests.py --installed

The runner copies only tests and documentation examples outside the source tree.
It checks that all seventeen compiled modules exist, verifies loaded paths and
accepts source fallback only for RPM-owned source files with the loader's explicit
optional-module diagnostic. Diagnostics remain visible. To qualify the installed
SDK as well, run debian/tests/compiler with AUTOPKGTEST_TMP set to an empty
writable directory; it compiles and executes a named-argument XML round trip.
