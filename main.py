import asyncio
import json
import logging
import os
import re
import time
import sqlite3
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

BOT_TOKEN = os.getenv("8210861967:AAFWXYLVZOgX-SPKkaIzZ_TxSiNfLsw0q2U")
ADMIN_ID = os.getenv("1573111356")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env")

API_URL = "http://my.telegram.org"
DEFAULT_CONFIDENCE = 60
CACHE_FILE = "profanity_cache.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

_http_session: Optional[aiohttp.ClientSession] = None

# SQLite setup
DB_FILE = "bot_data.db"
SETTINGS_CACHE: Dict[int, Dict] = {}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            chat_id INTEGER UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            chat_id INTEGER PRIMARY KEY,
            enabled BOOLEAN DEFAULT 1,
            confidence INTEGER DEFAULT 60
        )
    ''')
    conn.commit()
    conn.close()

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

def log_interaction(user_id: int, chat_id: int, chat_type: str):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        if chat_type == "private":
            c.execute("INSERT OR IGNORE INTO stats (user_id) VALUES (?)", (user_id,))
        else:
            c.execute("INSERT OR IGNORE INTO stats (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.warning(f"Stats log error: {e}")

def get_group_settings(chat_id: int) -> dict:
    if chat_id in SETTINGS_CACHE:
        return SETTINGS_CACHE[chat_id]
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT enabled, confidence FROM settings WHERE chat_id = ?", (chat_id,))
        row = c.fetchone()
        conn.close()
        if row:
            settings = {"enabled": bool(row[0]), "confidence": row[1]}
        else:
            settings = {"enabled": True, "confidence": DEFAULT_CONFIDENCE}
        SETTINGS_CACHE[chat_id] = settings
        return settings
    except Exception as e:
        logging.warning(f"Settings load error: {e}")
        return {"enabled": True, "confidence": DEFAULT_CONFIDENCE}

def save_group_settings(chat_id: int, enabled: bool, confidence: int):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO settings (chat_id, enabled, confidence) VALUES (?, ?, ?)",
            (chat_id, enabled, confidence)
        )
        conn.commit()
        conn.close()
        SETTINGS_CACHE[chat_id] = {"enabled": enabled, "confidence": confidence}
    except Exception as e:
        logging.warning(f"Settings save error: {e}")

async def is_user_admin(chat_id: int, user_id: int) -> bool:
    try:
        member: ChatMember = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

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
            "Admin commands in groups:\n"
            "• /profanity_on – Enable filtering\n"
            "• /profanity_off – Disable filtering\n"
            "• /confidence [0-100] – Set sensitivity\n"
            "• /test_profanity [text] – Test detection"
        )
    else:
        await message.answer(
            "🛡️ Profanity filter is active!\n\n"
            "I automatically delete messages containing offensive content.\n"
            "Admins' messages are never deleted.\n\n"
            "Use /confidence to adjust sensitivity (default: 60%)."
        )

@dp.message(Command("profanity_off"))
async def profanity_off(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return
    save_group_settings(message.chat.id, enabled=False, confidence=DEFAULT_CONFIDENCE)
    await message.reply("🔇 Profanity filter has been disabled.")

@dp.message(Command("profanity_on"))
async def profanity_on(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return
    current = get_group_settings(message.chat.id)
    save_group_settings(message.chat.id, enabled=True, confidence=current["confidence"])
    await message.reply("🔊 Profanity filter is now active.")

@dp.message(Command("confidence"))
async def set_confidence(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return
    if not message.text or len(message.text.split()) < 2:
        current = get_group_settings(message.chat.id)
        await message.reply(f"Current confidence: {current['confidence']}%\nUsage: /confidence 50")
        return
    
    try:
        value = int(message.text.split()[1])
        if not (0 <= value <= 100):
            raise ValueError
    except ValueError:
        await message.reply("Please provide a number between 0 and 100.\nExample: /confidence 75")
        return

    save_group_settings(message.chat.id, enabled=True, confidence=value)
    await message.reply(f"✅ Confidence threshold set to {value}%.")

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
    if str(message.from_user.id) != ADMIN_ID.strip():
        return
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT COUNT(DISTINCT user_id) FROM stats WHERE user_id IS NOT NULL")
        users = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(DISTINCT chat_id) FROM stats WHERE chat_id IS NOT NULL")
        groups = c.fetchone()[0] or 0
        conn.close()
        await message.answer(f"📊 Bot Statistics:\n\n👥 Total Users: {users}\n🏘️ Active Groups: {groups}")
    except Exception as e:
        await message.answer("Failed to fetch stats.")
        logging.error(f"Stats error: {e}")

@dp.my_chat_member()
async def on_bot_added(event: ChatMemberUpdated):
    if (
        event.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and
        event.new_chat_member.user.id == bot.id
    ):
        log_interaction(0, event.chat.id, "group")
        save_group_settings(event.chat.id, enabled=True, confidence=DEFAULT_CONFIDENCE)
        await bot.send_message(
            event.chat.id,
            f"🙏 Thanks for adding me to <b>{event.chat.title}</b>!\n\n"
            "To start filtering profanity:\n"
            "1. Make me an <b>admin</b>\n"
            "2. Grant <b>Delete Messages</b> permission\n\n"
            "I'll then automatically remove offensive messages. "
            "Use /confidence to adjust sensitivity (default: 60%).",
            parse_mode="HTML"
        )

@dp.message()
async def handle_messages(message: types.Message):
    if not message.from_user:
        return

    log_interaction(message.from_user.id, message.chat.id, message.chat.type)

    if message.text:
        lower_text = message.text.lower()
        if lower_text.startswith(("/start", "/profanity_off", "/profanity_on", "/confidence", "/test_profanity", "/stats")):
            return

    if message.chat.type == ChatType.PRIVATE:
        await message.answer(
            "👋 Hi! I'm a profanity filter bot.\n\n"
            "Add me to your group and make me an admin with <b>Delete Messages</b> permission. "
            "I'll automatically remove messages containing offensive language.",
            parse_mode="HTML"
        )
        return

    chat_id = message.chat.id
    settings = get_group_settings(chat_id)
    if not settings["enabled"]:
        return

    if not message.text:
        return

    if await is_user_admin(chat_id, message.from_user.id):
        return

    normalized = unidecode(message.text).lower()
    tokens = set(re.findall(r"\b\w+\b", normalized))

    BAD_WORDS = load_cache()
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
    if result and result.get("isProfanity"):
        score = result.get("score", 0)
        threshold = settings["confidence"] / 100.0
        if score >= threshold:
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
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
