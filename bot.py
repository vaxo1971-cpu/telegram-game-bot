import telebot
from telebot import types
import random
import string
import time
import json
import os
from typing import Optional

TOKEN = "8250941489:AAGq74NQ2anLdiQ8-t1SOmH2Qusr4c5kyZo"
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

    # trial stats
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


@bot.message_handler(commands=["start"])
def start(message):
    track_started(message.from_user.id)
    bot.send_message(
        message.chat.id,
        START_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


@bot.message_handler(commands=["stats", "stat"])
def stats_cmd(message):
    now = int(time.time())
    active_access = sum(1 for v in user_access.values() if v > now)
    text = (
        "📊 Stats / Статистика / სტატისტიკა:\n\n"
        f"👤 /start unique: {len(set(stats['started_users']))}\n"
        f"🎮 Play unique: {len(set(stats['play_users']))}\n"
        f"⬇️ Play clicks: {stats['play_clicks']}\n"
        f"🎟 Codes: {stats['codes']}\n"
        f"🎁 Trial unique: {len(set(stats['trial_users']))}\n"
        f"🎁 Trial uses: {stats['trial_count']}\n"
        f"💰 Payments count: {stats['payments']}\n"
        f"💸 Paid users: {len(set(stats['paid_users']))}\n"
        f"⭐ Paid amount (stars): {stats['paid_amount']}\n"
        f"👥 Users with access records (all): {len(user_access)}\n"
        f"🔓 Active access now: {active_access}\n"
    )
    bot.send_message(message.chat.id, text)


def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🎮 Играть / Play / თამაში", callback_data="play"))
    markup.row(types.InlineKeyboardButton("🃏 Игры / Games / თამაშები", callback_data="games"))
    markup.row(
        types.InlineKeyboardButton(
            "💰 Купить доступ / Buy Access / წვდომის ყიდვა", callback_data="buy"
        )
    )
    markup.row(
        types.InlineKeyboardButton("⚙️ Настройки / Settings / პარამეტრები", callback_data="settings")
    )
    return markup


def buy_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(
            "⏱ 1 час / 1 hour / 1 საათი — 50⭐", callback_data="pay_1"
        )
    )
    markup.row(
        types.InlineKeyboardButton(
            "📅 24 часа / 24 hours / 24 საათი — 150⭐", callback_data="pay_24"
        )
    )
    markup.row(
        types.InlineKeyboardButton(
            "🔥 48 часов / 48 hours / 48 საათი — 300⭐", callback_data="pay_48"
        )
    )
    markup.row(types.InlineKeyboardButton("⬅️ Назад / Back / უკან", callback_data="back"))
    return markup


@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_callback(call):
    bot.send_message(
        call.message.chat.id,
        START_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


@bot.callback_query_handler(func=lambda call: call.data == "buy")
def buy_menu(call):
    bot.send_message(
        call.message.chat.id,
        """💰 Выберите доступ:
💰 Choose access:
💰 აირჩიეთ წვდომა:""",
        reply_markup=buy_keyboard(),
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def send_stars_invoice(call):
    if call.data == "pay_1":
        title = "Ancient Card Games — 1 hour"
        description = "Доступ на 1 час / Access for 1 hour / წვდომა 1 საათით"
        amount = 50
        payload = "access_1"
    elif call.data == "pay_24":
        title = "Ancient Card Games — 24 hours"
        description = "Доступ на 24 часа / Access for 24 hours / წვდომა 24 საათით"
        amount = 150
        payload = "access_24"
    else:
        title = "Ancient Card Games — 48 hours"
        description = "Доступ на 48 часов / Access for 48 hours / წვდომა 48 საათით"
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
        start_parameter=payload,
    )


@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def successful_payment(message):
    user_id = str(message.from_user.id)
    payload = message.successful_payment.invoice_payload
    amount = getattr(message.successful_payment, "total_amount", None)
    track_payment(message.from_user.id, amount=amount)

    now = int(time.time())

    if payload == "access_1":
        user_access[user_id] = now + 3600
        text = """✅ Оплата прошла. Доступ активирован на 1 час.
✅ Payment successful. Access activated for 1 hour.
✅ გადახდა წარმატებულია. წვდომა გააქტიურდა 1 საათით."""
    elif payload == "access_24":
        user_access[user_id] = now + 24 * 3600
        text = """✅ Оплата прошла. Доступ активирован на 24 часа.
✅ Payment successful. Access activated for 24 hours.
✅ გადახდა წარმატებულია. წვდომა გააქტიურდა 24 საათით."""
    elif payload == "access_48":
        user_access[user_id] = now + 48 * 3600
        text = """✅ Оплата прошла. Доступ активирован на 48 часов.
✅ Payment successful. Access activated for 48 hours.
✅ გადახდა წარმატებულია. წვდომა გააქტიურდა 48 საათით."""
    else:
        text = """✅ Оплата получена, но тариф не найден.
✅ Payment received, but plan not found.
✅ გადახდა მიღებულია, მაგრამ ტარიფი ვერ მოიძებნა."""

    save_access(user_access)

    bot.send_message(
        message.chat.id,
        text + "\n\n🎮 Теперь нажмите Играть / Now press Play / ახლა დააჭირეთ თამაში.",
        reply_markup=main_menu(),
    )


@bot.callback_query_handler(func=lambda call: call.data == "play")
def play_callback(call):
    user_id_int = call.from_user.id
    user_id = str(user_id_int)
    now = int(time.time())

    # Access check
    if user_id not in user_access or user_access[user_id] < now:
        # Trial available once per user
        if user_id_int not in stats["trial_users"]:
            user_access[user_id] = now + TRIAL_SECONDS
            save_access(user_access)

            stats["trial_users"].append(int(user_id_int))
            stats["trial_count"] += 1
            save_stats()

            bot.send_message(
                call.message.chat.id,
                """🎁 Бесплатная 1 минута trial активирована.
🎁 Free 1 minute trial activated.
🎁 უფასო 1 წუთიანი trial გააქტიურდა.

После trial нужен доступ по прайсу.
After trial you need access.
Trial-ის შემდეგ საჭიროა წვდომა.
""",
                reply_markup=main_menu(),
            )
        else:
            bot.answer_callback_query(
                call.id,
                "Сначала купите доступ / Buy access first / ჯერ შეიძინეთ წვდომა",
                show_alert=True,
            )
            bot.send_message(
                call.message.chat.id,
                """🔒 Доступ не активен.
🔒 Access is not active.
🔒 წვდომა არ არის აქტიური.

Нажмите 💰 Купить доступ / Press 💰 Buy Access / დააჭირეთ 💰 წვდომის ყიდვა.""",
                reply_markup=main_menu(),
            )
            return

    # Play
    track_play(user_id_int)

    code = generate_code()
    url = f"{GAME_URL}/?code={code}&user={user_id}"

    bot.send_message(
        call.message.chat.id,
        f"""🎟 Code / Код / კოდი:
`{code}`

🎮 Game:
{url}""",
        parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda call: call.data == "games")
def games_callback(call):
    bot.send_message(
        call.message.chat.id,
        """🃏 Available games / Доступные игры / ხელმისაწვდომი თამაშები:

🎴 Poker
⚔️ Emperor’s 21

Для игры нужен активный доступ.
Active access is required to play.
თამაშისთვის საჭიროა აქტიური წვდომა.""",
        reply_markup=main_menu(),
    )


@bot.callback_query_handler(func=lambda call: call.data == "settings")
def settings_callback(call):
    user_id = str(call.from_user.id)
    now = int(time.time())

    if user_id in user_access and user_access[user_id] > now:
        left = user_access[user_id] - now
        hours = left // 3600
        minutes = (left % 3600) // 60

        text = f"""⚙️ Доступ активен.
Осталось: {hours} ч. {minutes} мин.

⚙️ Access is active.
Time left: {hours} h. {minutes} min.

⚙️ წვდომა აქტიურია.
დარჩენილია: {hours} სთ. {minutes} წთ."""
    else:
        text = """⚙️ Доступ не активен.
⚙️ Access is not active.
⚙️ წვდომა არ არის აქტიური."""

    bot.send_message(call.message.chat.id, text, reply_markup=main_menu())


while True:
    try:
        print("Бот запущен...")
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(3)
