import os
import time
import threading

from flask import Flask
import telebot
from telebot import types


# ================== НАСТРОЙКИ ==================

TOKEN = os.getenv("BOT_TOKEN", "8250941489:AAGq74NQ2anLdiQ8-t1SOmH2Qusr4c5kyZo")

# Твой Telegram ID для бесплатного админ-доступа
ADMIN_IDS = {
    123456789
}

TRIAL_TIME = 300  # 5 минут

ACCESS_TIME = {
    "1h": 3600,
    "24h": 86400,
    "48h": 172800,
}

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

users = {}


# ================== ДОСТУП ==================

def is_admin(user_id):
    return user_id in ADMIN_IDS


def start_trial(user_id):
    if user_id not in users:
        users[user_id] = {
            "trial_started": time.time(),
            "pro_until": 0
        }


def has_access(user_id):
    if is_admin(user_id):
        return True

    user = users.get(user_id)
    if not user:
        return False

    trial_started = user.get("trial_started", 0)
    pro_until = user.get("pro_until", 0)

    if time.time() - trial_started <= TRIAL_TIME:
        return True

    if time.time() <= pro_until:
        return True

    return False


def access_left_text(user_id):
    if is_admin(user_id):
        return "👑 У тебя админ-доступ без ограничения."

    user = users.get(user_id)
    if not user:
        return "Доступ не активирован."

    now = time.time()

    if now - user.get("trial_started", 0) <= TRIAL_TIME:
        left = int(TRIAL_TIME - (now - user["trial_started"]))
        return f"🎁 Бесплатно осталось: {left // 60} мин. {left % 60} сек."

    if now <= user.get("pro_until", 0):
        left = int(user["pro_until"] - now)
        return f"✅ PRO осталось: {left // 3600} ч. {(left % 3600) // 60} мин."

    return "⛔ Доступ закончился."


def buy_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⭐ 1 час", callback_data="buy_1h"))
    markup.add(types.InlineKeyboardButton("⭐ 24 часа", callback_data="buy_24h"))
    markup.add(types.InlineKeyboardButton("⭐ 48 часов", callback_data="buy_48h"))
    return markup


def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎮 Играть", callback_data="play"))
    markup.add(types.InlineKeyboardButton("⏳ Мой доступ", callback_data="access"))
    markup.add(types.InlineKeyboardButton("💳 Купить PRO", callback_data="buy_menu"))
    return markup


# ================== КОМАНДЫ ==================

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    start_trial(user_id)

    text = (
        "🎮 Добро пожаловать в Ancient Card Games!\n\n"
        "🎁 Первые 5 минут бесплатно.\n"
        "После окончания trial можно купить PRO-доступ.\n\n"
        f"{access_left_text(user_id)}"
    )

    bot.send_message(user_id, text, reply_markup=main_menu())


@bot.message_handler(commands=["id"])
def get_id(message):
    bot.send_message(message.chat.id, f"Твой Telegram ID:\n{message.chat.id}")


@bot.message_handler(commands=["status"])
def status(message):
    user_id = message.chat.id
    start_trial(user_id)
    bot.send_message(user_id, access_left_text(user_id), reply_markup=main_menu())


# ================== КНОПКИ ==================

@bot.callback_query_handler(func=lambda call: call.data == "access")
def access_callback(call):
    user_id = call.message.chat.id
    start_trial(user_id)
    bot.answer_callback_query(call.id)
    bot.send_message(user_id, access_left_text(user_id), reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: call.data == "buy_menu")
def buy_menu_callback(call):
    user_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    bot.send_message(user_id, "Выбери срок PRO-доступа:", reply_markup=buy_menu())


@bot.callback_query_handler(func=lambda call: call.data == "play")
def play_callback(call):
    user_id = call.message.chat.id
    start_trial(user_id)
    bot.answer_callback_query(call.id)

    if not has_access(user_id):
        bot.send_message(
            user_id,
            "⛔ Бесплатный доступ закончился.\n\nКупи PRO-доступ:",
            reply_markup=buy_menu()
        )
        return

    bot.send_message(
        user_id,
        "🎮 Игра открыта.\n\n"
        "Если у тебя игра на сайте, нажми кнопку/ссылку сайта в старом меню.\n"
        f"\n{access_left_text(user_id)}",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_callback(call):
    user_id = call.message.chat.id
    start_trial(user_id)

    option = call.data.replace("buy_", "")
    seconds = ACCESS_TIME.get(option)

    bot.answer_callback_query(call.id)

    if not seconds:
        bot.send_message(user_id, "Ошибка тарифа.")
        return

    current_until = users[user_id].get("pro_until", 0)
    base_time = max(time.time(), current_until)
    users[user_id]["pro_until"] = base_time + seconds

    bot.send_message(
        user_id,
        "✅ PRO-доступ активирован.\n\n"
        f"{access_left_text(user_id)}",
        reply_markup=main_menu()
    )


# ================== FLASK ДЛЯ RENDER ==================

@app.route("/")
def home():
    return "Bot is running"


# ================== ЗАПУСК ==================

def run_bot():
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        except Exception as e:
            print("BOT ERROR:", e)
            time.sleep(5)


if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
