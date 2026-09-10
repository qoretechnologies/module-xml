/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Private schema/automaton bridge. The position key is the particle pointer
 * within its containing use, not the declaration pointer or emission count.
 * Lowering counted groups may emit one source position more than once. Such
 * emissions retain one identity; separate uses of a shared group do not.
 */
typedef struct {
    size_t id;
} xmlRegParticleIdentity;

static void
xmlRegFreeParticleIdentity(void *payload, const xmlChar *name ATTRIBUTE_UNUSED) {
    xmlFree(payload);
}

XML_HIDDEN int
xmlAutomataPushParticle(xmlAutomata *am, const void *source, size_t *parent);
XML_HIDDEN void
xmlAutomataPopParticle(xmlAutomata *am, size_t parent);

int
xmlAutomataPushParticle(xmlAutomata *am, const void *source, size_t *parent) {
    /* %p needs at most 2*sizeof(void*) hex digits plus a platform prefix;
     * a size_t needs fewer than 3*sizeof(size_t) decimal digits. */
    char key[32 + 2 * sizeof(void*) + 3 * sizeof(size_t)];
    xmlRegParticleIdentity *identity;
    int length;

    if (am == NULL) {
        return -1;
    }
    *parent = am->particle;
    length = snprintf(key, sizeof(key), "%zu:%p", am->particle, source);
    if ((length < 0) || ((size_t) length >= sizeof(key))) {
        xmlRegexpErrMemory(am);
        return -1;
    }
    if (am->particleMap == NULL) {
        am->particleMap = xmlHashCreate(0);
        if (am->particleMap == NULL) {
            xmlRegexpErrMemory(am);
            return -1;
        }
    }
    identity = xmlHashLookup(am->particleMap, BAD_CAST key);
    if (identity == NULL) {
        if (am->nbParticles == SIZE_MAX) {
            xmlRegexpErrMemory(am);
            return -1;
        }
        identity = xmlMalloc(sizeof(*identity));
        if (identity == NULL) {
            xmlRegexpErrMemory(am);
            return -1;
        }
        identity->id = am->nbParticles + 1;
        if (xmlHashAddEntry(am->particleMap, BAD_CAST key, identity) < 0) {
            xmlFree(identity);
            xmlRegexpErrMemory(am);
            return -1;
        }
        am->nbParticles = identity->id;
    }
    am->particle = identity->id;
    return 0;
}

void
xmlAutomataPopParticle(xmlAutomata *am, size_t parent) {
    if (am != NULL) {
        am->particle = parent;
    }
}
