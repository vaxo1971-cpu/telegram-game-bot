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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row("🎰 Play", "🃏 Games")
    markup.row("💰 Buy Access", "⚙️ Settings")

    bot.send_message(
        message.chat.id,
        "🎰 Ancient Card Games\n\nВыбери действие:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "🎰 Play")
def play(message):
    code = generate_code()
    url = f"{GAME_URL}/?code={code}"

    bot.send_message(
        message.chat.id,
        f"🎟 Code:\n{code}\n👉 {url}"
    )


bot.polling()
