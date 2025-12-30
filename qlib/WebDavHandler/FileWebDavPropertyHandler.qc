# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavHandler module Copyright 2019 - 2025 Qore Technologies, s.r.o.

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

%requires json

#! Main public WebDavHandler namespace
public namespace WebDavHandler {

#! A file-based property handler that persists properties to a JSON file
/** This handler stores WebDAV properties in a JSON file, allowing properties to persist
    across server restarts. The file is stored in the WebDAV base directory.
*/
public class FileWebDavPropertyHandler inherits AbstractWebDavPropertyHandler {
    private {
        #! Read-write lock for atomicity
        RWLock m_lock();

        #! Path to the properties file
        string props_file;

        #! Property cache; URL -> namespace -> property -> value
        hash<string, hash<string, hash<auto>>> m_cache = {};

        #! Debug flag
        bool debug;

        #! Dirty flag to track if cache needs to be saved
        bool dirty = False;
    }

    #! Creates the handler with the given properties file path
    /** @param base_path the base directory for WebDAV files
        @param filename the name of the properties file (default: .webdav-props.json)
    */
    constructor(string base_path, string filename = ".webdav-props.json") {
        props_file = normalize_dir(base_path) + "/" + filename;
        load();
    }

    #! Destructor - ensures properties are saved
    destructor() {
        if (dirty) {
            save();
        }
    }

    #! Retrieves the value(s) of the given properties in the given namespace
    *hash<auto> get(string resource, string ns = DavNs, list<string> prop_names) {
        AutoReadLock al(m_lock);
        if (debug) {
            printf("FileWebDavPropertyHandler::get(%y, %y) %s: %y\n", prop_names, ns, resource,
                m_cache{resource}{ns}{prop_names});
        }
        return m_cache{resource}{ns}{prop_names};
    }

    #! Retrieves the value(s) of the given properties in the given namespace
    auto get(string resource, string ns = DavNs, string prop_name) {
        AutoReadLock al(m_lock);
        if (debug) {
            printf("FileWebDavPropertyHandler::get(%y, %y) %s: %y\n", prop_name, ns, resource,
                m_cache{resource}{ns}{prop_name});
        }
        return m_cache{resource}{ns}{prop_name};
    }

    #! Returns all properties in all namespaces
    /** @return a hash as NS -> property -> value
    */
    *hash<string, hash<auto>> getAll(string resource) {
        AutoReadLock al(m_lock);
        if (debug) {
            printf("FileWebDavPropertyHandler::getAll(%y): %y\n", resource, m_cache{resource});
        }
        return m_cache{resource};
    }

    #! Returns all properties in the given namespaces
    /** @return a hash as property -> value
    */
    *hash<auto> getAllInNamespace(string resource, string ns) {
        AutoReadLock al(m_lock);
        if (debug) {
            printf("FileWebDavPropertyHandler::getAll(%y, %y): %y\n", resource, ns, m_cache{resource});
        }
        return m_cache{resource}{ns};
    }

    #! Sets a property value
    set(string resource, string ns = DavNs, string prop_name, auto value) {
        {
            AutoWriteLock al(m_lock);
            m_cache{resource}{ns}{prop_name} = value;
            dirty = True;
            if (debug) {
                printf("FileWebDavPropertyHandler::set() CACHE %y\n", m_cache);
            }
        }
        saveAsync();
    }

    #! Deletes one or more properties
    del(string resource, string ns = DavNs, list<string> prop_names) {
        {
            AutoWriteLock al(m_lock);
            delete m_cache{resource}{ns}{prop_names};
            dirty = True;
        }
        saveAsync();
    }

    #! Deletes a property
    del(string resource, string ns = DavNs, string prop_name) {
        {
            AutoWriteLock al(m_lock);
            delete m_cache{resource}{ns}{prop_name};
            dirty = True;
        }
        saveAsync();
    }

    #! Deletes all properties for the given resource
    delAll(string resource) {
        {
            AutoWriteLock al(m_lock);
            delete m_cache{resource};
            dirty = True;
        }
        saveAsync();
    }

    #! Copies all properties to another target URL
    cp(string src_url, string target_url) {
        {
            AutoWriteLock al(m_lock);
            m_cache{target_url} = m_cache{src_url};
            dirty = True;
        }
        saveAsync();
    }

    #! Moves properties from one target URL to another
    move(string src_url, string target_url) {
        {
            AutoWriteLock al(m_lock);
            m_cache{target_url} = m_cache{src_url};
            delete m_cache{src_url};
            dirty = True;
        }
        saveAsync();
    }

    #! Forces an immediate save of properties to disk
    sync() {
        save();
    }

    #! Loads properties from the file
    private load() {
        AutoWriteLock al(m_lock);
        if (!is_file(props_file)) {
            m_cache = {};
            return;
        }

        try {
            string json_str = ReadOnlyFile::readTextFile(props_file);
            m_cache = parse_json(json_str);
            if (debug) {
                printf("FileWebDavPropertyHandler::load() loaded %d resources\n", m_cache.size());
            }
        } catch (hash<ExceptionInfo> ex) {
            # If we can't read the file, start with empty cache
            m_cache = {};
            if (debug) {
                printf("FileWebDavPropertyHandler::load() error: %s: %s\n", ex.err, ex.desc);
            }
        }
        dirty = False;
    }

    #! Saves properties to the file
    private save() {
        AutoReadLock al(m_lock);
        if (!dirty) {
            return;
        }

        try {
            string json_str = make_json(m_cache, JGF_ADD_FORMATTING);
            File f();
            if (f.open(props_file, O_CREAT | O_TRUNC | O_WRONLY, 0644)) {
                throw "FILE-OPEN-ERROR", sprintf("Could not open %y for writing: %s", props_file, strerror());
            }
            f.write(json_str);
            dirty = False;
            if (debug) {
                printf("FileWebDavPropertyHandler::save() saved %d resources\n", m_cache.size());
            }
        } catch (hash<ExceptionInfo> ex) {
            if (debug) {
                printf("FileWebDavPropertyHandler::save() error: %s: %s\n", ex.err, ex.desc);
            }
        }
    }

    #! Asynchronously saves properties (debounced)
    private saveAsync() {
        # For simplicity, we save synchronously for now
        # A more sophisticated implementation could use a background thread with debouncing
        save();
    }
} # class FileWebDavPropertyHandler
} # namespace WebDavHandler
