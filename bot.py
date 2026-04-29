import telebot
from telebot import types
import random
import string

TOKEN = "8250941489:AAEUlIUmBVMF2yr6uq-b9qmrpmnmLw0gUcg"

bot = telebot.TeleBot(TOKEN)

GAME_URL = "https://guileless-toffee-fec890.netlify.app"


def generate_code():
    return "LS-" + ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=6)
    )


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton("🎰 Play", callback_data="play"),
        types.InlineKeyboardButton("🃏 Games", callback_data="games")
    )
    markup.row(
        types.InlineKeyboardButton("💰 Buy Access", callback_data="buy"),
        types.InlineKeyboardButton("⚙️ Settings", callback_data="settings")
    )

    bot.send_message(
        message.chat.id,
        "🎰 Ancient Card Games\n\nВыбери действие:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "play")
def play_callback(call):
    code = generate_code()
    url = f"{GAME_URL}/?code={code}"

    bot.send_message(
        call.message.chat.id,
        f"🎟 Code:\n{code}\n👉 {url}"
    )


bot.infinity_polling()
