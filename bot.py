import os
import time
import telebot
from telebot import types

# ================== НАСТРОЙКИ ==================

TOKEN = os.getenv("BOT_TOKEN", "8250941489:AAGq74NQ2anLdiQ8-t1SOmH2Qusr4c5kyZo")

GAME_URL = "https://aquamarine-strudel-14e0ed.netlify.app"

ADMIN_IDS = {5274220765}

TRIAL_TIME = 300  # 5 минут

ACCESS_TIME = {
    "1h": 3600,
    "24h": 86400,
    "48h": 172800,
}

bot = telebot.TeleBot(TOKEN)
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

    if time.time() - user.get("trial_started", 0) <= TRIAL_TIME:
        return True

    if time.time() <= user.get("pro_until", 0):
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


def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎮 Играть", callback_data="play"))
    markup.add(types.InlineKeyboardButton("⏳ Мой доступ", callback_data="access"))
    markup.add(types.InlineKeyboardButton("💳 Купить PRO", callback_data="buy_menu"))
    return markup


def buy_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⏱ 1 час — 50⭐", callback_data="buy_1h"))
    markup.add(types.InlineKeyboardButton("📅 24 часа — 150⭐", callback_data="buy_24h"))
    markup.add(types.InlineKeyboardButton("🔥 48 часов — 300⭐", callback_data="buy_48h"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    return markup

# ================== КОМАНДЫ ==================

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    start_trial(user_id)

    text = (
        "🏛 Ancient Card Games\n\n"
        "🎴 Poker\n"
        "⚔️ Emperor’s 21\n"
        "🃏 Joker\n\n"
        "🎁 Бесплатно: 5 минут trial\n"
        "💰 После окончания можно купить PRO-доступ.\n\n"
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
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Выбери срок PRO-доступа:", reply_markup=buy_menu())


@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Главное меню:", reply_markup=main_menu())


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

    game_link = f"{GAME_URL}/?user={user_id}"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎮 Открыть игру", url=game_link))
    markup.add(types.InlineKeyboardButton("⏳ Мой доступ", callback_data="access"))

    bot.send_message(
        user_id,
        f"🎮 Игра открыта:\n{game_link}\n\n{access_left_text(user_id)}",
        reply_markup=markup
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

# ================== ЗАПУСК ==================

if __name__ == "__main__":
    print("Bot starting...")
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
