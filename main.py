import os
import logging
from aiogram import Bot, Dispatcher, types
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Config
API_ID = os.getenv("28961091")
API_HASH = os.getenv("fa3796dbdec1efdf151aca5f14815d06")
BOT_TOKEN = os.getenv("8210861967:AAFWXYLVZOgX-SPKkaIzZ_TxSiNfLsw0q2U")
HELPER_BOT_TOKEN = os.getenv("8078360814:AAHLhQtLqXI3_9tESrMigeEKRzHp5PkypAk")
OWNER_ID = int(os.getenv("1573111356"))
LOG_CHANNEL_1 = int(os.getenv("-1003030307131"))
LOG_CHANNEL_2 = int(os.getenv("-1003101356980"))

# MongoDB
MONGODB_URI_1 = os.getenv("mongodb+srv://tdanimehub_db_user:cPdMT253KSZpE11Z@helper.wallqjf.mongodb.net/?retryWrites=true&w=majority&appName=Helper")
MONGODB_URI_2 = os.getenv("mongodb+srv://tdanimehub_db_user:3fPbmCdShf91FPZ9@storage1.gwel1e6.mongodb.net/?retryWrites=true&w=majority&appName=Storage1")

client1 = MongoClient(MONGODB_URI_1)
client2 = MongoClient(MONGODB_URI_2)

db1 = client1["gwel1e6.mongodb.net/?retryWrites=true&w=majority&appName=Storage1"]
db2 = client2["mongodb+srv://tdanimehub_db_user:3fPbmCdShf91FPZ9@storage1.gwel1e6.mongodb.net/?retryWrites=true&w=majority&appName=Storage1"]

# Bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Logging
logging.basicConfig(level=logging.INFO)

# Example handler
@dp.message()
async def handle_msg(message: types.Message):
    # Check for spam or profanity
    pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
