/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * The public datatype API must distinguish allocation errors from bad input.
 * Install forwarding hooks before any libxml2 initialization in this process.
 */
static xmlFreeFunc value_probe_free;
static xmlMallocFunc value_probe_malloc;
static xmlReallocFunc value_probe_realloc;
static xmlStrdupFunc value_probe_strdup;
static int value_probe_armed;
static unsigned int value_probe_failures;
static unsigned int value_probe_attempts;
static unsigned int value_probe_fail_at;
static int value_probe_reject(void) {
    if (value_probe_armed) {
        ++value_probe_attempts;
        if (value_probe_fail_at != 0 && value_probe_attempts >= value_probe_fail_at) {
            ++value_probe_failures;
            return 1;
        }
    }
    return 0;
}

static void *value_probe_allocate(size_t size) {
    if (value_probe_reject()) {
        return NULL;
    }
    return value_probe_malloc(size);
}
static void *value_probe_resize(void *value, size_t size) {
    if (value_probe_reject()) {
        return NULL;
    }
    return value_probe_realloc(value, size);
}
static char *value_probe_duplicate(const char *value) {
    if (value_probe_reject()) {
        return NULL;
    }
    return value_probe_strdup(value);
}
static int prepare_value_allocation(void) {
    if (xmlMemGet(&value_probe_free, &value_probe_malloc, &value_probe_realloc, &value_probe_strdup) != 0) {
        return 1;
    }
    return xmlMemSetup(value_probe_free, value_probe_allocate, value_probe_resize, value_probe_duplicate) != 0;
}
static int check_integer_allocation(void) {
    xmlSchemaTypePtr type = xmlSchemaGetBuiltInType(XML_SCHEMAS_INT);
    int result;
    if (type == NULL) {
        return 1;
    }
    value_probe_failures = 0;
    value_probe_attempts = 0;
    value_probe_fail_at = 1;
    value_probe_armed = 1;
    result = xmlSchemaValidatePredefinedType(type, BAD_CAST "17", NULL);
    value_probe_armed = 0;
    /* Older or optimized implementations can validate without allocating.
     * No injected failure then means that this valid input must succeed. */
    return (value_probe_failures != 0 ? result != -1 : result != 0) ||
        xmlSchemaValidatePredefinedType(type, BAD_CAST "17", NULL) != 0 ||
        xmlSchemaValidatePredefinedType(type, BAD_CAST "invalid", NULL) <= 0;
}

static int check_value_allocation(void) {
    static const xmlSchemaValType types[] = {
        XML_SCHEMAS_ANYSIMPLETYPE, XML_SCHEMAS_STRING, XML_SCHEMAS_NORMSTRING,
        XML_SCHEMAS_TOKEN, XML_SCHEMAS_NCNAME, XML_SCHEMAS_ANYURI
    };
    size_t index;
    if (check_integer_allocation()) {
        return 1;
    }
    for (index = 0; index < sizeof(types) / sizeof(types[0]); ++index) {
        xmlSchemaTypePtr type = xmlSchemaGetBuiltInType(types[index]);
        unsigned int count = 0, fault;
        if (type == NULL) {
            return 1;
        }
        for (fault = 0; fault <= count; ++fault) {
            xmlSchemaValPtr value = NULL;
            int result, failed;
            value_probe_failures = 0;
            value_probe_attempts = 0;
            value_probe_fail_at = fault;
            value_probe_armed = 1;
            result = xmlSchemaValPredefTypeNodeNoNorm(type, BAD_CAST "part", &value, NULL);
            value_probe_armed = 0;
            if (fault == 0) {
                count = value_probe_attempts;
                failed = result != 0 || value == NULL;
            } else {
                failed = value_probe_failures == 0 || result != -1 || value != NULL;
            }
            xmlSchemaFreeValue(value);
            if (failed) {
                return 1;
            }
        }
    }
    return 0;
}
