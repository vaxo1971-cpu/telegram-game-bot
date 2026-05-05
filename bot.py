import os
import time
import json
from pathlib import Path

from flask import Flask, request, jsonify
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
SERVICE_URL = os.getenv("SERVICE_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FILE = Path("users.json")
LANG_FILE = Path("lang.json")

PLANS = {
    "1h": {"hours": 1, "stars": 50},
    "24h": {"hours": 24, "stars": 150},
    "48h": {"hours": 48, "stars": 300},
}

TEXT = {
    "ru": {
        "start": "🃏 Ancient Card Games",
        "play": "🎮 Играть",
        "buy": "💰 Купить доступ",
        "lang": "🌍 Язык",
        "choose_lang": "Выберите язык:",
        "ok": "✅ Готово",
        "paid": "✅ Оплата прошла! Доступ открыт",
        "access": "⏳ Мой доступ",
        "no_access": "⛔ Нет доступа",
        "access_until": "✅ Доступ до:",
        "plans": "Выберите тариф:"
    },
    "en": {
        "start": "🃏 Ancient Card Games",
        "play": "🎮 Play",
        "buy": "💰 Buy access",
        "lang": "🌍 Language",
        "choose_lang": "Choose language:",
        "ok": "✅ Done",
        "paid": "✅ Payment successful!",
        "access": "⏳ My access",
        "no_access": "⛔ No access",
        "access_until": "✅ Access until:",
        "plans": "Choose plan:"
    },
    "ka": {
        "start": "🃏 Ancient Card Games",
        "play": "🎮 თამაში",
        "buy": "💰 წვდომის ყიდვა",
        "lang": "🌍 ენა",
        "choose_lang": "აირჩიეთ ენა:",
        "ok": "✅ მზადაა",
        "paid": "✅ გადახდა წარმატებულია",
        "access": "⏳ წვდომა",
        "no_access": "⛔ წვდომა არ არის",
        "access_until": "✅ წვდომა:",
        "plans": "აირჩიეთ პაკეტი:"
    }
}

# ===== JSON =====

def load_json(file):
    if not file.exists():
        return {}
    try:
        return json.loads(file.read_text())
    except:
        return {}

def save_json(file, data):
    file.write_text(json.dumps(data))

# ===== ACCESS =====

def give_access(user_id, hours):
    users = load_json(DATA_FILE)
    uid = str(user_id)

    now = int(time.time())
    current = users.get(uid, {}).get("until", now)

    if current < now:
        current = now

    users[uid] = {"until": current + hours * 3600}
    save_json(DATA_FILE, users)

def get_access(user_id):
    users = load_json(DATA_FILE)
    return users.get(str(user_id), {}).get("until", 0)

# ===== LANG =====

def get_lang(user_id):
    data = load_json(LANG_FILE)
    return data.get(str(user_id), "ru")

def set_lang(user_id, lang):
    data = load_json(LANG_FILE)
    data[str(user_id)] = lang
    save_json(LANG_FILE, data)

# ===== MENU =====

def menu(user_id):
    t = TEXT[get_lang(user_id)]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(t["play"], url=f"{WEBAPP_URL}/?user={user_id}"))
    kb.add(types.InlineKeyboardButton(t["buy"], callback_data="buy"))
    kb.add(types.InlineKeyboardButton(t["access"], callback_data="access"))
    kb.add(types.InlineKeyboardButton(t["lang"], callback_data="lang"))
    return kb

# ===== BOT =====

@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, TEXT[get_lang(msg.chat.id)]["start"], reply_markup=menu(msg.chat.id))

@bot.callback_query_handler(func=lambda c: c.data == "lang")
def lang(call):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🇷🇺", callback_data="set_ru"),
        types.InlineKeyboardButton("🇬🇧", callback_data="set_en"),
        types.InlineKeyboardButton("🇬🇪", callback_data="set_ka")
    )
    bot.send_message(call.message.chat.id, "Choose language", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("set_"))
def setlang(call):
    l = call.data.split("_")[1]
    set_lang(call.message.chat.id, l)
    bot.send_message(call.message.chat.id, TEXT[l]["ok"], reply_markup=menu(call.message.chat.id))

@bot.callback_query_handler(func=lambda c: c.data == "access")
def access(call):
    uid = call.message.chat.id
    t = TEXT[get_lang(uid)]

    until = get_access(uid)

    if until > int(time.time()):
        msg = f"{t['access_until']} {time.strftime('%Y-%m-%d %H:%M', time.localtime(until))}"
    else:
        msg = t["no_access"]

    bot.send_message(uid, msg, reply_markup=menu(uid))

@bot.callback_query_handler(func=lambda c: c.data == "buy")
def buy(call):
    t = TEXT[get_lang(call.message.chat.id)]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("1h ⭐50", callback_data="pay_1h"))
    kb.add(types.InlineKeyboardButton("24h ⭐150", callback_data="pay_24h"))
    kb.add(types.InlineKeyboardButton("48h ⭐300", callback_data="pay_48h"))

    bot.send_message(call.message.chat.id, t["plans"], reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_"))
def pay(call):
    plan = call.data.split("_")[1]
    p = PLANS[plan]

    bot.send_invoice(
        call.message.chat.id,
        title="PRO",
        description=f"{p['hours']}h access",
        invoice_payload=plan,
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice(label="Access", amount=p["stars"])],
        start_parameter="buy"
    )

@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=["successful_payment"])
def paid(msg):
    plan = msg.successful_payment.invoice_payload
    give_access(msg.chat.id, PLANS[plan]["hours"])

    bot.send_message(msg.chat.id, TEXT[get_lang(msg.chat.id)]["paid"], reply_markup=menu(msg.chat.id))

# ===== WEB =====

@app.route("/")
def home():
    return "OK"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK"

@app.route("/check_access")
def check_access():
    uid = request.args.get("user")
    if not uid:
        return jsonify({"access": False})

    until = get_access(uid)

    return jsonify({
        "access": until > int(time.time()),
        "until": until
    })

# ===== START =====

with app.app_context():
    bot.remove_webhook()
    bot.set_webhook(url=f"{SERVICE_URL}/{TOKEN}")
