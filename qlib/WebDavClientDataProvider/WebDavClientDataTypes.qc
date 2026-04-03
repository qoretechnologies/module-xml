# -*- mode: qore; indent-tabs-mode: nil -*-

/*  WebDavClientDataProvider.qm Copyright 2019 - 2026 Qore Technologies, s.r.o.
    MIT License - see LICENSE file
*/

public namespace WebDavClientDataProvider {

# ============================================================
# List Directory
# ============================================================

public class WebDavListRequestDataType inherits HashDataType {
    public {
        const Fields = {
            "path": {
                "display_name": "Path",
                "type": StringOrNothingType,
                "desc": "The directory path to list on the WebDAV server",
                "example_value": "/documents",
                "default_value": "/",
            },
            "depth": {
                "display_name": "Depth",
                "type": StringOrNothingType,
                "desc": "The depth of the listing: `0` for the resource only, `1` for "
                    "immediate children (default), `infinity` for all descendants",
                "default_value": "1",
            },
        };
    }

    constructor() {
        addQoreFields(Fields);
    }
}

public class WebDavListResponseDataType inherits HashDataType {
    private {
        const Fields = {
            "resources": {
                "display_name": "Resources",
                "type": AutoListType,
                "desc": "List of resources found in the directory",
            },
        };
    }

    constructor() {
        addQoreFields(Fields);
    }
}

# ============================================================
# Get File
# ============================================================

public class WebDavGetRequestDataType inherits HashDataType {
    public {
        const Fields = {
            "path": {
                "display_name": "Path",
                "type": StringType,
                "desc": "The path to the file on the WebDAV server",
                "example_value": "/documents/report.pdf",
            },
        };
    }

    constructor() {
        addQoreFields(Fields);
    }
}

public class WebDavGetResponseDataType inherits HashDataType {
    private {
        const Fields = {
            "content": {
                "display_name": "Content",
                "type": DataOrNothingType,
                "desc": "The file content as binary data",
            },
            "found": {
                "display_name": "Found",
                "type": BoolType,
                "desc": "Whether the file was found on the server",
            },
        };
    }

    constructor() {
        addQoreFields(Fields);
    }
}

# ============================================================
# Put File
# ============================================================

public class WebDavPutRequestDataType inherits HashDataType {
    public {
        const Fields = {
            "path": {
                "display_name": "Path",
                "type": StringType,
                "desc": "The destination path on the WebDAV server",
                "example_value": "/documents/upload.pdf",
            },
            "content": {
                "display_name": "Content",
                "type": DataOrNothingType,
                "desc": "The file content to upload",
            },
            "content_type": {
                "display_name": "Content Type",
                "type": StringOrNothingType,
                "desc": "The MIME content type of the file (e.g., `application/pdf`)",
                "example_value": "application/pdf",
            },
        };
    }

    constructor() {
        addQoreFields(Fields);
    }
}

public class WebDavPutResponseDataType inherits HashDataType {
    private {
        const Fields = {
            "created": {
                "display_name": "Created",
                "type": BoolType,
                "desc": "Whether the file was newly created (`True`) or updated (`False`)",
            },
        };
    }

    constructor() {
        addQoreFields(Fields);
    }
}

# ============================================================
# Delete Resource
# ============================================================

public class WebDavDeleteRequestDataType inherits HashDataType {
    public {
        const Fields = {
            "path": {
                "display_name": "Path",
                "type": StringType,
                "desc": "The path to the resource to delete on the WebDAV server",
                "example_value": "/documents/old-file.pdf",
            },
        };
    }

    constructor() {
        addQoreFields(Fields);
    }
}

public class WebDavSuccessResponseDataType inherits HashDataType {
    private {
        const Fields = {
            "success": {
                "display_name": "Success",
                "type": BoolType,
                "desc": "Whether the operation completed successfully",
            },
        };
    }

    constructor() {
        addQoreFields(Fields);
    }
}

# ============================================================
# Mkdir
# ============================================================

public class WebDavMkdirRequestDataType inherits HashDataType {
    public {
        const Fields = {
            "path": {
                "display_name": "Path",
                "type": StringType,
                "desc": "The path of the new directory to create on the WebDAV server",
                "example_value": "/documents/new-folder",
            },
        };
    }

    constructor() {
        addQoreFields(Fields);
    }
}

# ============================================================
# Copy Resource
# ============================================================

public class WebDavCopyRequestDataType inherits HashDataType {
    public {
        const Fields = {
            "source": {
                "display_name": "Source Path",
                "type": StringType,
                "desc": "The source path of the resource to copy",
                "example_value": "/documents/original.pdf",
            },
            "destination": {
                "display_name": "Destination Path",
                "type": StringType,
                "desc": "The destination path for the copy",
                "example_value": "/backup/original.pdf",
            },
            "overwrite": {
                "display_name": "Overwrite",
                "type": SoftBoolOrNothingType,
                "desc": "Whether to overwrite the destination if it already exists (default: `True`)",
                "default_value": True,
            },
        };
    }

    constructor() {
        addQoreFields(Fields);
    }
}

# ============================================================
# Move Resource
# ============================================================

public class WebDavMoveRequestDataType inherits HashDataType {
    public {
        const Fields = {
            "source": {
                "display_name": "Source Path",
                "type": StringType,
                "desc": "The source path of the resource to move",
                "example_value": "/documents/file.pdf",
            },
            "destination": {
                "display_name": "Destination Path",
                "type": StringType,
                "desc": "The destination path for the move",
                "example_value": "/archive/file.pdf",
            },
            "overwrite": {
                "display_name": "Overwrite",
                "type": SoftBoolOrNothingType,
                "desc": "Whether to overwrite the destination if it already exists (default: `True`)",
                "default_value": True,
            },
        };
    }

    constructor() {
        addQoreFields(Fields);
    }
}

# ============================================================
# Static type instances for action registration
# ============================================================

public const WebDavListRequestType = new WebDavListRequestDataType();
public const WebDavListResponseType = new WebDavListResponseDataType();
public const WebDavGetRequestType = new WebDavGetRequestDataType();
public const WebDavGetResponseType = new WebDavGetResponseDataType();
public const WebDavPutRequestType = new WebDavPutRequestDataType();
public const WebDavPutResponseType = new WebDavPutResponseDataType();
public const WebDavDeleteRequestType = new WebDavDeleteRequestDataType();
public const WebDavSuccessResponseType = new WebDavSuccessResponseDataType();
public const WebDavMkdirRequestType = new WebDavMkdirRequestDataType();
public const WebDavCopyRequestType = new WebDavCopyRequestDataType();
public const WebDavMoveRequestType = new WebDavMoveRequestDataType();

}
