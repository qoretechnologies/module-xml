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

#! Main public WebDavHandler namespace
public namespace WebDavHandler {

#! In-memory implementation of WebDAV lock handler
/** This class provides an in-memory implementation of WebDAV lock management.
    Locks are lost when the server restarts.
*/
public class InMemoryWebDavLockHandler inherits AbstractWebDavLockHandler {
    private {
        #! Read-write lock for thread safety
        RWLock m_lock();

        #! Lock storage: token -> lock info
        hash<string, hash<WebDavLockInfo>> locks = {};

        #! Resource to tokens mapping: resource -> list of tokens
        hash<string, list<string>> resource_locks = {};
    }

    #! Acquire a lock on a resource
    string lock(string resource, hash<WebDavLockInfo> lock_info) {
        AutoWriteLock al(m_lock);

        # Clean expired locks first
        cleanExpiredInternal();

        # Normalize resource path
        resource = normalizeResource(resource);

        # Check for conflicts with existing locks
        if (*list<string> existing = resource_locks{resource}) {
            foreach string tok in (existing) {
                hash<WebDavLockInfo> existing_lock = locks{tok};
                # Exclusive locks conflict with any other lock
                # Shared locks only conflict with exclusive locks
                if (existing_lock.scope == "exclusive" || lock_info.scope == "exclusive") {
                    throw "LOCK-CONFLICT", sprintf("Resource %y is already locked with token %y",
                        resource, tok), 423;
                }
            }
        }

        # Check parent locks with depth=infinity
        string parent = dirname(resource);
        while (parent != "" && parent != "/" && parent != resource) {
            if (*list<string> parent_tokens = resource_locks{parent}) {
                foreach string tok in (parent_tokens) {
                    hash<WebDavLockInfo> parent_lock = locks{tok};
                    if (parent_lock.depth == "infinity") {
                        if (parent_lock.scope == "exclusive" || lock_info.scope == "exclusive") {
                            throw "LOCK-CONFLICT",
                                sprintf("Parent resource %y is locked with depth infinity", parent), 423;
                        }
                    }
                }
            }
            string new_parent = dirname(parent);
            if (new_parent == parent) {
                break;
            }
            parent = new_parent;
        }

        # Check child resources if this is a depth=infinity lock
        if (lock_info.depth == "infinity") {
            foreach string res in (keys resource_locks) {
                if (res.startsWith(resource + "/")) {
                    foreach string tok in (resource_locks{res}) {
                        hash<WebDavLockInfo> child_lock = locks{tok};
                        if (child_lock.scope == "exclusive" || lock_info.scope == "exclusive") {
                            throw "LOCK-CONFLICT",
                                sprintf("Child resource %y is already locked", res), 423;
                        }
                    }
                }
            }
        }

        # Store the lock
        locks{lock_info.token} = cast<hash<WebDavLockInfo>>(lock_info + {"resource": resource});

        # Add to resource mapping
        if (!resource_locks{resource}) {
            resource_locks{resource} = ();
        }
        resource_locks{resource} += lock_info.token;

        return lock_info.token;
    }

    #! Release a lock
    bool unlock(string resource, string token) {
        AutoWriteLock al(m_lock);

        resource = normalizeResource(resource);

        if (!locks{token}) {
            return False;
        }

        # Remove from resource mapping
        if (resource_locks{resource}) {
            resource_locks{resource} = remove_from_list(resource_locks{resource}, token);
            if (!resource_locks{resource}) {
                remove resource_locks{resource};
            }
        }

        # Remove lock
        remove locks{token};

        return True;
    }

    #! Refresh an existing lock's timeout
    bool refresh(string token, int timeout) {
        AutoWriteLock al(m_lock);

        if (!locks{token}) {
            return False;
        }

        locks{token}.timeout = timeout;
        locks{token}.expires = timeout == 0 ? 9999-12-31 : now() + seconds(timeout);

        return True;
    }

    #! Get lock information for a specific token
    *hash<WebDavLockInfo> getLock(string token) {
        AutoReadLock al(m_lock);
        return locks{token};
    }

    #! Get all locks on a resource
    list<hash<WebDavLockInfo>> getLocks(string resource) {
        AutoReadLock al(m_lock);

        resource = normalizeResource(resource);

        list<hash<WebDavLockInfo>> result = ();

        if (*list<string> tokens = resource_locks{resource}) {
            foreach string tok in (tokens) {
                result += locks{tok};
            }
        }

        return result;
    }

    #! Check if a resource is locked
    *string isLocked(string resource, *string exclude_token) {
        AutoReadLock al(m_lock);

        resource = normalizeResource(resource);

        # Check direct locks
        if (*list<string> tokens = resource_locks{resource}) {
            foreach string tok in (tokens) {
                if (tok != exclude_token) {
                    return tok;
                }
            }
        }

        # Check parent locks with depth=infinity
        string parent = dirname(resource);
        while (parent != "" && parent != "/" && parent != resource) {
            if (*list<string> parent_tokens = resource_locks{parent}) {
                foreach string tok in (parent_tokens) {
                    if (tok != exclude_token && locks{tok}.depth == "infinity") {
                        return tok;
                    }
                }
            }
            string new_parent = dirname(parent);
            if (new_parent == parent) {
                break;
            }
            parent = new_parent;
        }

        return NOTHING;
    }

    #! Clean up expired locks
    cleanExpired() {
        AutoWriteLock al(m_lock);
        cleanExpiredInternal();
    }

    #! Internal method to clean expired locks (must hold write lock)
    private cleanExpiredInternal() {
        date now_dt = now();
        list<string> expired = ();

        foreach hash<auto> i in (locks.pairIterator()) {
            if (i.value.expires < now_dt) {
                expired += i.key;
            }
        }

        foreach string tok in (expired) {
            string resource = locks{tok}.resource;

            # Remove from resource mapping
            if (resource_locks{resource}) {
                resource_locks{resource} = remove_from_list(resource_locks{resource}, tok);
                if (!resource_locks{resource}) {
                    remove resource_locks{resource};
                }
            }

            remove locks{tok};
        }
    }

    #! Normalize resource path
    private string normalizeResource(string resource) {
        # Remove trailing slash except for root
        if (resource != "/" && resource =~ /\/$/) {
            splice resource, -1;
        }
        return resource;
    }

    #! Helper to remove an element from a list
    private list<string> remove_from_list(list<string> l, string item) {
        return (map $1, l, $1 != item);
    }
}

} # namespace WebDavHandler
