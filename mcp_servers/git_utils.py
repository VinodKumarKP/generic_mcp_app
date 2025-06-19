import logging
import os
import shutil
import tempfile
from typing import List
from pathlib import Path

import nest_asyncio  # Added import
from git import Repo

nest_asyncio.apply()  # Added call

from fastmcp import FastMCP

# from pydantic import BaseModel # Removed unused import

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("git-tools")

class GitHubError(Exception):
    """Base exception class for GitHub utility errors."""
    pass

# File extensions to skip during repository analysis
SKIP_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip',
    '.jar', '.class', '.pyc', '.exe', '.dll', '.so',
    '.md', '.json', '.xml', '.txt'
}

@mcp.tool()
async def clone_repository(git_url:str, branch:str) -> str:
    """
    Clone the specified git repository.

    Returns:
        str: Path to the cloned repository

    Raises:
        GitHubError: If cloning fails
    """
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Cloning {git_url} (branch: {branch}) to {temp_dir}...")

    try:
        # Use GitPython to clone the repository
        repo = Repo.clone_from(git_url, temp_dir)
        repo.git.checkout(branch)
        logger.info(f"Successfully cloned repository to {temp_dir}")
        return temp_dir
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"Error cloning repository: {str(e)}")
        raise GitHubError(f"Failed to clone repository: {str(e)}") from e

@mcp.tool()
async def get_file_list(repo_path: str) -> List[str]:
    """
    Get list of files in the repository, excluding binary and hidden files.

    Args:
        repo_path: Path to repository

    Returns:
        list: List of file paths relative to repository root
    """
    file_list = []
    repo_path = Path(repo_path)

    try:
        for path in repo_path.rglob('*'):
            # Skip directories
            if path.is_dir():
                continue

            # Skip .git directory
            if '.git' in path.parts:
                continue

            # Skip hidden directories and files
            if any(part.startswith('.') for part in path.parts):
                continue

            # Skip __pycache__ and similar directories
            if any(part.startswith('__') for part in path.parts):
                continue

            # Skip files with extensions we want to ignore
            if path.suffix.lower() in SKIP_EXTENSIONS:
                continue

            # Add relative path to the list
            rel_path = str(path.relative_to(repo_path))
            file_list.append(rel_path)

        return file_list
    except Exception as e:
        logger.error(f"Error getting file list: {str(e)}")
        return []

if __name__ == "__main__":
    mcp.run()