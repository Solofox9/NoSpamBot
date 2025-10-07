import asyncio
import json
import logging
import os
import re
import time
from typing import Set, Optional, Dict

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, ChatMember
from aiogram.enums import ChatType
from dotenv import load_dotenv
from unidecode import unidecode
import aiohttp

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env")

API_URL = "https://vector.profanity.dev"
THRESHOLD = 0.60
CACHE_FILE = "profanity_cache.json"
SETTINGS_FILE = "bot_settings.json"
USER_LOG_FILE = "user_interactions.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

_http_session: Optional[aiohttp.ClientSession] = None

def get_session() -> aiohttp.ClientSession:
    global _http_session
    if _http_session is None or _http_session.closed:
        _http_session = aiohttp.ClientSession()
    return _http_session

def load_cache() -> Set[str]:
    try:
        with open(CACHE_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_cache(words: Set[str]):
    with open(CACHE_FILE, "w") as f:
        json.dump(list(words), f)

def load_settings() -> dict:
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_settings( dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f)

def load_user_log() -> dict:
    try:
        with open(USER_LOG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": [], "groups": []}

def save_user_log(data: dict):
    with open(USER_LOG_FILE, "w") as f:
        json.dump(data, f)

BAD_WORDS = load_cache()
SETTINGS = load_settings()
USER_LOG = load_user_log()

async def is_user_admin(chat_id: int, user_id: int) -> bool:
    try:
        member: ChatMember = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

def log_interaction(user_id: int, chat_id: int, chat_type: str):
    global USER_LOG
    if chat_type == "private":
        if user_id not in USER_LOG["users"]:
            USER_LOG["users"].append(user_id)
    else:
        if chat_id not in USER_LOG["groups"]:
            USER_LOG["groups"].append(chat_id)
    save_user_log(USER_LOG)

async def call_profanity_api(text: str, retries=1) -> Optional[dict]:
    session = get_session()
    for attempt in range(retries + 1):
        try:
            async with session.post(
                API_URL,
                json={"message": text},
                timeout=aiohttp.ClientTimeout(total=4)
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            if attempt == retries:
                return None
            await asyncio.sleep(0.5)
    return None

_deletion_warning_sent: Dict[int, float] = {}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    log_interaction(message.from_user.id, message.chat.id, message.chat.type)
    if message.chat.type == ChatType.PRIVATE:
        await message.answer(
            "👋 Hi! I'm a profanity filter bot.\n\n"
            "Add me to your group and make me an admin with <b>Delete Messages</b> permission. "
            "I'll automatically remove messages containing offensive language.\n\n"
            "Commands in groups:\n"
            "• /profanity_on – Enable filtering\n"
            "• /profanity_off – Disable filtering\n"
            "• /test_profanity [text] – Test detection (admin only)"
        )
    else:
        await message.answer(
            "🛡️ Profanity filter is active!\n\n"
            "I automatically delete messages containing offensive content (≥60% confidence).\n"
            "Admins' messages are never deleted.\n\n"
            "Available commands:\n"
            "• /profanity_on – Re-enable filtering\n"
            "• /profanity_off – Temporarily disable\n"
            "• /test_profanity [text] – Test detection"
        )

@dp.message(Command("profanity_off"))
async def profanity_off(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return
    SETTINGS[str(message.chat.id)] = {"enabled": False}
    save_settings(SETTINGS)
    await message.reply("🔇 Profanity filter has been disabled.")

@dp.message(Command("profanity_on"))
async def profanity_on(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return
    SETTINGS[str(message.chat.id)] = {"enabled": True}
    save_settings(SETTINGS)
    await message.reply("🔊 Profanity filter is now active.")

@dp.message(Command("test_profanity"))
async def test_profanity(message: types.Message):
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return
    if not message.text or len(message.text.split()) < 2:
        await message.reply("Usage: /test_profanity <text to check>")
        return
    test_text = " ".join(message.text.split()[1:])
    normalized = unidecode(test_text).lower()
    result = await call_profanity_api(normalized)
    if result and result.get("isProfanity"):
        await message.reply(
            f"✅ Profanity detected!\nScore: {result['score']:.2f}\nFlagged word: {result.get('flaggedFor', 'N/A')}"
        )
    else:
        await message.reply("✅ No profanity detected.")

@dp.message(Command("stats"))
async def stats(message: types.Message):
    if not ADMIN_ID:
        return
    try:
        if str(message.from_user.id) != ADMIN_ID.strip():
            return
    except:
        return
    total_users = len(USER_LOG["users"])
    total_groups = len(USER_LOG["groups"])
    await message.answer(f"📊 Bot Statistics:\n\n👥 Total Users: {total_users}\n🏘️ Active Groups: {total_groups}")

@dp.my_chat_member()
async def on_bot_added(event: ChatMemberUpdated):
    if (
        event.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and
        event.new_chat_member.user.id == bot.id
    ):
        log_interaction(0, event.chat.id, "group")
        await bot.send_message(
            event.chat.id,
            f"🙏 Thanks for adding me to <b>{event.chat.title}</b>!\n\n"
            "To start filtering profanity:\n"
            "1. Make me an <b>admin</b>\n"
            "2. Grant <b>Delete Messages</b> permission\n\n"
            "I'll then automatically remove offensive messages. "
            "Use /profanity_off to pause filtering anytime.",
            parse_mode="HTML"
        )

@dp.message()
async def handle_messages(message: types.Message):
    if not message.from_user:
        return

    log_interaction(message.from_user.id, message.chat.id, message.chat.type)

    if message.text:
        lower_text = message.text.lower()
        if lower_text.startswith(("/start", "/profanity_off", "/profanity_on", "/test_profanity", "/stats")):
            return

    if message.chat.type == ChatType.PRIVATE:
        await message.answer(
            "👋 Hi! I'm a profanity filter bot.\n\n"
            "Add me to your group and make me an admin with <b>Delete Messages</b> permission. "
            "I'll automatically remove messages containing offensive language."
        )
        return

    chat_id = message.chat.id
    chat_key = str(chat_id)
    if not SETTINGS.get(chat_key, {}).get("enabled", True):
        return

    if not message.text:
        return

    if await is_user_admin(chat_id, message.from_user.id):
        return

    normalized = unidecode(message.text).lower()
    tokens = set(re.findall(r"\b\w+\b", normalized))

    if tokens & BAD_WORDS:
        try:
            await message.delete()
        except:
            now = time.time()
            if chat_id not in _deletion_warning_sent or now - _deletion_warning_sent[chat_id] > 3600:
                _deletion_warning_sent[chat_id] = now
                try:
                    await message.reply(
                        "⚠️ I can't delete messages. Please grant me 'Delete Messages' permission."
                    )
                except:
                    pass
        return

    result = await call_profanity_api(normalized)
    if result and result.get("isProfanity") and result.get("score", 0) >= THRESHOLD:
        flagged = result.get("flaggedFor", "").lower().strip()
        if flagged:
            BAD_WORDS.add(flagged)
            save_cache(BAD_WORDS)
        try:
            await message.delete()
        except:
            now = time.time()
            if chat_id not in _deletion_warning_sent or now - _deletion_warning_sent[chat_id] > 3600:
                _deletion_warning_sent[chat_id] = now
                try:
                    await message.reply(
                        "⚠️ I can't delete messages. Please grant me 'Delete Messages' permission."
                    )
                except:
                    pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
