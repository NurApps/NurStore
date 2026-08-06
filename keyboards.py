# NurStore — Telegram bot for NurApps ecosystem
# Copyright (C) 2026  NurApps
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import DONATE_LINK


# ─── Reply Keyboards ─────────────────────────────────────────────────────────

def get_main_menu_kb(is_admin: bool = False):
    kb = [
        [KeyboardButton(text="📱 Приложения")],
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="⭐ Рейтинг приложений")],
        [KeyboardButton(text="ℹ️ О нас"), KeyboardButton(text="🆘 Связь")],
        [KeyboardButton(text="❤️ Поддержать нас")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="🔧 Админ панель")])
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие:"
    )


def get_admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить приложение"), KeyboardButton(text="📤 Загрузить версию")],
            [KeyboardButton(text="🌐 Синхр. GitHub"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="📢 Рассылка"), KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )


def get_cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


# ─── Inline Keyboards — User ─────────────────────────────────────────────────

def get_apps_inline_kb(apps_list: list):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for app_row in apps_list:
        app_id, name = app_row[0], app_row[1]
        icon = app_row[4] if len(app_row) > 4 and app_row[4] else "\U0001f4f1"
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=f"{icon} {name}", callback_data=f"appdetail_{app_id}")
        ])
    return kb


def get_app_detail_kb(app_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ Скачать последнюю", callback_data=f"dl_latest_{app_id}")],
        [InlineKeyboardButton(text="📜 Все версии", callback_data=f"app_versions_{app_id}")],
        [InlineKeyboardButton(text="📝 Что нового", callback_data=f"app_changelog_{app_id}")],
        [InlineKeyboardButton(text="⭐️ Оценить", callback_data=f"app_rate_{app_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_apps")]
    ])


RT_ICONS = {"stable": "✅", "beta": "🧪", "alpha": "⚙️"}

def release_icon(release_type: str, is_latest: bool) -> str:
    if is_latest:
        return "✅"
    return RT_ICONS.get(release_type, "📦")

def get_versions_inline_kb(versions: list, app_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for v in versions:
        vid, ver, changelog, fsize, min_android, dl_count, created, is_latest, file_id, rtype = v[:10]
        date_str = created[:10] if created else "???"
        icon = release_icon(rtype, bool(is_latest))
        label = f"{icon} {ver} — {date_str} — {dl_count} ⬇️"
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=label, callback_data=f"ver_{vid}")
        ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_app_{app_id}")
    ])
    return kb


def get_version_detail_kb(version_id: int, app_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать", callback_data=f"download_{version_id}")],
        [InlineKeyboardButton(text="🔙 Назад к версиям", callback_data=f"app_versions_{app_id}")]
    ])


def get_rating_kb(app_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    for i in range(1, 6):
        row.append(InlineKeyboardButton(text=f"{i}⭐", callback_data=f"rate_{app_id}_{i}"))
    kb.inline_keyboard.append(row)
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_app_{app_id}")
    ])
    return kb


def get_changelog_kb(app_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_app_{app_id}")]
    ])


def get_back_to_apps_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к приложениям", callback_data="back_to_apps")]
    ])


# ─── Inline Keyboards — Admin ────────────────────────────────────────────────

def get_admin_apps_inline_kb(apps_list: list, action: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for app in apps_list:
        app_id = app[0]
        name = app[1]
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=name, callback_data=f"admin_{action}_{app_id}")
        ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")
    ])
    return kb


def get_confirm_kb(action: str, app_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{action}_{app_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
    ])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} Б"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} КБ"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} МБ"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} ГБ"
