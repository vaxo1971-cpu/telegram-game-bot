import os
import time
import random
import string
import sqlite3
import telebot
from flask import Flask, request
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    LabeledPrice,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8250941489:AAFXYszmVt_9zWmlzjTiHAi54ZXJqp7eRcA")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://aquamarine-strudel-14e0ed.netlify.app")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "vaxo1971")
DB_PATH = os.getenv("DB_PATH", "bot.db")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)


TEXTS = {
    "ru": {
        "title": "🃏 Ancient Card Games",
        "description": (
            "Карточные игры против бота.\n\n"
            "🎮 Игры:\n"
            "• Poker\n"
            "• Emperor’s 21\n"
            "• Joker\n\n"
            "Это тренировочная игра без денежных ставок, без вывода средств и без азартных призов."
        ),
        "play": "🎮 Играть",
        "trial": "🎁 Бесплатно 5 минут",
        "access": "⏳ Мой доступ",
        "language": "🌍 Язык",
        "admin": "👑 Админ",
        "buy": "⭐ Купить доступ",
        "code": "🎟 Ввести код",
        "stats": "📊 Статистика",
        "trial_ok": "✅ Бесплатный доступ открыт на 5 минут.",
        "admin_ok": "👑 Админ-доступ активирован.",
        "admin_no": "Админ-доступ только для владельца.",
        "admin_status": "👑 У тебя админ-доступ без ограничения.",
        "left": "⏳ Осталось примерно {minutes} минут.",
        "expired": "⛔ Доступ закончился.",
        "choose_lang": "Выбери язык:",
        "lang_ok": "✅ Язык изменён.",
        "fallback": "Нажми /start, чтобы открыть меню.",
        "send_code": "Отправь код в формате: LS-XXXXXX",
        "bad_code": "❌ Код не найден или уже использован.",
        "good_code": "✅ Код принят. Доступ открыт.",
    },
    "en": {
        "title": "🃏 Ancient Card Games",
        "description": (
            "Card games against the bot.\n\n"
            "🎮 Games:\n"
            "• Poker\n"
            "• Emperor’s 21\n"
            "• Joker\n\n"
            "Training game only. No real-money betting, no withdrawals, no gambling prizes."
        ),
        "play": "🎮 Play",
        "trial": "🎁 Free 5 minutes",
        "access": "⏳ My access",
        "language": "🌍 Language",
        "admin": "👑 Admin",
        "buy": "⭐ Buy access",
        "code": "🎟 Enter code",
        "stats": "📊 Stats",
        "trial_ok": "✅ Free access opened for 5 minutes.",
        "admin_ok": "👑 Admin access activated.",
        "admin_no": "Admin access is only for owner.",
        "admin_status": "👑 You have unlimited admin access.",
        "left": "⏳ About {minutes} minutes left.",
        "expired": "⛔ Access expired.",
        "choose_lang": "Choose language:",
        "lang_ok": "✅ Language changed.",
        "fallback": "Press /start to open menu.",
        "send_code": "Send code like: LS-XXXXXX",
        "bad_code": "❌ Code not found or already used.",
        "good_code": "✅ Code accepted. Access opened.",
    },
    "ka": {
        "title": "🃏 Ancient Card Games",
        "description": (
            "კარტის თამაშები ბოტის წინააღმდეგ.\n\n"
            "🎮 თამაშები:\n"
            "• Poker\n"
            "• Emperor’s 21\n"
            "• Joker\n\n"
            "ეს არის სავარჯიშო თამაში ფულადი ფსონების, თანხის გამოტანისა და აზარტული პრიზების გარეშე."
        ),
        "play": "🎮 თამაში",
        "trial": "🎁 უფასო 5 წუთი",
        "access": "⏳ ჩემი წვდომა",
        "language": "🌍 ენა",
        "admin": "👑 ადმინი",
        "buy": "⭐ წვდომის ყიდვა",
        "code": "🎟 კოდის შეყვანა",
        "stats": "📊 სტატისტიკა",
        "trial_ok": "✅ უფასო წვდომა გაიხსნა 5 წუთით.",
        "admin_ok": "👑 ადმინ წვდომა გააქტიურდა.",
        "admin_no": "ადმინ წვდომა მხოლოდ მფლობელისთვისაა.",
        "admin_status": "👑 შენ გაქვს შეუზღუდავი ადმინ წვდომა.",
        "left": "⏳ დარჩენილია დაახლოებით {minutes} წუთი.",
        "expired": "⛔ წვდომა დასრულდა.",
        "choose_lang": "აირჩიე ენა:",
        "lang_ok": "✅ ენა შეიცვალა.",
        "fallback": "მენიუს გასახსნელად დააჭირე /start.",
        "send_code": "გამოაგზავნე კოდი ფორმატით: LS-XXXXXX",
        "bad_code": "❌ კოდი ვერ მოიძებნა ან უკვე გამოყენებულია.",
        "good_code": "✅ კოდი მიღებულია. წვდომა გაიხსნა.",
    },
}


PRODUCTS = {
    "buy_1h": {"title": "1 Hour Access", "stars": 50, "minutes": 60},
    "buy_24h": {"title": "24 Hours Access", "stars": 150, "minutes": 1440},
    "buy_7d": {"title": "7 Days Access", "stars": 300, "minutes": 10080},
}


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                lang TEXT DEFAULT 'ru',
                access_until INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                created_at INTEGER,
                last_seen INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                payload TEXT,
                stars INTEGER,
                minutes INTEGER,
                telegram_payment_charge_id TEXT,
                created_at INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS codes (
                code TEXT PRIMARY KEY,
                minutes INTEGER,
                used_by INTEGER,
                used_at INTEGER,
                created_at INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event TEXT,
                created_at INTEGER
            )
        """)


def now():
    return int(time.time())


def ensure_user(user):
    user_id = user.id
    username = user.username or ""

    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row is None:
            is_admin = 1 if username == ADMIN_USERNAME else 0
            conn.execute(
                "INSERT INTO users (user_id, username, lang, access_until, is_admin, created_at, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, username, "ru", 0, is_admin, now(), now())
            )
        else:
            if username == ADMIN_USERNAME:
                conn.execute(
                    "UPDATE users SET username=?, is_admin=1, last_seen=? WHERE user_id=?",
                    (username, now(), user_id)
                )
            else:
                conn.execute(
                    "UPDATE users SET username=?, last_seen=? WHERE user_id=?",
                    (username, now(), user_id)
                )


def log_event(user_id, event):
    with db() as conn:
        conn.execute(
            "INSERT INTO events (user_id, event, created_at) VALUES (?, ?, ?)",
            (user_id, event, now())
        )


def get_user(user_id):
    with db() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def get_lang(user_id):
    row = get_user(user_id)
    if row and row["lang"] in TEXTS:
        return row["lang"]
    return "ru"


def t(user_id, key):
    return TEXTS[get_lang(user_id)][key]


def set_lang(user_id, lang):
    with db() as conn:
        conn.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))


def is_admin_user(user_id):
    row = get_user(user_id)
    return bool(row and row["is_admin"] == 1)


def add_admin(user_id):
    with db() as conn:
        conn.execute("UPDATE users SET is_admin=1 WHERE user_id=?", (user_id,))


def give_access(user_id, minutes):
    row = get_user(user_id)
    current_until = row["access_until"] if row else 0
    base = max(current_until, now())
    new_until = base + minutes * 60

    with db() as conn:
        conn.execute(
            "UPDATE users SET access_until=? WHERE user_id=?",
            (new_until, user_id)
        )


def has_access(user_id):
    row = get_user(user_id)
    if not row:
        return False
    if row["is_admin"] == 1:
        return True
    return row["access_until"] > now()


def generate_code(minutes=1440):
    code = "LS-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    with db() as conn:
        conn.execute(
            "INSERT INTO codes (code, minutes, used_by, used_at, created_at) VALUES (?, ?, NULL, NULL, ?)",
            (code, minutes, now())
        )
    return code


def use_code(user_id, code):
    code = code.strip().upper()
    with db() as conn:
        row = conn.execute("SELECT * FROM codes WHERE code=?", (code,)).fetchone()
        if row is None or row["used_by"] is not None:
            return False, 0

        conn.execute(
            "UPDATE codes SET used_by=?, used_at=? WHERE code=?",
            (user_id, now(), code)
        )

    give_access(user_id, row["minutes"])
    return True, row["minutes"]


def game_url(user_id):
    return f"{WEBAPP_URL}?user={user_id}&lang={get_lang(user_id)}"


def main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=1)

    if has_access(user_id):
        markup.add(
            InlineKeyboardButton(
                t(user_id, "play"),
                web_app=WebAppInfo(url=game_url(user_id))
            )
        )
    else:
        markup.add(InlineKeyboardButton(t(user_id, "trial"), callback_data="trial"))

    markup.add(
        InlineKeyboardButton(t(user_id, "buy"), callback_data="buy_menu"),
        InlineKeyboardButton(t(user_id, "access"), callback_data="my_access"),
        InlineKeyboardButton(t(user_id, "code"), callback_data="enter_code"),
        InlineKeyboardButton(t(user_id, "language"), callback_data="language"),
        InlineKeyboardButton(t(user_id, "admin"), callback_data="admin_access"),
    )

    if is_admin_user(user_id):
        markup.add(InlineKeyboardButton(t(user_id, "stats"), callback_data="stats"))
        markup.add(InlineKeyboardButton("🎟 Generate 24h Code", callback_data="gen_code_24h"))
        markup.add(InlineKeyboardButton("🎟 Generate 7d Code", callback_data="gen_code_7d"))

    return markup


def language_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇬🇪 ქართული", callback_data="lang_ka"),
    )
    return markup


def buy_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⭐ 1 Hour — 50 Stars", callback_data="buy_1h"),
        InlineKeyboardButton("⭐ 24 Hours — 150 Stars", callback_data="buy_24h"),
        InlineKeyboardButton("⭐ 7 Days — 300 Stars", callback_data="buy_7d"),
    )
    return markup


@app.route("/", methods=["GET", "HEAD"])
def home():
    return "OK", 200


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@bot.message_handler(commands=["start"])
def start(message):
    ensure_user(message.from_user)
    user_id = message.from_user.id

    if message.from_user.username == ADMIN_USERNAME:
        add_admin(user_id)

    log_event(user_id, "start")

    bot.send_message(
        message.chat.id,
        f"{t(user_id, 'title')}\n\n{t(user_id, 'description')}",
        reply_markup=main_menu(user_id)
    )


@bot.message_handler(commands=["stats"])
def stats_command(message):
    ensure_user(message.from_user)
    user_id = message.from_user.id

    if not is_admin_user(user_id):
        return

    bot.send_message(message.chat.id, get_stats_text())


@bot.message_handler(commands=["gen24"])
def gen24_command(message):
    ensure_user(message.from_user)
    user_id = message.from_user.id

    if not is_admin_user(user_id):
        return

    code = generate_code(1440)
    bot.send_message(message.chat.id, f"🎟 Code 24h:\n{code}")


@bot.message_handler(commands=["gen7"])
def gen7_command(message):
    ensure_user(message.from_user)
    user_id = message.from_user.id

    if not is_admin_user(user_id):
        return

    code = generate_code(10080)
    bot.send_message(message.chat.id, f"🎟 Code 7d:\n{code}")


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    ensure_user(call.from_user)
    user_id = call.from_user.id

    if call.from_user.username == ADMIN_USERNAME:
        add_admin(user_id)

    if call.data == "trial":
        give_access(user_id, 5)
        log_event(user_id, "trial")
        bot.answer_callback_query(call.id, "OK")
        bot.edit_message_text(
            t(user_id, "trial_ok"),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu(user_id)
        )

    elif call.data == "my_access":
        row = get_user(user_id)

        if row["is_admin"] == 1:
            text = t(user_id, "admin_status")
        else:
            left = row["access_until"] - now()
            if left > 0:
                minutes = max(1, left // 60)
                text = t(user_id, "left").format(minutes=minutes)
            else:
                text = t(user_id, "expired")

        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, reply_markup=main_menu(user_id))

    elif call.data == "language":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, t(user_id, "choose_lang"), reply_markup=language_menu())

    elif call.data.startswith("lang_"):
        lang = call.data.replace("lang_", "")
        if lang in TEXTS:
            set_lang(user_id, lang)

        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            t(user_id, "lang_ok"),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu(user_id)
        )

    elif call.data == "admin_access":
        if call.from_user.username == ADMIN_USERNAME:
            add_admin(user_id)
            bot.answer_callback_query(call.id, "OK")
            bot.send_message(call.message.chat.id, t(user_id, "admin_ok"), reply_markup=main_menu(user_id))
        else:
            bot.answer_callback_query(call.id, t(user_id, "admin_no"))

    elif call.data == "buy_menu":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "⭐ Telegram Stars:", reply_markup=buy_menu(user_id))

    elif call.data in PRODUCTS:
        product = PRODUCTS[call.data]
        payload = call.data

        prices = [LabeledPrice(label=product["title"], amount=product["stars"])]

        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=product["title"],
            description=f"Access for {product['minutes']} minutes",
            invoice_payload=payload,
            provider_token="",
            currency="XTR",
            prices=prices
        )

        bot.answer_callback_query(call.id)

    elif call.data == "enter_code":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, t(user_id, "send_code"))

    elif call.data == "stats":
        bot.answer_callback_query(call.id)
        if is_admin_user(user_id):
            bot.send_message(call.message.chat.id, get_stats_text())

    elif call.data == "gen_code_24h":
        bot.answer_callback_query(call.id)
        if is_admin_user(user_id):
            code = generate_code(1440)
            bot.send_message(call.message.chat.id, f"🎟 Code 24h:\n{code}")

    elif call.data == "gen_code_7d":
        bot.answer_callback_query(call.id)
        if is_admin_user(user_id):
            code = generate_code(10080)
            bot.send_message(call.message.chat.id, f"🎟 Code 7d:\n{code}")


@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def successful_payment(message):
    ensure_user(message.from_user)
    user_id = message.from_user.id

    payload = message.successful_payment.invoice_payload
    product = PRODUCTS.get(payload)

    if not product:
        bot.send_message(message.chat.id, "Payment received, but product not found.")
        return

    give_access(user_id, product["minutes"])

    with db() as conn:
        conn.execute(
            """
            INSERT INTO payments 
            (user_id, payload, stars, minutes, telegram_payment_charge_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                payload,
                product["stars"],
                product["minutes"],
                message.successful_payment.telegram_payment_charge_id,
                now()
            )
        )

    log_event(user_id, f"paid_{payload}")

    bot.send_message(
        message.chat.id,
        f"✅ Payment received: {product['title']}\n\nAccess activated.",
        reply_markup=main_menu(user_id)
    )


@bot.message_handler(func=lambda message: message.text and message.text.upper().startswith("LS-"))
def code_handler(message):
    ensure_user(message.from_user)
    user_id = message.from_user.id

    ok, minutes = use_code(user_id, message.text)

    if ok:
        log_event(user_id, "code_used")
        bot.send_message(message.chat.id, t(user_id, "good_code"), reply_markup=main_menu(user_id))
    else:
        bot.send_message(message.chat.id, t(user_id, "bad_code"), reply_markup=main_menu(user_id))


@bot.message_handler(func=lambda message: True)
def fallback(message):
    ensure_user(message.from_user)
    user_id = message.from_user.id

    bot.send_message(
        message.chat.id,
        t(user_id, "fallback"),
        reply_markup=main_menu(user_id)
    )


def get_stats_text():
    with db() as conn:
        users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        admins = conn.execute("SELECT COUNT(*) AS c FROM users WHERE is_admin=1").fetchone()["c"]
        active = conn.execute("SELECT COUNT(*) AS c FROM users WHERE access_until > ?", (now(),)).fetchone()["c"]
        payments = conn.execute("SELECT COUNT(*) AS c FROM payments").fetchone()["c"]
        stars = conn.execute("SELECT COALESCE(SUM(stars), 0) AS s FROM payments").fetchone()["s"]
        unused_codes = conn.execute("SELECT COUNT(*) AS c FROM codes WHERE used_by IS NULL").fetchone()["c"]
        used_codes = conn.execute("SELECT COUNT(*) AS c FROM codes WHERE used_by IS NOT NULL").fetchone()["c"]

    return (
        "📊 Bot Stats\n\n"
        f"👥 Users: {users}\n"
        f"👑 Admins: {admins}\n"
        f"✅ Active access: {active}\n"
        f"💳 Payments: {payments}\n"
        f"⭐ Stars received: {stars}\n"
        f"🎟 Unused codes: {unused_codes}\n"
        f"🎟 Used codes: {used_codes}"
    )


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
