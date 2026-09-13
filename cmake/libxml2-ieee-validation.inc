/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XML lexical grammar is independent of whether a computed value is requested.
 * Decimal conversion rounds directly to the selected IEEE precision.
 */
        case XML_SCHEMAS_FLOAT:
        case XML_SCHEMAS_DOUBLE: {
            const xmlChar *cur = value, *first, *last;
            size_t before = 0, digits = 0, nonzero = (size_t)-1, exponent = 0;
            int negative = 0, exponentNegative = 0, special = 0, underflow;
            double wide = 0.0;
            float narrow = 0.0f;
            if (normOnTheFly) {
                while (IS_WSP_BLANK_CH(*cur)) {
                    ++cur;
                }
            }
            first = cur;
            if (cur[0] == 'N' && cur[1] == 'a' && cur[2] == 'N') {
                cur += 3;
                special = 1;
                wide = xmlSchemaNAN;
            } else {
                if (*cur == '-') {
                    negative = 1;
                    ++cur;
                }
                if (cur[0] == 'I' && cur[1] == 'N' && cur[2] == 'F') {
                    cur += 3;
                    special = 1;
                    wide = negative ? xmlSchemaNINF : xmlSchemaPINF;
                } else {
                    if (!negative && *cur == '+') {
                        first = ++cur;
                    }
                    while (*cur >= '0' && *cur <= '9') {
                        if (*cur != '0' && nonzero == (size_t)-1) {
                            nonzero = digits;
                        }
                        ++digits;
                        ++cur;
                    }
                    before = digits;
                    if (*cur == '.') {
                        ++cur;
                        while (*cur >= '0' && *cur <= '9') {
                            if (*cur != '0' && nonzero == (size_t)-1) {
                                nonzero = digits;
                            }
                            ++digits;
                            ++cur;
                        }
                    }
                    if (digits == 0) {
                        goto return1;
                    }
                    if (*cur == 'e' || *cur == 'E') {
                        ++cur;
                        if (*cur == '-' || *cur == '+') {
                            exponentNegative = *cur == '-';
                            ++cur;
                        }
                        if (*cur < '0' || *cur > '9') {
                            goto return1;
                        }
                        while (*cur >= '0' && *cur <= '9') {
                            size_t digit = (size_t)(*cur - '0');
                            if (exponent <= ((size_t)-1 - digit) / 10) {
                                exponent = exponent * 10 + digit;
                            } else {
                                exponent = (size_t)-1;
                            }
                            ++cur;
                        }
                    }
                }
            }
            last = cur;
            if (normOnTheFly) {
                while (IS_WSP_BLANK_CH(*cur)) {
                    ++cur;
                }
            }
            if (*cur != 0) {
                goto return1;
            }
            if (val == NULL) {
                goto return0;
            }
            if (!special) {
                ret = type == xmlSchemaTypeFloatDef
                    ? qoreXmlParseFloat((const char *)first, (const char *)last, &narrow)
                    : qoreXmlParseDouble((const char *)first, (const char *)last, &wide);
                if (ret < 0) {
                    goto error;
                }
                if (ret == 2) {
                    /* Only the sign of the decimal order is needed to classify
                     * an out-of-range value. Saturated exponents cannot cancel
                     * a significand longer than the addressable input. */
                    if (nonzero == (size_t)-1) {
                        underflow = 1;
                    } else if (nonzero < before) {
                        underflow = exponentNegative && exponent > before - nonzero - 1;
                    } else {
                        underflow = exponentNegative || exponent < nonzero - before + 1;
                    }
                    wide = underflow ? (negative ? -0.0 : 0.0)
                        : (negative ? xmlSchemaNINF : xmlSchemaPINF);
                    narrow = (float)wide;
                }
            } else {
                narrow = (float)wide;
            }
            v = xmlSchemaNewValue(type->builtInType);
            if (v == NULL) {
                goto error;
            }
            if (type == xmlSchemaTypeFloatDef) {
                v->value.f = narrow;
            } else {
                v->value.d = wide;
            }
            *val = v;
            goto return0;
        }
