import asyncio, logging, os, json, re
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.middleware import BaseMiddleware
from aiogram.utils.executor import start_polling
from unidecode import unidecode
import aiohttp

TOKEN   = os.getenv("BOT_TOKEN")
CACHE   = "profanity_cache.json"
API_URL = "https://vector.profanity.dev"
THRESH  = 0.60

bot = Bot(token=TOKEN, parse_mode="html")
dp  = Dispatcher(bot)
session = None

# ---------- cache helpers ----------
def load_cache() -> set:
    try:
        with open(CACHE) as f:
            return set(json.load(f))
    except:
        return set()

def save_cache(words: set):
    with open(CACHE, "w") as f:
        json.dump(list(words), f)

BAD_WORDS = load_cache()

# ---------- middleware ----------
class ProfanityMW(BaseMiddleware):
    async def on_pre_process_message(self, m: types.Message, _):
        if not m.text:
            return
        norm = unidecode(m.text).lower()
        tokens = re.findall(r"\b\w+\b", norm)

        # 1. fast cache hit
        if any(w in BAD_WORDS for w in tokens):
            await self.act(m, 1.0, "cached")
            return

        # 2. ask API for whole sentence
        async with session.post(API_URL, json={"message": norm}) as r:
            if r.status != 200:
                return
            j = await r.json()
            if j.get("isProfanity") and j.get("score", 0) >= THRESH:
                # cache the flagged token(s)
                flagged = j.get("flaggedFor", "").lower()
                if flagged:
                    BAD_WORDS.add(flagged)
                    save_cache(BAD_WORDS)
                await self.act(m, j["score"], flagged)

    async def act(self, m: types.Message, score: float, reason: str):
        try:
            await m.delete()
        except:
            await m.reply(f"I am {score*100:.0f}% confident this message is spam or profanity, but i don't have permission to delete this message.")

dp.middleware.setup(ProfanityMW())

# ---------- events ----------
@dp.message_handler(content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
async def on_add(m: types.Message):
    if m.new_chat_members[-1].id == bot.id:
        await m.answer(
            f"Thanks for adding me to <b>{m.chat.title}</b>! "
            "Please give me permission to delete messages so I can remove spam/profanity."
        )

@dp.message_handler(commands="start", chat_type=[types.ChatType.PRIVATE, types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def start(m: types.Message):
    await m.answer(
        "👋 I auto-remove profanity/spam messages. "
        "Add me to a group and grant delete-message permission. "
        "I check every message (including service ones) and delete anything ≥60% profanity."
    )

# ---------- lifecycle ----------
async def on_startup(_):
    global session
    session = aiohttp.ClientSession()
    logging.basicConfig(level=logging.ERROR)

async def on_shutdown(_):
    await session.close()

if __name__ == "__main__":
    start_polling(dp, skip_updates=False, on_startup=on_startup, on_shutdown=on_shutdown)
