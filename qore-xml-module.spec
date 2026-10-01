# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
# Use the pinned source epoch for RPM headers and installed file timestamps.
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
%bcond_without tests
%bcond_without docs
Name: qore-xml-module
Version: 2.3.0
Release: 1%{?dist}
Summary: XML, SOAP and WebDAV integration for Qore
License: (LGPL-2.1-or-later OR MIT) AND MIT
URL: https://github.com/qoretechnologies/module-xml
Source0: %{name}-%{version}.tar.xz
Source1: libxml2-2.15.4.tar.xz
Provides: bundled(libxml2) = 2.15.4
Provides: bundled(fast_float) = 8.3.0
%global _find_debuginfo_dwz_opts %{nil}
BuildRequires: cmake >= 3.18
BuildRequires: make
BuildRequires: gcc-c++
BuildRequires: pkgconfig(openssl)
BuildRequires: pkgconfig(zlib)
BuildRequires: patch
BuildRequires: qore-uuid-module
%if %{with tests}
BuildRequires: python3
BuildRequires: litmus >= 0.18
BuildRequires: qore-process-module >= 2.1.0
BuildRequires: qore-misc-tools >= 3.0.0~
%endif
BuildRequires: qore-devel >= 3.0.0~
BuildRequires: qore-rpm-macros >= 3.0.0~
%if %{with docs}
BuildRequires: doxygen
%if 0%{?suse_version}
BuildRequires: util-linux
%else
BuildRequires: util-linux-core
%endif
%endif
%{?qore_enable_aot_post}

%description
XML parsing, generation and validation, WSDL/SOAP, XML-RPC and WebDAV.
Includes source and compiled modules, compiler metadata, provider resources,
translations and command-line tools. Uses a private patched XML parser.

%if %{with docs}
%package doc
Summary: XML and web service module reference documentation
BuildArch: noarch
%description doc
Native and user-module API references, tutorials and web service examples.
%endif

%prep
%autosetup -a 1
%build
%{?set_build_flags}
. %{_rpmconfigdir}/qore/module-env.sh
qore_set_source_prefix_maps "%{qore_debug_source_dir}"
cmake -S . -B build -G 'Unix Makefiles' \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS_RELEASE=-DNDEBUG \
  -DCMAKE_INSTALL_PREFIX=%{_prefix} -DCMAKE_INSTALL_LIBDIR=%{_lib} \
  -DCMAKE_SKIP_RPATH=ON -DCMAKE_IGNORE_PREFIX_PATH=/usr/local \
  -DQore_DIR=%{_libdir}/cmake/Qore -DQORE_EXECUTABLE=/usr/bin/qore \
  -DQORE_QPP_EXECUTABLE=/usr/bin/qpp -DQORE_QCC_EXECUTABLE=/usr/bin/qcc \
  -DQORE_XML_LIBXML2_PROVIDER=BUNDLED \
  -DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2:PATH=$PWD/libxml2-2.15.4 \
  -DFETCHCONTENT_FULLY_DISCONNECTED=ON \
  -DQORE_BUILD_AOT_MODULES=ON -DQORE_AOT_LINK_SOURCE_MODULES=OFF \
  -DQORE_XML_STRICT_DOCS=ON \
  -DQORE_GENERATE_JAVA_BINDINGS=OFF \
  -DQORE_QM_METADATA_ENV:STRING="QORE_MODULE_DIR=$QORE_MODULE_DIR:$PWD/qlib;QORE_MODULE_DIR_ONLY=1;QORE_INCLUDE_DIR=;LD_LIBRARY_PATH=" \
  -DCMAKE_DISABLE_FIND_PACKAGE_Doxygen=%{!?with_docs:ON}%{?with_docs:OFF}
cmake --build build -- %{?_smp_mflags}
%if %{with docs}
cmake --build build --target docs -- %{?_smp_mflags}
%endif
%install
DESTDIR=%{buildroot} cmake --install build
for command in soaputil webdav-server; do
    sed -i '1s|.*|#!/usr/bin/qore|' %{buildroot}%{_bindir}/$command
    install -Dm644 debian/man/$command.1 %{buildroot}%{_mandir}/man1/$command.1
done
%qore_install_aot_sources qlib
find %{buildroot}%{_libdir}/qore-modules -type f -name '*.qmod' -exec chmod 755 {} +
%if %{with docs}
install -d %{buildroot}%{_docdir}/%{name}-doc
cp -a build/docs %{buildroot}%{_docdir}/%{name}-doc/
hardlink -t -O %{buildroot}%{_docdir}/%{name}-doc
%endif
%check
%if %{with tests}
. %{_rpmconfigdir}/qore/module-env.sh
python3 -B -W error debian/tests/test_aot_metadata.py
python3 -B -W error test/cmake/test_libxml2_occurrence_flow.py \
  build/_deps/qore_xml_libxml2-build/qore-name-edition-fix/xmlschemas.c -v
cmake --build build --parallel %{_smp_build_ncpus} --target \
  qore-xml-namespace-probe qore-xml-float-test qore-xml-uri-allocation qore-xml-entity-allocation
build/qore-xml-namespace-probe
build/qore-xml-float-test
build/qore-xml-uri-allocation
build/qore-xml-entity-allocation
python3 -B -W error rpm/run-tests.py --build-dir "$PWD/build"
qore-data-provider-i18n --no-color --check-source-tree --require-standard-locales \
  --require-complete-locales --output "$PWD/qlib"
%endif
%files
%license COPYING.MIT COPYING.LGPL cmake/third-party/fast_float/LICENSE-MIT
%license %{_datadir}/licenses/qore-xml/
%doc README
%{_bindir}/soaputil
%{_bindir}/webdav-server
%{_mandir}/man1/soaputil.1*
%{_mandir}/man1/webdav-server.1*
%{_libdir}/qore-modules/*
%{_datadir}/qore-modules/*
%dir %{_datadir}/qore/metadata/xml
%{_datadir}/qore/metadata/xml/*.meta.json
%{_datadir}/qore/i18n/
%if %{with docs}
%files doc
%license COPYING.MIT COPYING.LGPL
%doc %{_docdir}/%{name}-doc/
%endif
%changelog
* Thu Oct 01 2026 David Nichols <david@qore.org> - 2.3.0-1
- Package native and compiled XML modules with verified private parser sources.
- Require complete offline suites, WebDAV compliance and native regression probes.
