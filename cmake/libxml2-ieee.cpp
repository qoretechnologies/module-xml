/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * SPDX-License-Identifier: LGPL-2.1-or-later
 * Private libxml2 IEEE conversion: no allocation, locale or rounding-mode state.
 */
#include <charconv>
#include "third-party/fast_float/fast_float.h"
#include <cfenv>
#include <cmath>
#include <cstring>
#include <limits>

static_assert(std::numeric_limits<float>::is_iec559 && std::numeric_limits<float>::digits == 24
    && std::numeric_limits<double>::is_iec559 && std::numeric_limits<double>::digits == 53,
    "XSD IEEE conversion requires binary32 and binary64");

// Decimal conversion chooses nearest rounding, but its implementation can still raise
// floating-point status flags. Suppress traps and restore all caller state.
template<class Function> static int guarded(Function function) noexcept {
    std::fenv_t environment;
    if (std::feholdexcept(&environment) != 0) {
        return -1;
    }
    int result = -1;
    if (std::fesetround(FE_TONEAREST) == 0) {
        result = function();
    }
    if (std::fesetenv(&environment) != 0) {
        return -1;
    }
    return result;
}

template<class Float> static int canonical(Float value, char* output, size_t capacity) noexcept {
    char buffer[64];
    if (std::isnan(value) || std::isinf(value) || value == 0) {
        const char* text = std::isnan(value) ? "NaN" : std::isinf(value)
            ? (std::signbit(value) ? "-INF" : "INF") : "0.0E0";
        size_t length = std::strlen(text);
        if (capacity <= length) { return -1; }
        std::memcpy(output, text, length + 1);
        return static_cast<int>(length);
    }
    auto result = std::to_chars(buffer, buffer + sizeof(buffer), value, std::chars_format::scientific);
    if (result.ec != std::errc()) { return -1; }
    char* exponent = buffer;
    bool point = false;
    while (exponent != result.ptr && *exponent != 'e') {
        point |= *exponent == '.';
        ++exponent;
    }
    if (exponent == result.ptr) { return -1; }
    const char* start = exponent + 1;
    if (start != result.ptr && *start == '+') { ++start; }
    int power;
    auto parsed = std::from_chars(start, result.ptr, power);
    if (parsed.ec != std::errc() || parsed.ptr != result.ptr) { return -1; }
    char normalized[64];
    size_t mantissa = static_cast<size_t>(exponent - buffer);
    std::memcpy(normalized, buffer, mantissa);
    char* cursor = normalized + mantissa;
    if (!point) { *cursor++ = '.'; *cursor++ = '0'; }
    *cursor++ = 'E';
    auto encoded = std::to_chars(cursor, normalized + sizeof(normalized) - 1, power);
    if (encoded.ec != std::errc()) { return -1; }
    size_t length = static_cast<size_t>(encoded.ptr - normalized);
    if (capacity <= length) { return -1; }
    *encoded.ptr = 0;
    std::memcpy(output, normalized, length + 1);
    return static_cast<int>(length);
}

// C callers validate XML syntax and strip its optional leading plus/whitespace.
// Range errors are distinguished so the caller can map XSD overflow/underflow.
template<class Float> static int parse(const char* first, const char* last, Float* output) noexcept {
    Float value = 0;
    auto result = fast_float::from_chars(first, last, value, fast_float::chars_format::general);
    if (result.ptr != last) {
        return -1;
    }
    if (result.ec == std::errc::result_out_of_range) {
        return 2;
    }
    if (result.ec != std::errc()) {
        return -1;
    }
    *output = value;
    return 0;
}

extern "C" {
int qoreXmlFormatFloat(float value, char* output, size_t capacity) noexcept {
    return guarded([=]() noexcept { return canonical(value, output, capacity); });
}
int qoreXmlFormatDouble(double value, char* output, size_t capacity) noexcept {
    return guarded([=]() noexcept { return canonical(value, output, capacity); });
}
int qoreXmlParseFloat(const char* first, const char* last, float* output) noexcept {
    return guarded([=]() noexcept { return parse(first, last, output); });
}
int qoreXmlParseDouble(const char* first, const char* last, double* output) noexcept {
    return guarded([=]() noexcept { return parse(first, last, output); });
}
}
