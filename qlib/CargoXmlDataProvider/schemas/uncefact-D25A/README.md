# UN/CEFACT D25A XML Schemas

This directory contains the UN/CEFACT D25A XML schema package, bundled with the
CargoXmlDataProvider module so the data provider has a working set of message
definitions out of the box.

## Source

UN/CEFACT (United Nations Centre for Trade Facilitation and Electronic Business),
release D25A, published by UNECE.

## License

UN/CEFACT permits free redistribution under the standard UN/CEFACT IPR terms
included verbatim at the top of every XSD file in this tree:

> Copyright (C) UN/CEFACT. All Rights Reserved.
>
> This document and translations of it may be copied and furnished to others,
> and derivative works that comment on or otherwise explain it or assist in
> its implementation may be prepared, copied, published and distributed, in
> whole or in part, without restriction of any kind, provided that the above
> copyright notice and this paragraph are included on all such copies and
> derivative works. However, this document itself may not be modified in any
> way, such as by removing the copyright notice or references to UN/CEFACT,
> except as needed for the purpose of developing UN/CEFACT specifications, in
> which case the procedures for copyrights defined in the UN/CEFACT
> Intellectual Property Rights document must be followed, or as required to
> translate it into languages other than English.

## Layout

- `data/standard/` — message-level XSDs (Cross-Industry Despatch Advice,
  Invoice, Order, Remittance Advice, Supply Instruction, etc.) and the data
  type modules they import (Unqualified/Qualified Data Types, Reusable
  Aggregate Business Information Entity, Core Component Type)
- `codelist/standard/` — codelist XSDs (currencies, transport modes, package
  codes, etc.) imported transitively via `xsd:import`
- `identifierlist/standard/` — identifier list XSDs (country codes, freight
  cost codes, etc.) imported transitively

## Notes for IATA Cargo-XML users

This is the UN/CEFACT message family, which is not the same as the IATA
Cargo-XML toolkit (FWB / FHL / FFM / XFFM / XFWB / XFHL / FSU / etc.). If your
trading partners use IATA Cargo-XML, override the `schema_dir` constructor
option of `CargoXmlDataProvider` to point at your IATA-licensed XSD package
instead of this bundled directory; the provider will discover and validate
those messages identically.
