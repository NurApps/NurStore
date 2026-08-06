# NurStore — Telegram bot for NurApps ecosystem
# Copyright (C) 2026  NurApps
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import aiohttp
import re
from datetime import datetime
from database import add_version, get_app_by_slug, get_versions_by_app

GITHUB_API = "https://api.github.com/repos"


async def fetch_releases(owner: str, repo: str, token: str = ""):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{GITHUB_API}/{owner}/{repo}/releases?per_page=30"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            return data


def parse_version_tag(tag: str) -> str:
    tag = tag.lstrip("vV")
    return f"v{tag}"


def detect_release_type(tag: str, prerelease: bool) -> str:
    if prerelease:
        return "beta"
    tag_lower = tag.lower()
    if any(x in tag_lower for x in ["alpha", "pre", "dev"]):
        return "alpha"
    return "stable"


async def sync_github_releases(
    owner: str, repo: str,
    app_slug: str, token: str = ""
) -> dict:
    result = {"added": 0, "skipped": 0, "errors": 0}

    app = await get_app_by_slug(app_slug)
    if not app:
        result["errors"] = 1
        return result

    app_id = app["app_id"]
    existing = await get_versions_by_app(app_id)
    existing_versions = {v[1] for v in existing}

    releases = await fetch_releases(owner, repo, token)
    if not releases:
        result["errors"] = 1
        return result

    for rel in releases:
        tag = rel.get("tag_name", "")
        version = parse_version_tag(tag)
        if version in existing_versions:
            result["skipped"] += 1
            continue

        prerelease = rel.get("prerelease", False)
        rtype = detect_release_type(tag, prerelease)
        body = rel.get("body", "") or ""
        created_raw = rel.get("published_at") or rel.get("created_at", "")
        created_date = created_raw[:10] if created_raw else datetime.now().strftime("%Y-%m-%d")

        assets = rel.get("assets", [])
        if not assets:
            result["skipped"] += 1
            continue

        asset = assets[0]
        download_url = asset.get("browser_download_url", "")
        file_size = asset.get("size", 0)

        if not download_url:
            result["skipped"] += 1
            continue

        file_name = asset.get("name", f"{version}.apk")

        try:
            await add_version(
                app_id=app_id,
                version=version,
                changelog=body,
                file_id="",
                file_path="",
                file_size=file_size,
                min_android="",
                release_type=rtype
            )
            result["added"] += 1
        except Exception:
            result["errors"] += 1

    return result
