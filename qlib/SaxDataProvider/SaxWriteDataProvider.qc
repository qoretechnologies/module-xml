# -*- mode: qore; indent-tabs-mode: nil -*-

/*  SaxWriteDataProvider.qc Copyright 2012 - 2026 Qore Technologies, s.r.o.

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

#! The main namespace for the SaxDataProvider module
public namespace SaxDataProvider {

#! Provides a data provider for writing XML files from records
/** Records are accumulated as child elements under a configurable root element.
    The XML is written when commit() is called or the provider is destroyed.
*/
public class SaxWriteDataProvider inherits DataProvider::AbstractDataProvider {
    public {
        #! Provider info
        const ProviderInfo = <DataProviderInfo>{
            "name": "saxwrite",
            "desc": "XML SAX data writer; writes records as XML elements to a file or stream",
            "type": "SaxWriteDataProvider",
            "supports_read": False,
            "supports_create": True,
            "supports_update": False,
            "supports_delete": False,
            "supports_request": False,
            "has_record": True,
            "constructor_options": ConstructorOptions,
        };

        #! Constructor options
        const ConstructorOptions = {
            "path": <DataProviderOptionInfo>{
                "display_name": "File Path",
                "short_desc": "Path to output XML file",
                "type": AbstractDataProviderType::get(StringType),
                "desc": "The output file location; mutually exclusive with `stream`. "
                    "Resolved with a call to "
                    "`FileLocationHandler::getOutputStreamForLocation()`",
                "example_value": "/data/output.xml",
            },
            "stream": <DataProviderOptionInfo>{
                "display_name": "Output Stream",
                "short_desc": "An output stream for XML data",
                "type": AbstractDataProviderType::get(new Type("OutputStream")),
                "desc": "An output stream for XML data; mutually exclusive with `path`",
            },
            "root_element_name": <DataProviderOptionInfo>{
                "display_name": "Root Element Name",
                "short_desc": "The name of the root XML element",
                "type": AbstractDataProviderTypeMap."string",
                "desc": "The name of the root XML element that wraps all records",
                "default_value": "records",
                "example_value": "records",
            },
            "element_name": <DataProviderOptionInfo>{
                "display_name": "Record Element Name",
                "short_desc": "The name of each record XML element",
                "type": AbstractDataProviderTypeMap."string",
                "desc": "The name of the XML element used for each record",
                "default_value": "record",
                "example_value": "record",
            },
            "encoding": <DataProviderOptionInfo>{
                "display_name": "Character Encoding",
                "short_desc": "The character encoding for the output XML",
                "type": AbstractDataProviderTypeMap."string",
                "desc": "The character encoding for the output XML",
                "default_value": "UTF-8",
            },
        };
    }

    private {
        #! options
        *string path;
        *OutputStream stream;
        string root_element_name;
        string element_name;
        string encoding;

        #! accumulated records
        list<hash<auto>> records = ();
    }

    #! Creates the object from constructor options
    constructor(*hash<auto> options) {
        *hash<auto> copts = checkOptions("CONSTRUCTOR-ERROR", ConstructorOptions, options);
        if (exists copts.path && exists copts.stream) {
            error("CONSTRUCTOR-ERROR", "options `path` and `stream` are mutually exclusive; "
                "provide one or the other, not both");
        }
        path = copts.path;
        stream = copts.stream;
        root_element_name = copts.root_element_name ?? "records";
        element_name = copts.element_name ?? "record";
        encoding = copts.encoding ?? "UTF-8";
    }

    #! Returns the object name
    string getName() {
        return path ?? "saxwrite";
    }

    #! Returns the description
    *string getDesc() {
        if (path) {
            return sprintf("XML writer for `%s`", path);
        }
        if (stream) {
            return "XML writer for output stream";
        }
        return "XML writer";
    }

    #! Adds a record to the write buffer
    private *hash<auto> createRecordImpl(hash<auto> rec, *hash<auto> create_options) {
        push records, rec;
        return rec;
    }

    #! Writes accumulated records as XML to the output destination
    commit() {
        binary data = getData();
        if (path) {
            OutputStreamWrapper os = FileLocationHandler::getOutputStreamForLocation(path);
            on_exit {
                os.close();
                os.waitForIo();
            }
            os.write(data);
        } else if (stream) {
            stream.write(data);
        }
    }

    #! Returns the accumulated XML as binary data
    binary getData() {
        hash<auto> xml_hash = {
            root_element_name: {element_name: records},
        };
        return binary(make_xml(xml_hash, XGF_ADD_FORMATTING));
    }

    #! Returns data provider static info
    private hash<DataProviderInfo> getStaticInfoImpl() {
        return ProviderInfo;
    }
}

}
