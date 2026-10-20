import os
import shutil
import ctypes
import ctypes.wintypes as wintypes
import subprocess
import webbrowser
from pathlib import Path

import psutil

from core.system import get_system_info
from core.app_registry import find_registered_application


# =========================
# Application launcher
# =========================

def find_application(application):

    application = application.lower().strip()

    for word in ["app", "application", "program"]:
        application = application.replace(word, "").strip()

    # Application registry
    registered_app = find_registered_application(
        application
    )

    if registered_app:
        return registered_app

    # PATH
    executable = shutil.which(application)

    if executable:
        return {
            "type": "executable",
            "path": executable,
        }

    # Start Menu fallback
    start_menu_locations = [
        Path(os.environ.get("APPDATA", "")) /
        "Microsoft/Windows/Start Menu/Programs",

        Path(os.environ.get("PROGRAMDATA", "")) /
        "Microsoft/Windows/Start Menu/Programs",
    ]

    for location in start_menu_locations:

        if not location.exists():
            continue

        try:

            for shortcut in location.rglob("*"):

                if shortcut.suffix.lower() not in [
                    ".lnk",
                    ".exe"
                ]:
                    continue

                name = shortcut.stem.lower()

                if application == name:
                    return {
                        "type": "executable",
                        "path": str(shortcut),
                    }

                if application in name:
                    return {
                        "type": "executable",
                        "path": str(shortcut),
                    }

        except (PermissionError, OSError):
            continue

    return None


def open_application(application):

    application = application.strip()

    app = find_application(application)

    if not app:

        return {
            "success": False,
            "message": (
                f"I couldn't find an application named "
                f"'{application}' on this computer."
            ),
        }

    try:

        if app["type"] == "executable":

            os.startfile(
                app["path"]
            )

        elif app["type"] == "windows_app":

            app_id = app["app_id"]

            subprocess.Popen(
                [
                    "explorer.exe",
                    f"shell:AppsFolder\\{app_id}"
                ]
            )

        else:

            return {
                "success": False,
                "message": (
                    f"I found '{application}', "
                    "but I don't know how to launch it."
                ),
            }

        return {
            "success": True,
            "application": application,
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e),
        }


# =========================
# Battery
# =========================

def get_battery_status():

    battery = psutil.sensors_battery()

    if battery is None:

        return {
            "success": False,
            "message": "Battery information is unavailable."
        }

    return {
        "success": True,
        "percent": battery.percent,
        "plugged_in": battery.power_plugged,
        "charging": battery.power_plugged
    }


# =========================
# Folder launcher
# =========================

def open_folder(folder):

    folder = folder.lower().strip()

    common_folders = {

        "downloads":
            Path.home() / "Downloads",

        "documents":
            Path.home() / "Documents",

        "desktop":
            Path.home() / "Desktop",

        "pictures":
            Path.home() / "Pictures",

        "videos":
            Path.home() / "Videos",

        "music":
            Path.home() / "Music",

        "home":
            Path.home(),

    }

    if folder in common_folders:

        path = common_folders[folder]

    else:

        path = Path(folder)

    if not path.exists():

        return {
            "success": False,
            "message": (
                f"I couldn't find the folder '{folder}'."
            ),
        }

    if not path.is_dir():

        return {
            "success": False,
            "message": (
                f"'{folder}' is not a folder."
            ),
        }

    try:

        os.startfile(path)

        return {
            "success": True,
            "folder": str(path)
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================
# Folder creation
# =========================

def create_folder(folder):

    folder = folder.strip()

    common_folders = {

        "desktop":
            Path.home() / "Desktop",

        "downloads":
            Path.home() / "Downloads",

        "documents":
            Path.home() / "Documents",

        "pictures":
            Path.home() / "Pictures",

        "videos":
            Path.home() / "Videos",

        "music":
            Path.home() / "Music",

        "home":
            Path.home(),

    }

    normalized = folder.replace("\\", "/")
    parts = normalized.split("/")

    if parts[0].lower() in common_folders:

        base_folder = common_folders[
            parts[0].lower()
        ]

        if len(parts) > 1:

            path = base_folder.joinpath(
                *parts[1:]
            )

        else:

            return {
                "success": False,
                "message": (
                    f"'{folder}' refers to an existing "
                    "special folder."
                ),
            }

    else:

        path = Path(folder)

        if not path.is_absolute():

            path = Path.home() / path

    if path.exists():

        if path.is_dir():

            return {
                "success": False,
                "message": (
                    f"The folder '{path}' already exists."
                ),
            }

        return {
            "success": False,
            "message": (
                f"'{path}' already exists and is not a folder."
            ),
        }

    try:

        path.mkdir(
            parents=True,
            exist_ok=False
        )

        return {
            "success": True,
            "folder": str(path)
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================
# File creation
# =========================

def create_file(filename, location="Desktop", content=""):
    filename = filename.strip().strip('"')
    location = location.strip().strip('"')

    if not filename:
        return {
            "success": False,
            "message": "Please provide a filename."
        }

    # Only accept a filename, not a path
    if Path(filename).name != filename or filename in (".", ".."):
        return {
            "success": False,
            "message": "Please provide a filename without a folder path."
        }

    # Supported text and code file formats
    allowed_extensions = {
        ".txt", ".md", ".csv", ".json", ".py",
        ".html", ".css", ".js", ".xml", ".yaml",
        ".yml", ".log", ".ini", ".bat", ".ps1",
        ".sql", ".toml", ".ts", ".jsx", ".tsx",
        ".java", ".c", ".cpp", ".h", ".cs",
        ".php", ".rb", ".go", ".rs", ".sh",
        ".r", ".swift", ".kt", ".dart", ".vue",
        ".svelte", ".ipynb"
    }

    extension = Path(filename).suffix.lower()

    if extension not in allowed_extensions:
        return {
            "success": False,
            "message": (
                f"File type '{extension or '(no extension)'}' "
                "isn't supported by this version yet."
            )
        }

    # Resolve common destination folders
    common_folders = {
        "desktop": Path.home() / "Desktop",
        "downloads": Path.home() / "Downloads",
        "documents": Path.home() / "Documents",
        "pictures": Path.home() / "Pictures",
        "videos": Path.home() / "Videos",
        "music": Path.home() / "Music",
        "home": Path.home(),
    }

    if location.lower() in common_folders:
        destination = common_folders[location.lower()]
    else:
        destination = Path(location).expanduser()

        if not destination.is_absolute():
            destination = Path.home() / destination

    if not destination.exists() or not destination.is_dir():
        return {
            "success": False,
            "message": (
                f"The destination folder '{destination}' "
                "doesn't exist."
            )
        }

    target = destination / filename

    # Never overwrite an existing file or folder
    if target.exists():
        return {
            "success": False,
            "message": (
                f"'{target}' already exists. "
                "I didn't overwrite it."
            )
        }

    try:
        # Exclusive creation prevents overwriting an existing file
        with target.open("x", encoding="utf-8", newline="") as file:
            file.write(content)

        return {
            "success": True,
            "file": str(target),
            "message": f"Created '{filename}' successfully."
        }

    except (OSError, ValueError, UnicodeError) as e:
        return {
            "success": False,
            "message": str(e)
        }

# =========================
# File launcher
# =========================

def open_file(file_path):

    file_path = Path(
        file_path.strip()
    )

    if not file_path.exists():

        return {
            "success": False,
            "message": (
                f"I couldn't find the file "
                f"'{file_path}'."
            ),
        }

    if not file_path.is_file():

        return {
            "success": False,
            "message": (
                f"'{file_path}' is not a file."
            ),
        }

    try:

        os.startfile(file_path)

        return {
            "success": True,
            "file": str(file_path)
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================
# Move file
# =========================

def move_file(source, destination):

    source = Path(source.strip())
    destination = Path(destination.strip())

    # Resolve relative paths from the user's home directory
    if not source.is_absolute():
        source = Path.home() / source

    if not destination.is_absolute():
        destination = Path.home() / destination

    # Check source
    if not source.exists():

        return {
            "success": False,
            "message": (
                f"I couldn't find the source "
                f"'{source}'."
            ),
        }

    if not source.is_file():

        return {
            "success": False,
            "message": (
                f"'{source}' is not a file."
            ),
        }

    # Destination must be a folder
    if not destination.exists():

        return {
            "success": False,
            "message": (
                f"The destination folder "
                f"'{destination}' does not exist."
            ),
        }

    if not destination.is_dir():

        return {
            "success": False,
            "message": (
                f"'{destination}' is not a folder."
            ),
        }

    target = destination / source.name

    # Prevent accidental overwrite
    if target.exists():

        return {
            "success": False,
            "message": (
                f"A file named '{source.name}' "
                f"already exists in '{destination}'."
            ),
        }

    try:

        shutil.move(
            str(source),
            str(target)
        )

        return {
            "success": True,
            "source": str(source),
            "destination": str(target)
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================
# Copy file or folder
# =========================

def copy_item(source, destination):

    source = Path(source.strip())
    destination = Path(destination.strip())

    # Resolve relative paths from the user's home directory
    if not source.is_absolute():
        source = Path.home() / source

    if not destination.is_absolute():
        destination = Path.home() / destination

    if not source.exists():
        return {
            "success": False,
            "message": f"I couldn't find the source '{source}'."
        }

    if not destination.exists():
        return {
            "success": False,
            "message": f"The destination folder '{destination}' does not exist."
        }

    if not destination.is_dir():
        return {
            "success": False,
            "message": f"'{destination}' is not a folder."
        }

    target = destination / source.name

    # Prevent overwriting an existing file or folder
    if target.exists():
        return {
            "success": False,
            "message": f"'{target}' already exists. I didn't overwrite it."
        }

    # Prevent copying a folder into itself or one of its descendants
    if source.is_dir():
        try:
            source_resolved = source.resolve()
            destination_resolved = destination.resolve()
            if destination_resolved == source_resolved or source_resolved in destination_resolved.parents:
                return {
                    "success": False,
                    "message": "A folder cannot be copied into itself or one of its subfolders."
                }
        except OSError as e:
            return {
                "success": False,
                "message": str(e)
            }

    try:
        if source.is_dir():
            shutil.copytree(source, target)
            item_type = "folder"
        else:
            shutil.copy2(source, target)
            item_type = "file"

        return {
            "success": True,
            "item_type": item_type,
            "source": str(source),
            "destination": str(target)
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================
# Rename file or folder
# =========================

def rename_file(path, new_name):

    path = Path(path.strip())
    new_name = new_name.strip()

    # Resolve relative paths from the user's home directory
    if not path.is_absolute():
        path = Path.home() / path

    if not path.exists():
        return {
            "success": False,
            "message": f"I couldn't find '{path}'."
        }

    if not new_name:
        return {
            "success": False,
            "message": "The new name cannot be empty."
        }

    # Accept a name, not a different destination path
    if Path(new_name).name != new_name or new_name in (".", ".."):
        return {
            "success": False,
            "message": "Please provide a new name, not a folder path."
        }

    target = path.with_name(new_name)

    # Prevent accidental overwrite
    if target.exists():
        return {
            "success": False,
            "message": f"'{target}' already exists."
        }

    try:
        path.rename(target)

        return {
            "success": True,
            "old_path": str(path),
            "new_path": str(target)
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================
# Delete file or folder safely
# =========================

def delete_item(path):

    raw_path = path.strip().strip('"')

    if not raw_path:
        return {
            "success": False,
            "message": "Please provide the path of the file or folder to delete."
        }

    target = Path(raw_path).expanduser()

    # Resolve relative paths from the user's home directory
    if not target.is_absolute():
        target = Path.home() / target

    # Refuse symlinks so the operation cannot unexpectedly target another location
    if target.is_symlink():
        return {
            "success": False,
            "message": "For safety, I won't delete a symbolic link or shortcut this way."
        }

    if not target.exists():
        return {
            "success": False,
            "message": f"I couldn't find '{target}'."
        }

    try:
        target = target.resolve(strict=True)
        home = Path.home().resolve()
    except OSError as e:
        return {
            "success": False,
            "message": str(e)
        }

    # Protect the user's profile root and its parent directories
    if target == home or target in home.parents:
        return {
            "success": False,
            "message": "For safety, I won't delete your user profile folder or any of its parent directories."
        }

    # Protect Windows and installed-program directories
    protected_roots = [
        Path(os.environ.get("WINDIR", r"C:\Windows")),
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    ]

    for protected in protected_roots:
        try:
            protected = protected.resolve()
            if target == protected or protected in target.parents:
                return {
                    "success": False,
                    "message": "For safety, I won't delete items inside Windows or installed-program directories."
                }
        except OSError:
            continue

    # Never allow deleting a drive root
    if target.parent == target:
        return {
            "success": False,
            "message": "For safety, a drive root cannot be deleted."
        }

    if os.name != "nt":
        return {
            "success": False,
            "message": "Sending items to the Recycle Bin is supported here only on Windows."
        }

    item_type = "folder" if target.is_dir() else "file"

    try:
        # SHFileOperation with FO_DELETE and FOF_ALLOWUNDO sends the item to
        # the Windows Recycle Bin rather than permanently deleting it.
        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("wFunc", wintypes.UINT),
                ("pFrom", wintypes.LPCWSTR),
                ("pTo", wintypes.LPCWSTR),
                ("fFlags", wintypes.WORD),
                ("fAnyOperationsAborted", wintypes.BOOL),
                ("hNameMappings", wintypes.LPVOID),
                ("lpszProgressTitle", wintypes.LPCWSTR),
            ]

        # A double-NUL-terminated path is required by the Windows shell API.
        from_buffer = ctypes.create_unicode_buffer(str(target) + "\0")
        operation = SHFILEOPSTRUCTW()
        operation.hwnd = None
        operation.wFunc = 3  # FO_DELETE
        operation.pFrom = ctypes.cast(from_buffer, wintypes.LPCWSTR)
        operation.pTo = None
        operation.fFlags = 0x0040 | 0x0010 | 0x0004 | 0x0400  # undo, no confirm, silent, no error UI
        operation.fAnyOperationsAborted = False
        operation.hNameMappings = None
        operation.lpszProgressTitle = None

        result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operation))

        if result != 0 or operation.fAnyOperationsAborted:
            return {
                "success": False,
                "message": "Windows couldn't move this item to the Recycle Bin. It may be in use or access may be denied."
            }

        return {
            "success": True,
            "item_type": item_type,
            "deleted_path": str(target),
            "message": "Moved to the Recycle Bin. You can restore it from there if needed."
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================
# File and folder search
# =========================

def search_files(query, location="home"):

    query = query.strip().lower()

    search_locations = {

        "home":
            Path.home(),

        "desktop":
            Path.home() / "Desktop",

        "downloads":
            Path.home() / "Downloads",

        "documents":
            Path.home() / "Documents",

        "pictures":
            Path.home() / "Pictures",

        "videos":
            Path.home() / "Videos",

        "music":
            Path.home() / "Music",

    }

    root = search_locations.get(
        location.lower().strip(),
        Path.home()
    )

    if not root.exists():

        return {
            "success": False,
            "message": (
                f"Search location '{location}' "
                "does not exist."
            ),
        }

    matches = []

    try:

        for item in root.rglob("*"):

            try:

                name = item.name.lower()

            except OSError:

                continue

            if query in name:

                matches.append({
                    "name": item.name,
                    "path": str(item),
                    "type": (
                        "folder"
                        if item.is_dir()
                        else "file"
                    )
                })

            if len(matches) >= 25:
                break

    except (PermissionError, OSError):

        pass

    if not matches:

        return {
            "success": True,
            "found": 0,
            "results": []
        }

    return {
        "success": True,
        "found": len(matches),
        "results": matches
    }


# =========================
# Open website
# =========================

def open_website(url):

    url = url.strip()

    if not url.startswith(
        ("http://", "https://")
    ):

        url = "https://" + url

    try:

        webbrowser.open(url)

        return {
            "success": True,
            "url": url
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================
# Lock computer
# =========================

def lock_computer():

    try:

        subprocess.run(
            [
                "rundll32.exe",
                "user32.dll",
                "LockWorkStation"
            ]
        )

        return {
            "success": True,
            "message": "Computer locked."
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================
# Open Windows Settings
# =========================

def open_settings():

    try:

        os.startfile(
            "ms-settings:"
        )

        return {
            "success": True,
            "message": "Windows Settings opened."
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================
# Tool registry
# =========================

TOOLS = {

    "get_system_info":
        get_system_info,

    "open_application":
        open_application,

    "get_battery_status":
        get_battery_status,

    "open_folder":
        open_folder,

    "create_folder":
        create_folder,

    "create_file": 
        create_file,

    "open_file":
        open_file,

    "move_file":
        move_file,

    "rename_file":
        rename_file,

    "copy_item":
        copy_item,

    "delete_item":
        delete_item,

    "open_website":
        open_website,

    "lock_computer":
        lock_computer,

    "open_settings":
        open_settings,

    "search_files":
        search_files,
}


# =========================
# Groq tool declarations
# =========================

TOOL_DECLARATIONS = [

    {
        "type": "function",
        "name": "get_system_info",

        "description": (
            "Gets the current computer's system information, "
            "including CPU usage, RAM usage, disk usage, "
            "and operating system."
        ),

        "parameters": {
            "type": "object",
            "properties": {},
        },
    },

    {
        "type": "function",
        "name": "open_application",

        "description": (
            "Opens an application installed on the user's "
            "Windows computer. Use this whenever the user "
            "asks to open, launch, start, or run an application."
        ),

        "parameters": {
            "type": "object",
            "properties": {

                "application": {
                    "type": "string",
                    "description": (
                        "The name of the application "
                        "the user wants to open."
                    ),
                }

            },

            "required": ["application"],
        },
    },

    {
        "type": "function",
        "name": "get_battery_status",

        "description": (
            "Gets the computer's current battery percentage "
            "and whether it is connected to power."
        ),

        "parameters": {
            "type": "object",
            "properties": {},
        },
    },

    {
        "type": "function",
        "name": "open_folder",

        "description": (
            "Opens a folder in Windows File Explorer. "
            "Common folders include Downloads, Documents, "
            "Desktop, Pictures, Videos, Music, and Home. "
            "It can also open an exact folder path."
        ),

        "parameters": {
            "type": "object",
            "properties": {

                "folder": {
                    "type": "string",
                    "description": (
                        "The folder the user wants to open."
                    ),
                }

            },

            "required": ["folder"],
        },
    },

    {
        "type": "function",
        "name": "create_folder",

        "description": (
            "Creates a new folder on the user's computer. "
            "Use this when the user asks to create or make "
            "a new folder. The folder can be specified using "
            "a complete path."
        ),

        "parameters": {
            "type": "object",
            "properties": {

                "folder": {
                    "type": "string",
                    "description": (
                        "The complete path of the new folder "
                        "to create."
                    ),
                }

            },

            "required": ["folder"],
        },
    },

    {
        "type": "function",
        "name": "create_file",
        "description": (
            "Creates a new text or code file on the user's computer. "
            "Use this whenever the user asks to make, create, write, "
            "or generate a file. Supported formats include Python, "
            "JavaScript, HTML, CSS, JSON, CSV, Markdown, and plain text, "
            "as well as other supported text-based programming formats. "
            "Generate appropriate content for the requested purpose. "
            "Pass only the filename in filename, the destination folder "
            "in location, and the complete generated text in content. "
            "The location defaults to Desktop. Never overwrite an existing file."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filename including its extension."
                },
                "location": {
                    "type": "string",
                    "description": (
                        "Destination folder name or complete path. "
                        "Defaults to Desktop."
                    ),
                    "default": "Desktop"
                },
                "content": {
                    "type": "string",
                    "description": (
                        "The complete text or source code to write "
                        "into the new file."
                    ),
                    "default": ""
                }
            },
            "required": ["filename"]
        }
    },

    {
        "type": "function",
        "name": "open_file",

        "description": (
            "Opens a specific file using the default Windows "
            "application associated with that file type. "
            "Use this after finding a file when the user asks "
            "to open it."
        ),

        "parameters": {
            "type": "object",
            "properties": {

                "file_path": {
                    "type": "string",
                    "description": (
                        "The complete path of the file to open."
                    ),
                }

            },

            "required": ["file_path"],
        },
    },

    {
        "type": "function",
        "name": "move_file",

        "description": (
            "Moves a file from one location to another folder. "
            "Use this when the user asks to move a file. "
            "The source must be the complete file path and "
            "the destination must be an existing folder. "
            "Do not overwrite an existing file."
        ),

        "parameters": {
            "type": "object",
            "properties": {

                "source": {
                    "type": "string",
                    "description": (
                        "The complete path of the file "
                        "that should be moved."
                    ),
                },

                "destination": {
                    "type": "string",
                    "description": (
                        "The folder where the file should "
                        "be moved."
                    ),
                }

            },

            "required": [
                "source",
                "destination"
            ],
        },
    },

    {
        "type": "function",
        "name": "copy_item",

        "description": (
            "Copies an existing file or folder into an existing destination folder. "
            "Use this when the user asks to copy or duplicate a file or folder. "
            "The source must be the complete path of the existing file or folder, "
            "and destination must be the complete path of an existing folder. "
            "Never overwrite an existing item. Do not copy a folder into itself "
            "or one of its own subfolders."
        ),

        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "The complete path of the file or folder to copy."
                },
                "destination": {
                    "type": "string",
                    "description": "The complete path of the existing folder to copy the item into."
                }
            },
            "required": ["source", "destination"],
        },
    },

    {
        "type": "function",
        "name": "delete_item",

        "description": (
            "Moves a specified file or folder to the Windows Recycle Bin. "
            "Use this when the user explicitly asks to delete a file or folder. "
            "Pass the complete path of exactly one existing item. "
            "This is recoverable through the Recycle Bin, not a permanent delete. "
            "Never delete broad or protected system locations."
        ),

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The complete path of the single file or folder to move to the Recycle Bin."
                }
            },
            "required": ["path"],
        },
    },

    {
        "type": "function",
        "name": "rename_file",

        "description": (
            "Renames an existing file or folder without moving it. "
            "Use this when the user asks to rename a file or folder. "
            "The path must identify the existing item, and new_name "
            "must be only the new name, not a destination path. "
            "Preserve the file extension unless the user asks to change it. "
            "Never overwrite an existing item."
        ),

        "parameters": {
            "type": "object",
            "properties": {

                "path": {
                    "type": "string",
                    "description": "The complete path of the existing file or folder."
                },

                "new_name": {
                    "type": "string",
                    "description": "The new filename or folder name."
                }

            },

            "required": ["path", "new_name"],
        },
    },

    {
        "type": "function",
        "name": "search_files",

        "description": (
            "Searches the user's files and folders by name. "
            "Use this when the user asks to find a file or folder. "
            "The search is read-only and does not modify anything."
        ),

        "parameters": {
            "type": "object",
            "properties": {

                "query": {
                    "type": "string",
                    "description": (
                        "The filename or folder name, or part "
                        "of the name, that the user wants to find."
                    ),
                },

                "location": {
                    "type": "string",
                    "description": (
                        "Where to search. Use 'home', 'desktop', "
                        "'downloads', 'documents', 'pictures', "
                        "'videos', or 'music'."
                    ),
                    "default": "home",
                },

            },

            "required": ["query"],
        },
    },

    {
        "type": "function",
        "name": "open_website",

        "description": (
            "Opens a website in the user's default web browser."
        ),

        "parameters": {
            "type": "object",
            "properties": {

                "url": {
                    "type": "string",
                    "description": (
                        "The website URL to open."
                    ),
                }

            },

            "required": ["url"],
        },
    },

    {
        "type": "function",
        "name": "lock_computer",

        "description": (
            "Locks the user's Windows computer."
        ),

        "parameters": {
            "type": "object",
            "properties": {},
        },
    },

    {
        "type": "function",
        "name": "open_settings",

        "description": (
            "Opens Windows Settings."
        ),

        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]


# =========================
# Tool executor
# =========================

def execute_tool(
    tool_name,
    arguments=None
):

    if tool_name not in TOOLS:

        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    function = TOOLS[tool_name]

    no_argument_tools = [
        "get_system_info",
        "get_battery_status",
        "lock_computer",
        "open_settings",
    ]

    if tool_name in no_argument_tools:

        return function()

    if arguments:

        return function(**arguments)

    return function()