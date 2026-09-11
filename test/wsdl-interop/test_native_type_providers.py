#!/usr/bin/env python3
"""Captured values pass through receiving providers before independent validation.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import unittest

import test_native_type_values


class NativeTypeProvidersTest(test_native_type_values.NativeTypeValuesTest):
    worker = 'native-type-providers.qr'
    manual_error = 'RUNTIME-TYPE-ERROR'


if __name__ == '__main__':
    unittest.main()
