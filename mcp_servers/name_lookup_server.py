#!/usr/bin/env python3
"""
MCP Server for Name Lookup Tools using Free APIs
Run with: python name_lookup_server.py
"""

import logging
import aiohttp
import asyncio
from typing import Dict, Any
import random

import nest_asyncio  # Added import

nest_asyncio.apply()  # Added call

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("name-lookup-tools")

# API endpoints
NAMEY_API_BASE = "https://namey.muffinlabs.com/name.json"
RANDOM_USER_API = "https://api.api-ninjas.com/v1/randomuser"

# Fallback database for when APIs are unavailable
FALLBACK_NAMES_DB = {
    'smith': ['John Smith', 'Jane Smith', 'Robert Smith', 'Mary Smith', 'James Smith'],
    'johnson': ['Michael Johnson', 'Sarah Johnson', 'David Johnson', 'Lisa Johnson'],
    'williams': ['James Williams', 'Jennifer Williams', 'Christopher Williams', 'Amanda Williams'],
    'brown': ['William Brown', 'Elizabeth Brown', 'Joseph Brown', 'Michelle Brown'],
    'jones': ['Thomas Jones', 'Patricia Jones', 'Charles Jones', 'Linda Jones'],
    'garcia': ['Antonio Garcia', 'Maria Garcia', 'Jose Garcia', 'Carmen Garcia'],
    'miller': ['Richard Miller', 'Susan Miller', 'Paul Miller', 'Karen Miller'],
    'davis': ['Richard Davis', 'Nancy Davis', 'Kevin Davis', 'Donna Davis'],
    'rodriguez': ['Carlos Rodriguez', 'Ana Rodriguez', 'Luis Rodriguez', 'Elena Rodriguez'],
    'wilson': ['Daniel Wilson', 'Betty Wilson', 'Mark Wilson', 'Helen Wilson']
}


async def fetch_random_names_from_api(count: int = 5) -> list:
    """Fetch random names from the Namey API"""
    names = []
    try:
        async with aiohttp.ClientSession() as session:
            for _ in range(count):
                # Namey API: get full names with both first and last
                async with session.get(f"{NAMEY_API_BASE}?frequency=common&count=1") as response:
                    if response.status == 200:
                        data = await response.json()
                        # The API returns a list, get the first (and only) name
                        if data and len(data) > 0:
                            names.append(data[0])
                    await asyncio.sleep(0.1)  # Small delay to be respectful to the API
    except Exception as e:
        logger.error(f"Error fetching names from API: {e}")

    return names


async def fetch_names_with_surname_from_api(surname: str, count: int = 5) -> list:
    """Generate names with specific surname using random first names from API"""
    names = []
    try:
        async with aiohttp.ClientSession() as session:
            for _ in range(count):
                # Get only first names from Namey
                async with session.get(f"{NAMEY_API_BASE}?type=first&frequency=common&count=1") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            first_name = data[0]
                            names.append(f"{first_name} {surname.title()}")
                    await asyncio.sleep(0.1)  # Small delay to be respectful to the API
    except Exception as e:
        logger.error(f"Error fetching first names from API: {e}")

    return names


@mcp.tool()
async def get_names_by_surname(surname: str) -> str:
    """Get a list of common names for a given surname using free name APIs"""
    logger.info(f"Looking up names for surname: {surname}")

    # First try to get names from API
    api_names = await fetch_names_with_surname_from_api(surname, 5)

    if api_names:
        return f"Found {len(api_names)} names for '{surname}' from API: {', '.join(api_names)}"

    # Fallback to local database if API fails
    surname_lower = surname.lower()
    fallback_names = FALLBACK_NAMES_DB.get(surname_lower, [])

    if fallback_names:
        return f"Found {len(fallback_names)} names for '{surname}' from fallback database: {', '.join(fallback_names)}"

    # If no fallback names, generate some with common first names
    common_first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa', 'James', 'Jennifer']
    generated_names = [f"{name} {surname.title()}" for name in
                       random.sample(common_first_names, min(5, len(common_first_names)))]

    return f"Generated {len(generated_names)} names for '{surname}': {', '.join(generated_names)}"


@mcp.tool()
async def get_random_names(count: int = 5) -> str:
    """Get random names from free name APIs"""
    logger.info(f"Fetching {count} random names from API")

    if count > 10:
        count = 10  # Limit to avoid overwhelming the API

    # Try to get names from API
    api_names = await fetch_random_names_from_api(count)

    if api_names:
        return f"Found {len(api_names)} random names from API: {', '.join(api_names)}"

    # Fallback to generating names from local data
    all_names = []
    for surname_names in FALLBACK_NAMES_DB.values():
        all_names.extend(surname_names)

    random_names = random.sample(all_names, min(count, len(all_names)))
    return f"Generated {len(random_names)} random names from fallback: {', '.join(random_names)}"


@mcp.tool()
async def capitalize_name(string: str) -> str:
    """Capitalize the first letter of a name"""
    logger.info(f"Capitalizing: {string}")

    if not string:
        return "Empty string provided"

    result = string.capitalize()
    return f"'{string}' capitalized to '{result}'"


@mcp.tool()
async def format_names(names: str, format_type: str = "upper") -> str:
    """Format a list of names (upper, lower, title)"""
    logger.info(f"Formatting names with type: {format_type}")

    if not names:
        return "No names provided"

    name_list = [name.strip() for name in names.split(',')]

    if format_type == "upper":
        formatted = [name.upper() for name in name_list]
    elif format_type == "lower":
        formatted = [name.lower() for name in name_list]
    elif format_type == "title":
        formatted = [name.title() for name in name_list]
    else:
        return f"Unknown format type: {format_type}. Available types: upper, lower, title"

    return f"Formatted names ({format_type}): {', '.join(formatted)}"


@mcp.tool()
async def get_name_statistics() -> str:
    """Get statistics about available names"""
    try:
        # Try to get a sample from the API to check if it's working
        sample_names = await fetch_random_names_from_api(2)

        if sample_names:
            status = "API is working"
            api_sample = f"Sample names from API: {', '.join(sample_names)}"
        else:
            status = "API unavailable, using fallback database"
            api_sample = ""

        fallback_count = sum(len(names) for names in FALLBACK_NAMES_DB.values())

        result = f"Name Lookup Service Status: {status}\n"
        result += f"Fallback database contains {fallback_count} names across {len(FALLBACK_NAMES_DB)} surnames\n"
        if api_sample:
            result += api_sample

        return result

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return f"Error getting statistics: {str(e)}"


if __name__ == "__main__":
    mcp.run()