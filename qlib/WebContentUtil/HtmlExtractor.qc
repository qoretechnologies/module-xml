# -*- mode: qore; indent-tabs-mode: nil -*-

/*  HtmlExtractor.qc Copyright 2026 Qore Technologies, s.r.o.

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

#! HTML text extraction utility class
/** Extracts readable plain text from HTML by removing non-content elements
    (script, style, nav, footer, header, noscript), converting block elements
    to newlines, stripping remaining tags, and decoding HTML entities.

    All methods are static.

    @par Example
    @code{.py}
string text = HtmlExtractor::extractText("<html><body><p>Hello</p></body></html>");
# returns "Hello"
    @endcode

    @since WebContentUtil 1.0
*/
public class HtmlExtractor {
    #! Default element names to strip (content removed entirely)
    const DefaultStripElements = ("script", "style", "nav", "footer", "header", "noscript");

    #! Extract readable text from HTML, stripping tags and non-content elements
    /** Removes script, style, nav, footer, header, and noscript elements and their content.
        Converts block-level elements (p, div, br, h1-6, li, tr, td, th) to newlines.
        Strips all remaining HTML tags. Decodes HTML entities. Collapses whitespace.

        @param html raw HTML string
        @param strip_elements optional list of additional element names to strip (content removed);
            these are added to the default list (script, style, nav, footer, header, noscript)
        @return plain text content
    */
    static string extractText(string html, *list<string> strip_elements) {
        string text = html;

        # Strip default non-content elements
        foreach string elem in (DefaultStripElements) {
            text = regex_subst(text, sprintf("(?si)<%s[^>]*>.*?</%s>", elem, elem), " ");
        }

        # Strip additional elements if provided
        if (strip_elements) {
            foreach string elem in (strip_elements) {
                text = regex_subst(text, sprintf("(?si)<%s[^>]*>.*?</%s>", elem, elem), " ");
            }
        }

        # Replace block-level tags with newlines
        text = regex_subst(text, "<(?:p|div|br|h[1-6]|li|tr|td|th)[^>]*>", "\n", RE_Global);

        # Remove all remaining HTML tags
        text = regex_subst(text, "<[^>]+>", " ", RE_Global);

        # Decode HTML entities
        text = html_decode(text);

        # Collapse whitespace
        text = regex_subst(text, "[ \t]+", " ", RE_Global);
        text = regex_subst(text, "\n[ \t]+", "\n", RE_Global);
        text = regex_subst(text, "\n{3,}", "\n\n", RE_Global);

        return trim(text);
    }

    #! Extract the page title from HTML
    /** @param html raw HTML string
        @return title text, or @ref nothing if no \c <title> tag found
    */
    static *string extractTitle(string html) {
        *string t = (html =~ x/<title[^>]*>([^<]+)<\/title>/i)[0];
        if (t.val()) {
            return html_decode(trim(t));
        }
    }
}

} # namespace WebContentUtil
