# NurStore — Telegram bot for NurApps ecosystem
# Copyright (C) 2026  NurApps
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import db_start
from handlers import user, admin


async def on_startup(bot: Bot):
    await db_start()
    me = await bot.get_me()
    print(f"[NurStore] Bot started: @{me.username} (ID: {me.id})")


async def on_shutdown(bot: Bot):
    print("[NurStore] Bot stopped.")


async def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set in .env")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(user.router)
    dp.include_router(admin.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[NurStore] Bot stopped by user.")
