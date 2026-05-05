import os
import time
import json
from pathlib import Path

import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
GAME_URL = os.getenv("WEBAPP_URL")

ADMIN_IDS = {5274220765}
TRIAL_TIME = 300
DATA_FILE = Path("users_access.json")

bot = telebot.TeleBot(TOKEN)

# 🌍 языки
LANG = {}

def get_lang(user_id):
    return LANG.get(user_id, "ru")

def set_lang(user_id, lang):
    LANG[user_id] = lang

# тексты
TEXT = {
    "ru": {
        "menu": "🎮 Играть",
        "access": "⏳ Мой доступ",
        "lang": "🌍 Язык",
        "trial": "🎁 Осталось",
        "expired": "⛔ Время закончилось",
        "admin": "👑 Админ доступ"
    },
    "en": {
        "menu": "🎮 Play",
        "access": "⏳ My access",
        "lang": "🌍 Language",
        "trial": "🎁 Left",
        "expired": "⛔ Time expired",
        "admin": "👑 Admin access"
    },
    "ka": {
        "menu": "🎮 თამაში",
        "access": "⏳ წვდომა",
        "lang": "🌍 ენა",
        "trial": "🎁 დარჩა",
        "expired": "⛔ დრო დასრულდა",
        "admin": "👑 ადმინისტრატორი"
    }
}

def load_users():
    if not DATA_FILE.exists():
        return {}
    return json.loads(DATA_FILE.read_text())

def save_users(data):
    DATA_FILE.write_text(json.dumps(data))

def ensure_user(user_id):
    users = load_users()
    uid = str(user_id)

    if uid not in users:
        users[uid] = {"trial_started": int(time.time())}
        save_users(users)

    return users[uid]

def is_admin(user_id):
    return user_id in ADMIN_IDS

def trial_left(user_id):
    if is_admin(user_id):
        return 999999

    user = ensure_user(user_id)
    left = TRIAL_TIME - (int(time.time() - user["trial_started"]))
    return max(0, left)

def access_text(user_id):
    lang = get_lang(user_id)
    t = TEXT[lang]

    if is_admin(user_id):
        return t["admin"]

    left = trial_left(user_id)

    if left > 0:
        return f"{t['trial']}: {left//60}:{left%60}"
    return t["expired"]

def main_menu(user_id):
    lang = get_lang(user_id)
    t = TEXT[lang]

    kb = types.InlineKeyboardMarkup()

    if is_admin(user_id):
        url = f"{GAME_URL}/?admin=vaxo1971"
    else:
        url = f"{GAME_URL}/?user={user_id}"

    kb.add(types.InlineKeyboardButton(t["menu"], url=url))
    kb.add(types.InlineKeyboardButton(t["access"], callback_data="access"))
    kb.add(types.InlineKeyboardButton(t["lang"], callback_data="lang"))

    return kb

# команды
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    ensure_user(user_id)

    bot.send_message(
        user_id,
        "🃏 Ancient Card Games",
        reply_markup=main_menu(user_id)
    )

@bot.callback_query_handler(func=lambda c: c.data == "access")
def access_cb(call):
    uid = call.message.chat.id
    bot.send_message(uid, access_text(uid), reply_markup=main_menu(uid))

@bot.callback_query_handler(func=lambda c: c.data == "lang")
def lang_menu(call):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🇷🇺", callback_data="lang_ru"),
        types.InlineKeyboardButton("🇬🇧", callback_data="lang_en"),
        types.InlineKeyboardButton("🇬🇪", callback_data="lang_ka"),
    )
    bot.send_message(call.message.chat.id, "Choose language", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def set_lang_cb(call):
    lang = call.data.split("_")[1]
    set_lang(call.message.chat.id, lang)
    bot.send_message(call.message.chat.id, "OK", reply_markup=main_menu(call.message.chat.id))

# запуск
def run_bot():
    print("Deleting webhook...")
    bot.remove_webhook()
    time.sleep(2)

    print("Bot started...")
    bot.infinity_polling(
        skip_pending=True,
        timeout=20,
        long_polling_timeout=20
    )

if __name__ == "__main__":
    run_bot()
