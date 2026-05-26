# -*- mode: qore; indent-tabs-mode: nil -*-
#! Qore CdaDataProvider factory definition

/*  CdaDataProviderFactory.qc Copyright 2026 Qore Technologies, s.r.o.

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
*/

#! contains all public definitions in the CdaDataProvider module
public namespace CdaDataProvider {
#! The CDA data provider factory
public class CdaDataProviderFactory inherits AbstractDataProviderFactory {
    private {
        static Class cls = new Class("CdaDataProvider");

        const FactoryInfo = <DataProviderFactoryInfo>{
            "name": CdaDataProvider::FactoryName,
            "desc": "CDA document data provider factory",
            "children_can_support_apis": True,
        };
    }

    private hash<DataProviderFactoryInfo> getInfoImpl() {
        return FactoryInfo;
    }

    private hash<DataProviderInfo> getProviderInfoImpl() {
        return CdaDataProvider::ProviderInfo;
    }

    private Class getClassImpl() {
        return cls;
    }
}
}
