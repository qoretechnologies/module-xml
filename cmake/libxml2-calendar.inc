#include "private/buf.h"
#include <assert.h>
/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Exact Gregorian calendar arithmetic for the opaque native schema value.
 * No floating point conversion participates in parsing, comparison or output.
 */
static int
qoreXmlCalendarType(xmlSchemaValType type) {
    return type == XML_SCHEMAS_DATETIME || type == XML_SCHEMAS_TIME ||
        type == XML_SCHEMAS_DATE || type == XML_SCHEMAS_GYEAR ||
        type == XML_SCHEMAS_GYEARMONTH || type == XML_SCHEMAS_GMONTH ||
        type == XML_SCHEMAS_GMONTHDAY || type == XML_SCHEMAS_GDAY;
}

static xmlChar *
qoreXmlCalendarString(const xmlChar *text, size_t length) {
    xmlChar *result;
    if (length == SIZE_MAX) {
        return NULL;
    }
    result = xmlMalloc(length + 1);
    if (result != NULL) {
        memcpy(result, text, length);
        result[length] = 0;
    }
    return result;
}

static int
qoreXmlCalendarCopy(xmlSchemaValDate *target, const xmlSchemaValDate *source) {
    assert(target != source);
    assert(source->year != NULL && source->yearLength >= 4);
    *target = *source;
    target->year = qoreXmlCalendarString(source->year, source->yearLength);
    target->fraction = NULL;
    if (target->year == NULL) {
        return -1;
    }
    if (source->fractionLength != 0) {
        target->fraction = qoreXmlCalendarString(source->fraction, source->fractionLength);
        if (target->fraction == NULL) {
            xmlFree(target->year);
            target->year = NULL;
            return -1;
        }
    }
    return 0;
}

static void
qoreXmlCalendarClear(xmlSchemaValDate *date) {
    xmlFree(date->year);
    xmlFree(date->fraction);
}

static int
qoreXmlCalendarLastDay(const xmlSchemaValDate *date) {
    static const int days[] = {31,28,31,30,31,30,31,31,30,31,30,31};
    unsigned cycle = 0;
    size_t i;
    assert(date->year != NULL && date->yearLength >= 4);
    assert(date->mon >= 1 && date->mon <= 12);
    for (i = date->yearLength - 4; i < date->yearLength; ++i) {
        cycle = cycle * 10 + date->year[i] - '0';
    }
    return date->mon == 2 && cycle % 4 == 0 &&
        (cycle % 100 != 0 || cycle % 400 == 0) ? 29 : days[date->mon - 1];
}

/* Change the year label by one, skipping year zero. Own the new buffer before
 * releasing the old one; a failed allocation leaves the input untouched. */
static int
qoreXmlCalendarYear(xmlSchemaValDate *date, int direction) {
    int increase = date->negative ? direction < 0 : direction > 0;
    size_t length = date->yearLength, i;
    xmlChar *next;
    assert(direction == -1 || direction == 1);
    assert(date->year != NULL && date->yearLength >= 4);
    if (!increase && length == 4 && memcmp(date->year, "0001", 4) == 0) {
        date->negative = !date->negative;
        return 0;
    }
    if (length > SIZE_MAX - 2) {
        return -1;
    }
    next = xmlMalloc(length + 2);
    if (next == NULL) {
        return -1;
    }
    memcpy(next, date->year, length + 1);
    i = length;
    if (increase) {
        while (i != 0 && next[i - 1] == '9') {
            next[--i] = '0';
        }
        if (i != 0) {
            ++next[i - 1];
        } else {
            memmove(next + 1, next, length + 1);
            next[0] = '1';
            ++length;
        }
    } else {
        while (i != 0 && next[i - 1] == '0') {
            next[--i] = '9';
        }
        --next[i - 1];
        if (length > 4 && next[0] == '0') {
            memmove(next, next + 1, length);
            --length;
        }
    }
    xmlFree(date->year);
    date->year = next;
    date->yearLength = length;
    return 0;
}

static int
qoreXmlCalendarDay(xmlSchemaValDate *date, int direction) {
    assert(direction == -1 || direction == 1);
    date->day += direction;
    if (date->day < 1) {
        if (--date->mon == 0) {
            date->mon = 12;
            if (qoreXmlCalendarYear(date, -1) != 0) {
                return -1;
            }
        }
        date->day = qoreXmlCalendarLastDay(date);
    } else if (date->day > qoreXmlCalendarLastDay(date)) {
        date->day = 1;
        if (++date->mon == 13) {
            date->mon = 1;
            if (qoreXmlCalendarYear(date, 1) != 0) {
                return -1;
            }
        }
    }
    return 0;
}

static int
qoreXmlCalendarDigits(const xmlChar **cursor, const xmlChar *end, int *result) {
    const xmlChar *p = *cursor;
    if (end - p < 2 || p[0] < '0' || p[0] > '9' || p[1] < '0' || p[1] > '9') {
        return 1;
    }
    *result = (p[0] - '0') * 10 + p[1] - '0';
    *cursor += 2;
    return 0;
}

static int
qoreXmlCalendarChar(const xmlChar **cursor, const xmlChar *end, xmlChar ch) {
    if (*cursor == end || **cursor != ch) {
        return 1;
    }
    ++*cursor;
    return 0;
}

static int
xmlSchemaValidateDates(xmlSchemaValType type, const xmlChar *text,
                       xmlSchemaValPtr *value, int collapse) {
    const xmlChar *p, *end, *start;
    xmlSchemaValPtr result;
    xmlSchemaValDate *d;
    size_t length;
    int error = 1;
    if (value != NULL) {
        *value = NULL;
    }
    if (text == NULL || !qoreXmlCalendarType(type)) {
        return -1;
    }
    p = text;
    end = text + strlen((const char *)text);
    if (collapse) {
        while (p != end && IS_WSP_BLANK_CH(*p)) {
            ++p;
        }
        while (p != end && IS_WSP_BLANK_CH(end[-1])) {
            --end;
        }
    }
    result = xmlSchemaNewValue(type);
    if (result == NULL) {
        return -1;
    }
    d = &result->value.date;
    d->mon = d->day = 1;
    if (type == XML_SCHEMAS_DATETIME || type == XML_SCHEMAS_DATE ||
            type == XML_SCHEMAS_GYEAR || type == XML_SCHEMAS_GYEARMONTH) {
        if (p != end && *p == '-') {
            d->negative = 1;
            ++p;
        }
        start = p;
        while (p != end && *p >= '0' && *p <= '9') {
            ++p;
        }
        length = (size_t)(p - start);
        if (length < 4 || (length > 4 && start[0] == '0') ||
                (length == 4 && memcmp(start, "0000", 4) == 0)) {
            goto error;
        }
    } else {
        start = BAD_CAST "2000";
        length = 4;
    }
    d->year = qoreXmlCalendarString(start, length);
    if (d->year == NULL) {
        error = -1;
        goto error;
    }
    d->yearLength = length;
    if (type == XML_SCHEMAS_GMONTH || type == XML_SCHEMAS_GMONTHDAY || type == XML_SCHEMAS_GDAY) {
        if (qoreXmlCalendarChar(&p, end, '-') || qoreXmlCalendarChar(&p, end, '-')) {
            goto error;
        }
    }
    if (type == XML_SCHEMAS_DATETIME || type == XML_SCHEMAS_DATE || type == XML_SCHEMAS_GYEARMONTH) {
        if (qoreXmlCalendarChar(&p, end, '-')) {
            goto error;
        }
    }
    if (type == XML_SCHEMAS_DATETIME || type == XML_SCHEMAS_DATE ||
            type == XML_SCHEMAS_GYEARMONTH || type == XML_SCHEMAS_GMONTH || type == XML_SCHEMAS_GMONTHDAY) {
        if (qoreXmlCalendarDigits(&p, end, &d->mon)) {
            goto error;
        }
    }
    if (type == XML_SCHEMAS_DATETIME || type == XML_SCHEMAS_DATE ||
            type == XML_SCHEMAS_GMONTHDAY || type == XML_SCHEMAS_GDAY) {
        if (qoreXmlCalendarChar(&p, end, '-') || qoreXmlCalendarDigits(&p, end, &d->day)) {
            goto error;
        }
    }
    if (d->mon < 1 || d->mon > 12 || d->day < 1 || d->day > qoreXmlCalendarLastDay(d)) {
        goto error;
    }
    if (type == XML_SCHEMAS_DATETIME && qoreXmlCalendarChar(&p, end, 'T')) {
        goto error;
    }
    if (type == XML_SCHEMAS_DATETIME || type == XML_SCHEMAS_TIME) {
        if (qoreXmlCalendarDigits(&p, end, &d->hour) || qoreXmlCalendarChar(&p, end, ':') ||
                qoreXmlCalendarDigits(&p, end, &d->min) || qoreXmlCalendarChar(&p, end, ':') ||
                qoreXmlCalendarDigits(&p, end, &d->sec)) {
            goto error;
        }
        if (p != end && *p == '.') {
            start = ++p;
            while (p != end && *p >= '0' && *p <= '9') {
                ++p;
            }
            length = (size_t)(p - start);
            if (length == 0) {
                goto error;
            }
            while (length != 0 && start[length - 1] == '0') {
                --length;
            }
            if (length != 0) {
                d->fraction = qoreXmlCalendarString(start, length);
                if (d->fraction == NULL) {
                    error = -1;
                    goto error;
                }
                d->fractionLength = length;
            }
        }
        if (d->hour > 24 || d->min > 59 || d->sec > 60 ||
                (d->hour == 24 && (d->min || d->sec || d->fractionLength))) {
            goto error;
        }
        if (d->hour == 24) {
            d->hour = 0;
            if (type == XML_SCHEMAS_DATETIME && qoreXmlCalendarDay(d, 1) != 0) {
                error = -1;
                goto error;
            }
        }
    }
    if (p != end) {
        int negative, hour, minute;
        d->tz_flag = 1;
        if (*p == 'Z') {
            ++p;
        } else {
            if (*p != '-' && *p != '+') {
                goto error;
            }
            negative = *p++ == '-';
            if (qoreXmlCalendarDigits(&p, end, &hour) || qoreXmlCalendarChar(&p, end, ':') ||
                    qoreXmlCalendarDigits(&p, end, &minute) || hour > 14 || minute > 59 || (hour == 14 && minute)) {
                goto error;
            }
            d->tzo = (hour * 60 + minute) * (negative ? -1 : 1);
        }
    }
    if (p != end) {
        goto error;
    }
    if (value != NULL) {
        *value = result;
    } else {
        xmlSchemaFreeValue(result);
    }
    return 0;
error:
    xmlSchemaFreeValue(result);
    return error;
}

/* DateTime leap candidates match XSD 1.0 Appendix D's quarter ends. Unknown
 * timezones retain a leap second whenever a permitted whole-minute zone can
 * place it at a quarter end; this is the existing WSDL temporal contract. */
static int
qoreXmlCalendarFloatingLeap(const xmlSchemaValDate *d, xmlSchemaValType type) {
    int minute = d->hour * 60 + d->min;
    if (type == XML_SCHEMAS_TIME) {
        return 1;
    }
    if (minute >= 599 && d->mon % 3 == 0 && d->day == qoreXmlCalendarLastDay(d)) {
        return 1;
    }
    return minute <= 839 && d->day == 1 && d->mon % 3 == 1;
}

static int
qoreXmlCalendarNormalize(xmlSchemaValDate *d, int offset, xmlSchemaValType type, int endpoint) {
    int floating = d->sec == 60 && !d->tz_flag && !endpoint && qoreXmlCalendarFloatingLeap(d, type);
    int minute = d->hour * 60 + d->min - offset;
    assert(offset >= -840 && offset <= 840);
    if (minute < 0) {
        minute += 1440;
        if (qoreXmlCalendarDay(d, -1) != 0) {
            return -1;
        }
    } else if (minute >= 1440) {
        minute -= 1440;
        if (qoreXmlCalendarDay(d, 1) != 0) {
            return -1;
        }
    }
    if (d->sec == 60 && !floating && (minute != 1439 || (type == XML_SCHEMAS_DATETIME &&
            (d->mon % 3 != 0 || d->day != qoreXmlCalendarLastDay(d))))) {
        d->sec = 0;
        if (++minute == 1440) {
            minute = 0;
            if (qoreXmlCalendarDay(d, 1) != 0) {
                return -1;
            }
        }
    }
    if (type == XML_SCHEMAS_TIME && !endpoint) {
        /* A daily clock has no date; its allocated anchor always has room. */
        memcpy(d->year, "2000", 5);
        d->yearLength = 4;
        d->negative = 0;
        d->mon = d->day = 1;
    }
    d->hour = minute / 60;
    d->min = minute % 60;
    return 0;
}

static int
qoreXmlCalendarInstantCompare(const xmlSchemaValDate *x, const xmlSchemaValDate *y) {
    int relation;
    size_t length;
    if (x->negative != y->negative) {
        return x->negative ? -1 : 1;
    }
    if (x->yearLength != y->yearLength) {
        relation = x->yearLength < y->yearLength ? -1 : 1;
    } else {
        relation = memcmp(x->year, y->year, x->yearLength);
        relation = (relation > 0) - (relation < 0);
    }
    if (relation != 0) {
        return x->negative ? -relation : relation;
    }
#define QORE_XML_CALENDAR_COMPARE(field) \
    if (x->field != y->field) { return x->field < y->field ? -1 : 1; }
    QORE_XML_CALENDAR_COMPARE(mon)
    QORE_XML_CALENDAR_COMPARE(day)
    QORE_XML_CALENDAR_COMPARE(hour)
    QORE_XML_CALENDAR_COMPARE(min)
    QORE_XML_CALENDAR_COMPARE(sec)
#undef QORE_XML_CALENDAR_COMPARE
    length = x->fractionLength < y->fractionLength ? x->fractionLength : y->fractionLength;
    relation = length ? memcmp(x->fraction, y->fraction, length) : 0;
    if (relation != 0) {
        return relation < 0 ? -1 : 1;
    }
    return (x->fractionLength > y->fractionLength) - (x->fractionLength < y->fractionLength);
}

static int
qoreXmlCalendarCompareOffsets(xmlSchemaValPtr x, int xoffset, int xendpoint,
                             xmlSchemaValPtr y, int yoffset, int yendpoint) {
    xmlSchemaValDate a, b;
    int result = -2;
    if (qoreXmlCalendarCopy(&a, &x->value.date) != 0) {
        return -2;
    }
    if (qoreXmlCalendarCopy(&b, &y->value.date) != 0) {
        qoreXmlCalendarClear(&a);
        return -2;
    }
    if (qoreXmlCalendarNormalize(&a, xoffset, x->type, xendpoint) == 0 &&
            qoreXmlCalendarNormalize(&b, yoffset, y->type, yendpoint) == 0) {
        result = qoreXmlCalendarInstantCompare(&a, &b);
    }
    qoreXmlCalendarClear(&a);
    qoreXmlCalendarClear(&b);
    return result;
}

static int
xmlSchemaCompareDates(xmlSchemaValPtr x, xmlSchemaValPtr y) {
    int result, xzone, yzone;
    if (x == NULL || y == NULL) {
        return -2;
    }
    if (x->type != y->type) {
        return 2;
    }
    xzone = x->value.date.tz_flag;
    yzone = y->value.date.tz_flag;
    if (xzone == yzone) {
        return qoreXmlCalendarCompareOffsets(x, x->value.date.tzo, 0, y, y->value.date.tzo, 0);
    }
    result = qoreXmlCalendarCompareOffsets(x, xzone ? x->value.date.tzo : -840, !xzone,
                                          y, yzone ? y->value.date.tzo : 840, !yzone);
    if (result == -2 || result == -1) {
        return result;
    }
    result = qoreXmlCalendarCompareOffsets(x, xzone ? x->value.date.tzo : 840, !xzone,
                                          y, yzone ? y->value.date.tzo : -840, !yzone);
    return result == -2 || result == 1 ? result : 2;
}

static int
qoreXmlCalendarCanonical(xmlSchemaValPtr value, const xmlChar **output) {
    xmlSchemaValDate d;
    xmlSchemaValType type = value->type;
    xmlBufPtr buffer;
    char part[40];
    int length;
    *output = NULL;
    if (qoreXmlCalendarCopy(&d, &value->value.date) != 0) {
        return -1;
    }
    if (type == XML_SCHEMAS_DATE) {
        if (d.tz_flag && d.tzo > 720) {
            d.tzo -= 1440;
            if (qoreXmlCalendarDay(&d, -1) != 0) {
                goto error_date;
            }
        } else if (d.tz_flag && d.tzo <= -720) {
            d.tzo += 1440;
            if (qoreXmlCalendarDay(&d, 1) != 0) {
                goto error_date;
            }
        }
    } else if (type == XML_SCHEMAS_TIME || type == XML_SCHEMAS_DATETIME) {
        if (qoreXmlCalendarNormalize(&d, d.tzo, type, 0) != 0) {
            goto error_date;
        }
        d.tzo = 0;
    }
    buffer = xmlBufCreate(64);
    if (buffer == NULL) {
        goto error_date;
    }
#define QORE_XML_CALENDAR_ADD(text, length) \
    if (xmlBufAdd(buffer, BAD_CAST (text), (length)) != 0) { goto error_buffer; }
    if (type == XML_SCHEMAS_DATETIME || type == XML_SCHEMAS_DATE ||
            type == XML_SCHEMAS_GYEAR || type == XML_SCHEMAS_GYEARMONTH) {
        if (d.negative) {
            QORE_XML_CALENDAR_ADD("-", 1)
        }
        QORE_XML_CALENDAR_ADD(d.year, d.yearLength)
    }
    if (type == XML_SCHEMAS_DATETIME || type == XML_SCHEMAS_DATE) {
        length = snprintf(part, sizeof(part), "-%02d-%02d", d.mon, d.day);
        if (length < 0 || (size_t)length >= sizeof(part)) {
            goto error_buffer;
        }
        QORE_XML_CALENDAR_ADD(part, (size_t)length)
    } else if (type == XML_SCHEMAS_GYEARMONTH) {
        length = snprintf(part, sizeof(part), "-%02d", d.mon);
        if (length < 0 || (size_t)length >= sizeof(part)) {
            goto error_buffer;
        }
        QORE_XML_CALENDAR_ADD(part, (size_t)length)
    } else if (type == XML_SCHEMAS_GMONTHDAY) {
        length = snprintf(part, sizeof(part), "--%02d-%02d", d.mon, d.day);
        if (length < 0 || (size_t)length >= sizeof(part)) {
            goto error_buffer;
        }
        QORE_XML_CALENDAR_ADD(part, (size_t)length)
    } else if (type == XML_SCHEMAS_GMONTH) {
        length = snprintf(part, sizeof(part), "--%02d", d.mon);
        if (length < 0 || (size_t)length >= sizeof(part)) {
            goto error_buffer;
        }
        QORE_XML_CALENDAR_ADD(part, (size_t)length)
    } else if (type == XML_SCHEMAS_GDAY) {
        length = snprintf(part, sizeof(part), "---%02d", d.day);
        if (length < 0 || (size_t)length >= sizeof(part)) {
            goto error_buffer;
        }
        QORE_XML_CALENDAR_ADD(part, (size_t)length)
    }
    if (type == XML_SCHEMAS_DATETIME) {
        QORE_XML_CALENDAR_ADD("T", 1)
    }
    if (type == XML_SCHEMAS_DATETIME || type == XML_SCHEMAS_TIME) {
        length = snprintf(part, sizeof(part), "%02d:%02d:%02d", d.hour, d.min, d.sec);
        if (length < 0 || (size_t)length >= sizeof(part)) {
            goto error_buffer;
        }
        QORE_XML_CALENDAR_ADD(part, (size_t)length)
        if (d.fractionLength != 0) {
            QORE_XML_CALENDAR_ADD(".", 1)
            QORE_XML_CALENDAR_ADD(d.fraction, d.fractionLength)
        }
    }
    if (d.tz_flag) {
        if (d.tzo == 0) {
            QORE_XML_CALENDAR_ADD("Z", 1)
        } else {
            int magnitude = d.tzo < 0 ? -d.tzo : d.tzo;
            length = snprintf(part, sizeof(part), "%c%02d:%02d", d.tzo < 0 ? '-' : '+', magnitude / 60, magnitude % 60);
            if (length < 0 || (size_t)length >= sizeof(part)) {
                goto error_buffer;
            }
            QORE_XML_CALENDAR_ADD(part, (size_t)length)
        }
    }
    *output = xmlBufDetach(buffer);
    xmlBufFree(buffer);
    qoreXmlCalendarClear(&d);
    return *output == NULL ? -1 : 0;
error_buffer:
    xmlBufFree(buffer);
error_date:
    qoreXmlCalendarClear(&d);
    return -1;
#undef QORE_XML_CALENDAR_ADD
}
