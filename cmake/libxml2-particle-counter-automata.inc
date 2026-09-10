/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Private schema-to-automaton exact occurrence bridge. Counter arrays own bounds.
 */
XML_HIDDEN int
xmlAutomataSetExactCounter(xmlAutomata *automaton, int counter, const char *minimum,
                           const char *maximum, int firstEmitted, int nullable);

int
xmlAutomataSetExactCounter(xmlAutomata *automaton, int counter, const char *minimum,
                           const char *maximum, int firstEmitted, int nullable) {
    xmlRegCountBounds *bounds;
    int low, high;
    if (automaton == NULL || counter < 0 || counter >= automaton->nbCounters
            || !(automaton->flags & AM_AUTOMATA_SCHEMA) || automaton->counters[counter].exact != NULL) {
        return -1;
    }
    bounds = xmlRegCountNewBounds(minimum, maximum, firstEmitted, nullable);
    if (bounds == NULL) {
        xmlRegexpErrMemory(automaton);
        return -1;
    }
    if (!bounds->unbounded && xmlRegCountAsInt(bounds->digits, bounds->size, &low) == 0
            && xmlRegCountAsInt(bounds->digits + bounds->size, bounds->size, &high) == 0) {
        automaton->counters[counter].min = low;
        automaton->counters[counter].max = high;
        xmlFree(bounds);
        return 0;
    }
    if (bounds->size > SIZE_MAX / (2 * sizeof(uint32_t))
            || automaton->wideCountSize > SIZE_MAX / (2 * sizeof(uint32_t)) - bounds->size) {
        xmlFree(bounds);
        xmlRegexpErrMemory(automaton);
        return -1;
    }
    bounds->offset = automaton->wideCountSize;
    automaton->wideCountSize += bounds->size;
    automaton->counters[counter].exact = bounds;
    return 0;
}

static int
xmlRegCounterCanIncrement(xmlRegExecCtxtPtr execution, int index, int error) {
    const xmlRegCounter *counter = &execution->comp->counters[index];
    if (counter->exact != NULL) {
        const uint32_t *values = error ? execution->errWideCounts : execution->wideCounts;
        return xmlRegCountCanIncrement(counter->exact, values + counter->exact->offset);
    }
    return (error ? execution->errCounts : execution->counts)[index] < counter->max;
}

static int
xmlRegCounterInRange(xmlRegExecCtxtPtr execution, int index) {
    const xmlRegCounter *counter = &execution->comp->counters[index];
    if (counter->exact != NULL) {
        return xmlRegCountInRange(counter->exact, execution->wideCounts + counter->exact->offset);
    }
    return execution->counts[index] >= counter->min && execution->counts[index] <= counter->max;
}

static int
xmlRegCounterIncrement(xmlRegExecCtxtPtr execution, int index) {
    const xmlRegCounter *counter = &execution->comp->counters[index];
    if (counter->exact != NULL) {
        return xmlRegCountIncrement(counter->exact, execution->wideCounts + counter->exact->offset);
    }
    ++execution->counts[index];
    return 0;
}

static void
xmlRegCounterReset(xmlRegExecCtxtPtr execution, int index) {
    const xmlRegCounter *counter = &execution->comp->counters[index];
    execution->counts[index] = 0;
    if (counter->exact != NULL) {
        memset(execution->wideCounts + counter->exact->offset, 0, counter->exact->size * sizeof(uint32_t));
    }
}

static size_t
xmlRegCounterStorageSize(const xmlRegexp *compiled, int mainStorage) {
    size_t normalSlots = (compiled->flags & AM_AUTOMATA_SCHEMA) ? 2 : 1;
    size_t wideSlots = mainStorage ? 2 : 1;
    size_t bytes;
    if (mainStorage) {
        ++normalSlots;
    }
    if ((size_t)compiled->nbCounters > SIZE_MAX / (sizeof(int) * normalSlots)) {
        return 0;
    }
    bytes = (size_t)compiled->nbCounters * sizeof(int) * normalSlots;
    if (compiled->wideCountSize > (SIZE_MAX - bytes) / (sizeof(uint32_t) * wideSlots)) {
        return 0;
    }
    return bytes + compiled->wideCountSize * sizeof(uint32_t) * wideSlots;
}
