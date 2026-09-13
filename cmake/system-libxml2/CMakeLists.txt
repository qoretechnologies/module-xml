# Copyright (C) 2026 Qore Technologies, s.r.o.
find_package(LibXml2 QUIET)
if(NOT LIBXML2_FOUND)
    message(STATUS "XML module: no system libxml2 found")
    return()
endif()
if(CMAKE_CROSSCOMPILING AND NOT CMAKE_CROSSCOMPILING_EMULATOR)
    message(STATUS "XML module: cannot verify system libxml2 without a cross-compiling emulator")
    return()
endif()

unset(_qore_xml_namespace_run CACHE)
unset(_qore_xml_namespace_compiled CACHE)
try_run(_qore_xml_namespace_run _qore_xml_namespace_compiled
    "${CMAKE_CURRENT_BINARY_DIR}/namespace-probe"
    "${CMAKE_CURRENT_LIST_DIR}/../libxml2-namespace-probe.c"
    LINK_LIBRARIES LibXml2::LibXml2 ${QORE_XML_PROBE_LIBRARIES}
    RUN_OUTPUT_VARIABLE _qore_xml_namespace_output
    COMPILE_OUTPUT_VARIABLE _qore_xml_namespace_compile_output)
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/namespace-probe.log"
    "${_qore_xml_namespace_compile_output}\n${_qore_xml_namespace_output}")
if(_qore_xml_namespace_compiled AND "${_qore_xml_namespace_run}" STREQUAL "0")
    add_library(qore_xml_system_libxml2 INTERFACE)
    target_link_libraries(qore_xml_system_libxml2 INTERFACE LibXml2::LibXml2)
    set(QORE_XML_CHECK_LIBRARIES "${LIBXML2_LIBRARIES}" PARENT_SCOPE)
    set(QORE_XML_CHECK_INCLUDES "${LIBXML2_INCLUDE_DIRS}" PARENT_SCOPE)
    message(STATUS "XML module: system libxml2 ${LIBXML2_VERSION_STRING} passes namespace identity probe")
else()
    message(STATUS "XML module: system libxml2 ${LIBXML2_VERSION_STRING} failed namespace identity probe "
        "(compile=${_qore_xml_namespace_compiled}, run=${_qore_xml_namespace_run}); see "
        "${CMAKE_CURRENT_BINARY_DIR}/namespace-probe.log")
endif()
