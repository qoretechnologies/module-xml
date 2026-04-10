# -*- mode: qore; indent-tabs-mode: nil -*-

/*  TextChunker.qc Copyright 2026 Qore Technologies, s.r.o.

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

#! Text chunking utility class
/** Chunks text into segments suitable for embedding, with configurable target size
    and overlap. Uses paragraph boundaries for natural splits, falling back to
    sentence boundaries for oversized paragraphs.

    All methods are static.

    @par Example
    @code{.py}
list<hash<auto>> chunks = TextChunker::chunk(text, "https://docs.example.com/page", "Page Title", {
    "target_tokens": 512,
    "overlap_tokens": 50,
});
    @endcode

    @since WebContentUtil 1.0
*/
public class TextChunker {
    #! Default target chunk size in tokens
    const DefaultTargetTokens = 512;

    #! Default overlap between chunks in tokens
    const DefaultOverlapTokens = 50;

    #! Approximate characters per token (matches bge-m3 tokenizer closely enough for chunking)
    const CharsPerToken = 4;

    #! Chunk text into segments suitable for embedding
    /** Splits text into chunks at paragraph boundaries (\c \\n\\n), with overlap between
        adjacent chunks for context preservation. Oversized paragraphs are split at sentence
        boundaries (\c ". ") or character boundaries as a last resort.

        @param text plain text to chunk
        @param source_url the source URL for metadata
        @param title the page title for metadata
        @param opts chunking options:
          - \c target_tokens (int, default 512): target chunk size in estimated tokens
          - \c overlap_tokens (int, default 50): overlap between chunks in estimated tokens
        @return list of chunk hashes, each containing:
          - \c source_url (string): the source URL
          - \c title (string): the page title
          - \c content (string): the chunk text
          - \c chunk_index (int): sequential chunk number (0-indexed)
    */
    static list<hash<auto>> chunk(string text, string source_url, string title,
            *hash<auto> opts) {
        int target_chars = (opts.target_tokens ?? DefaultTargetTokens) * CharsPerToken;
        int overlap_chars = (opts.overlap_tokens ?? DefaultOverlapTokens) * CharsPerToken;

        list<hash<auto>> chunks = ();
        list<string> paragraphs = text.split("\n\n");
        string current = "";
        int chunk_idx = 0;

        foreach string para in (paragraphs) {
            para = trim(para);
            if (!para.val()) {
                continue;
            }
            if (current.val() && (current.size() + para.size() + 2) > target_chars) {
                chunks += {
                    "source_url": source_url, "title": title,
                    "content": trim(current), "chunk_index": chunk_idx++,
                };
                if (current.size() > overlap_chars) {
                    current = current.substr(current.size() - overlap_chars);
                    int nl = current.find("\n");
                    if (nl >= 0) {
                        current = current.substr(nl + 1);
                    }
                } else {
                    current = "";
                }
            }
            if (current.val()) {
                current += "\n\n";
            }
            current += para;

            # Handle oversized paragraphs
            while (current.size() > target_chars) {
                string segment = current.substr(0, target_chars);
                int split_pos = segment.rfind(". ");
                if (split_pos < target_chars / 2) {
                    split_pos = target_chars;
                } else {
                    split_pos += 2;
                }
                chunks += {
                    "source_url": source_url, "title": title,
                    "content": trim(current.substr(0, split_pos)),
                    "chunk_index": chunk_idx++,
                };
                current = current.substr(max(0, split_pos - overlap_chars));
            }
        }

        if (trim(current).val()) {
            chunks += {
                "source_url": source_url, "title": title,
                "content": trim(current), "chunk_index": chunk_idx,
            };
        }

        return chunks;
    }

    #! Estimate token count for a text string
    /** Uses the ~4 chars/token heuristic (matches bge-m3 tokenizer closely enough
        for chunking purposes).

        @param text the text to estimate
        @return estimated token count
    */
    static int estimateTokens(string text) {
        return text.size() / CharsPerToken;
    }
}

} # namespace WebContentUtil
