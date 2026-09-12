# P5-16e native anyType particles

Copyright (C) 2026 Qore Technologies, s.r.o.

This native prerequisite fixes a memory error in module-xml's private libxml2
corrections. Earlier attribution/range changes extended `xmlSchemaParticle` only
in `xmlschemas.c`; builtin particles were still allocated with the smaller
definition in `xmlschemastypes.c`. An empty extension of `xs:anyType` reached
`countSource` past the builtin allocation. Valgrind identified that first read
and its `xmlSchemaAddParticle` allocation; GDB identified the corresponding
attribution traversal. The original reproducer and reports remain under
`/tmp/wsdl-anytype-particle-layout/`. This issue requires no Qore change.

Both translation units now use one header. Builtin occurrence metadata is
initialized once and never rewritten by per-schema attribution. Allocation tests
compare both entire builtin particles before and after each failed and successful
traversal. Their copies preserve padding bytes as well as named members.

Independent tests also found that native type fixup collapsed a reference to an
empty group into absent effective content. That reference still supplies a
particle under XSD 1.0's component mapping. Fixup now keeps this distinction:
an explicitly mixed extension is valid; an element-only extension of the mixed
base is rejected. The original disagreement remains recorded in
`/tmp/wsdl-p5-16e-anytype/anytype-oracle.json` and `anytype-matrix.log`; final
tests preserve that negative case and add the valid mixed counterpart.

Requirements and implementation are described in
[the durable design](../../design/native-anytype-particles.md), with direct links
to the XSD 1.0 component mapping, derivation constraint and builtin ur-type.
No upstream fixture, adjudication or validator expectation is weakened.

## Reproduce

All final artifacts are under `/tmp/wsdl-p5-16e-anytype/`. Tests use the local
Debug module and the frozen, byte-identical deployed Qore runtime from
`/tmp/wsdl-p5-16d-values/confirmed/runtime/`; WSDL source is unchanged.

```sh
export LD_LIBRARY_PATH=/tmp/wsdl-p5-16d-values/confirmed/runtime
export QORE_MODULE_DIR=/home/david/src/qore/git/module-xml/build-debug:/home/david/src/qore/git/module-xml/qlib
export PATH=/tmp/wsdl-p5-16d-values/accepted/bin:$PATH
qore -b --enable-debug test/xml-anytype-particles.qtest
python3 test/wsdl-interop/test_anytype_particles.py -v
python3 test/cmake/test_libxml2_provider.py -v
python3 /tmp/wsdl-p5-16e-anytype/gate.py
python3 /tmp/wsdl-p5-16e-anytype/run-corpus-gate.py
python3 /tmp/wsdl-p5-16e-anytype/run-supplement.py
```

The standalone native allocation executable is `attribution-schema-allocation`
in `/tmp/qore-xml-libxml2-test-31x1b6th/bundled/`. It and `probe` are run under
Valgrind with full leak checking and `--error-exitcode=99`. The new Qore suite
uses the same options, `qore -b --enable-debug` and `QORE_PCRE2_NO_JIT=1`.
PCRE2 JIT remains enabled for normal tests.

The final inventory records regression counts, all three execution modes,
independent comparison, provider selection, allocation faults, source hashes,
Valgrind, the executed shipment example and warning-free documentation. Both
complete corpus report objects are identical to P5-16d: 144 selected WSDLs and
1,388 directions pass; eight valid-input directions and 24 broader failures
remain visible. Python/coverage CI enforcement remains assigned to P9; no push
or remote pipeline is part of this local increment.

See [validation inventory](P5-16e-validation.json) and
[all 62 audit checks](audits/P5-16e-native-anytype.md). Next is WSDL's missing
inherited anyType wildcard, then the remaining fixed/default, identity and P5-P9
acceptance work. Native acceptance alone does not close those requirements.
