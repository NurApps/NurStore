# NurStore — Telegram bot for NurApps ecosystem
# Copyright (C) 2026  NurApps
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DONATE_LINK = os.getenv("DONATE_LINK")
CHANNEL_LINK = os.getenv("CHANNEL_LINK")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME")

GITHUB_OWNER = os.getenv("GITHUB_OWNER", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

DB_PATH = "nurapps.db"
DOWNLOADS_DIR = "downloads"