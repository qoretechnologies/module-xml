/* Copyright (C) 2026 Qore Technologies, s.r.o.
   SPDX-License-Identifier: LGPL-2.1-or-later */

#include "XsdFloat.h"

#include <cfenv>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <locale>
#include <limits>
#include <stdexcept>

namespace {

unsigned checks = 0;

void require(bool condition, const char* message) {
    ++checks;
    if (!condition) {
        throw std::runtime_error(message);
    }
}

class CommaPunctuation : public std::numpunct<char> {
public:
    // This stack-owned facet outlives every locale using it, including on error.
    CommaPunctuation() : std::numpunct<char>(1) {
    }

private:
    char do_decimal_point() const override {
        return ',';
    }
};

void check(QoreValue value, bool wide, double expected, bool valid = true) {
    ExceptionSink xsink;
    int mode = std::fegetround();
    std::feclearexcept(FE_ALL_EXCEPT);
    std::feraiseexcept(FE_DIVBYZERO);
    int flags = std::fetestexcept(FE_ALL_EXCEPT);
    double result = qore_xml_convert_xsd_float(value, wide, &xsink);
    require(std::fegetround() == mode, "caller rounding direction changed");
    require(std::fetestexcept(FE_ALL_EXCEPT) == flags, "caller floating-point flags changed");
    require(static_cast<bool>(xsink) != valid, "unexpected conversion exception outcome");
    if (valid) {
        require(!std::memcmp(&result, &expected, sizeof(result)), "incorrect IEEE bits");
    } else {
        require(xsink.getExceptionErr().get<const QoreStringNode>()->equal("XSD-FLOAT-LEXICAL-ERROR"),
            "wrong lexical exception category");
        xsink.clear();
    }
}

void lexical(const char* value, bool wide, double expected, bool valid = true) {
    ExceptionSink xsink;
    ReferenceHolder<QoreStringNode> text(new QoreStringNode(value), &xsink);
    check(*text, wide, expected, valid);
}

void integer(int64 value, bool wide, double expected) {
    ExceptionSink xsink;
    // Large integers are boxed allocations in NaN-boxed Qore builds.
    ValueHolder owned(QoreValue(value), &xsink);
    check(*owned, wide, expected);
}

void run() {
    const int modes[] = {FE_TONEAREST, FE_DOWNWARD, FE_UPWARD, FE_TOWARDZERO};
    double infinity = std::numeric_limits<double>::infinity();
    double midpoint = 1.0 + std::ldexp(1.0, -24);
    double next = 1.0 + std::ldexp(1.0, -23);
    double huge = std::ldexp(1.0, 62);
    int64 integer_midpoint = (int64(1) << 62) + (int64(1) << 38);
    ExceptionSink xsink;
    ReferenceHolder<QoreNumberNode> above(new QoreNumberNode(
        "1.00000005960464477539062500000000000000000000000000000001", 512), &xsink);
    ReferenceHolder<QoreNumberNode> below(new QoreNumberNode(
        "1.00000005960464477539062499999999999999999999999999999999", 512), &xsink);
    for (int mode : modes) {
        require(!std::fesetround(mode), "cannot set test rounding direction");
        lexical("16777217", false, 16777216.0);
        lexical("16777217", true, 16777217.0);
        lexical("1.000000059604644775390625", false, 1.0);
        lexical("1.0000000596046447753906250000000000000001", false, next);
        lexical("1.0000000596046447753906249999999999999999", false, 1.0);
        lexical("1.00000000000000011102230246251565404236316680908203125", true, 1.0);
        lexical("1.000000000000000111022302462515654042363166809082031250001", true,
            std::nextafter(1.0, 2.0));
        lexical("1e-50", false, 0.0);
        lexical("-1e-50", false, -0.0);
        lexical("3.5e38", false, infinity);
        lexical("-3.5e38", false, -infinity);
        lexical("1e9999999999999999999999", true, infinity);
        lexical("-1e-9999999999999999999999", true, -0.0);
        lexical("0e9999999999999999999999", false, 0.0);
        lexical("-0e9999999999999999999999", true, -0.0);
        lexical("1.401298464324817070923729583289916131280e-45", false, std::ldexp(1.0, -149));
        lexical("4.940656458412465441765687928682213723650598026143247644255856825e-324", true,
            std::numeric_limits<double>::denorm_min());
        lexical("\t\r\n +1.25 \n", false, 1.25);
        lexical(" .5 ", true, 0.5);
        lexical("1.", false, 1.0);
        lexical("-0", false, -0.0);
        lexical(" INF\n", false, infinity);
        lexical("-INF", true, -infinity);
        lexical("", false, 0, false);
        lexical(" \t\n", true, 0, false);
        lexical("1e", false, 0, false);
        lexical("1.25tail", true, 0, false);
        lexical("+INF", false, 0, false);
        lexical("1,25", true, 0, false);
        lexical("0x1p0", false, 0, false);
        lexical("\v1", true, 0, false);
        check(midpoint, false, 1.0);
        check(std::nextafter(midpoint, 2.0), false, next);
        check(std::nextafter(midpoint, 1.0), false, 1.0);
        check(-0.0, false, -0.0);
        integer(integer_midpoint, false, huge);
        integer(integer_midpoint + 1, false, huge + std::ldexp(1.0, 39));
        integer(integer_midpoint - 1, false, huge);
        integer(-integer_midpoint - 1, false, -huge - std::ldexp(1.0, 39));
        check(*above, false, next);
        check(*below, false, 1.0);
        integer(int64(9007199254740993ll), true, 9007199254740992.0);
    }
}

void cancellation() {
    for (const char* lexical : {"NaN", "INF", "-INF", "1e9999", "-1e-9999", "1.00000001", ""}) {
        ExceptionSink xsink;
        ReferenceHolder<QoreStringNode> input(new QoreStringNode(lexical), &xsink);
        int rounding = std::fegetround();
        int flags = std::fetestexcept(FE_ALL_EXCEPT);
        require(!qore_cancel_thread(q_gettid(), "XSD floating-point conversion test"), "cannot request cancellation");
        qore_xml_convert_xsd_float(*input, false, &xsink);
        bool cancelled = xsink && xsink.getExceptionErr().get<const QoreStringNode>()->equal("THREAD-CANCELLED");
        qore_clear_thread_cancel();
        xsink.clear();
        require(cancelled, "conversion did not propagate cancellation");
        require(std::fegetround() == rounding && std::fetestexcept(FE_ALL_EXCEPT) == flags,
            "cancellation changed floating-point state");
        ReferenceHolder<QoreStringNode> valid(new QoreStringNode("1.25"), &xsink);
        require(qore_xml_convert_xsd_float(*valid, false, &xsink) == 1.25 && !xsink,
            "conversion did not recover after cancellation");
    }
}

} // namespace

int main() {
    qore_init(QL_MIT, "UTF-8", true, QLO_DISABLE_SIGNAL_HANDLING);
    std::fenv_t environment;
    std::fegetenv(&environment);
    std::locale original = std::locale();
    CommaPunctuation punctuation;
    int status = 0;
    try {
        run();
        std::locale::global(std::locale(std::locale::classic(), &punctuation));
        run();
        cancellation();
        std::printf("XSD IEEE native conversion: %u checks passed\n", checks);
    } catch (const std::exception& error) {
        std::fprintf(stderr, "XSD IEEE native conversion failed after %u checks: %s\n", checks, error.what());
        status = 1;
    }
    std::locale::global(original);
    std::fesetenv(&environment);
    qore_cleanup();
    return status;
}
