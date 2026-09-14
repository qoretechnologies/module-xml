# Copyright (C) 2026 Qore Technologies, s.r.o.
# Use the installed dependency only when its namespace identity behavior is correct.
include_guard(GLOBAL)
set(_qore_xml_libxml2_cmake_dir "${CMAKE_CURRENT_LIST_DIR}")

# The behavior probe changes the floating-point environment directly. A shared
# libxml2 dependency does not supply its own libm link flags to that executable.
set(QORE_XML_PROBE_LIBRARIES "")
if(UNIX)
    list(APPEND QORE_XML_PROBE_LIBRARIES m)
endif()

set(QORE_XML_LIBXML2_PROVIDER AUTO CACHE STRING "libxml2 provider: AUTO, SYSTEM, or BUNDLED")
set_property(CACHE QORE_XML_LIBXML2_PROVIDER PROPERTY STRINGS AUTO SYSTEM BUNDLED)
if(NOT QORE_XML_LIBXML2_PROVIDER MATCHES "^(AUTO|SYSTEM|BUNDLED)$")
    message(FATAL_ERROR "QORE_XML_LIBXML2_PROVIDER must be AUTO, SYSTEM, or BUNDLED")
endif()

if(NOT QORE_XML_LIBXML2_PROVIDER STREQUAL "BUNDLED")
    # Keep FindLibXml2's imported target in its own directory, so the fetched
    # project's alias cannot collide with it when the installed library fails.
    add_subdirectory("${CMAKE_CURRENT_LIST_DIR}/system-libxml2"
        "${CMAKE_CURRENT_BINARY_DIR}/system-libxml2")
endif()

if(TARGET qore_xml_system_libxml2)
    set(QORE_XML_LIBXML2_TARGET qore_xml_system_libxml2)
    set(QORE_XML_BUNDLED_LIBXML2 FALSE)
elseif(QORE_XML_LIBXML2_PROVIDER STREQUAL "SYSTEM")
    message(FATAL_ERROR "System libxml2 is missing, unusable, or failed the namespace identity probe. "
        "Install a fixed libxml2 or use QORE_XML_LIBXML2_PROVIDER=AUTO/BUNDLED. "
        "Cross builds need CMAKE_CROSSCOMPILING_EMULATOR to verify the system library.")
else()
    # Enable C++ before FetchContent creates libxml2's directory scope. Its
    # private IEEE conversion unit needs the standard C++17 charconv runtime.
    enable_language(CXX)
    include(FetchContent)
    if(POLICY CMP0135)
        cmake_policy(SET CMP0135 NEW)
    endif()
    # Latest stable release verified on 2026-09-08. Never resolve a floating tag
    # during configure: the same source checkout must fetch the same archive.
    FetchContent_Declare(qore_xml_libxml2
        URL https://download.gnome.org/sources/libxml2/2.15/libxml2-2.15.4.tar.xz
        URL_HASH SHA256=98087fd181d9070724f3fbc65c7377db03038eb92bd882374daff44940138821
        TLS_VERIFY TRUE)

    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2CatalogFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2QNameFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2UriFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2EntityFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2OccursFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2ParticleIdentityFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2ParticleAttributionFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2ParticleCounterFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2ParticleRangeFix.cmake")

    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2TypeFinalFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2ElementSubstitutionFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2ElementConsistencyFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2WildcardIdFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2WildcardTypeFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2SchemaWhitespaceFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2CharacterContentFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2FixedValueFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2TimeValueFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2ValueAllocationFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2ParticleLayoutFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2IdBindingFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2NumericDefaultsFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2IeeeFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2CalendarFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2ElementDefaultsFix.cmake")

    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2NotationFix.cmake")

    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2AnnotationFix.cmake")
    include("${_qore_xml_libxml2_cmake_dir}/QoreXmlLibXml2IdentityPathFix.cmake")

    function(qore_xml_fetch_libxml2)
        # Normal variables are scoped to this function; do not overwrite the
        # caller's BUILD_SHARED_LIBS or any other project's cache options.
        set(BUILD_SHARED_LIBS OFF)
        set(LIBXML2_WITH_PROGRAMS OFF)
        set(LIBXML2_WITH_TESTS OFF)
        set(LIBXML2_WITH_DOCS OFF)
        set(LIBXML2_WITH_PYTHON OFF)
        set(LIBXML2_WITH_LEGACY ON)
        set(LIBXML2_WITH_ZLIB ON)
        set(LIBXML2_WITH_ICONV ON)
        set(LIBXML2_WITH_THREADS ON)
        set(LIBXML2_WITH_OUTPUT ON)
        set(LIBXML2_WITH_PUSH ON)
        set(LIBXML2_WITH_PATTERN ON)
        set(LIBXML2_WITH_REGEXPS ON)
        set(LIBXML2_WITH_READER ON)
        set(LIBXML2_WITH_WRITER ON)
        set(LIBXML2_WITH_SCHEMAS ON)
        set(LIBXML2_WITH_RELAXNG ON)
        set(LIBXML2_WITH_HTML ON)
        set(LIBXML2_WITH_SAX1 ON)
        set(LIBXML2_WITH_XPATH ON)
        FetchContent_MakeAvailable(qore_xml_libxml2)
        file(STRINGS "${qore_xml_libxml2_BINARY_DIR}/libxml/xmlversion.h" _qore_xml_version
            REGEX "^#define LIBXML_DOTTED_VERSION ")
        if(NOT _qore_xml_version STREQUAL "#define LIBXML_DOTTED_VERSION \"2.15.4\"")
            message(FATAL_ERROR "The libxml2 source override must provide pinned version 2.15.4")
        endif()
        qore_xml_fix_libxml2_catalog("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_qnames("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_uris("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_entities("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_occurs("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_particle_identity("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_particle_attribution("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_particle_counters("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_particle_ranges("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_type_finals("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_element_substitution("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_element_consistency("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_wildcard_ids("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_wildcard_types("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_schema_whitespace("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_character_content("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_fixed_values("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_time_values("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_value_allocation("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_particle_layout("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_id_bindings("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_numeric_defaults("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_ieee("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_calendar("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_element_defaults("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_notations("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_annotations("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        qore_xml_fix_libxml2_identity_paths("${qore_xml_libxml2_SOURCE_DIR}" "${qore_xml_libxml2_BINARY_DIR}")
        # Neither upstream tools nor headers/libraries belong in our install.
        set_property(DIRECTORY "${qore_xml_libxml2_SOURCE_DIR}" PROPERTY EXCLUDE_FROM_ALL TRUE)
        set_target_properties(LibXml2 PROPERTIES POSITION_INDEPENDENT_CODE ON C_VISIBILITY_PRESET hidden)
        set(QORE_XML_CHECK_INCLUDES
            "${qore_xml_libxml2_BINARY_DIR};${qore_xml_libxml2_SOURCE_DIR}/include" PARENT_SCOPE)
    endfunction()
    qore_xml_fetch_libxml2()
    set(QORE_XML_LIBXML2_TARGET LibXml2)
    set(QORE_XML_CHECK_LIBRARIES "")
    set(QORE_XML_BUNDLED_LIBXML2 TRUE)
    include(GNUInstallDirs)
    install(FILES "${_qore_xml_libxml2_cmake_dir}/libxml2-NOTICES.txt"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/licenses/qore-xml")
    message(STATUS "XML module: using private static libxml2 2.15.4 (FetchContent)")
endif()
