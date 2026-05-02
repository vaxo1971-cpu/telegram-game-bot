import telebot
from telebot import types
import random
import string
import time
import json
import os
import threading
from typing import Optional

TOKEN = os.getenv("BOT_TOKEN")

GAME_URL = "https://guileless-toffee-fec890.netlify.app"
ACCESS_FILE = "access.json"
STATS_FILE = "stats.json"

TRIAL_SECONDS = 60

bot = telebot.TeleBot(TOKEN)


def load_access():
    if os.path.exists(ACCESS_FILE):
        try:
            with open(ACCESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_access(data):
    try:
        with open(ACCESS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_stats():
    data = {}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    data.setdefault("started_users", [])
    data.setdefault("play_users", [])
    data.setdefault("play_clicks", 0)
    data.setdefault("payments", 0)
    data.setdefault("paid_users", [])
    data.setdefault("paid_amount", 0)
    data.setdefault("codes", 0)
    data.setdefault("trial_users", [])
    data.setdefault("trial_count", 0)

    return data


def save_stats():
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def track_started(user_id: int):
    if user_id not in stats["started_users"]:
        stats["started_users"].append(int(user_id))
        save_stats()


def track_play(user_id: int):
    stats["play_clicks"] += 1
    stats["codes"] += 1
    if user_id not in stats["play_users"]:
        stats["play_users"].append(int(user_id))
    save_stats()


def track_payment(user_id: int, amount: Optional[int]):
    stats["payments"] += 1
    if amount is not None:
        try:
            stats["paid_amount"] += int(amount)
        except Exception:
            pass

    if user_id not in stats["paid_users"]:
        stats["paid_users"].append(int(user_id))

    save_stats()


def generate_code():
    return "LS-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


user_access = load_access()
stats = load_stats()


START_TEXT = """🏛 *Ancient Card Games*

🇷🇺 Добро пожаловать в мир древних карточных игр.
🇬🇧 Welcome to the world of ancient card games.
🇬🇪 კეთილი იყოს თქვენი მობრძანება უძველესი კარტის თამაშების სამყაროში.

🎴 Poker
⚔️ Emperor’s 21

🎁 Бесплатно: 1 минута trial
🎁 Free: 1 minute trial
🎁 უფასოდ: 1 წუთი trial

💰 Доступ / Access / წვდომა:
⏱ 1 час / 1 hour / 1 საათი — 50⭐
📅 24 часа / 24 hours / 24 საათი — 150⭐
🔥 48 часов / 48 hours / 48 საათი — 300⭐

👇 Выберите действие / Choose action / აირჩიეთ მოქმედება:
"""


def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🎮 Играть / Play / თამაში", callback_data="play"))
    markup.row(types.InlineKeyboardButton("🃏 Игры / Games / თამაშები", callback_data="games"))
    markup.row(types.InlineKeyboardButton("💰 Купить доступ / Buy Access / წვდომის ყიდვა", callback_data="buy"))
    markup.row(types.InlineKeyboardButton("⚙️ Настройки / Settings / პარამეტრები", callback_data="settings"))
    return markup


def buy_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("⏱ 1 час / 1 hour / 1 საათი — 50⭐", callback_data="pay_1"))
    markup.row(types.InlineKeyboardButton("📅 24 часа / 24 hours / 24 საათი — 150⭐", callback_data="pay_24"))
    markup.row(types.InlineKeyboardButton("🔥 48 часов / 48 hours / 48 საათი — 300⭐", callback_data="pay_48"))
    markup.row(types.InlineKeyboardButton("⬅️ Назад / Back / უკან", callback_data="back"))
    return markup


def trial_finished_message(chat_id, user_id):
    now = int(time.time())
    user_id = str(user_id)

    if user_id in user_access and user_access[user_id] > now:
        return

    bot.send_message(
        chat_id,
        """⏳ Бесплатный доступ закончился.
⏳ Free trial has ended.
⏳ უფასო წვდომა დასრულდა.

💰 Купите доступ:
💰 Buy access:
💰 შეიძინეთ წვდომა:""",
        reply_markup=buy_keyboard(),
    )


@bot.message_handler(commands=["start"])
def start(message):
    track_started(message.from_user.id)
    bot.send_message(message.chat.id, START_TEXT, parse_mode="Markdown", reply_markup=main_menu())


@bot.message_handler(commands=["stats"])
def stats_cmd(message):
    now = int(time.time())
    active_access = sum(1 for v in user_access.values() if v > now)

    text = f"""📊 Stats:

/start: {len(stats['started_users'])}
Play: {len(stats['play_users'])}
Clicks: {stats['play_clicks']}
Trial: {stats['trial_count']}
Payments: {stats['payments']}
Active: {active_access}"""

    bot.send_message(message.chat.id, text)


@bot.callback_query_handler(func=lambda call: call.data == "play")
def play_callback(call):
    user_id_int = call.from_user.id
    user_id = str(user_id_int)
    now = int(time.time())

    if user_id not in user_access or user_access[user_id] < now:
        if user_id_int not in stats["trial_users"]:
            user_access[user_id] = now + TRIAL_SECONDS
            save_access(user_access)

            stats["trial_users"].append(user_id_int)
            stats["trial_count"] += 1
            save_stats()

            bot.send_message(call.message.chat.id, "🎁 1 minute trial started!", reply_markup=main_menu())

            threading.Timer(TRIAL_SECONDS, trial_finished_message, args=(call.message.chat.id, user_id_int)).start()
        else:
            bot.send_message(call.message.chat.id, "🔒 Buy access first", reply_markup=buy_keyboard())
            return

    track_play(user_id_int)

    code = generate_code()
    url = f"{GAME_URL}/?code={code}&user={user_id}"

    bot.send_message(call.message.chat.id, f"🎮 {url}")


while True:
    try:
        print("Бот запущен...")
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        time.sleep(3)
