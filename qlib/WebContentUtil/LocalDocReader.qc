# -*- mode: qore; indent-tabs-mode: nil -*-

/*  LocalDocReader.qc Copyright 2026 Qore Technologies, s.r.o.

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

#! Main namespace
public namespace WebContentUtil {

#! Recursive local HTML document reader
/** Reads HTML files from a local directory tree, extracting text content and titles.
    Supports directory filtering via callback.

    All methods are static.

    @par Example
    @code{.py}
list<hash<auto>> pages = LocalDocReader::read("/var/www/docs/", {
    "max_pages": 10000,
    "skip_dir": \LocalDocReader::defaultSkipDir(),
    "progress": sub (int pages) {
        stderr.printf("  read %d pages\n", pages);
    },
});
    @endcode

    @since WebContentUtil 1.0
*/
public class LocalDocReader {
    #! Default maximum pages to read
    const DefaultMaxPages = 500000;

    #! Minimum text length to keep a page (characters)
    const MinTextLength = 50;

    #! Read HTML files from a local directory
    /** Recursively scans the given directory for HTML files (.html, .htm), extracts text
        content and titles from each file, and returns the results as a list of page hashes.

        @param dir_path root directory to scan
        @param opts options hash:
          - \c max_pages (int, default 500000): maximum files to read
          - \c skip_dir (code<bool(string dirname)>, optional): return True to skip a directory;
            called with the directory basename (not full path)
          - \c progress (code<nothing(int pages)>, optional): progress callback invoked periodically
        @return list of page hashes, each containing:
          - \c url (string): file:// URI for the file
          - \c title (string): the page title (from HTML &lt;title&gt; tag, or file path if none)
          - \c content (string): extracted plain text content
    */
    static list<hash<auto>> read(string dir_path, *hash<auto> opts) {
        int max_pages = opts.max_pages ?? DefaultMaxPages;
        *code<bool(string)> skip_dir = opts.skip_dir;
        *code<nothing(int)> progress = opts.progress;

        list<hash<auto>> pages = ();
        list<string> files = LocalDocReader::findHtmlFiles(dir_path, skip_dir);

        foreach string filepath in (files) {
            if (pages.size() >= max_pages) {
                break;
            }
            string html;
            try {
                html = ReadOnlyFile::readTextFile(filepath);
            } catch () {
                continue;
            }

            *string title = HtmlExtractor::extractTitle(html);
            if (!title) {
                title = filepath;
            }

            string text = HtmlExtractor::extractText(html);
            if (text.size() < MinTextLength) {
                continue;
            }

            pages += {"url": "file://" + filepath, "title": title, "content": text};
            if (progress && pages.size() % 500 == 0) {
                progress(pages.size());
            }
        }

        return pages;
    }

    #! Default directory skip filter
    /** Skips directories ending with "DataProvider" (e.g., GrpcDataProvider,
        AvroDataProvider) but keeps the core "DataProvider" directory itself.
        This is useful when crawling Qore/Qorus documentation where DataProvider
        app modules have their own embeddings via the system-tools collection.

        @param dirname the directory basename to check
        @return True to skip the directory, False to include it
    */
    static bool defaultSkipDir(string dirname) {
        if (dirname.endsWith("DataProvider") && dirname != "DataProvider") {
            return True;
        }
        return False;
    }

    #! Find all HTML files recursively under a directory
    /** @param dir_path root directory to scan
        @param skip_dir optional callback to filter directories
        @return list of full file paths
    */
    private static list<string> findHtmlFiles(string dir_path,
            *code<bool(string)> skip_dir) {
        list<string> result = ();
        Dir d();
        if (!d.chdir(dir_path)) {
            return result;
        }

        # Add HTML files in this directory
        *list<string> entries = d.listFiles("\\.(html?|HTML?)$");
        if (entries) {
            result += map dir_path + "/" + $1, entries;
        }

        # Recurse into subdirectories
        *list<string> subdirs = d.listDirs();
        if (subdirs) {
            foreach string subdir in (subdirs) {
                if (skip_dir && skip_dir(subdir)) {
                    continue;
                }
                result += LocalDocReader::findHtmlFiles(dir_path + "/" + subdir, skip_dir);
            }
        }

        return result;
    }
}

} # namespace WebContentUtil
