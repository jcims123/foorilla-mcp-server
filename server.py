#!/usr/bin/env python3
"""Foorilla Job Market MCP Server — exposes Foorilla API tools to Claude."""

import os
import functools
from typing import Optional
import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = "https://foorilla.com/api/v1"

mcp = FastMCP("foorilla")


def _headers() -> dict:
    api_key = os.environ.get("FOORILLA_API_KEY", "")
    if not api_key:
        raise RuntimeError("FOORILLA_API_KEY environment variable not set")
    return {"Api-Key": api_key}


def _get(path: str, params: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    with httpx.Client(timeout=30) as client:
        resp = client.get(url, headers=_headers(), params=params or {})
        resp.raise_for_status()
        return resp.json()


@functools.lru_cache(maxsize=1)
def _all_countries() -> dict:
    """Cached fetch of all countries (ID, code, name)."""
    return {c["code"].upper(): c["id"] for c in _get("/core/geocountry/", {"page_size": 500})["results"]}


def _resolve_country_codes(codes: list[str]) -> list[int]:
    mapping = _all_countries()
    return [mapping[c.upper()] for c in codes if c.upper() in mapping]


@mcp.tool()
def search_jobs(
    country_codes: Optional[list[str]] = None,
    topic_ids: Optional[list[int]] = None,
    tag_ids: Optional[list[int]] = None,
    published_after: Optional[str] = None,
    published_before: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    """Search job listings on Foorilla.

    Args:
        country_codes: ISO-2 country codes, e.g. ["CH", "DE"]. Omit for all countries.
        topic_ids: Foorilla topic IDs (use list_topics to find them).
        tag_ids: Foorilla tag IDs (use list_topics to find them).
        published_after: Filter jobs published after this date, e.g. "2026-01-01".
        published_before: Filter jobs published before this date, e.g. "2026-03-01".
        page: Page number (default 1).
        page_size: Results per page (1-1000, default 25).
    """
    params: dict = {"page": page, "page_size": page_size}
    if country_codes:
        params["country"] = _resolve_country_codes(country_codes)
    if topic_ids:
        params["topic"] = topic_ids
    if tag_ids:
        params["tag"] = tag_ids
    if published_after:
        params["published_after"] = published_after
    if published_before:
        params["published_before"] = published_before
    return _get("/hiring/job/", params)


@mcp.tool()
def get_job(job_id: int) -> dict:
    """Get full details for a single job by its Foorilla ID."""
    return _get(f"/hiring/job/{job_id}")


@mcp.tool()
def search_salaries(
    country_codes: Optional[list[str]] = None,
    topic_ids: Optional[list[int]] = None,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    """Get salary benchmarks from Foorilla.

    Args:
        country_codes: ISO-2 codes, e.g. ["CH"] for Switzerland.
        topic_ids: Foorilla topic IDs to filter by skill/technology area.
        page: Page number.
        page_size: Results per page.
    """
    params: dict = {"page": page, "page_size": page_size}
    if country_codes:
        params["country"] = _resolve_country_codes(country_codes)
    if topic_ids:
        params["topic"] = topic_ids
    return _get("/insight/salary/", params)


@mcp.tool()
def list_topics(search: Optional[str] = None, page_size: int = 200) -> dict:
    """List Foorilla topics (technology/skill areas) and their IDs.

    Use search to filter by name. Topic IDs are required by search_jobs and search_salaries.

    Args:
        search: Optional keyword to filter topics by name or description.
        page_size: Max results to return.
    """
    data = _get("/core/topic/", {"page_size": page_size})
    if search:
        sl = search.lower()
        data["results"] = [
            t for t in data["results"]
            if sl in t.get("name", "").lower() or sl in t.get("description", "").lower()
        ]
    return data


@mcp.tool()
def list_countries(search: Optional[str] = None) -> dict:
    """List all countries with their Foorilla IDs and ISO codes.

    Use search to filter. Useful for discovering country IDs.

    Args:
        search: Optional keyword to filter by country name or ISO code.
    """
    data = _get("/core/geocountry/", {"page_size": 500})
    if search:
        sl = search.lower()
        data["results"] = [
            c for c in data["results"]
            if sl in c.get("name", "").lower() or sl in c.get("code", "").lower()
        ]
    return data


@mcp.tool()
def get_company(company_id: int) -> dict:
    """Get details for a company by Foorilla company ID (name, website, HQ, size, founding year)."""
    return _get(f"/hiring/company/{company_id}")


@mcp.tool()
def list_companies(page: int = 1, page_size: int = 50) -> dict:
    """List companies active on Foorilla (paginated)."""
    return _get("/hiring/company/", {"page": page, "page_size": page_size})


if __name__ == "__main__":
    mcp.run()
