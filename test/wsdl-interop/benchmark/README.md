# WSDL/SOAP performance benchmark (P9b)

Copyright (C) 2026 Qore Technologies, s.r.o.

A deterministic benchmark for the WSDL, SOAP and XML Schema processing in `qlib/WSDL.qm`. It tracks performance
with pinned workloads and a recorded reference, not with test timeouts: timeouts in the test gates are hang
guards with measured headroom, never performance assertions (see `PLAN.md`, P9).

## Workloads

Both workloads are pinned: `reference.json` records their SHA-256 digests, and the benchmark refuses changed input.

- **`list-values`** (`workloads/list-values.tar.xz`): the 384-row manifest captured from `test_list_values.py`'s
  sized-facet worker during the 2026-09-21 performance triage (float and double facets; atomic, record and
  repeated values; element and message providers; SOAP 1.1 and 1.2), with its 193 generated WSDL documents.
  Its phases are those of the worker:
  - `construction`: `WebService` construction;
  - `copy`: a `Serializable` copy of the service;
  - `provider`: data provider type construction and copy;
  - `conversion`: `acceptsValue()`;
  - `serialization`: request and response serialization;
  - `sample`: example message generation.
- **`binding-styles`** (`workloads/binding-styles.wsdl`): one order message, with 50 line items, for each SOAP
  binding style (document/literal, RPC/literal and RPC/encoded, each for SOAP 1.1 and 1.2), run 20 times.
  Its phases are:
  - `construction` and `copy`;
  - `request` (client serialization);
  - `envelope` (SOAP node processing);
  - `request-decode` (server parsing and decoding);
  - `response` and `response-decode`.

`bench.qr` runs a workload once. It prints the accumulated time of each phase in nanoseconds, and SHA-256 digests
of every output (per list-values item and per binding style), so outputs can be compared byte for byte.

## Running

```
python3 test/wsdl-interop/benchmark/benchmark.py            # compare with the reference
python3 test/wsdl-interop/benchmark/benchmark.py --record   # record a new reference
```

The benchmark requires the optimized `build` directory (`CMAKE_BUILD_TYPE=Release`). It runs each workload five
times (`--repetitions`) and compares the median of each phase with the reference:
- **A slower phase** beyond the tolerance (25% by default, stored in the reference; `--tolerance`) is reported as
  a regression finding (exit status 1).
- **Output** that differs from the reference digests is a failure (exit status 2): a performance change must not
  change results. An intended output change needs a new reference.

Timing depends on the machine. `reference.json` records the environment it was measured in: CPU, Qore version,
libqore digest, module-xml commit and build type. Compare only on the same machine class, or record a new
reference first. Record a reference only from a clean working tree, and state in the commit why it changed.

`test_benchmark.py` is the suite gate. It makes no timing assertions. It checks:
- the pinned workload digests and manifest;
- that the current code reproduces the reference outputs for every binding style, and for one list-values item for
  each value model, SOAP version and provider kind;
- the comparison rules;
- that the benchmark requires a Release build.
