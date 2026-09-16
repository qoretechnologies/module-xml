# Private IEEE decimal parser

Copyright (C) 2026 Qore Technologies, s.r.o.

`fast_float.h` is the unmodified single-header asset from fast_float **v8.3.0**,
commit `b0ab987b3dfdde13fa1915f65ef2a5c068d9208c`:

- Header: https://github.com/fastfloat/fast_float/releases/download/v8.3.0/fast_float.h
- License: https://github.com/fastfloat/fast_float/blob/v8.3.0/LICENSE-MIT
- Header SHA-256: `f23d93a4d1adf052e7b50e2a55ac54feeef91e188b71d35ae3038597e2659b90`
- License SHA-256: `e562f3f974ced7e69dd1db77b820b36bcf8f30377f1aa105723fba449c53c4e6`

This copy is used under the MIT license, preserved in the header and
`LICENSE-MIT`, and included in the installed `libxml2-NOTICES.txt`. Upstream
copyright statements remain unchanged.

Only the private libxml2 IEEE conversion unit includes this header. It supplies
allocation-free, locale-independent binary32/binary64 decimal parsing with
nearest-even rounding on C++ libraries without floating-point `std::from_chars`.
The existing floating-point environment guard and XSD lexical/range checks
surround the call. Formatting uses the standard library's `std::to_chars`.

Updates require replacing the header and license with verified upstream assets,
updating these checksums and the provenance regression, and running the complete
provider suite, independent IEEE oracle, and allocation/Valgrind checks.
