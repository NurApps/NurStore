# NurStore — Telegram bot for NurApps ecosystem
# Copyright (C) 2026  NurApps
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os

from config import CHANNEL_LINK, SUPPORT_USERNAME, DONATE_LINK, ADMIN_ID
from database import (
    add_user, get_all_apps, get_app_by_id, get_versions_by_app,
    get_version, get_latest_version, increment_download_count,
    record_download, get_app_rating, get_user_rating, set_rating,
    get_all_ratings_summary, search_apps
)
from keyboards import (
    get_main_menu_kb, get_apps_inline_kb, get_app_detail_kb,
    get_versions_inline_kb, get_version_detail_kb, get_rating_kb,
    get_changelog_kb, get_back_to_apps_kb, format_size
)

router = Router()


class Search(StatesGroup):
    query = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    await add_user(user.id, user.username or "")
    is_admin = user.id == ADMIN_ID

    apps = await get_all_apps()
    apps_text = ""
    for a in apps:
        icon = a[4] if a[4] else "\U0001f4f1"
        apps_text += f"{icon} {a[1]}\n"

    text = (
        "\U0001f31f \u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c \u0432 NurStore!\n\n"
        "\u041c\u0430\u0433\u0430\u0437\u0438\u043d \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0439 NurApps. "
        "\u0417\u0434\u0435\u0441\u044c \u0432\u044b \u043c\u043e\u0436\u0435\u0442\u0435 \u0441\u043a\u0430\u0447\u0430\u0442\u044c "
        "\u0432\u0441\u0435 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u044d\u043a\u043e\u0441\u0438\u0441\u0442\u0435\u043c\u044b.\n\n"
        f"\U0001f4f1 \u0414\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0435 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f:\n{apps_text}\n"
        "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0438 \u043d\u0438\u0436\u0435, \u0447\u0442\u043e\u0431\u044b \u043d\u0430\u0447\u0430\u0442\u044c."
    )
    await message.answer(text, reply_markup=get_main_menu_kb(is_admin))


@router.message(F.text == "\U0001f4f1 \u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f")
async def show_apps(message: Message):
    apps = await get_all_apps()
    if not apps:
        await message.answer("\U0001f615 \u041f\u043e\u043a\u0430 \u043d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0445 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0439.")
        return
    await message.answer(
        "\U0001f4f1 \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435:",
        reply_markup=get_apps_inline_kb(apps)
    )


@router.message(F.text == "\U0001f50d \u041f\u043e\u0438\u0441\u043a")
async def search_start(message: Message, state: FSMContext):
    await state.set_state(Search.query)
    await message.answer("\U0001f50d \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u0434\u043b\u044f \u043f\u043e\u0438\u0441\u043a\u0430:")


@router.message(Search.query)
async def search_result(message: Message, state: FSMContext):
    query = message.text
    results = await search_apps(query)
    if results:
        await message.answer(
            f"\u2705 \u041d\u0430\u0439\u0434\u0435\u043d\u043e \u043f\u043e \u0437\u0430\u043f\u0440\u043e\u0441\u0443 \u00ab{query}\u00bb:",
            reply_markup=get_apps_inline_kb(results)
        )
    else:
        await message.answer(f"\U0001f615 \u041f\u043e \u0437\u0430\u043f\u0440\u043e\u0441\u0443 \u00ab{query}\u00bb \u043d\u0438\u0447\u0435\u0433\u043e \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e.")
    await state.clear()


@router.message(F.text == "\u2b50 \u0420\u0435\u0439\u0442\u0438\u043d\u0433 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0439")
async def show_ratings(message: Message):
    ratings = await get_all_ratings_summary()
    if not ratings:
        await message.answer("\U0001f615 \u041f\u043e\u043a\u0430 \u043d\u0435\u0442 \u0440\u0435\u0439\u0442\u0438\u043d\u0433\u043e\u0432.")
        return
    lines = ["\u2b50\ufe0f \u0420\u0435\u0439\u0442\u0438\u043d\u0433 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0439\n"]
    for r in ratings:
        app_id, name, slug, icon, avg, count = r
        icon = icon if icon else "\U0001f4f1"
        stars = "\u2b50" * max(1, min(5, round(avg)))
        lines.append(f"{icon} {name} \u2014 {stars} {avg:.1f} ({count} \u043e\u0446\u0435\u043d\u043e\u043a)")
    await message.answer("\n".join(lines))


@router.message(F.text == "\u2139\ufe0f \u041e \u043d\u0430\u0441")
async def about(message: Message):
    text = (
        "\u2139\ufe0f **\u041e NurStore**\n\n"
        "NurStore \u2014 \u043e\u0444\u0438\u0446\u0438\u0430\u043b\u044c\u043d\u044b\u0439 \u043c\u0430\u0433\u0430\u0437\u0438\u043d \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0439 NurApps.\n"
        "\u0417\u0434\u0435\u0441\u044c \u0432\u044b \u043c\u043e\u0436\u0435\u0442\u0435 \u0441\u043a\u0430\u0447\u0430\u0442\u044c \u0432\u0441\u0435 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f "
        "\u044d\u043a\u043e\u0441\u0438\u0441\u0442\u0435\u043c\u044b: "
        "\u043a\u043d\u0438\u0433\u0438, \u043c\u0435\u0441\u0441\u0435\u043d\u0434\u0436\u0435\u0440, \u043a\u0430\u043b\u044c\u043a\u0443\u043b\u044f\u0442\u043e\u0440 \u0438 \u0434\u0440\u0443\u0433\u0438\u0435.\n\n"
        "\u0412\u0441\u0435 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u0440\u0430\u0437\u0440\u0430\u0431\u0430\u0442\u044b\u0432\u0430\u044e\u0442\u0441\u044f "
        "\u0441 \u043b\u044e\u0431\u043e\u0432\u044c\u044e \u043a \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f\u043c.\n"
        "\u041a\u0430\u0436\u0434\u043e\u0435 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u043f\u0440\u0438\u043d\u043e\u0441\u0438\u0442 "
        "\u043d\u043e\u0432\u044b\u0435 \u0444\u0443\u043d\u043a\u0446\u0438\u0438 \u0438 \u0438\u0441\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f.\n\n"
        "\u041f\u043e\u0434\u043f\u0438\u0441\u044b\u0432\u0430\u0439\u0442\u0435\u0441\u044c \u043d\u0430 \u043d\u0430\u0448 \u043a\u0430\u043d\u0430\u043b, "
        "\u0447\u0442\u043e\u0431\u044b \u0431\u044b\u0442\u044c \u0432 \u043a\u0443\u0440\u0441\u0435 \u043d\u043e\u0432\u043e\u0441\u0442\u0435\u0439!"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = None
    if CHANNEL_LINK:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\U0001f4e2 \u041d\u0430\u0448 \u043a\u0430\u043d\u0430\u043b", url=CHANNEL_LINK)]
        ])
    await message.answer(text, reply_markup=kb)


@router.message(F.text == "\U0001f718 \u0421\u0432\u044f\u0437\u044c")
async def contact(message: Message):
    support = SUPPORT_USERNAME if SUPPORT_USERNAME else "@\u0442\u0432\u043e\u0439_\u044e\u0437\u0435\u0440\u043d\u0435\u0439\u043c"
    text = (
        "\U0001f718 **\u0421\u0432\u044f\u0437\u044c \u0441 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u043e\u0439**\n\n"
        f"\u041f\u043e \u0432\u0441\u0435\u043c \u0432\u043e\u043f\u0440\u043e\u0441\u0430\u043c \u043f\u0438\u0448\u0438\u0442\u0435: {support}\n"
        "\u041c\u044b \u0441\u0442\u0430\u0440\u0430\u0435\u043c\u0441\u044f \u043e\u0442\u0432\u0435\u0447\u0430\u0442\u044c \u0432 \u0442\u0435\u0447\u0435\u043d\u0438\u0435 24 \u0447\u0430\u0441\u043e\u0432."
    )
    await message.answer(text)


@router.message(F.text == "\u2764\ufe0f \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u0430\u0442\u044c \u043d\u0430\u0441")
async def donate(message: Message):
    if DONATE_LINK:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2764\ufe0f \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u0430\u0442\u044c", url=DONATE_LINK)]
        ])
        await message.answer(
            "\u2764\ufe0f **\u041f\u043e\u0434\u0434\u0435\u0440\u0436\u0430\u0442\u044c \u043d\u0430\u0441**\n\n"
            "\u0415\u0441\u043b\u0438 \u0432\u0430\u043c \u043d\u0440\u0430\u0432\u044f\u0442\u0441\u044f \u043d\u0430\u0448\u0438 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f, "
            "\u0432\u044b \u043c\u043e\u0436\u0435\u0442\u0435 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0430\u0442\u044c \u043d\u0430\u0441 \u0434\u043e\u043d\u0430\u0442\u043e\u043c.\n"
            "\u042d\u0442\u043e \u043f\u043e\u043c\u043e\u0433\u0430\u0435\u0442 \u043d\u0430\u043c \u0440\u0430\u0437\u0432\u0438\u0432\u0430\u0442\u044c "
            "\u043f\u0440\u043e\u0435\u043a\u0442\u044b \u0438 \u0432\u044b\u043f\u0443\u0441\u043a\u0430\u0442\u044c \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f!",
            reply_markup=kb
        )
    else:
        await message.answer(
            "\u2764\ufe0f \u0421\u043f\u0430\u0441\u0438\u0431\u043e \u0437\u0430 \u0432\u0430\u0448\u0443 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0443! "
            "\u0421\u0441\u044b\u043b\u043a\u0430 \u0434\u043b\u044f \u0434\u043e\u043d\u0430\u0442\u0430 \u043f\u043e\u043a\u0430 \u043d\u0435 \u043d\u0430\u0441\u0442\u0440\u043e\u0435\u043d\u0430."
        )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    is_admin = message.from_user.id == ADMIN_ID
    await message.answer("\U0001f3e0 \u0413\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e:", reply_markup=get_main_menu_kb(is_admin))


@router.message(F.text == "\U0001f527 \u0410\u0434\u043c\u0438\u043d \u043f\u0430\u043d\u0435\u043b\u044c")
async def goto_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("\u26d4 \u0423 \u0432\u0430\u0441 \u043d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0430.")
        return
    from handlers.admin import cmd_admin
    await cmd_admin(message)


@router.callback_query(F.data.startswith("appdetail_"))
async def app_detail(callback: CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) < 2:
        await callback.answer()
        return
    app_id = int(parts[1])

    app = await get_app_by_id(app_id)
    if not app:
        await callback.message.edit_text("\U0001f615 \u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e.")
        await callback.answer()
        return

    latest = await get_latest_version(app_id)
    rating, rating_count = await get_app_rating(app_id)

    icon = app["icon_url"] if app["icon_url"] else "\U0001f4f1"
    text = f"{icon} **{app['name']}**\n\n{app['description']}\n"

    if latest:
        size_str = format_size(latest["file_size"])
        text += f"\n\U0001f4ab \u041f\u043e\u0441\u043b\u0435\u0434\u043d\u044f\u044f \u0432\u0435\u0440\u0441\u0438\u044f: {latest['version']} ({size_str})"
    else:
        text += "\n\U0001f4ab \u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0445 \u0432\u0435\u0440\u0441\u0438\u0439"

    if rating_count > 0:
        text += f"\n\u2b50\ufe0f \u0420\u0435\u0439\u0442\u0438\u043d\u0433: {rating:.1f} ({rating_count} \u043e\u0446\u0435\u043d\u043e\u043a)"

    await callback.message.edit_text(text, reply_markup=get_app_detail_kb(app_id))
    await callback.answer()


@router.callback_query(F.data == "back_to_apps")
async def back_to_apps(callback: CallbackQuery):
    apps = await get_all_apps()
    await callback.message.edit_text(
        "\U0001f4f1 \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435:",
        reply_markup=get_apps_inline_kb(apps)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_app_"))
async def back_to_app(callback: CallbackQuery):
    app_id = int(callback.data.split("_")[3])
    app = await get_app_by_id(app_id)
    if not app:
        await callback.answer()
        return

    latest = await get_latest_version(app_id)
    rating, rating_count = await get_app_rating(app_id)

    icon = app["icon_url"] if app["icon_url"] else "\U0001f4f1"
    text = f"{icon} **{app['name']}**\n\n{app['description']}\n"

    if latest:
        size_str = format_size(latest["file_size"])
        text += f"\n\U0001f4ab \u041f\u043e\u0441\u043b\u0435\u0434\u043d\u044f\u044f \u0432\u0435\u0440\u0441\u0438\u044f: {latest['version']} ({size_str})"
    if rating_count > 0:
        text += f"\n\u2b50\ufe0f \u0420\u0435\u0439\u0442\u0438\u043d\u0433: {rating:.1f} ({rating_count} \u043e\u0446\u0435\u043d\u043e\u043a)"

    await callback.message.edit_text(text, reply_markup=get_app_detail_kb(app_id))
    await callback.answer()


@router.callback_query(F.data.startswith("app_versions_"))
async def show_versions(callback: CallbackQuery):
    app_id = int(callback.data.split("_")[2])
    app = await get_app_by_id(app_id)
    if not app:
        await callback.answer()
        return

    versions = await get_versions_by_app(app_id)
    if not versions:
        await callback.message.edit_text(
            "\U0001f615 \u0423 \u044d\u0442\u043e\u0433\u043e \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u043f\u043e\u043a\u0430 \u043d\u0435\u0442 \u0432\u0435\u0440\u0441\u0438\u0439.",
            reply_markup=get_back_to_apps_kb()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"\U0001f4dc **{app['name']}** \u2014 \u0432\u0441\u0435 \u0432\u0435\u0440\u0441\u0438\u0438:",
        reply_markup=get_versions_inline_kb(versions, app_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ver_"))
async def version_detail(callback: CallbackQuery):
    version_id = int(callback.data.split("_")[1])
    ver = await get_version(version_id)
    if not ver:
        await callback.answer("\u0412\u0435\u0440\u0441\u0438\u044f \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.", show_alert=True)
        return

    app = await get_app_by_id(ver["app_id"])
    if not app:
        await callback.answer()
        return

    icon = app["icon_url"] if app["icon_url"] else "\U0001f4e6"
    size_str = format_size(ver["file_size"])
    android = ver["min_android"] if ver["min_android"] else "\u041d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d\u043e"
    changelog = ver["changelog"] if ver["changelog"] else "\u041d\u0435\u0442 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u044f"
    date_str = ver["created_at"][:10] if ver["created_at"] else "???"
    latest_badge = " \u2705 \u041f\u043e\u0441\u043b\u0435\u0434\u043d\u044f\u044f" if ver["is_latest"] else ""
    rtype = ver.get("release_type", "stable")
    rtype_icons = {"stable": "\u2705", "beta": "\U0001f9ea", "alpha": "\u2699\ufe0f"}
    rtype_icon = rtype_icons.get(rtype, "\U0001f4e6")
    rtype_label = {"stable": "Stable", "beta": "Beta", "alpha": "Alpha"}.get(rtype, rtype)

    text = (
        f"{icon} **{app['name']} {ver['version']}**{latest_badge}\n\n"
        f"{rtype_icon} **{rtype_label}**\n"
        f"\U0001f4c5 \u0414\u0430\u0442\u0430: {date_str}\n"
        f"\U0001f4cf \u0420\u0430\u0437\u043c\u0435\u0440: {size_str}\n"
        f"\U0001f4f1 Android: {android}\n"
        f"\u2b07\ufe0f \u0421\u043a\u0430\u0447\u0438\u0432\u0430\u043d\u0438\u0439: {ver['download_count']}\n\n"
        f"\U0001f4dd **\u0427\u0442\u043e \u043d\u043e\u0432\u043e\u0433\u043e:**\n{changelog}"
    )

    await callback.message.edit_text(text, reply_markup=get_version_detail_kb(version_id, ver["app_id"]))
    await callback.answer()


@router.callback_query(F.data.startswith("dl_latest_"))
async def download_latest(callback: CallbackQuery):
    app_id = int(callback.data.split("_")[2])
    latest = await get_latest_version(app_id)
    if not latest:
        await callback.answer("\u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0445 \u0432\u0435\u0440\u0441\u0438\u0439.", show_alert=True)
        return
    await _do_download(callback, latest["version_id"])


@router.callback_query(F.data.startswith("download_"))
async def download_version(callback: CallbackQuery):
    version_id = int(callback.data.split("_")[1])
    await _do_download(callback, version_id)


MAX_TG_FILE_SIZE = 50 * 1024 * 1024

async def _do_download(callback: CallbackQuery, version_id: int):
    ver = await get_version(version_id)
    if not ver:
        await callback.answer("\u0412\u0435\u0440\u0441\u0438\u044f \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.", show_alert=True)
        return

    user_id = callback.from_user.id

    await increment_download_count(version_id)
    await record_download(user_id, version_id)

    if ver["file_id"]:
        try:
            await callback.message.answer_document(
                document=ver["file_id"],
                caption=f"\U0001f4e6 {ver['version']}"
            )
            await callback.answer("\u2705 \u0421\u043a\u0430\u0447\u0438\u0432\u0430\u043d\u0438\u0435 \u043d\u0430\u0447\u0430\u0442\u043e!")
            return
        except Exception:
            pass

    if ver["file_size"] > MAX_TG_FILE_SIZE:
        await callback.answer(
            f"\u26a0\ufe0f \u0424\u0430\u0439\u043b ({format_size(ver['file_size'])}) \u043f\u0440\u0435\u0432\u044b\u0448\u0430\u0435\u0442 \u043b\u0438\u043c\u0438\u0442 Telegram (50 \u041c\u0411). "
            "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 \u0432\u043d\u0435\u0448\u043d\u0438\u0439 \u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a.",
            show_alert=True
        )
        return

    if ver["file_path"] and os.path.exists(ver["file_path"]):
        try:
            await callback.message.answer_document(
                document=FSInputFile(ver["file_path"]),
                caption=f"\U0001f4e6 {ver['version']}"
            )
            await callback.answer("\u2705 \u0421\u043a\u0430\u0447\u0438\u0432\u0430\u043d\u0438\u0435 \u043d\u0430\u0447\u0430\u0442\u043e!")
            return
        except Exception:
            pass

    await callback.answer("\u274c \u0424\u0430\u0439\u043b \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u043f\u043e\u0437\u0436\u0435.", show_alert=True)


@router.callback_query(F.data.startswith("app_changelog_"))
async def show_changelog(callback: CallbackQuery):
    app_id = int(callback.data.split("_")[2])
    app = await get_app_by_id(app_id)
    if not app:
        await callback.answer()
        return

    latest = await get_latest_version(app_id)
    if not latest:
        await callback.message.edit_text(
            "\U0001f615 \u041d\u0435\u0442 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u0438 \u043e \u043d\u043e\u0432\u044b\u0445 \u0432\u0435\u0440\u0441\u0438\u044f\u0445.",
            reply_markup=get_changelog_kb(app_id)
        )
        await callback.answer()
        return

    changelog = latest["changelog"] if latest["changelog"] else "\u041d\u0435\u0442 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u044f"
    text = (
        f"\U0001f4dd **\u0427\u0442\u043e \u043d\u043e\u0432\u043e\u0433\u043e \u0432 {app['name']} {latest['version']}**\n\n"
        f"{changelog}"
    )
    await callback.message.edit_text(text, reply_markup=get_changelog_kb(app_id))
    await callback.answer()


@router.callback_query(F.data.startswith("app_rate_"))
async def rate_app(callback: CallbackQuery):
    app_id = int(callback.data.split("_")[2])
    app = await get_app_by_id(app_id)
    if not app:
        await callback.answer()
        return

    user_rating = await get_user_rating(app_id, callback.from_user.id)
    rating, count = await get_app_rating(app_id)

    text = (
        f"\u2b50\ufe0f **\u041e\u0446\u0435\u043d\u0438\u0442\u0435 {app['name']}**\n\n"
        f"\u0422\u0435\u043a\u0443\u0449\u0438\u0439 \u0440\u0435\u0439\u0442\u0438\u043d\u0433: {rating:.1f} ({count} \u043e\u0446\u0435\u043d\u043e\u043a)\n"
    )
    if user_rating:
        text += f"\u0412\u0430\u0448\u0430 \u043e\u0446\u0435\u043d\u043a\u0430: {user_rating}\u2b50"
    else:
        text += "\u0412\u044b \u0435\u0449\u0451 \u043d\u0435 \u043e\u0446\u0435\u043d\u0438\u0432\u0430\u043b\u0438 \u044d\u0442\u043e \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435."

    await callback.message.edit_text(text, reply_markup=get_rating_kb(app_id))
    await callback.answer()


@router.callback_query(F.data.startswith("rate_"))
async def submit_rating(callback: CallbackQuery):
    parts = callback.data.split("_")
    app_id = int(parts[1])
    score = int(parts[2])
    user_id = callback.from_user.id

    await set_rating(app_id, user_id, score)

    rating, count = await get_app_rating(app_id)

    await callback.message.edit_text(
        f"\u2705 \u0421\u043f\u0430\u0441\u0438\u0431\u043e! \u0412\u044b \u043e\u0446\u0435\u043d\u0438\u043b\u0438 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435 \u043d\u0430 {score}\u2b50\n\n"
        f"\u0422\u0435\u043a\u0443\u0449\u0438\u0439 \u0440\u0435\u0439\u0442\u0438\u043d\u0433: {rating:.1f} ({count} \u043e\u0446\u0435\u043d\u043e\u043a)"
    )
    await callback.answer(f"\u0412\u044b \u043f\u043e\u0441\u0442\u0430\u0432\u0438\u043b\u0438 {score}\u2b50")
