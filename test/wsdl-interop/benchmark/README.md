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

Other work on the machine distorts the timings, so `--record` refuses a busy machine: one whose load, the higher of
its 1- and 5-minute load averages, exceeds a quarter of its CPUs. It checks before the run and again after each
workload, since the load can rise after a run starts on a quiet machine; a workload runs for minutes, and the
5-minute average still shows other work that the 1-minute average no longer does when it finishes. Each workload's
load is stored in the reference. `--force` records
anyway.

### Comparing another WSDL source

The driver loads `qlib/WSDL.qm` beside it by an explicit path, so `QORE_MODULE_DIR` cannot select another version
of WSDL. To time another version with the same Qore and modules, pass the directory of its `WSDL.qm`:

```
git show 0ee292d:qlib/WSDL.qm > /tmp/wsdl-before/WSDL.qm
python3 test/wsdl-interop/benchmark/benchmark.py --wsdl-dir /tmp/wsdl-before
```

The benchmark then runs a temporary copy of the driver that loads that file, and fails unless the file the driver
actually loaded (`get_module_hash()`) is the requested one. The other modules still come from the checkout. Every
result records the loaded file (`wsdl_module`) and its SHA-256 (`wsdl_module_sha256`). `--wsdl-dir` cannot be
combined with `--record`: a reference always measures the checkout's own source.

`test_benchmark.py` is the suite gate. It makes no timing assertions. It checks:
- the pinned workload digests and manifest;
- that the current code reproduces the reference outputs for every binding style, and for one list-values item for
  each value model, SOAP version and provider kind;
- the comparison rules;
- that a comparison loads the requested WSDL source, although the driver has a sibling `qlib`, and reports it;
- that the benchmark requires a Release build.
