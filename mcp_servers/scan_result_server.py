#!/usr/bin/env python3
"""
Security Scan Results MCP Server (Client)
Fetches scan results from Flask API server and provides them via MCP tools
"""
import os
import sys

import requests
from typing import Dict, Any
from fastmcp import FastMCP

file_root = os.path.dirname(os.path.abspath(__file__))
path_list = [
    file_root,
    os.path.dirname(file_root)
]
for path in path_list:
    if path not in sys.path:
        sys.path.append(path)

# Initialize FastMCP
mcp = FastMCP("Security Scan Results MCP Client")

# Configuration
FLASK_SERVER_BASE_URL = "http://localhost:5001"

from utils.scan_results import (get_nexus_scan_results_impl,
                                get_sonar_scan_results_impl,
                                get_fortify_scan_results_impl,
                                get_all_scan_results as get_all_scan_results_impl)


def _make_api_request(endpoint: str, params: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Make HTTP request to Flask API server
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        JSON response as dictionary
        
    Raises:
        Exception: If API request fails
    """
    try:
        url = f"{FLASK_SERVER_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        raise Exception(f"Failed to connect to Flask server at {FLASK_SERVER_BASE_URL}. Make sure the server is running.")
    except requests.exceptions.Timeout:
        raise Exception("Request to Flask server timed out")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP error from Flask server: {e}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


@mcp.tool()
def get_sonar_scan_results(project_key: str = "default-project") -> Dict[str, Any]:
    """
    Collect SonarQube scan results for code quality and security analysis.

    Args:
        project_key: The project identifier in SonarQube

    Returns:
        Dictionary containing SonarQube scan results
    """
    try:
        return _make_api_request("/api/scans/sonar", {"project_key": project_key})
    except Exception as e:
        return get_sonar_scan_results_impl(project_key=project_key)


@mcp.tool()
def get_fortify_scan_results(application_name: str = "default-app") -> Dict[str, Any]:
    """
    Collect Fortify Static Code Analyzer (SCA) scan results for security vulnerabilities.

    Args:
        application_name: The application name in Fortify

    Returns:
        Dictionary containing Fortify scan results
    """
    try:
        return _make_api_request("/api/scans/fortify", {"application_name": application_name})
    except Exception as e:
        return get_fortify_scan_results_impl(application_name=application_name)


@mcp.tool()
def get_nexus_scan_results(repository_name: str = "default-repo") -> Dict[str, Any]:
    """
    Collect Nexus IQ scan results for open source component vulnerabilities and license compliance.

    Args:
        repository_name: The repository name in Nexus IQ

    Returns:
        Dictionary containing Nexus IQ scan results
    """
    try:
        return _make_api_request("/api/scans/nexus", {"repository_name": repository_name})
    except Exception as e:
        return get_nexus_scan_results_impl(repository_name=repository_name)


@mcp.tool()
def get_all_scan_results(project_identifier: str = "default-project") -> Dict[str, Any]:
    """
    Collect scan results from all three security tools (Sonar, Fortify, Nexus) for a given project.

    Args:
        project_identifier: Common project identifier used across all tools

    Returns:
        Dictionary containing consolidated scan results from all tools
    """
    try:
        return _make_api_request("/api/scans/all", {"project_identifier": project_identifier})
    except Exception as e:
        return get_all_scan_results_impl(project_identifier=project_identifier)


@mcp.tool()
def check_flask_server_health() -> Dict[str, Any]:
    """
    Check if the Flask server is running and healthy.

    Returns:
        Dictionary containing server health status
    """
    try:
        return _make_api_request("/")
    except Exception as e:
        return {
            "error": True,
            "message": str(e),
            "server_url": FLASK_SERVER_BASE_URL,
            "status": "unhealthy"
        }


if __name__ == "__main__":
    print(f"Starting Security Scan Results MCP Client Server...")
    print(f"Flask server URL: {FLASK_SERVER_BASE_URL}")
    print("Available MCP tools:")
    print("  - get_sonar_scan_results")
    print("  - get_fortify_scan_results")
    print("  - get_nexus_scan_results")
    print("  - get_all_scan_results")
    print("  - check_flask_server_health")
    mcp.run()
