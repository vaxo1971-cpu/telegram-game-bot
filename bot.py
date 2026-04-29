import telebot
from telebot import types
import random
import string
import time

TOKEN = "8250941489:AAEUlIUmBVMF2yr6uq-b9qmrpmnmLw0gUcg"

bot = telebot.TeleBot(TOKEN)

GAME_URL = "https://guileless-toffee-fec890.netlify.app"

user_access = {}


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


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🏛 Ancient Card Games\n\nВыбери действие:",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data == "play")
def play_callback(call):
    user_id = call.from_user.id
    now = time.time()

    if user_id not in user_access or user_access[user_id] < now:
        bot.answer_callback_query(call.id, "Нужно купить доступ", show_alert=True)
        bot.send_message(
            call.message.chat.id,
            "🔒 Доступ не активен.\nНажми 💰 Buy Access.",
            reply_markup=main_menu()
        )
        return

    code = generate_code()
    url = f"{GAME_URL}/?code={code}"

    bot.send_message(
        call.message.chat.id,
        f"🎟 Code:\n{code}\n👉 {url}"
    )


@bot.callback_query_handler(func=lambda call: call.data == "buy")
def buy_menu(call):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("⏱ 1 час — 50⭐", callback_data="buy_1"))
    markup.row(types.InlineKeyboardButton("📅 24 часа — 150⭐", callback_data="buy_24"))
    markup.row(types.InlineKeyboardButton("🔥 48 часов — 300⭐", callback_data="buy_48"))
    markup.row(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))

    bot.send_message(
        call.message.chat.id,
        "💰 Выбери доступ:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_process(call):
    user_id = call.from_user.id
    now = time.time()

    if call.data == "buy_1":
        user_access[user_id] = now + 3600
        text = "✅ Доступ активирован на 1 час.\n\nТеперь нажми 🎰 Play."
    elif call.data == "buy_24":
        user_access[user_id] = now + 24 * 3600
        text = "✅ Доступ активирован на 24 часа.\n\nТеперь нажми 🎰 Play."
    elif call.data == "buy_48":
        user_access[user_id] = now + 48 * 3600
        text = "✅ Доступ активирован на 48 часов.\n\nТеперь нажми 🎰 Play."
    else:
        text = "Ошибка выбора."

    bot.send_message(
        call.message.chat.id,
        text,
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data == "games")
def games_callback(call):
    bot.send_message(
        call.message.chat.id,
        "🃏 Игры доступны на сайте после активации доступа.",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data == "settings")
def settings_callback(call):
    bot.send_message(
        call.message.chat.id,
        "⚙️ Settings пока в разработке.",
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
