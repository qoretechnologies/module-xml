# Native XSD occurrence parsing

Copyright (C) 2026 Qore Technologies, s.r.o.

The libxml2 selection probe checks occurrence lexical values and zero-count
element validation through both DOM and streaming APIs. AUTO uses a working
installed library when the complete probe passes, otherwise the pinned private
fallback. SYSTEM rejects an installed library that fails. A previously fixed
QName/URI/ENTITY library that lacks the occurrence fixes is tested explicitly.

`QoreXmlLibXml2OccursFix.cmake` applies two corrections to the fallback's
`xmlschemas.c`, after the existing QName, URI and ENTITY corrections:

1. Parse occurrence attributes as XSD nonNegativeInteger values with XML
   whitespace collapse. Accept `+001`, `-000`, and surrounding whitespace on
   `unbounded`; reject two signs, internal spaces, negative nonzero values,
   exponents, fractions and non-XML whitespace. Arithmetic saturates before an
   integer overflow and retains the dependency's existing range diagnostics.
2. A local element with both occurrence values zero contributes no particle,
   as required by XSD 1.0 section 3.3.2. Parse and retain its declaration in the
   schema arena, but return no particle to the parent content model. The old
   local-declaration path returned the zero particle, unlike the reference path;
   the automaton compiler then subtracted one from zero and created a consuming
   transition. Omitting the particle fixes the accepted language at its source.

The patch checks the complete preceding and resulting SHA-256 values before
selecting the build-tree source. The downloaded source and all upstream notices
remain unchanged. Reconfiguration preserves the output timestamp when contents
are identical. Autotools source distributions include the probe, replacement and
patch driver, as well as the preceding ENTITY probe and driver.

This correction retains libxml2's integer-sized native occurrence representation.
It does not claim arbitrary-size native counters. The WSDL construction model
stores exact decimal occurrence values independently. The new native scanner is
linear in attribute length with constant auxiliary storage; it allocates nothing
and performs no I/O. As part of standalone libxml2 C code it has no dependency on
the Qore runtime. Qore's existing schema entry/read boundaries retain interruption
and sandbox checks. Tests cover long lexical attributes, interruption and reuse;
there is no new mid-attribute cancellation callback in libxml2.

Run `qore -b --enable-debug test/xml-particle-counts.qtest`,
`python3 test/wsdl-interop/test_particle_counts.py -v`, and
`python3 test/cmake/test_libxml2_provider.py -v`. The CMake runtime probe is also
an executable target, `qore-xml-namespace-probe`, and is checked under Valgrind.
See [normative and independent evidence](../test/wsdl-interop/particle-counts-evidence.md).
