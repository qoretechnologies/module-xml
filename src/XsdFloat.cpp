/* Copyright (C) 2026 Qore Technologies, s.r.o.
   SPDX-License-Identifier: LGPL-2.1-or-later */

#include "XsdFloat.h"

#include <cassert>
#include <cfenv>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <locale>
#include <sstream>
#include <string>

namespace {

static_assert(std::numeric_limits<float>::is_iec559 && std::numeric_limits<float>::digits == 24
    && std::numeric_limits<float>::radix == 2 && std::numeric_limits<float>::min_exponent == -125
    && std::numeric_limits<float>::max_exponent == 128
    && std::numeric_limits<double>::is_iec559 && std::numeric_limits<double>::digits == 53
    && std::numeric_limits<double>::radix == 2 && std::numeric_limits<double>::min_exponent == -1021
    && std::numeric_limits<double>::max_exponent == 1024,
    "XSD float conversion requires IEEE binary32 and binary64");

// Decimal input conversion must not inherit the caller's rounding direction or
// raise enabled floating-point traps. Restore both the direction and all flags.
class XsdFloatEnvironment {
public:
    explicit XsdFloatEnvironment(ExceptionSink* xsink) : xsink(xsink), saved(!std::feholdexcept(&environment)) {
        if (!saved || std::fesetround(FE_TONEAREST)) {
            xsink->raiseException("XSD-FLOAT-CONVERSION-ERROR", "cannot select nearest IEEE rounding");
        }
    }

    ~XsdFloatEnvironment() {
        if (saved && std::fesetenv(&environment)) {
            xsink->raiseException("XSD-FLOAT-CONVERSION-ERROR", "cannot restore the caller's IEEE environment");
        }
    }

    XsdFloatEnvironment(const XsdFloatEnvironment&) = delete;
    XsdFloatEnvironment& operator=(const XsdFloatEnvironment&) = delete;

private:
    ExceptionSink* xsink;
    std::fenv_t environment;
    bool saved;
};

bool xmlSpace(char c) {
    return c == ' ' || c == '\t' || c == '\r' || c == '\n';
}

bool digit(char c) {
    return c >= '0' && c <= '9';
}

// Consume once, using the string's length so embedded NULs cannot truncate it.
// XML collapse permits surrounding whitespace, but never inside a number.
bool validateLexical(const QoreString& text, size_t& start, size_t& end, ExceptionSink* xsink) {
    enum class State { Leading, Sign, Integer, Point, Fraction, Exponent, ExponentSign, ExponentDigits, Trailing };
    State state = State::Leading;
    bool mantissa_digit = false;
    const char* data = text.c_str();
    start = end = 0;
    for (size_t i = 0; i < text.size(); ++i) {
        if (!(i % 100) && qore_check_cancel(xsink, "XSD floating-point lexical validation")) {
            return false;
        }
        const char c = data[i];
        if (state == State::Leading) {
            if (xmlSpace(c)) {
                continue;
            }
            start = i;
            state = State::Sign;
            if (c == '+' || c == '-') {
                end = i + 1;
                continue;
            }
        }
        if (state == State::Trailing) {
            if (!xmlSpace(c)) {
                return false;
            }
            continue;
        }
        if (digit(c)) {
            if (state == State::Exponent || state == State::ExponentSign || state == State::ExponentDigits) {
                state = State::ExponentDigits;
            } else {
                mantissa_digit = true;
                state = state == State::Point || state == State::Fraction ? State::Fraction : State::Integer;
            }
        } else if (c == '.' && (state == State::Sign || state == State::Integer)) {
            state = State::Point;
        } else if ((c == 'e' || c == 'E') && mantissa_digit
                && (state == State::Integer || state == State::Point || state == State::Fraction)) {
            state = State::Exponent;
        } else if ((c == '+' || c == '-') && state == State::Exponent) {
            state = State::ExponentSign;
        } else if (xmlSpace(c) && mantissa_digit
                && (state == State::Integer || state == State::Point || state == State::Fraction
                    || state == State::ExponentDigits)) {
            state = State::Trailing;
            continue;
        } else {
            return false;
        }
        end = i + 1;
    }
    return mantissa_digit && (state == State::Integer || state == State::Point || state == State::Fraction
        || state == State::ExponentDigits || state == State::Trailing);
}

template<typename Float>
double parseFinite(const QoreString& text, size_t start, size_t end, ExceptionSink* xsink) {
    XsdFloatEnvironment environment(xsink);
    if (*xsink) {
        return 0.0;
    }
    std::istringstream input(std::string(text.c_str() + start, end - start));
    input.imbue(std::locale::classic());
    Float result = 0;
    input >> result; // num_get converts directly with strtof or strtod, respectively.
    if (qore_check_cancel(xsink, "XSD floating-point conversion")) {
        return 0.0;
    }
    if (input.bad() || !input.eof()) {
        xsink->raiseException("XSD-FLOAT-CONVERSION-ERROR", "incomplete IEEE decimal conversion");
        return 0.0;
    }
    if (input.fail()) {
        // Libraries report overflow as infinity or a clamped largest finite value.
        // XSD's nearest-value mapping includes infinities. Underflow results
        // (zero or subnormal) already have their correctly rounded value.
        if (std::isinf(result) || std::fabs(result) == std::numeric_limits<Float>::max()) {
            return std::copysign(std::numeric_limits<double>::infinity(), result);
        }
        if (result != 0 && std::fpclassify(result) != FP_SUBNORMAL) {
            xsink->raiseException("XSD-FLOAT-CONVERSION-ERROR", "IEEE decimal conversion failed");
            return 0.0;
        }
    }
    return result;
}

// Interpret an ordered positive binary32 index exactly in binary64. At the
// infinity index, 2^128 is the next finite significand used to derive its rounding
// boundary. No host float cast, byte-order assumption or rounding mode is involved.
double float32Endpoint(uint32_t bits) {
    assert(bits <= 0x7f800000u);
    uint32_t exponent = bits >> 23;
    uint32_t significand = bits & 0x7fffffu;
    if (exponent) {
        significand |= 0x800000u;
    }
    return std::ldexp(static_cast<double>(significand), exponent ? static_cast<int>(exponent) - 150 : -149);
}

template<typename Compare>
double roundFloat32(bool negative, Compare compare) {
    uint32_t low = 0;
    uint32_t high = 0x7f800000u;
    // At most 31 comparisons. Every midpoint requires at most 25 binary digits
    // and is exactly representable in double, including 2^-150 and overflow.
    while (low < high) {
        uint32_t middle = low + (high - low) / 2;
        double boundary = (float32Endpoint(middle) + float32Endpoint(middle + 1)) * 0.5;
        int order = compare(boundary);
        if (order < 0 || (!order && !(middle & 1u))) {
            high = middle;
        } else {
            low = middle + 1;
        }
    }
    double result = low == 0x7f800000u ? std::numeric_limits<double>::infinity() : float32Endpoint(low);
    return negative ? -result : result;
}

double convertNative(QoreValue value, bool double_precision, ExceptionSink* xsink) {
    if (value.getType() == NT_FLOAT) {
        double input = value.getAsFloat();
        if (double_precision || !std::isfinite(input) || input == 0) {
            return input;
        }
        double magnitude = std::fabs(input);
        return roundFloat32(std::signbit(input), [magnitude](double boundary) {
            return magnitude < boundary ? -1 : magnitude > boundary ? 1 : 0;
        });
    }
    // int -> number is exact. Do not convert a native float to number here:
    // Qore intentionally uses a decimal spelling for that public conversion.
    ReferenceHolder<QoreNumberNode> input(value.getType() == NT_INT ? new QoreNumberNode(value.getAsBigInt())
        : value.get<const QoreNumberNode>()->numberRefSelf(), xsink);
    double approximate = input->getAsFloat();
    if (double_precision || input->nan() || input->zero()) {
        return approximate;
    }
    bool negative = input->sign() < 0;
    return roundFloat32(negative, [&input, negative](double boundary) {
        if (negative) {
            return input->greaterThan(-boundary) ? -1 : input->lessThan(-boundary) ? 1 : 0;
        }
        return input->lessThan(boundary) ? -1 : input->greaterThan(boundary) ? 1 : 0;
    });
}

} // namespace

double qore_xml_convert_xsd_float(QoreValue value, bool double_precision, ExceptionSink* xsink) {
    if (qore_check_cancel(xsink, "XSD floating-point conversion")) {
        return 0.0;
    }
    switch (value.getType()) {
        case NT_INT:
        case NT_FLOAT:
        case NT_NUMBER:
            return convertNative(value, double_precision, xsink);
        case NT_STRING:
            break;
        default:
            xsink->raiseException("XSD-FLOAT-LEXICAL-ERROR", "XSD %s requires a string, int, float or number; got %s",
                double_precision ? "double" : "float", value.getTypeName());
            return 0.0;
    }
    TempEncodingHelper text(value.get<const QoreStringNode>(), QCS_UTF8, xsink);
    if (!text) {
        return 0.0;
    }
    size_t start = 0;
    size_t end = text->size();
    // Special spellings have no internal whitespace. This scan is also bounded
    // by input length, with cancellation during arbitrarily long padding.
    for (size_t i = 0; i < text->size(); ++i) {
        if (!(i % 100) && qore_check_cancel(xsink, "XSD floating-point whitespace")) {
            return 0.0;
        }
        if (!xmlSpace(text->c_str()[i])) {
            start = i;
            break;
        }
        start = i + 1;
    }
    for (size_t i = end; i > start; --i) {
        if (!(i % 100) && qore_check_cancel(xsink, "XSD floating-point whitespace")) {
            return 0.0;
        }
        if (!xmlSpace(text->c_str()[i - 1])) {
            end = i;
            break;
        }
        end = i - 1;
    }
    const char* data = text->c_str() + start;
    if (end - start == 3 && !std::memcmp(data, "NaN", 3)) {
        return std::numeric_limits<double>::quiet_NaN();
    }
    if (end - start == 3 && !std::memcmp(data, "INF", 3)) {
        return std::numeric_limits<double>::infinity();
    }
    if (end - start == 4 && !std::memcmp(data, "-INF", 4)) {
        return -std::numeric_limits<double>::infinity();
    }
    if (!validateLexical(*text, start, end, xsink)) {
        if (!*xsink) {
            xsink->raiseException("XSD-FLOAT-LEXICAL-ERROR", "invalid XML Schema %s lexical value",
                double_precision ? "double" : "float");
        }
        return 0.0;
    }
    return double_precision ? parseFinite<double>(*text, start, end, xsink) : parseFinite<float>(*text, start, end, xsink);
}
