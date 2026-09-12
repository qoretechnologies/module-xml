/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Shared private particle layout for libxml2 schema parsing and builtin types.
 * Included after each translation unit's xmlSchemaTreeItem declarations.
 */
#ifndef QORE_XML_SCHEMA_PARTICLE_LAYOUT_H
#define QORE_XML_SCHEMA_PARTICLE_LAYOUT_H

typedef struct _xmlSchemaParticle xmlSchemaParticle;
typedef xmlSchemaParticle *xmlSchemaParticlePtr;
struct _xmlSchemaParticle {
    xmlSchemaTypeType type;
    xmlSchemaAnnotPtr annot;
    xmlSchemaTreeItemPtr next;
    xmlSchemaTreeItemPtr children;
    int minOccurs;
    int maxOccurs;
    xmlNodePtr node;
    xmlSchemaParticlePtr countSource; /* Borrowed original occurrence source. */
    int termNullable; /* Intrinsic term can match an empty sequence. */
    int maxFinite; /* Numeric maximum is distinct from the unbounded sentinel. */
    int isBuiltin; /* Immutable shared particle initialized with the builtin types. */
};

#endif
