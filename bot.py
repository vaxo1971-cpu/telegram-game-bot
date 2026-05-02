import telebot
from telebot import types
import random
import string
import time
import json
import os
import threading

TOKEN = os.getenv("BOT_TOKEN")
GAME_URL = "https://guileless-toffee-fec890.netlify.app"

ACCESS_FILE = "access.json"
STATS_FILE = "stats.json"

TRIAL_SECONDS = 60

PRICES = {
    "pay_1": {"seconds": 3600, "stars": 50, "title": "1 hour access"},
    "pay_24": {"seconds": 86400, "stars": 150, "title": "24 hours access"},
    "pay_48": {"seconds": 172800, "stars": 300, "title": "48 hours access"},
}

bot = telebot.TeleBot(TOKEN)


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


user_access = load_json(ACCESS_FILE, {})

stats = load_json(STATS_FILE, {
    "started_users": [],
    "play_users": [],
    "play_clicks": 0,
    "payments": 0,
    "paid_users": [],
    "paid_amount": 0,
    "codes": 0,
    "trial_users": [],
    "trial_count": 0
})


def save_access():
    save_json(ACCESS_FILE, user_access)


def save_stats():
    save_json(STATS_FILE, stats)


def generate_code():
    return "LS-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


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
    markup.row(types.InlineKeyboardButton("💰 Купить доступ / Buy Access / წვდომის ყიდვა", callback_data="buy"))
    return markup


def buy_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("⏱ 1 час / 1 hour / 1 საათი — 50⭐", callback_data="pay_1"))
    markup.row(types.InlineKeyboardButton("📅 24 часа / 24 hours / 24 საათი — 150⭐", callback_data="pay_24"))
    markup.row(types.InlineKeyboardButton("🔥 48 часов / 48 hours / 48 საათი — 300⭐", callback_data="pay_48"))
    markup.row(types.InlineKeyboardButton("⬅️ Назад / Back / უკან", callback_data="back"))
    return markup


def game_link(user_id):
    code = generate_code()
    return f"{GAME_URL}/?code={code}&user={user_id}"


def trial_finished_message(chat_id, user_id):
    now = int(time.time())
    user_id_str = str(user_id)

    if user_access.get(user_id_str, 0) > now:
        return

    bot.send_message(
        chat_id,
        """⏳ Бесплатный доступ закончился.
⏳ Free trial has ended.
⏳ უფასო წვდომა დასრულდა.

💰 Купите доступ:
💰 Buy access:
💰 შეიძინეთ წვდომა:""",
        reply_markup=buy_keyboard()
    )


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id

    if user_id not in stats["started_users"]:
        stats["started_users"].append(user_id)
        save_stats()

    bot.send_message(
        message.chat.id,
        START_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


@bot.message_handler(commands=["stats"])
def stats_cmd(message):
    now = int(time.time())
    active_access = sum(1 for v in user_access.values() if v > now)

    text = f"""📊 Stats:

/start: {len(stats['started_users'])}
Play users: {len(stats['play_users'])}
Clicks: {stats['play_clicks']}
Trial: {stats['trial_count']}
Payments: {stats['payments']}
Paid users: {len(stats['paid_users'])}
Paid amount: {stats['paid_amount']}⭐
Active access: {active_access}
Codes: {stats['codes']}"""

    bot.send_message(message.chat.id, text)


@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_callback(call):
    bot.send_message(call.message.chat.id, START_TEXT, parse_mode="Markdown", reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: call.data == "buy")
def buy_callback(call):
    bot.send_message(
        call.message.chat.id,
        """💰 Выберите доступ:
💰 Choose access:
💰 აირჩიეთ წვდომა:""",
        reply_markup=buy_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data in PRICES)
def pay_callback(call):
    item = PRICES[call.data]

    prices = [
        types.LabeledPrice(
            label=item["title"],
            amount=item["stars"]
        )
    ]

    bot.send_invoice(
        chat_id=call.message.chat.id,
        title=item["title"],
        description="Ancient Card Games access",
        invoice_payload=call.data,
        provider_token="",
        currency="XTR",
        prices=prices
    )


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def successful_payment(message):
    user_id = str(message.from_user.id)
    payload = message.successful_payment.invoice_payload

    if payload not in PRICES:
        return

    item = PRICES[payload]
    now = int(time.time())

    current_until = user_access.get(user_id, 0)
    if current_until < now:
        current_until = now

    user_access[user_id] = current_until + item["seconds"]
    save_access()

    stats["payments"] += 1
    stats["paid_amount"] += item["stars"]

    if message.from_user.id not in stats["paid_users"]:
        stats["paid_users"].append(message.from_user.id)

    save_stats()

    bot.send_message(
        message.chat.id,
        f"""✅ Доступ оплачен.
✅ Access paid.
✅ წვდომა გადახდილია.

🎮 Играть / Play / თამაში:
{game_link(user_id)}""",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data == "play")
def play_callback(call):
    user_id_int = call.from_user.id
    user_id = str(user_id_int)
    now = int(time.time())

    has_access = user_access.get(user_id, 0) > now

    if not has_access:
        if user_id_int not in stats["trial_users"]:
            user_access[user_id] = now + TRIAL_SECONDS
            save_access()

            stats["trial_users"].append(user_id_int)
            stats["trial_count"] += 1
            save_stats()

            bot.send_message(
                call.message.chat.id,
                """🎁 Бесплатный доступ на 1 минуту начался.
🎁 Free 1 minute trial started.
🎁 უფასო 1 წუთიანი წვდომა დაიწყო."""
            )

            threading.Timer(
                TRIAL_SECONDS,
                trial_finished_message,
                args=(call.message.chat.id, user_id_int)
            ).start()
        else:
            bot.send_message(
                call.message.chat.id,
                """🔒 Бесплатный доступ уже использован.
🔒 Free trial already used.
🔒 უფასო წვდომა უკვე გამოყენებულია.

💰 Купите доступ / Buy access / შეიძინეთ წვდომა:""",
                reply_markup=buy_keyboard()
            )
            return

    stats["play_clicks"] += 1
    stats["codes"] += 1

    if user_id_int not in stats["play_users"]:
        stats["play_users"].append(user_id_int)

    save_stats()

    bot.send_message(
        call.message.chat.id,
        f"🎮 {game_link(user_id)}"
    )


while True:
    try:
        print("Бот запущен...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(e)
        time.sleep(3)
