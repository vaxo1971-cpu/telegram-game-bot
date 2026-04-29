import telebot
from telebot import types
import time

TOKEN = "8250941489:AAEUlIUmBVMF2yr6uq-b9qmrpmnmLw0gUcg"  # <-- вставь сюда свой токен
bot = telebot.TeleBot(TOKEN)

GAME_URL = "https://guileless-toffee-fec890.netlify.app/"

# хранилище доступа (временно в памяти)
users_access = {}

# тарифы (в секундах)
TARIFFS = {
    "1h": (50, 3600),
    "24h": (150, 86400),
    "48h": (300, 172800)
}


@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row("🎰 Play", "🃏 Games")
    markup.row("💰 Buy Access", "⚙️ Settings")

    bot.send_message(
        message.chat.id,
        "🎰 Ancient Card Games\n\nВыбери действие:",
        reply_markup=markup
    )    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Играть", "💳 Купить доступ")

    bot.send_message(
        message.chat.id,
        "🎰 Ancient Card Games\n\nВыбери действие:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda m: m.text == "💳 Купить доступ")
def buy(message):
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton("1 час — 50 ⭐", callback_data="buy_1h"))
    markup.add(types.InlineKeyboardButton("24 часа — 150 ⭐", callback_data="buy_24h"))
    markup.add(types.InlineKeyboardButton("48 часов — 300 ⭐", callback_data="buy_48h"))

    bot.send_message(message.chat.id, "Выбери тариф:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_buy(call):
    tariff = call.data.split("_")[1]

    price, duration = TARIFFS[tariff]

    # тут имитация оплаты (позже подключим реальные Stars)
    users_access[call.from_user.id] = time.time() + duration

    bot.answer_callback_query(call.id, "Оплата успешна!")
    bot.send_message(call.message.chat.id, "✅ Доступ открыт!")


@bot.message_handler(func=lambda m: m.text == "🎮 Играть")
def play(message):
    user_id = message.from_user.id

    if user_id not in users_access:
        bot.send_message(message.chat.id, "❌ У тебя нет доступа. Купи доступ.")
        return

    if time.time() > users_access[user_id]:
        bot.send_message(message.chat.id, "⏳ Доступ истёк.")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶ Открыть игру", url=GAME_URL))

    bot.send_message(
        message.chat.id,
        "🎮 Нажми кнопку, чтобы играть:",
        reply_markup=markup
    )


print("Bot started...")
bot.infinity_polling()
