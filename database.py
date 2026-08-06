# NurStore — Telegram bot for NurApps ecosystem
# Copyright (C) 2026  NurApps
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import aiosqlite
import os
from config import DB_PATH, DOWNLOADS_DIR
from datetime import datetime


async def db_start():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='versions'")
        if await cursor.fetchone():
            cursor2 = await db.execute("PRAGMA table_info(versions)")
            cols = [r[1] for r in await cursor2.fetchall()]
            if 'version_name' in cols:
                await db.execute("DROP TABLE IF EXISTS versions")
                await db.execute("DROP TABLE IF EXISTS apps")
                await db.execute("DROP TABLE IF EXISTS downloads")
                await db.execute("DROP TABLE IF EXISTS ratings")

        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_seen DATE,
            last_active DATE
        )""")

        await db.execute("""CREATE TABLE IF NOT EXISTS apps (
            app_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            icon_url TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at DATE
        )""")

        await db.execute("""CREATE TABLE IF NOT EXISTS versions (
            version_id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id INTEGER NOT NULL,
            version TEXT NOT NULL,
            changelog TEXT,
            file_id TEXT,
            file_path TEXT,
            file_size INTEGER DEFAULT 0,
            min_android TEXT,
            is_latest BOOLEAN DEFAULT 0,
            download_count INTEGER DEFAULT 0,
            created_at DATE,
            FOREIGN KEY (app_id) REFERENCES apps(app_id)
        )""")

        await db.execute("""CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            version_id INTEGER,
            downloaded_at DATE,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (version_id) REFERENCES versions(version_id)
        )""")

        await db.execute("""CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id INTEGER,
            user_id INTEGER,
            score INTEGER CHECK(score >= 1 AND score <= 5),
            created_at DATE,
            FOREIGN KEY (app_id) REFERENCES apps(app_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(app_id, user_id)
        )""")

        cursor3 = await db.execute("PRAGMA table_info(versions)")
        existing_cols = [r[1] for r in await cursor3.fetchall()]
        if 'release_type' not in existing_cols:
            await db.execute("ALTER TABLE versions ADD COLUMN release_type TEXT DEFAULT 'stable'")
            await db.commit()

        cursor4 = await db.execute("SELECT COUNT(*) FROM apps")
        if (await cursor4.fetchone())[0] == 0:
            await _seed_defaults(db)

    os.makedirs(DOWNLOADS_DIR, exist_ok=True)


async def _seed_defaults(db):
    now = datetime.now().strftime("%Y-%m-%d")
    defaults = [
        ("NurBooks", "nurbooks", "Удобное приложение для чтения книг с поддержкой всех форматов. Читайте где угодно и когда угодно.", "📚"),
        ("NurChat", "nurchat", "Современный мессенджер с шифрованием, групповыми чатами и голосовыми звонками.", "💬"),
        ("Byteculator", "byteculator", "Мощный калькулятор с поддержкой программирования, конвертации систем счисления и расширенной математики.", "🧮"),
    ]
    for name, slug, desc, icon in defaults:
        await db.execute(
            "INSERT INTO apps (name, slug, description, icon_url, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, slug, desc, icon, now)
        )
    await db.commit()


# ─── Users ───────────────────────────────────────────────────────────────────

async def add_user(user_id: int, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        now = datetime.now().strftime("%Y-%m-%d")
        if await cursor.fetchone():
            await db.execute(
                "UPDATE users SET last_active = ?, username = ? WHERE user_id = ?",
                (now, username, user_id)
            )
        else:
            await db.execute(
                "INSERT INTO users (user_id, username, first_seen, last_active) VALUES (?, ?, ?, ?)",
                (user_id, username, now, now)
            )
        await db.commit()


async def get_user_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_daily_active_users() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE last_active = ?", (today,))
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id, username FROM users")
        return await cursor.fetchall()


# ─── Apps ────────────────────────────────────────────────────────────────────

async def add_app(name: str, slug: str, description: str, icon_url: str = ""):
    now = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO apps (name, slug, description, icon_url, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, slug, description, icon_url, now)
        )
        await db.commit()


async def get_all_apps():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT app_id, name, slug, description, icon_url FROM apps WHERE is_active = 1 ORDER BY app_id"
        )
        return await cursor.fetchall()


async def get_app_by_id(app_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT app_id, name, slug, description, icon_url FROM apps WHERE app_id = ? AND is_active = 1",
            (app_id,)
        )
        row = await cursor.fetchone()
        if row:
            return {"app_id": row[0], "name": row[1], "slug": row[2], "description": row[3], "icon_url": row[4]}
        return None


async def get_app_by_slug(slug: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT app_id, name, slug, description, icon_url FROM apps WHERE slug = ? AND is_active = 1",
            (slug,)
        )
        row = await cursor.fetchone()
        if row:
            return {"app_id": row[0], "name": row[1], "slug": row[2], "description": row[3], "icon_url": row[4]}
        return None


async def search_apps(query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT app_id, name, slug, description, icon_url FROM apps WHERE is_active = 1 AND name LIKE ?",
            (f"%{query}%",)
        )
        return await cursor.fetchall()


async def update_app(app_id: int, **kwargs):
    allowed = {"name", "slug", "description", "icon_url", "is_active"}
    sets = {k: v for k, v in kwargs.items() if k in allowed}
    if not sets:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        set_clause = ", ".join(f"{k} = ?" for k in sets)
        values = list(sets.values()) + [app_id]
        await db.execute(f"UPDATE apps SET {set_clause} WHERE app_id = ?", values)
        await db.commit()


# ─── Versions ────────────────────────────────────────────────────────────────

async def add_version(
    app_id: int, version: str, changelog: str = "",
    file_id: str = "", file_path: str = "",
    file_size: int = 0, min_android: str = "",
    release_type: str = "stable"
):
    now = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE versions SET is_latest = 0 WHERE app_id = ?", (app_id,))
        await db.execute(
            """INSERT INTO versions
               (app_id, version, changelog, file_id, file_path, file_size, min_android, release_type, is_latest, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
            (app_id, version, changelog, file_id, file_path, file_size, min_android, release_type, now)
        )
        await db.commit()


async def get_versions_by_app(app_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT version_id, version, changelog, file_size, min_android,
                      download_count, created_at, is_latest, file_id, release_type
               FROM versions WHERE app_id = ? ORDER BY created_at DESC""",
            (app_id,)
        )
        return await cursor.fetchall()


async def get_version(version_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT version_id, app_id, version, changelog, file_id, file_path,
                      file_size, min_android, download_count, created_at, is_latest, release_type
               FROM versions WHERE version_id = ?""",
            (version_id,)
        )
        row = await cursor.fetchone()
        if row:
            return {
                "version_id": row[0], "app_id": row[1], "version": row[2],
                "changelog": row[3], "file_id": row[4], "file_path": row[5],
                "file_size": row[6], "min_android": row[7],
                "download_count": row[8], "created_at": row[9], "is_latest": row[10],
                "release_type": row[11]
            }
        return None


async def get_latest_version(app_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT version_id, version, changelog, file_id, file_size, min_android,
                      download_count, created_at, release_type
               FROM versions WHERE app_id = ? AND is_latest = 1""",
            (app_id,)
        )
        row = await cursor.fetchone()
        if row:
            return {
                "version_id": row[0], "version": row[1], "changelog": row[2],
                "file_id": row[3], "file_size": row[4], "min_android": row[5],
                "download_count": row[6], "created_at": row[7], "release_type": row[8]
            }
        cursor2 = await db.execute(
            """SELECT version_id, version, changelog, file_id, file_size, min_android,
                      download_count, created_at, release_type
               FROM versions WHERE app_id = ? ORDER BY created_at DESC LIMIT 1""",
            (app_id,)
        )
        row2 = await cursor2.fetchone()
        if row2:
            return {
                "version_id": row2[0], "version": row2[1], "changelog": row2[2],
                "file_id": row2[3], "file_size": row2[4], "min_android": row2[5],
                "download_count": row2[6], "created_at": row2[7], "release_type": row2[8]
            }
        return None


async def increment_download_count(version_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE versions SET download_count = download_count + 1 WHERE version_id = ?", (version_id,))
        await db.commit()


# ─── Downloads ───────────────────────────────────────────────────────────────

async def record_download(user_id: int, version_id: int):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO downloads (user_id, version_id, downloaded_at) VALUES (?, ?, ?)",
            (user_id, version_id, now)
        )
        await db.commit()


async def get_total_downloads() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM downloads")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_downloads_per_app():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT a.app_id, a.name, a.slug, COUNT(d.id) as dl_count
            FROM apps a
            LEFT JOIN versions v ON a.app_id = v.app_id
            LEFT JOIN downloads d ON v.version_id = d.version_id
            WHERE a.is_active = 1
            GROUP BY a.app_id
            ORDER BY dl_count DESC
        """)
        return await cursor.fetchall()


async def get_downloads_per_version(app_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT v.version_id, v.version, COUNT(d.id) as dl_count
            FROM versions v
            LEFT JOIN downloads d ON v.version_id = d.version_id
            WHERE v.app_id = ?
            GROUP BY v.version_id
            ORDER BY v.created_at DESC
        """, (app_id,))
        return await cursor.fetchall()


# ─── Ratings ─────────────────────────────────────────────────────────────────

async def set_rating(app_id: int, user_id: int, score: int):
    now = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO ratings (app_id, user_id, score, created_at) VALUES (?, ?, ?, ?)",
            (app_id, user_id, score, now)
        )
        await db.commit()


async def get_app_rating(app_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT AVG(score), COUNT(*) FROM ratings WHERE app_id = ?",
            (app_id,)
        )
        row = await cursor.fetchone()
        return (round(row[0], 1), row[1]) if row and row[0] else (0.0, 0)


async def get_user_rating(app_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT score FROM ratings WHERE app_id = ? AND user_id = ?",
            (app_id, user_id)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_all_ratings_summary():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT a.app_id, a.name, a.slug, a.icon_url,
                   COALESCE(AVG(r.score), 0) as avg_score,
                   COUNT(r.id) as rating_count
            FROM apps a
            LEFT JOIN ratings r ON a.app_id = r.app_id
            WHERE a.is_active = 1
            GROUP BY a.app_id
            ORDER BY avg_score DESC
        """)
        return await cursor.fetchall()


# ─── Admin Stats ─────────────────────────────────────────────────────────────

async def get_stats_for_admin():
    daily = await get_daily_active_users()
    total_dl = await get_total_downloads()
    total_users = await get_user_count()
    return daily, total_dl, total_users
