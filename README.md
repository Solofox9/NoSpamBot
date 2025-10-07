# NoSpamBot 🛡️

A smart, lightweight Telegram bot that **automatically deletes profanity and spam** in your groups, so you don’t have to.

Made for group admins who want a cleaner, safer chat without constant moderation.

---

## ✨ Features

- **Auto-deletes** messages containing offensive language (using [profanity.dev](https://profanity.dev))
- **Ignores admins** — your team can speak freely
- **Adjustable sensitivity** (`/confidence 70`) — set how strict the filter is
- **Toggle on/off** anytime (`/profanity_off` / `/profanity_on`)
- **Test mode** for admins (`/test_profanity hello`)
- **Lightweight & fast** — won’t slow down your group
- Works with **accents & symbols** (e.g., "fúck", "sh!t" → still caught)

---

## 🚀 How to Use

1. **Add [@NoSpamBot](https://telegram.me/NoSpamBot)** to your group  
2. **Make it an admin** with **“Delete Messages”** permission  
3. That’s it! It starts working immediately 🎉

> 💡 Tip: Use `/confidence 80` to make it stricter, or `/confidence 40` to be more relaxed.

---

## 🔒 Privacy

- Only checks message text — **no logs, no storage**
- Never reads private chats (only works in groups)
- Open source & transparent

---

## 🛠️ Self-Hosting (for developers)

Want to run your own version?

```bash
git clone https://github.com/Harshit-shrivastav/NoSpamBot
cd NoSpamBot
pip install -r requirements.txt
```

Create a `.env` file:
```env
BOT_TOKEN=your_bot_token_from_botfather
# Optional: for /stats command
ADMIN_ID=your_telegram_user_id
```

Then run:
```bash
python bot.py
```

---

## ❤️ Made with care

By [Harshit Shrivastav](https://github.com/Harshit-shrivastav)  
Free, open-source, and always improving.

[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://telegram.me/NoSpamBot)  
[![GitHub](https://img.shields.io/badge/GitHub-Repo-black?logo=github)](https://github.com/Harshit-shrivastav/NoSpamBot)
