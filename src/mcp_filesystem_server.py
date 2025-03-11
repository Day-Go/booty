import os
import json
import shutil
import glob
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn


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


# Initialize FastAPI app
app = FastAPI(
    title="MCP Filesystem Server",
    description="Model Control Protocol server for filesystem operations",
    version="0.1.0",
)

# Define allowed directories (for security)
ALLOWED_DIRECTORIES = ["/home/dago/dev/projects/llm"]


# Helper to validate path is within allowed directories
def validate_path(path: str) -> bool:
    path = os.path.abspath(path)
    return any(path.startswith(allowed_dir) for allowed_dir in ALLOWED_DIRECTORIES)


# Filesystem Operations
@app.post("/read_file", response_model=FileReadResponse)
async def read_file(request: FileReadRequest):
    if not validate_path(request.path):
        raise HTTPException(
            status_code=403, detail="Access to this path is not allowed"
        )

    try:
        with open(request.path, "r") as file:
            content = file.read()
        return {"content": content, "path": request.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@app.post("/write_file", response_model=FileWriteResponse)
async def write_file(request: FileWriteRequest):
    if not validate_path(request.path):
        raise HTTPException(
            status_code=403, detail="Access to this path is not allowed"
        )

    try:
        os.makedirs(os.path.dirname(request.path), exist_ok=True)
        with open(request.path, "w") as file:
            file.write(request.content)
        return {"success": True, "path": request.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {str(e)}")


@app.post("/list_directory", response_model=DirListResponse)
async def list_directory(request: DirListRequest):
    if not validate_path(request.path):
        raise HTTPException(
            status_code=403, detail="Access to this path is not allowed"
        )

    try:
        entries = []
        for entry in os.listdir(request.path):
            entry_path = os.path.join(request.path, entry)
            entry_info = {
                "name": entry,
                "path": entry_path,
                "type": "directory" if os.path.isdir(entry_path) else "file",
                "size": os.path.getsize(entry_path)
                if os.path.isfile(entry_path)
                else None,
            }
            entries.append(entry_info)
        return {"entries": entries, "path": request.path}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing directory: {str(e)}"
        )


@app.post("/create_directory", response_model=DirCreateResponse)
async def create_directory(request: DirCreateRequest):
    if not validate_path(request.path):
        raise HTTPException(
            status_code=403, detail="Access to this path is not allowed"
        )

    try:
        os.makedirs(request.path, exist_ok=True)
        return {"success": True, "path": request.path}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating directory: {str(e)}"
        )


@app.post("/search_files", response_model=SearchResponse)
async def search_files(request: SearchRequest):
    if not validate_path(request.path):
        raise HTTPException(
            status_code=403, detail="Access to this path is not allowed"
        )

    try:
        search_pattern = os.path.join(request.path, request.pattern)
        matches = glob.glob(search_pattern, recursive=True)
        return {"matches": matches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching files: {str(e)}")


@app.get("/list_allowed_directories")
async def list_allowed_directories():
    return {"allowed_directories": ALLOWED_DIRECTORIES}


# Main entry point
if __name__ == "__main__":
    uvicorn.run("mcp_filesystem_server:app", host="127.0.0.1", port=8000, reload=True)

