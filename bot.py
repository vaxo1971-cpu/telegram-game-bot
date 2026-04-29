import telebot
from telebot import types
import random
import string
import time
import json
import os

TOKEN = "8250941489:AAEUlIUmBVMF2yr6uq-b9qmrpmnmLw0gUcg"
GAME_URL = "https://guileless-toffee-fec890.netlify.app"
ACCESS_FILE = "access.json"

bot = telebot.TeleBot(TOKEN)


def load_access():
    if os.path.exists(ACCESS_FILE):
        with open(ACCESS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_access(data):
    with open(ACCESS_FILE, "w") as f:
        json.dump(data, f)


user_access = load_access()


def generate_code():
    return "LS-" + ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=6)
    )


def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🎰 Play", callback_data="play"),
        types.InlineKeyboardButton("🃏 Games", callback_data="games")
    )
    markup.row(
        types.InlineKeyboardButton("💰 Buy Access", callback_data="buy"),
        types.InlineKeyboardButton("⚙️ Settings", callback_data="settings")
    )
    return markup


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🏛 Ancient Card Games\n\nВыбери действие:",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data == "play")
def play_callback(call):
    user_id = str(call.from_user.id)
    now = int(time.time())

    if user_id not in user_access or user_access[user_id] < now:
        bot.answer_callback_query(call.id, "Сначала купи доступ", show_alert=True)
        bot.send_message(
            call.message.chat.id,
            "🔒 Доступ не активен.\nНажми 💰 Buy Access.",
            reply_markup=main_menu()
        )
        return

    code = generate_code()
    url = f"{GAME_URL}/?code={code}&user={user_id}"

    bot.send_message(
        call.message.chat.id,
        f"🎟 Code:\n{code}\n👉 {url}"
    )


@bot.callback_query_handler(func=lambda call: call.data == "buy")
def buy_menu(call):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("⏱ 1 час — 50⭐", callback_data="pay_1"))
    markup.row(types.InlineKeyboardButton("📅 24 часа — 150⭐", callback_data="pay_24"))
    markup.row(types.InlineKeyboardButton("🔥 48 часов — 300⭐", callback_data="pay_48"))
    markup.row(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))

    bot.send_message(
        call.message.chat.id,
        "💰 Выбери доступ:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def send_stars_invoice(call):
    if call.data == "pay_1":
        title = "Access 1 hour"
        description = "Доступ к игре на 1 час"
        amount = 50
        payload = "access_1"
    elif call.data == "pay_24":
        title = "Access 24 hours"
        description = "Доступ к игре на 24 часа"
        amount = 150
        payload = "access_24"
    else:
        title = "Access 48 hours"
        description = "Доступ к игре на 48 часов"
        amount = 300
        payload = "access_48"

    prices = [types.LabeledPrice(label=title, amount=amount)]

    bot.send_invoice(
        chat_id=call.message.chat.id,
        title=title,
        description=description,
        invoice_payload=payload,
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter=payload
    )


@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def successful_payment(message):
    user_id = str(message.from_user.id)
    payload = message.successful_payment.invoice_payload
    now = int(time.time())

    if payload == "access_1":
        user_access[user_id] = now + 3600
        text = "✅ Оплата прошла.\nДоступ активирован на 1 час."
    elif payload == "access_24":
        user_access[user_id] = now + 24 * 3600
        text = "✅ Оплата прошла.\nДоступ активирован на 24 часа."
    elif payload == "access_48":
        user_access[user_id] = now + 48 * 3600
        text = "✅ Оплата прошла.\nДоступ активирован на 48 часов."
    else:
        text = "Оплата получена, но тариф не найден."

    save_access(user_access)

    bot.send_message(
        message.chat.id,
        text + "\n\nТеперь нажми 🎰 Play.",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data == "games")
def games_callback(call):
    bot.send_message(
        call.message.chat.id,
        "🃏 Игры доступны после покупки доступа.",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data == "settings")
def settings_callback(call):
    user_id = str(call.from_user.id)
    now = int(time.time())

    if user_id in user_access and user_access[user_id] > now:
        left = user_access[user_id] - now
        hours = left // 3600
        minutes = (left % 3600) // 60
        text = f"⚙️ Доступ активен.\nОсталось: {hours} ч. {minutes} мин."
    else:
        text = "⚙️ Доступ не активен."

    bot.send_message(
        call.message.chat.id,
        text,
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_callback(call):
    bot.send_message(
        call.message.chat.id,
        "🏛 Ancient Card Games\n\nВыбери действие:",
        reply_markup=main_menu()
    )


bot.infinity_polling()
