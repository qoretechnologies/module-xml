moddir = $(userlibdir)

AUTOMAKE_OPTIONS = foreign

SUBDIRS = src

noinst_HEADERS = src/QC_XmlDoc.h \
	src/XsdFloat.h \
	src/QC_XmlNode.h \
	src/QC_XmlReader.h \
	src/QC_XmlRpcClient.h \
	src/QC_SaxIterator.h \
	src/QoreXPath.h \
	src/QoreXmlDoc.h \
	src/QoreXmlReader.h \
	src/QoreXmlRpcReader.h \
	src/ql_xml.h \
	src/qore-xml-module.h \
	src/MakeXmlOpts.h \
    src/QC_AbstractXmlIoInputCallback.h

USER_MODULES = qlib/XmlRpcHandler.qm qlib/WSDL.qm qlib/SoapClient.qm qlib/SoapHandler.qm qlib/XmlRpcConnection.qm \
    qlib/SalesforceSoapClient.qm qlib/WebDavClient.qm

USER_SPLIT_MODULES = qlib/SoapClientIo qlib/XmlRpcClientIo qlib/SaxDataProvider qlib/SoapDataProvider qlib/CargoXmlDataProvider qlib/CdaDataProvider qlib/WebDavClientDataProvider qlib/WebDavClientIo qlib/WebDavHandler

SaxDataProvider_moddir= $(moddir)/SaxDataProvider
dist_SaxDataProvider_mod_DATA = $(wildcard qlib/SaxDataProvider*.q[cm])

SoapDataProvider_moddir= $(moddir)/SoapDataProvider
dist_SoapDataProvider_mod_DATA = $(wildcard qlib/SoapDataProvider/*.q[cm])

CargoXmlDataProvider_moddir = $(moddir)/CargoXmlDataProvider
dist_CargoXmlDataProvider_mod_DATA = $(wildcard qlib/CargoXmlDataProvider/*.q[cm]) $(wildcard qlib/CargoXmlDataProvider/*.svg)

CdaDataProvider_moddir = $(moddir)/CdaDataProvider
dist_CdaDataProvider_mod_DATA = $(wildcard qlib/CdaDataProvider/*.q[cm]) $(wildcard qlib/CdaDataProvider/*.svg)

# bundled UN/CEFACT D25A schema tree (data/standard, codelist/standard, identifierlist/standard)
CargoXmlDataProvider_data_moddir = $(moddir)/CargoXmlDataProvider/schemas/uncefact-D25A/data/standard
dist_CargoXmlDataProvider_data_mod_DATA = $(wildcard qlib/CargoXmlDataProvider/schemas/uncefact-D25A/data/standard/*.xsd)
CargoXmlDataProvider_codelist_moddir = $(moddir)/CargoXmlDataProvider/schemas/uncefact-D25A/codelist/standard
dist_CargoXmlDataProvider_codelist_mod_DATA = $(wildcard qlib/CargoXmlDataProvider/schemas/uncefact-D25A/codelist/standard/*.xsd)
CargoXmlDataProvider_idlist_moddir = $(moddir)/CargoXmlDataProvider/schemas/uncefact-D25A/identifierlist/standard
dist_CargoXmlDataProvider_idlist_mod_DATA = $(wildcard qlib/CargoXmlDataProvider/schemas/uncefact-D25A/identifierlist/standard/*.xsd)

WebDavClientDataProvider_moddir= $(moddir)/WebDavClientDataProvider
dist_WebDavClientDataProvider_mod_DATA = $(wildcard qlib/WebDavClientDataProvider/*.q[cm])

WebDavClientIo_moddir = $(moddir)/WebDavClientIo
dist_WebDavClientIo_mod_DATA = $(wildcard qlib/WebDavClientIo/*.q[cm])

SoapClientIo_moddir = $(moddir)/SoapClientIo
dist_SoapClientIo_mod_DATA = $(wildcard qlib/SoapClientIo/*.q[cm])

XmlRpcClientIo_moddir = $(moddir)/XmlRpcClientIo
dist_XmlRpcClientIo_mod_DATA = $(wildcard qlib/XmlRpcClientIo/*.q[cm])

WebDavHandler_moddir= $(moddir)/WebDavHandler
dist_WebDavHandler_mod_DATA = $(wildcard qlib/WebDavHandler/*.q[cm])

EXTRA_DIST = COPYING.LGPL COPYING.MIT AUTHORS README \
	RELEASE-NOTES \
    CMakeLists.txt \
    cmake/QoreXmlLibXml2.cmake cmake/QoreXmlLibXml2CatalogFix.cmake cmake/QoreXmlLibXml2QNameFix.cmake \
    cmake/QoreXmlLibXml2AnyUriFix.cmake cmake/libxml2-anyuri-probe.h \
    cmake/QoreXmlLibXml2NameEditionFix.cmake cmake/libxml2-name-edition-probe.h \
    cmake/QoreXmlLibXml2UriFix.cmake cmake/QoreXmlLibXml2EntityFix.cmake \
    cmake/QoreXmlLibXml2OccursFix.cmake cmake/libxml2-occurs.inc \
    cmake/QoreXmlLibXml2ParticleAttributionFix.cmake cmake/QoreXmlLibXml2ParticleCounterFix.cmake \
    cmake/libxml2-particle-attribution-math.inc cmake/libxml2-particle-attribution-sets.inc \
    cmake/libxml2-particle-attribution-schema.inc cmake/libxml2-particle-attribution-elements.inc \
    cmake/libxml2-particle-attribution-probe.h \
    cmake/QoreXmlLibXml2TypeFinalFix.cmake cmake/libxml2-type-final-probe.h \
    cmake/QoreXmlLibXml2ElementSubstitutionFix.cmake cmake/libxml2-element-substitution-probe.h \
    cmake/QoreXmlLibXml2ElementConsistencyFix.cmake cmake/libxml2-element-consistency.inc \
    cmake/libxml2-element-consistency-probe.h \
    cmake/QoreXmlLibXml2WildcardIdFix.cmake cmake/libxml2-wildcard-id-probe.h \
    cmake/QoreXmlLibXml2WildcardTypeFix.cmake cmake/libxml2-wildcard-type-probe.h \
    cmake/QoreXmlLibXml2SchemaWhitespaceFix.cmake cmake/libxml2-schema-whitespace-probe.h \
    cmake/QoreXmlLibXml2CharacterContentFix.cmake cmake/libxml2-character-content-probe.h \
    cmake/QoreXmlLibXml2FixedValueFix.cmake \
    cmake/QoreXmlLibXml2TimeValueFix.cmake cmake/QoreXmlLibXml2ValueAllocationFix.cmake \
    cmake/libxml2-value-space-probe.h cmake/libxml2-value-allocation-probe.h \
    cmake/QoreXmlLibXml2ParticleLayoutFix.cmake cmake/libxml2-particle-layout.h \
    cmake/QoreXmlLibXml2IdBindingFix.cmake cmake/libxml2-id-binding-probe.h \
    cmake/third-party/fast_float/fast_float.h cmake/third-party/fast_float/LICENSE-MIT cmake/third-party/fast_float/README.md \
    cmake/QoreXmlLibXml2IeeeFix.cmake cmake/libxml2-ieee.cpp cmake/libxml2-ieee-validation.inc cmake/libxml2-ieee-probe.h \
    cmake/QoreXmlLibXml2CalendarFix.cmake cmake/libxml2-calendar-type.inc \
    cmake/QoreXmlLibXml2ElementDefaultsFix.cmake cmake/libxml2-qname-owned.inc \
    cmake/libxml2-default-namespace.inc cmake/libxml2-element-default.inc \
    cmake/libxml2-element-defaults-probe.h \
    cmake/QoreXmlLibXml2AnnotationFix.cmake cmake/libxml2-annotation-probe.h \
    cmake/QoreXmlLibXml2IdentityPathFix.cmake cmake/libxml2-identity-path-probe.h \
    cmake/QoreXmlLibXml2ComponentQNameFix.cmake cmake/libxml2-component-qname.inc \
    cmake/libxml2-component-qname-probe.h \
    cmake/QoreXmlLibXml2KeyNillableFix.cmake cmake/libxml2-key-nillable-probe.h \
    cmake/QoreXmlLibXml2NilIdentityFix.cmake cmake/libxml2-nil-identity-probe.h \
    cmake/QoreXmlLibXml2IdentityTableFix.cmake cmake/libxml2-identity-table-probe.h \
    cmake/libxml2-identity-tables.inc \
    cmake/QoreXmlLibXml2InstanceIdentityFix.cmake cmake/libxml2-instance-identities.inc \
    cmake/libxml2-instance-identity-probe.h \
    cmake/QoreXmlLibXml2SaxReferenceFix.cmake cmake/QoreXmlLibXml2CalendarYearGuardFix.cmake \
    cmake/QoreXmlLibXml2NotationFix.cmake cmake/libxml2-notation-parse.inc \
    cmake/libxml2-notation-use.inc cmake/libxml2-notation-probe.h \
    cmake/libxml2-calendar.inc cmake/libxml2-calendar-probe.h \
    cmake/QoreXmlLibXml2NumericDefaultsFix.cmake cmake/libxml2-numeric-defaults.inc \
    cmake/libxml2-numeric-defaults-probe.h \
    cmake/QoreXmlLibXml2ParticleRangeFix.cmake cmake/libxml2-particle-range-probe.h \
    cmake/libxml2-particle-counter-lexical.inc cmake/libxml2-particle-counter-values.inc \
    cmake/libxml2-particle-counter-automata.inc cmake/libxml2-particle-counter-schema.inc \
    cmake/QoreXmlLibXml2ParticleIdentityFix.cmake cmake/libxml2-particle-identity.inc \
    cmake/system-libxml2/CMakeLists.txt \
    cmake/libxml2-namespace-probe.c cmake/libxml2-qname-probe.h \
    cmake/libxml2-uri-probe.h cmake/libxml2-schema-uri-probe.h \
    cmake/libxml2-entity-probe.h cmake/libxml2-occurs-probe.h \
    cmake/libxml2-particle-identity-probe.h \
    cmake/libxml2-NOTICES.txt \
	src/QC_XmlDoc.qpp \
	src/QC_XmlNode.qpp \
	src/QC_XmlReader.qpp \
	src/QC_XmlRpcClient.qpp \
	src/QC_SaxIterator.qpp \
	src/QC_FileSaxIterator.qpp \
	src/QC_InputStreamSaxIterator.qpp \
	src/ql_xml.qpp \
	src/qc_option.qpp \
	src/MakeXmlOpts.qpp \
    src/QC_AbstractXmlIoInputCallback.qpp \
	test/ \
	examples/ \
    docs/mainpage.doxygen.tmpl \
    docs/footer_template.html \
	$(USER_MODULES) \
    ${USER_SPLIT_MODULES} \
	qore-xml-module.spec

ACLOCAL_AMFLAGS=-I m4

dist_mod_DATA = $(USER_MODULES)
dist_bin_SCRIPTS = bin/soaputil bin/webdav-server

if COND_DOXYGEN
USER_MODS = $(basename $(notdir $(USER_MODULES)))
USER_SPLIT_MODS = $(basename $(notdir $(USER_SPLIT_MODULES)))
DOXYGEN_OUTPUT = docs/xml/html $(addprefix docs/,$(addsuffix /html,$(USER_MODS) $(USER_SPLIT_MODS)))
DOXYFILES = docs/doxyfile docs/mainpage.doxygen
DOXYFILES_SRC = docs/doxyfile.tmpl docs/qlib/Doxyfile.tmpl docs/footer_template.html
TMP_MOD_TARG = docs/qlib/XmlRpcHandler.qm.dox.h docs/qlib/Doxyfile.XmlRpcHandler \
	docs/qlib/SoapClient.qm.dox.h docs/qlib/Doxyfile.SoapClient \
	docs/qlib/SoapHandler.qm.dox.h docs/qlib/Doxyfile.SoapHandler \
	docs/qlib/WSDL.qm.dox.h docs/qlib/Doxyfile.WSDL \
	docs/qlib/SalesforceSoapClient.qm.dox.h docs/qlib/Doxyfile.SalesforceSoapClient \
	docs/qlib/WebDavClient.qm.dox.h docs/qlib/Doxyfile.WebDavClient \
	docs/qlib/XmlRpcConnection.qm.dox.h
QLIB_TMP_DOXYFILES = $(TMP_MOD_TARG) $(addsuffix .tag,$(USER_MODS) $(USER_SPLIT_MODS))
QDX = qdx

DOXYFILE_SPLIT_TARG = $(addprefix docs/qlib/Doxyfile.,$(USER_SPLIT_MODS))
$(DOXYFILE_SPLIT_TARG): docs/qlib/Doxyfile.%: docs/qlib/Doxyfile.tmp $(QDX_DEP)
	$(QDX) -M=qlib/$*:qlib/$*.qm -txml.tag=../../xml/html -tWSDL.tag=../../WSDL/html $< $@

TMP_MOD_SPLIT_TARG = $(addprefix docs/qlib/,$(addsuffix .qm,$(USER_SPLIT_MODS)))
$(TMP_MOD_SPLIT_TARG): docs/qlib/%.qm: qlib/% $(QDX_DEP)
	$(QDX) $< $@

TMP_MOD_HTML_TARG = $(addsuffix /html,$(addprefix docs/,$(USER_SPLIT_MODS)))
$(TMP_MOD_HTML_TARG): docs/%/html: docs/qlib/%.qm docs/qlib/Doxyfile.%
	$(MKDIR_P) $@
	cd docs; $(DOXYGEN_CMD) qlib/Doxyfile.$*
	$(QDX) --post $@ $@/search

DX_CLEANFILES = ${DOXYFILES} $(QLIB_TMP_DOXYFILES) $(DOXYFILE_SPLIT_TARG) docs/qlib/Doxyfile.tmp

docs/qlib/Doxyfile.tmp: docs/qlib/Doxyfile.tmpl
	sed s:__USERMODDIR__:${usermoddir}: $< > $@

docs/qlib/Doxyfile.SoapClient: docs/qlib/Doxyfile.tmp
	$(QDX) -M=qlib/SoapClient.qm:qlib/SoapClient.qm.dox.h -txml.tag=../../xml/html -tWSDL.tag=../../WSDL/html $< $@

docs/qlib/SoapClient.qm.dox.h: qlib/SoapClient.qm
	$(QDX) $< $@

docs/SoapClient/html: docs/qlib/SoapClient.qm.dox.h docs/qlib/Doxyfile.SoapClient
	cd docs; $(DOXYGEN_CMD) qlib/Doxyfile.SoapClient
	$(QDX) --post docs/SoapClient/html docs/SoapClient/html/search

docs/qlib/Doxyfile.SalesforceSoapClient: docs/qlib/Doxyfile.tmp
	$(QDX) -M=qlib/SalesforceSoapClient.qm:qlib/SalesforceSoapClient.qm.dox.h -txml.tag=../../xml/html -tWSDL.tag=../../WSDL/html -tSoapClient.tag=../../SoapClient/html $< $@

docs/qlib/SalesforceSoapClient.qm.dox.h: qlib/SalesforceSoapClient.qm
	$(QDX) $< $@

docs/SalesforceSoapClient/html: docs/qlib/SalesforceSoapClient.qm.dox.h docs/qlib/Doxyfile.SalesforceSoapClient
	cd docs; $(DOXYGEN_CMD) qlib/Doxyfile.SalesforceSoapClient
	$(QDX) --post docs/SalesforceSoapClient/html docs/SalesforceSoapClient/html/search

docs/qlib/Doxyfile.SoapHandler: docs/qlib/Doxyfile.tmp
	$(QDX) -M=qlib/SoapHandler.qm:qlib/SoapHandler.qm.dox.h -txml.tag=../../xml/html $< $@

docs/qlib/SoapHandler.qm.dox.h: qlib/SoapHandler.qm
	$(QDX) $< $@

docs/SoapHandler/html: docs/qlib/SoapHandler.qm.dox.h docs/qlib/Doxyfile.SoapHandler
	cd docs; $(DOXYGEN_CMD) qlib/Doxyfile.SoapHandler
	$(QDX) --post docs/SoapHandler/html docs/SoapHandler/html/search

docs/qlib/Doxyfile.WSDL: docs/qlib/Doxyfile.tmp
	$(QDX) -M=qlib/WSDL.qm:qlib/WSDL.qm.dox.h -txml.tag=../../xml/html $< $@

docs/qlib/WSDL.qm.dox.h: qlib/WSDL.qm
	$(QDX) $< $@

docs/WSDL/html: docs/qlib/WSDL.qm.dox.h docs/qlib/Doxyfile.WSDL
	cd docs; $(DOXYGEN_CMD) qlib/Doxyfile.WSDL
	$(QDX) --post docs/WSDL/html docs/WSDL/html/search

docs/qlib/Doxyfile.XmlRpcHandler: docs/qlib/Doxyfile.tmp
	$(QDX) -M=qlib/XmlRpcHandler.qm:qlib/XmlRpcHandler.qm.dox.h -txml.tag=../../xml/html $< $@

docs/qlib/XmlRpcHandler.qm.dox.h: qlib/XmlRpcHandler.qm
	$(QDX) $< $@

docs/XmlRpcHandler/html: docs/qlib/XmlRpcHandler.qm.dox.h docs/qlib/Doxyfile.XmlRpcHandler
	cd docs; $(DOXYGEN_CMD) qlib/Doxyfile.XmlRpcHandler
	$(QDX) --post docs/XmlRpcHandler/html docs/XmlRpcHandler/html/search

docs/qlib/Doxyfile.XmlRpcConnection: docs/qlib/Doxyfile.tmp
	$(QDX) -M=qlib/XmlRpcConnection.qm:qlib/XmlRpcConnection.qm.dox.h -txml.tag=../../xml/html $< $@

docs/qlib/XmlRpcConnection.qm.dox.h: qlib/XmlRpcConnection.qm
	$(QDX) $< $@

docs/XmlRpcConnection/html: docs/qlib/XmlRpcConnection.qm.dox.h docs/qlib/Doxyfile.XmlRpcConnection
	cd docs; $(DOXYGEN_CMD) qlib/Doxyfile.XmlRpcConnection
	$(QDX) --post docs/XmlRpcConnection/html docs/XmlRpcConnection/html/search

docs/qlib/Doxyfile.WebDavClient: docs/qlib/Doxyfile.tmp
	$(QDX) -M=qlib/WebDavClient.qm:qlib/WebDavClient.qm.dox.h -txml.tag=../../xml/html $< $@

docs/qlib/WebDavClient.qm.dox.h: qlib/WebDavClient.qm
	$(QDX) $< $@

docs/WebDavClient/html: docs/qlib/WebDavClient.qm.dox.h docs/qlib/Doxyfile.WebDavClient
	cd docs; $(DOXYGEN_CMD) qlib/Doxyfile.WebDavClient
	$(QDX) --post docs/WebDavClient/html docs/WebDavClient/html/search

docs/xml/html: $(DOXYFILES)
	cd docs; $(DOXYGEN_CMD) doxyfile;
	$(QDX) --post docs/xml/html docs/xml/search

docs/mainpage.doxygen: docs/mainpage.doxygen.tmpl
	$(QDX) -d $< $@

docs/doxyfile: docs/doxyfile.tmpl
	sed -e s/__VERSION__/${VERSION}/ -e s:__USERMODDIR__:${usermoddir}: $< > $@

doxygen-doc: $(DOXYGEN_OUTPUT)

EXTRA_DIST += $(DOXYGEN_OUTPUT)

html-local: $(DOXYGEN_OUTPUT)

install-html-local:
	for dox in xml $(USER_MODS) $(USER_SPLIT_MODS); do $(MKDIR_P) $(DESTDIR)$(datadir)/$(PACKAGE)/docs/$$dox/html/search; done
	for dir in $(DOXYGEN_OUTPUT); do \
	   for f in $$dir/*; do if [ -f $$f ]; then $(INSTALL_DATA) $$f $(DESTDIR)$(datadir)/$(PACKAGE)/$$dir; fi; done; \
	   for f in $$dir/search/*; do $(INSTALL_DATA) $$f $(DESTDIR)$(datadir)/$(PACKAGE)/$$dir/search; done; \
	done

clean-local:
	$(RM) -rf $(DOXYGEN_OUTPUT)

uninstall-local:
	$(RM) -rf $(DESTDIR)$(datadir)/$(PACKAGE)/docs

else
doxygen-doc:
	echo no doxygen support
endif

mostlyclean-local:
	rm -rf ${DOXYGEN_OUTPUT} ${DX_CLEANFILES}

libtool: $(LIBTOOL_DEPS)
	$(SHELL) ./config.status --recheck
