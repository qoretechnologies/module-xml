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

#! Abstract interface for WebDAV lock handlers
/** This class provides the interface for managing WebDAV locks on resources.
    Implementations must handle lock storage, conflict detection, and expiration.
*/
public class AbstractWebDavLockHandler {
    #! Acquire a lock on a resource
    /** @param resource the resource path to lock
        @param lock_info the lock information

        @return the lock token

        @throw LOCK-CONFLICT if the resource is already locked in a conflicting way
    */
    abstract string lock(string resource, hash<WebDavLockInfo> lock_info);

    #! Release a lock
    /** @param resource the resource path
        @param token the lock token to release

        @return True if the lock was found and released, False otherwise
    */
    abstract bool unlock(string resource, string token);

    #! Refresh an existing lock's timeout
    /** @param token the lock token to refresh
        @param timeout the new timeout in seconds

        @return True if the lock was found and refreshed, False otherwise
    */
    abstract bool refresh(string token, int timeout);

    #! Get lock information for a specific token
    /** @param token the lock token

        @return the lock information, or NOTHING if not found
    */
    abstract *hash<WebDavLockInfo> getLock(string token);

    #! Get all locks on a resource
    /** @param resource the resource path

        @return a list of lock information hashes, or an empty list if none
    */
    abstract list<hash<WebDavLockInfo>> getLocks(string resource);

    #! Check if a resource is locked
    /** @param resource the resource path to check
        @param exclude_token optional token to exclude from conflict check

        @return the conflicting lock token if locked, or NOTHING if not locked
    */
    abstract *string isLocked(string resource, *string exclude_token);

    #! Clean up expired locks
    abstract cleanExpired();

    #! Generate a new unique lock token
    /** @return a unique lock token URI in the format "urn:uuid:..."
    */
    string generateLockToken() {
%ifndef NO_UUID
        return sprintf("urn:uuid:%s", UUID::get());
%else
        return sprintf("urn:qore:%s", get_random_string(32));
%endif
    }
}

} # namespace WebDavHandler
