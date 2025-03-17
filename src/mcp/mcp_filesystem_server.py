import os
import json
import shutil
import glob
import subprocess
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn
from pathlib import Path


# MCP Models for request/response
class FileReadRequest(BaseModel):
    path: str = Field(..., description="Path to the file to read")


class FileReadResponse(BaseModel):
    content: str = Field(..., description="Content of the file")
    path: str = Field(..., description="Path of the file that was read")


class FileWriteRequest(BaseModel):
    path: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")


class FileWriteResponse(BaseModel):
    success: bool = Field(..., description="Whether the write operation was successful")
    path: str = Field(..., description="Path of the file that was written")


class DirListRequest(BaseModel):
    path: str = Field(..., description="Path to the directory to list")


class DirListResponse(BaseModel):
    entries: List[Dict[str, Any]] = Field(..., description="List of directory entries")
    path: str = Field(..., description="Path that was listed")


class DirCreateRequest(BaseModel):
    path: str = Field(..., description="Path to the directory to create")


class DirCreateResponse(BaseModel):
    success: bool = Field(
        ..., description="Whether the directory creation was successful"
    )
    path: str = Field(..., description="Path of the directory that was created")


class SearchRequest(BaseModel):
    path: str = Field(..., description="Base path to search in")
    pattern: str = Field(..., description="Glob pattern to match files")


class SearchResponse(BaseModel):
    matches: List[str] = Field(..., description="List of matching file paths")


class GrepSearchRequest(BaseModel):
    path: str = Field(..., description="Base path to search in")
    pattern: str = Field(..., description="Grep pattern to search for")
    recursive: bool = Field(True, description="Whether to search recursively")
    case_sensitive: bool = Field(
        False, description="Whether to use case-sensitive matching"
    )


class GrepSearchResponse(BaseModel):
    matches: List[Dict[str, str]] = Field(
        ..., description="List of matching files with line content"
    )


class ChangeDirectoryRequest(BaseModel):
    path: str = Field(..., description="Directory to change to")


class ChangeDirectoryResponse(BaseModel):
    success: bool = Field(
        ..., description="Whether the directory change was successful"
    )
    current_dir: str = Field(..., description="New current working directory")
    previous_dir: str = Field(..., description="Previous working directory")


class WorkingDirectoryResponse(BaseModel):
    current_dir: str = Field(..., description="Current working directory")
    script_dir: str = Field(..., description="Directory containing the server script")


# Initialize FastAPI app
app = FastAPI(
    title="MCP Filesystem Server",
    description="Model Control Protocol server for filesystem operations",
    version="0.1.0",
)

# Define allowed directories (for security)
ALLOWED_DIRECTORIES = [
    "/home/dago/dev/projects/llm",
]

# Track the current working directory
# This will be initialized to the directory from which the script was run
CURRENT_WORKING_DIRECTORY = os.getcwd()

# Store the original script directory for reference
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


# Helper to validate path is within allowed directories
def validate_path(path: str) -> bool:
    path = os.path.abspath(path)
    return True
    # return any(path.startswith(allowed_dir) for allowed_dir in ALLOWED_DIRECTORIES)


def get_current_working_directory() -> str:
    """
    Get the current working directory.

    Returns:
        The current working directory path
    """
    global CURRENT_WORKING_DIRECTORY
    return CURRENT_WORKING_DIRECTORY


def set_current_working_directory(path: str) -> str:
    """
    Update the stored current working directory.

    Args:
        path: New directory path

    Returns:
        The new current working directory path
    """
    global CURRENT_WORKING_DIRECTORY
    path = os.path.abspath(path)
    CURRENT_WORKING_DIRECTORY = path
    return CURRENT_WORKING_DIRECTORY


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Filesystem Operations
@app.post("/read_file", response_model=FileReadResponse)
async def read_file(request: FileReadRequest):
    """
    Read a file from the filesystem.
    Returns the content of the file if successful.
    """
    if not validate_path(request.path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this path is not allowed due to security restrictions",
        )

    try:
        path = Path(request.path)

        # Check if path exists
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {request.path}",
            )

        # Check if path is a file
        if not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path exists but is not a file: {request.path}",
            )

        # Check if file is readable
        if not os.access(path, os.R_OK):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot read file {request.path}",
            )

        # Try to read the file
        try:
            with open(path, "r") as file:
                content = file.read()
            return {"content": content, "path": request.path}
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File contains non-text content and cannot be read as text: {request.path}",
            )
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot access file {request.path}",
            )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Convert other exceptions to proper HTTP errors with context
        error_message = f"Error reading file: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


@app.post("/write_file", response_model=FileWriteResponse)
async def write_file(request: FileWriteRequest):
    """
    Write content to a file.
    Creates the file if it does not exist.
    Creates parent directories if they do not exist.
    """
    if not validate_path(request.path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this path is not allowed due to security restrictions",
        )

    try:
        path = Path(request.path)

        # Ensure parent directory exists
        parent_dir = path.parent
        if not parent_dir.exists():
            try:
                os.makedirs(parent_dir, exist_ok=True)
            except PermissionError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: Cannot create directory {parent_dir}",
                )
            except OSError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create parent directory: {str(e)}",
                )

        # Check if the path exists and is not a directory
        if path.exists() and path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot write to {request.path}: Path exists and is a directory",
            )

        # Check if parent directory is writable
        if not os.access(parent_dir, os.W_OK):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot write to directory {parent_dir}",
            )

        # If file exists, check if it's writable
        if path.exists() and not os.access(path, os.W_OK):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot write to file {request.path}",
            )

        # Try to write to the file
        try:
            with open(path, "w") as file:
                file.write(request.content)
            return {"success": True, "path": request.path}
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot write to file {request.path}",
            )
        except OSError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to write to file: {str(e)}",
            )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Convert other exceptions to proper HTTP errors with context
        error_message = f"Error writing file: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


@app.post("/list_directory", response_model=DirListResponse)
async def list_directory(request: DirListRequest):
    """
    List contents of a directory.
    Returns information about files and subdirectories.
    """
    if not validate_path(request.path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this path is not allowed due to security restrictions",
        )

    try:
        path = Path(request.path)

        # Check if path exists
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {request.path}",
            )

        # Check if path is a directory
        if not path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path exists but is not a directory: {request.path}",
            )

        # Check if directory is readable
        if not os.access(path, os.R_OK):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot read directory {request.path}",
            )

        # Try to list the directory
        try:
            entries = []
            for entry in os.listdir(path):
                entry_path = path / entry
                try:
                    size = os.path.getsize(entry_path) if entry_path.is_file() else None
                except OSError:
                    size = None  # Fall back if we can't get size for some reason

                entry_info = {
                    "name": entry,
                    "path": str(entry_path),
                    "type": "directory" if entry_path.is_dir() else "file",
                    "size": size,
                }
                entries.append(entry_info)
            return {"entries": entries, "path": request.path}
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot access directory {request.path}",
            )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Convert other exceptions to proper HTTP errors with context
        error_message = f"Error listing directory: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


@app.post("/create_directory", response_model=DirCreateResponse)
async def create_directory(request: DirCreateRequest):
    """
    Create a new directory.
    Creates parent directories if they do not exist.
    """
    if not validate_path(request.path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this path is not allowed due to security restrictions",
        )

    try:
        path = Path(request.path)

        # Check if path already exists
        if path.exists():
            if path.is_dir():
                # Directory already exists
                return {"success": True, "path": request.path}
            else:
                # Path exists but is not a directory
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot create directory: Path exists and is not a directory: {request.path}",
                )

        # Check if parent directory is writable
        parent_dir = path.parent
        if parent_dir.exists() and not os.access(parent_dir, os.W_OK):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot create directory in {parent_dir}",
            )

        # Try to create the directory
        try:
            os.makedirs(path, exist_ok=True)
            return {"success": True, "path": request.path}
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot create directory {request.path}",
            )
        except OSError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create directory: {str(e)}",
            )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Convert other exceptions to proper HTTP errors with context
        error_message = f"Error creating directory: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


@app.post("/search_files", response_model=SearchResponse)
async def search_files(request: SearchRequest):
    """
    Search for files matching a glob pattern.
    Returns a list of matching file paths.
    """
    if not validate_path(request.path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this path is not allowed due to security restrictions",
        )

    try:
        path = Path(request.path)

        # Check if path exists
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {request.path}",
            )

        # Check if path is a directory
        if not path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path exists but is not a directory: {request.path}",
            )

        # Check if directory is readable
        if not os.access(path, os.R_OK):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot read directory {request.path}",
            )

        # Try to search for files
        try:
            search_pattern = os.path.join(request.path, request.pattern)
            matches = glob.glob(search_pattern, recursive=True)
            return {"matches": matches}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in glob pattern: {str(e)}",
            )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Convert other exceptions to proper HTTP errors with context
        error_message = f"Error searching files: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


@app.get("/list_allowed_directories")
async def list_allowed_directories():
    """
    List all directories that the server is allowed to access.
    """
    return {"allowed_directories": ALLOWED_DIRECTORIES}


@app.get("/get_working_directory", response_model=WorkingDirectoryResponse)
async def get_working_directory():
    """
    Get the current working directory and script directory.

    Returns:
        Dict with current working directory and script directory
    """
    try:
        return {
            "current_dir": get_current_working_directory(),
            "script_dir": SCRIPT_DIRECTORY,
        }
    except Exception as e:
        error_message = f"Error getting working directory: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


@app.post("/change_directory", response_model=ChangeDirectoryResponse)
async def change_directory(request: ChangeDirectoryRequest):
    """
    Change the current working directory.
    Returns the new current working directory.

    This does not actually change the OS process's working directory,
    but updates the server's tracking of the current directory.
    """
    if not validate_path(request.path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this path is not allowed due to security restrictions",
        )

    try:
        path = Path(request.path)

        # Check if path exists
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {request.path}",
            )

        # Check if path is a directory
        if not path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path exists but is not a directory: {request.path}",
            )

        # Check if directory is accessible
        if not os.access(path, os.X_OK):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot access directory {request.path}",
            )

        # Change the tracked directory
        try:
            previous_dir = get_current_working_directory()
            new_dir = set_current_working_directory(str(path))

            return {
                "success": True,
                "current_dir": new_dir,
                "previous_dir": previous_dir,
            }
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot change to directory {request.path}",
            )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Convert other exceptions to proper HTTP errors with context
        error_message = f"Error changing directory: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


@app.post("/grep_search", response_model=GrepSearchResponse)
async def grep_search(request: GrepSearchRequest):
    """
    Search files using grep for content matching.
    Returns matches with file path, line number, and line content.
    """
    if not validate_path(request.path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this path is not allowed due to security restrictions",
        )

    try:
        path = Path(request.path)

        # Check if path exists
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {request.path}",
            )

        # Check if path is a directory (for recursive search) or a file
        if not (path.is_dir() or path.is_file()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path does not exist or is not accessible: {request.path}",
            )

        # Check if path is readable
        if not os.access(path, os.R_OK):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Cannot read from {request.path}",
            )

        # Validate pattern is not empty
        if not request.pattern.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search pattern cannot be empty",
            )

        # Try to run grep command
        try:
            # Build grep command
            grep_cmd = ["grep"]

            # Add options
            if request.recursive:
                grep_cmd.append("-r")
            if not request.case_sensitive:
                grep_cmd.append("-i")

            # Add pattern matching and some context
            grep_cmd.extend(["-n", "--color=never", request.pattern, str(path)])

            # Execute the grep command
            result = subprocess.run(
                grep_cmd,
                capture_output=True,
                text=True,
                check=False,  # Don't raise exception on non-zero exit (no matches)
                timeout=30,
            )

            # Check for grep errors (excluding "no matches" which is exit code 1)
            if result.returncode > 1:
                error_msg = (
                    result.stderr.strip() if result.stderr else "Unknown grep error"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Grep command failed: {error_msg}",
                )

            # Process results
            matches = []
            if result.stdout:
                for line in result.stdout.splitlines():
                    # Parse the grep output (filename:line_number:content)
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        matches.append(
                            {"file": parts[0], "line": parts[1], "content": parts[2]}
                        )

            return {"matches": matches}
        except subprocess.SubprocessError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error executing grep command: {str(e)}",
            )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Convert other exceptions to proper HTTP errors with context
        error_message = f"Error searching with grep: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


# Main entry point
if __name__ == "__main__":
    uvicorn.run("mcp_filesystem_server:app", host="127.0.0.1", port=8000, reload=True)
