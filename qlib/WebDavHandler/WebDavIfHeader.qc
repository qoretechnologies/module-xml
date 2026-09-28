# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavHandler module Copyright 2019 - 2026 Qore Technologies, s.r.o.

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

#! Main public WebDavHandler namespace
public namespace WebDavHandler {
#! One condition of a WebDAV If header list (RFC 4918 section 10.4)
/** @since %WebDavHandler 1.3
*/
public hashdecl WebDavIfCondition {
    #! True if the condition is negated with \c "Not"
    bool negated = False;
    #! the state token (a Coded-URL without its angle brackets), such as a lock token
    *string token;
    #! the entity tag, including its quotes and any weak prefix, as in \c "W/\"abc\""
    *string etag;
}

#! One list of a WebDAV If header (RFC 4918 section 10.4)
/** @since %WebDavHandler 1.3
*/
public hashdecl WebDavIfList {
    #! the tagged resource (the Simple-ref without its angle brackets), or @ref nothing for the request resource
    *string resource;
    #! the conditions, all of which must be true for the list to be true
    list<hash<WebDavIfCondition>> conditions = ();
}

#! Parses a WebDAV If header (RFC 4918 section 10.4)
/** The header is true if any of its lists is true; a list is true if all of its conditions are true. A state token
    condition is true if the token identifies a lock that applies to the list's resource, and an entity tag
    condition is true if it matches the resource's current entity tag.

    @par Example:
    @code{.py}
WebDavIfHeader header("</locked/doc> (<urn:uuid:181d4fae-7d8c-11d0-a765-00a0c91e6bf2> [\"etag-1\"])");
# ("urn:uuid:181d4fae-7d8c-11d0-a765-00a0c91e6bf2")
list<string> tokens = header.getStateTokens();
    @endcode

    @since %WebDavHandler 1.3
*/
public class WebDavIfHeader {
    public {
        #! the lists of the header, in order
        list<hash<WebDavIfList>> lists = ();
        #! True if the lists are tagged with resources
        bool tagged = False;
    }

    private {
        string value;
        int pos = 0;
    }

    #! Parses the header value
    /** @param value the value of the If header

        @throw WEBDAV-IF-HEADER-ERROR the value is not a valid If header
    */
    constructor(string value) {
        self.value = value;
        *string resource;
        bool first = True;
        while (True) {
            skipSpace();
            if (pos == value.length()) {
                break;
            }
            string c = value[pos];
            if (c == "<") {
                if (!first && !tagged) {
                    error("a resource tag follows an untagged list");
                }
                tagged = True;
                resource = readBracketed("<", ">");
                skipSpace();
                if (pos == value.length() || value[pos] != "(") {
                    error("a resource tag must be followed by a list");
                }
                continue;
            }
            if (c != "(") {
                error(sprintf("unexpected character %y", c));
            }
            if (tagged && !exists resource) {
                error("an untagged list follows a tagged list");
            }
            lists += readList(resource);
            first = False;
        }
        if (!lists) {
            error("the header has no list");
        }
    }

    #! Returns the state tokens of all non-negated conditions, which submit lock tokens (RFC 4918 section 10.4.1)
    /** @return the state tokens of all conditions not negated with \c "Not", in header order; an empty list if
        there are none
    */
    list<string> getStateTokens() {
        list<string> rv = ();
        foreach hash<WebDavIfList> l in (lists) {
            foreach hash<WebDavIfCondition> c in (l.conditions) {
                if (exists c.token && !c.negated) {
                    rv += c.token;
                }
            }
        }
        return rv;
    }

    #! Returns True if two entity tags match with the weak comparison function (RFC 9110 section 8.8.3.2)
    /** @param a the first entity tag, including its quotes and any \c "W/" weak prefix
        @param b the second entity tag, including its quotes and any \c "W/" weak prefix

        @return True if the tags are equal after removing any \c "W/" weak prefix from both
    */
    static bool etagMatches(string a, string b) {
        return regex_subst(a, "^W/", "") == regex_subst(b, "^W/", "");
    }

    private hash<WebDavIfList> readList(*string resource) {
        # skip "("
        ++pos;
        hash<WebDavIfList> rv = <WebDavIfList>{"resource": resource};
        while (True) {
            skipSpace();
            if (pos == value.length()) {
                error("unterminated list");
            }
            if (value[pos] == ")") {
                ++pos;
                break;
            }
            hash<WebDavIfCondition> cond();
            if (value.substr(pos, 3) == "Not" && (pos + 3 == value.length() || value[pos + 3] =~ /[ \t\r\n<\[]/)) {
                cond.negated = True;
                pos += 3;
                skipSpace();
                if (pos == value.length()) {
                    error("\"Not\" without a condition");
                }
            }
            if (value[pos] == "<") {
                cond.token = readBracketed("<", ">");
            } else if (value[pos] == "[") {
                cond.etag = readEntityTag();
            } else {
                error(sprintf("unexpected character %y in a list", value[pos]));
            }
            rv.conditions += cond;
        }
        if (!rv.conditions) {
            error("empty list");
        }
        return rv;
    }

    # reads a Coded-URL or Simple-ref; returns its content
    private string readBracketed(string open, string close) {
        int end = value.find(close, pos + 1);
        if (end < 0) {
            error(sprintf("unterminated %y", open));
        }
        string rv = value.substr(pos + 1, end - pos - 1);
        if (!rv.val() || rv =~ /[ \t\r\n<]/) {
            error(sprintf("invalid reference %y", rv));
        }
        pos = end + 1;
        return rv;
    }

    # reads "[" entity-tag "]"; returns the entity tag
    private string readEntityTag() {
        # skip "["
        ++pos;
        int start = pos;
        if (value.substr(pos, 2) == "W/") {
            pos += 2;
        }
        if (pos == value.length() || value[pos] != "\"") {
            error("an entity tag must be a quoted string");
        }
        ++pos;
        while (pos < value.length() && value[pos] != "\"") {
            ++pos;
        }
        if (pos == value.length()) {
            error("unterminated entity tag");
        }
        ++pos;
        string rv = value.substr(start, pos - start);
        if (pos == value.length() || value[pos] != "]") {
            error("an entity tag must be followed by \"]\"");
        }
        ++pos;
        return rv;
    }

    private skipSpace() {
        while (pos < value.length() && value[pos] =~ /[ \t\r\n]/) {
            ++pos;
        }
    }

    private error(string msg) {
        throw "WEBDAV-IF-HEADER-ERROR", sprintf("invalid If header %y: %s", value, msg);
    }
}
} # namespace WebDavHandler
