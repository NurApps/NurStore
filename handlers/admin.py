# NurStore — Telegram bot for NurApps ecosystem
# Copyright (C) 2026  NurApps
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os

from config import ADMIN_ID, DOWNLOADS_DIR, GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN
from database import (
    add_user, get_user_count, get_daily_active_users, get_all_users,
    add_app, get_all_apps, get_app_by_id, get_app_by_slug,
    add_version, get_versions_by_app,
    get_total_downloads, get_downloads_per_app,
    get_stats_for_admin
)
from keyboards import (
    get_admin_kb, get_main_menu_kb, get_cancel_kb,
    get_admin_apps_inline_kb, format_size
)

router = Router()


class AddApp(StatesGroup):
    name = State()
    slug = State()
    description = State()


class AddVersion(StatesGroup):
    select_app = State()
    upload_file = State()
    version_name = State()
    changelog = State()
    min_android = State()
    release_type = State()


class Broadcast(StatesGroup):
    message = State()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ─── /admin ──────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return
    await message.answer(
        "🔧 **Панель администратора**\n\n"
        "➕ Добавить приложение\n"
        "📤 Загрузить новую версию\n"
        "📊 Статистика\n"
        "📢 Рассылка\n"
        "👥 Пользователи",
        reply_markup=get_admin_kb()
    )


@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    if is_admin(message.from_user.id):
        await message.answer("❌ Действие отменено.", reply_markup=get_admin_kb())
    else:
        await message.answer("❌ Действие отменено.", reply_markup=get_main_menu_kb())


# ─── Admin Menu Text Handlers ────────────────────────────────────────────────

@router.message(F.text == "🏠 Главное меню")
async def go_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Главное меню:", reply_markup=get_main_menu_kb())


@router.message(F.text == "📊 Статистика")
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    daily, total_dl, total_users = await get_stats_for_admin()
    dl_per_app = await get_downloads_per_app()
    
    text = "📊 **Статистика**\n\n"
    text += f"👥 Всего пользователей: {total_users}\n"
    text += f"📅 Активных сегодня: {daily}\n"
    text += f"⬇️ Всего скачиваний: {total_dl}\n\n"
    text += "**По приложениям:**\n"
    for app in dl_per_app:
        text += f"• {app[1]}: {app[3]} ⬇️\n"
    
    await message.answer(text)


@router.message(F.text == "👥 Пользователи")
async def admin_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    count = await get_user_count()
    await message.answer(f"👥 **Всего пользователей в боте:** {count}")


@router.message(F.text == "🌐 Синхр. GitHub")
async def admin_github_sync(message: Message):
    if not is_admin(message.from_user.id):
        return
    if not GITHUB_OWNER or not GITHUB_REPO:
        await message.answer(
            "❌ GitHub не настроен.\n"
            "Добавьте в .env:\n"
            "GITHUB_OWNER=ваш_логин\n"
            "GITHUB_REPO=ваш_репозиторий\n"
            "GITHUB_TOKEN=ваш_токен (опционально)"
        )
        return

    msg = await message.answer("🔄 Синхронизация с GitHub...")

    from github_sync import sync_github_releases
    from database import get_all_apps

    apps = await get_all_apps()
    total_added = 0
    total_skipped = 0
    total_errors = 0
    lines = []

    for app in apps:
        slug = app[2]
        app_name = app[1]
        try:
            result = await sync_github_releases(
                GITHUB_OWNER, GITHUB_REPO, slug, GITHUB_TOKEN
            )
            total_added += result["added"]
            total_skipped += result["skipped"]
            total_errors += result["errors"]
            lines.append(
                f"• {app_name}: +{result['added']} / пропущено {result['skipped']}"
            )
        except Exception as e:
            total_errors += 1
            lines.append(f"• {app_name}: ❌ {e}")

    text = (
        f"🌐 **Синхронизация с GitHub завершена**\n\n"
        + "\n".join(lines)
        + f"\n\n✅ Добавлено: {total_added}\n"
        + f"⏭ Пропущено: {total_skipped}\n"
        + f"❌ Ошибок: {total_errors}"
    )
    await msg.edit_text(text)


# ─── Add App Flow ────────────────────────────────────────────────────────────

@router.message(F.text == "➕ Добавить приложение")
async def add_app_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddApp.name)
    await message.answer(
        "✏️ Введите название приложения:",
        reply_markup=get_cancel_kb()
    )


@router.message(AddApp.name)
async def add_app_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 1 or len(name) > 64:
        await message.answer("❌ Название должно быть от 1 до 64 символов.")
        return
    await state.update_data(name=name)
    await state.set_state(AddApp.slug)
    await message.answer(
        f"🔖 Введите slug (уникальный идентификатор латиницей, например: {name.lower().replace(' ', '_')}):"
    )


@router.message(AddApp.slug)
async def add_app_slug(message: Message, state: FSMContext):
    slug = message.text.strip().lower().replace(" ", "_")
    if not slug or not slug.replace("_", "").isalnum():
        await message.answer("❌ Slug должен содержать только латиницу, цифры и символ подчёркивания.")
        return
    
    existing = await get_app_by_slug(slug)
    if existing:
        await message.answer(f"❌ Приложение с slug «{slug}» уже существует.")
        return
    
    await state.update_data(slug=slug)
    await state.set_state(AddApp.description)
    await message.answer("📝 Введите описание приложения:")


@router.message(AddApp.description)
async def add_app_desc(message: Message, state: FSMContext):
    description = message.text.strip()
    data = await state.get_data()
    
    await add_app(data["name"], data["slug"], description)
    await state.clear()
    
    await message.answer(
        f"✅ Приложение «{data['name']}» успешно добавлено!",
        reply_markup=get_admin_kb()
    )


# ─── Add Version Flow ────────────────────────────────────────────────────────

@router.message(F.text == "📤 Загрузить версию")
async def add_version_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    apps = await get_all_apps()
    if not apps:
        await message.answer("❌ Сначала добавьте приложение.")
        return
    
    await state.set_state(AddVersion.select_app)
    await message.answer(
        "Выберите приложение для новой версии:",
        reply_markup=get_admin_apps_inline_kb(apps, "addver")
    )


@router.callback_query(F.data.startswith("admin_addver_"))
async def add_version_select_app(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    
    app_id = int(callback.data.split("_")[2])
    app = await get_app_by_id(app_id)
    if not app:
        await callback.answer("Приложение не найдено.", show_alert=True)
        return
    
    await state.update_data(app_id=app_id)
    await state.set_state(AddVersion.upload_file)
    
    await callback.message.edit_text(
        f"📤 Приложение: **{app['name']}**\n\n"
        "Отправьте файл (.apk, .exe, .msi и т.д.):"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.answer()


@router.message(AddVersion.upload_file, F.document)
async def add_version_file(message: Message, state: FSMContext, bot: Bot):
    doc = message.document
    file_id = doc.file_id
    file_name = doc.file_name or f"file_{doc.file_unique_id}"
    file_size = doc.file_size
    
    data = await state.get_data()
    app_id = data["app_id"]
    app = await get_app_by_id(app_id)
    if not app:
        await message.answer("❌ Приложение не найдено.")
        await state.clear()
        return
    
    save_dir = os.path.join(DOWNLOADS_DIR, app["slug"])
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, file_name)
    
    tg_file = await bot.get_file(file_id)
    await bot.download_file(tg_file.file_path, save_path)
    
    await state.update_data(
        file_id=file_id, file_path=save_path,
        file_size=file_size, file_name=file_name
    )
    await state.set_state(AddVersion.version_name)
    
    await message.answer(
        f"✅ Файл сохранён: {file_name} ({format_size(file_size)})\n\n"
        "🔖 Введите номер версии (например: v1.2.75):"
    )


@router.message(AddVersion.upload_file)
async def add_version_file_invalid(message: Message):
    await message.answer("❌ Пожалуйста, отправьте файл (документ).")


@router.message(AddVersion.version_name)
async def add_version_name(message: Message, state: FSMContext):
    version = message.text.strip()
    if not version:
        await message.answer("❌ Версия не может быть пустой.")
        return
    await state.update_data(version=version)
    await state.set_state(AddVersion.changelog)
    await message.answer(
        "📝 Введите changelog (что нового в этой версии)\n"
        "Или отправьте «-» чтобы пропустить:"
    )


@router.message(AddVersion.changelog)
async def add_version_changelog(message: Message, state: FSMContext):
    changelog = message.text.strip()
    if changelog == "-":
        changelog = ""
    await state.update_data(changelog=changelog)
    await state.set_state(AddVersion.min_android)
    await message.answer(
        "📱 Введите минимальную версию Android (например: 8.0)\n"
        "Или отправьте «-» чтобы пропустить:"
    )


@router.message(AddVersion.min_android)
async def add_version_min_android(message: Message, state: FSMContext):
    min_android = message.text.strip()
    if min_android == "-":
        min_android = ""
    
    await state.update_data(min_android=min_android)
    await state.set_state(AddVersion.release_type)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Stable", callback_data="rt_stable")],
        [InlineKeyboardButton(text="🧪 Beta", callback_data="rt_beta")],
        [InlineKeyboardButton(text="⚙️ Alpha", callback_data="rt_alpha")],
    ])
    await message.answer("🏷 Выберите тип релиза:", reply_markup=kb)


@router.callback_query(F.data.startswith("rt_"))
async def add_version_release_type(callback: CallbackQuery, state: FSMContext):
    rtype = callback.data.split("_")[1]
    data = await state.get_data()
    
    await add_version(
        app_id=data["app_id"],
        version=data["version"],
        changelog=data.get("changelog", ""),
        file_id=data.get("file_id", ""),
        file_path=data.get("file_path", ""),
        file_size=data.get("file_size", 0),
        min_android=data.get("min_android", ""),
        release_type=rtype
    )
    
    app = await get_app_by_id(data["app_id"])
    app_name = app["name"] if app else "?"
    
    await state.clear()
    await callback.message.edit_text(
        f"✅ Версия **{data['version']}** ({rtype}) для **{app_name}** успешно добавлена!"
    )
    await callback.message.answer(
        "🔧 Панель администратора:", reply_markup=get_admin_kb()
    )
    await callback.answer()


# ─── Broadcast ───────────────────────────────────────────────────────────────

@router.message(F.text == "📢 Рассылка")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(Broadcast.message)
    await message.answer(
        "📢 Введите текст для рассылки всем пользователям:",
        reply_markup=get_cancel_kb()
    )


@router.message(Broadcast.message)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    text = message.text.strip()
    if not text:
        await message.answer("❌ Текст не может быть пустым.")
        return
    
    users = await get_all_users()
    sent = 0
    failed = 0
    
    status_msg = await message.answer(f"📢 Начинаю рассылку {len(users)} пользователям...")
    
    for user_id, username in users:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            sent += 1
        except Exception:
            failed += 1
    
    await state.clear()
    await status_msg.edit_text(
        f"📢 **Рассылка завершена**\n\n"
        f"✅ Отправлено: {sent}\n"
        f"❌ Не удалось: {failed}\n"
        f"👥 Всего: {len(users)}",
        reply_markup=get_admin_kb()
    )


# ─── Quick Commands ──────────────────────────────────────────────────────────

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    await admin_stats(message)


@router.message(Command("users"))
async def cmd_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    await admin_users(message)


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await broadcast_start(message, state)


@router.message(Command("add_version"))
async def cmd_add_version(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await add_version_start(message, state)
