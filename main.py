# main.py

import os
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# 1) టోకెన్ సెట్ చేయండి
TELEGRAM_BOT_TOKEN = os.getenv("8210861967:AAFWXYLVZOgX-SPKkaIzZ_TxSiNfLsw0q2U")  # పోస్టు చేయడానికి შესაბამისად సెట్ చేయండి

# 2) సరళమైన స్పామ్-రేట-లిమిట్: యూజర్‌కి ఇంకొంచెట్లు మెసేజ్‌ಗಳು పంపొద్దు
USER_TIMEOUT = 30  # ప్రతి యూజర్ కి 30 సెకండ్ల తరువాత మాత్రమే మెసేజ్
user_last_seen = {}

# 3) బేసిక్ క్రిఇటింగ్: కొద్దిపాటి కీవర్డ్-ఆధారిత స్పందన
KEY_RESPONSES = {
    "hello": "హैलो! మీరు ఎలా ఉన్నారు?",
    "hi": "హాయ్! మీకు ఎలా సహాయం చెయ్యము?",
    "help": "మీ ప్రశ్నలను అడగండి. నేను సానుకూల సహాయం చెయ్యడానికి ప్రయత్నిస్తాను.",
}

# 4) కమాండ్ హ్యాండ్లర్
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_last_seen[user_id] = time.time()
    update.message.reply_text("నమస్కారం! నేను మీకు సహాయం చేసేది నమూనా బటన్ని. సబమ్ కాకుండా మాట్లాడుదాం!")

# 5) మెసేజ్ హ్యాండ్లర్: స్పామ్-రెస్ట్‌లను అడ్డుకోవడం
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    now = time.time()

    last = user_last_seen.get(user_id, 0)
    if now - last < USER_TIMEOUT:
        # తక్కువ సమయం లో many messages: స్వల్ప ప్రతిస్పందన ఇవ్వటం
        update.message.reply_text("దయచేసి కొద్దిగా ఆసక్తిగా స్పందించండి. స్క్రిప్ట్ బద్దలు సંતુష్టంగా ఉంది.")
        return

    user_last_seen[user_id] = now
    text = update.message.text.lower()

    # 6) కీవర్డ్-ఆధారిత స్పందన
    for key, resp in KEY_RESPONSES.items():
        if key in text:
            update.message.reply_text(resp)
            return

    # 7) డిఫాడ్ట్ రిస్పాన్స్
    update.message.reply_text("మీ సందేశాన్ని స్వీకరించాము. నేను త్వరగా సమాధానాన్ని చూసి తిరిగి చెప్పుతాను.")

# 8) main వాటర్: బాటింగ్స్-కాంపైల్
def main():
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("టోకెన్ సెట్ చేయబడాలి. TELEGRAM_BOT_TOKEN వాతావరణ చర పరిశీలించండి.")

    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
