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

    #! Chunk multiple text blocks with metadata threading and accurate token counting
    /** Token-aware variant of @ref chunk() for callers that have multiple text blocks
        with associated metadata and an accurate tokenizer (e.g. a real bge-m3 tokenizer
        rather than the 4-chars/token heuristic).

        Algorithm: each block is split on paragraph boundaries (\c \\n\\n).  Paragraphs
        are accumulated into chunks until reaching \c target_tokens.  Oversized paragraphs
        are split at sentence boundaries (\c ". ", \c "! ", \c "? ").  Overlap between
        consecutive chunks is preserved by backing up by full paragraphs that fit within
        the overlap budget.  Each chunk inherits its starting paragraph's source-block
        metadata.

        Used by callers like @ref QorusAiDocumentIngester that need:
        - real tokenizer accuracy (bge-m3) instead of the 4-chars/token heuristic
        - per-block metadata threading (so chunk N knows which source it came from)
        - token_count in the output for downstream consumers

        @param blocks list of \c {content, metadata} hashes; each block contributes
            paragraphs to the chunk stream and associates its metadata with chunks
            that start in that block
        @param opts chunking options:
          - \c target_tokens (int, default 512): target chunk size
          - \c overlap_tokens (int, default 50): overlap between chunks
          - \c token_counter (\c *code<int(string)>, optional): callback that returns the
            token count for a given string.  Defaults to the @ref estimateTokens() heuristic.
            Pass a real tokenizer (e.g. bge-m3) for accurate counts.
        @return list of chunk hashes, each containing:
          - \c content (string): the chunk text
          - \c token_count (int): token count via the supplied counter
          - \c metadata (\c *hash<auto>): metadata from the chunk's starting block
          - \c chunk_index (int): sequential chunk number (0-indexed)

        @par Example
        @code{.py}
list<hash<auto>> blocks = (
    {"content": para1_text, "metadata": {"page": 1}},
    {"content": para2_text, "metadata": {"page": 2}},
);
list<hash<auto>> chunks = TextChunker::chunkBlocks(blocks, {
    "target_tokens": 512,
    "overlap_tokens": 50,
    "token_counter": code<int(string)> sub (string t) {
        return real_tokenizer.countTokens(t);
    },
});
        @endcode
    */
    static list<hash<auto>> chunkBlocks(list<hash<auto>> blocks, *hash<auto> opts) {
        int target_tokens = opts.target_tokens ?? DefaultTargetTokens;
        int overlap_tokens = opts.overlap_tokens ?? DefaultOverlapTokens;
        # Local closure to count tokens — uses the supplied counter or the
        # default 4-chars/token heuristic
        code<int(string)> count_tokens;
        if (opts.token_counter) {
            count_tokens = opts.token_counter;
        } else {
            count_tokens = int sub (string t) {
                return TextChunker::estimateTokens(t);
            };
        }

        # Step 1: split each block into paragraphs (with metadata threaded through)
        list<hash<auto>> paragraphs = ();
        foreach hash<auto> block in (blocks) {
            list<string> parts = block.content.split("\n\n");
            foreach string part in (parts) {
                string trimmed = trim(part);
                if (trimmed.val()) {
                    paragraphs += {
                        "text": trimmed,
                        "tokens": count_tokens(trimmed),
                        "metadata": block.metadata,
                    };
                }
            }
        }

        if (!paragraphs) {
            return ();
        }

        # Step 2: accumulate paragraphs into chunks
        list<hash<auto>> result = ();
        int chunk_index = 0;
        int i = 0;

        while (i < paragraphs.size()) {
            string chunk_text = "";
            int chunk_tokens = 0;
            *hash<auto> chunk_metadata = paragraphs[i].metadata;
            int start_i = i;

            # Accumulate paragraphs until we reach target
            while (i < paragraphs.size() && chunk_tokens < target_tokens) {
                # If a single paragraph exceeds target, split it by sentences
                if (paragraphs[i].tokens > target_tokens && !chunk_text.val()) {
                    list<hash<auto>> sentence_chunks = TextChunker::splitBySentences(
                        paragraphs[i].text, paragraphs[i].metadata, target_tokens,
                        count_tokens);
                    foreach hash<auto> sc in (sentence_chunks) {
                        result += sc + {"chunk_index": chunk_index++};
                    }
                    ++i;
                    break;
                }

                if (chunk_text.val()) {
                    chunk_text += "\n\n";
                }
                chunk_text += paragraphs[i].text;
                chunk_tokens += paragraphs[i].tokens;
                ++i;
            }

            if (chunk_text.val()) {
                result += {
                    "content": chunk_text,
                    "token_count": count_tokens(chunk_text),
                    "metadata": chunk_metadata,
                    "chunk_index": chunk_index++,
                };
            }

            # Apply overlap: back up by paragraphs whose combined tokens fit the budget
            if (i < paragraphs.size() && overlap_tokens > 0) {
                int overlap_used = 0;
                int backup = i - 1;
                while (backup > start_i && overlap_used < overlap_tokens) {
                    overlap_used += paragraphs[backup].tokens;
                    --backup;
                }
                if (backup + 1 < i) {
                    i = backup + 1;
                }
            }
        }

        return result;
    }

    #! Split a large paragraph into sentence-based chunks
    /** Used internally by @ref chunkBlocks() when a single paragraph exceeds
        \c target_tokens.

        @param text the paragraph text
        @param metadata metadata to associate with each output chunk
        @param target_tokens max tokens per chunk
        @param count_tokens token-counter callback
        @return list of \c {content, token_count, metadata} hashes (no chunk_index;
            the caller assigns that)
    */
    private static list<hash<auto>> splitBySentences(string text, *hash<auto> metadata,
            int target_tokens, code<int(string)> count_tokens) {
        # Split on sentence-ending punctuation followed by whitespace using a SOH
        # delimiter (\x01).  NUL (\x00) does NOT work here because regex_subst's
        # replacement string treats embedded NUL as a terminator and silently drops
        # everything after it — a subtle pre-existing bug carried over from earlier
        # implementations.  SOH is similarly unlikely to appear in real text.
        string delim = "\x01";
        string delimited = regex_subst(text, "([.!?]+)\\s+", "$1" + delim, RE_Global);
        list<string> sentences = delimited.split(delim);
        if (!sentences || sentences.size() < 2) {
            return ({
                "content": text,
                "token_count": count_tokens(text),
                "metadata": metadata,
            },);
        }

        list<hash<auto>> result = ();
        string current = "";
        int current_tokens = 0;

        foreach string sent in (sentences) {
            string trimmed = trim(sent);
            if (!trimmed.val()) {
                continue;
            }
            int sent_tokens = count_tokens(trimmed);

            if (current_tokens + sent_tokens > target_tokens && current.val()) {
                result += {
                    "content": current,
                    "token_count": count_tokens(current),
                    "metadata": metadata,
                };
                current = "";
                current_tokens = 0;
            }

            if (current.val()) {
                current += " ";
            }
            current += trimmed;
            current_tokens += sent_tokens;
        }

        if (current.val()) {
            result += {
                "content": current,
                "token_count": count_tokens(current),
                "metadata": metadata,
            };
        }

        return result;
    }

    #! Estimate token count for a text string
    /** Uses the ~4 chars/token heuristic (matches bge-m3 tokenizer closely enough
        for chunking purposes).  Callers needing accurate counts should pass a
        custom \c token_counter to @ref chunkBlocks() instead.

        @param text the text to estimate
        @return estimated token count
    */
    static int estimateTokens(string text) {
        return text.size() / CharsPerToken;
    }
}

} # namespace WebContentUtil
