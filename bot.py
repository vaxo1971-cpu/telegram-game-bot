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
        "paid": "✅ Оплата прошла! Доступ открыт.",
        "access": "⏳ Мой доступ",
        "no_access": "⛔ Активного доступа нет",
        "access_until": "✅ Доступ активен до:",
        "buy_title": "Выберите тариф:",
        "p1": "⏳ 1 час — 50 ⭐",
        "p24": "🌙 24 часа — 150 ⭐",
        "p48": "🔥 48 часов — 300 ⭐",
        "invoice_title": "PRO доступ",
        "invoice_desc": "Доступ к игре",
    },
    "en": {
        "start": "🃏 Ancient Card Games",
        "play": "🎮 Play",
        "buy": "💰 Buy access",
        "lang": "🌍 Language",
        "choose_lang": "Choose language:",
        "ok": "✅ Done",
        "paid": "✅ Payment successful! Access granted.",
        "access": "⏳ My access",
        "no_access": "⛔ No active access",
        "access_until": "✅ Access active until:",
        "buy_title": "Choose plan:",
        "p1": "⏳ 1 hour — 50 ⭐",
        "p24": "🌙 24 hours — 150 ⭐",
        "p48": "🔥 48 hours — 300 ⭐",
        "invoice_title": "PRO access",
        "invoice_desc": "Game access",
    },
    "ka": {
        "start": "🃏 Ancient Card Games",
        "play": "🎮 თამაში",
        "buy": "💰 წვდომის ყიდვა",
        "lang": "🌍 ენა",
        "choose_lang": "აირჩიეთ ენა:",
        "ok": "✅ მზადაა",
        "paid": "✅ გადახდა წარმატებულია! წვდომა გახსნილია.",
        "access": "⏳ ჩემი წვდომა",
        "no_access": "⛔ აქტიური წვდომა არ არის",
        "access_until": "✅ წვდომა აქტიურია:",
        "buy_title": "აირჩიეთ პაკეტი:",
        "p1": "⏳ 1 საათი — 50 ⭐",
        "p24": "🌙 24 საათი — 150 ⭐",
        "p48": "🔥 48 საათი — 300 ⭐",
        "invoice_title": "PRO წვდომა",
        "invoice_desc": "თამაშზე წვდომა",
    },
}


def load_json(file):
    if not file.exists():
        return {}
    try:
        return json.loads(file.read_text())
    except Exception:
        return {}


def save_json(file, data):
    file.write_text(json.dumps(data))


def get_lang(user_id):
    data = load_json(LANG_FILE)
    return data.get(str(user_id), "ru")


def set_lang(user_id, lang):
    data = load_json(LANG_FILE)
    data[str(user_id)] = lang
    save_json(LANG_FILE, data)


def give_access(user_id, hours):
    users = load_json(DATA_FILE)
    uid = str(user_id)
    now = int(time.time())

    current = users.get(uid, {}).get("until", now)
    if current < now:
        current = now

    users[uid] = {"until": current + hours * 3600}
    save_json(DATA_FILE, users)


def get_access_until(user_id):
    users = load_json(DATA_FILE)
    return users.get(str(user_id), {}).get("until", 0)


def main_menu(user_id):
    lang = get_lang(user_id)
    t = TEXT[lang]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(t["play"], url=f"{WEBAPP_URL}/?user={user_id}"))
    kb.add(types.InlineKeyboardButton(t["buy"], callback_data="buy"))
    kb.add(types.InlineKeyboardButton(t["access"], callback_data="access"))
    kb.add(types.InlineKeyboardButton(t["lang"], callback_data="lang"))
    return kb


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    bot.send_message(user_id, TEXT[get_lang(user_id)]["start"], reply_markup=main_menu(user_id))


@bot.callback_query_handler(func=lambda c: c.data == "lang")
def lang_menu(call):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="set_en"),
        types.InlineKeyboardButton("🇬🇪 ქართული", callback_data="set_ka"),
    )
    bot.send_message(call.message.chat.id, TEXT[get_lang(call.message.chat.id)]["choose_lang"], reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("set_"))
def set_lang_cb(call):
    lang = call.data.split("_")[1]
    set_lang(call.message.chat.id, lang)
    bot.send_message(call.message.chat.id, TEXT[lang]["ok"], reply_markup=main_menu(call.message.chat.id))


@bot.callback_query_handler(func=lambda c: c.data == "access")
def access_cb(call):
    user_id = call.message.chat.id
    lang = get_lang(user_id)
    t = TEXT[lang]

    until = get_access_until(user_id)
    if until > int(time.time()):
        msg = f"{t['access_until']} {time.strftime('%Y-%m-%d %H:%M', time.localtime(until))}"
    else:
        msg = t["no_access"]

    bot.send_message(user_id, msg, reply_markup=main_menu(user_id))


@bot.callback_query_handler(func=lambda c: c.data == "buy")
def buy_menu(call):
    lang = get_lang(call.message.chat.id)
    t = TEXT[lang]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(t["p1"], callback_data="pay_1h"))
    kb.add(types.InlineKeyboardButton(t["p24"], callback_data="pay_24h"))
    kb.add(types.InlineKeyboardButton(t["p48"], callback_data="pay_48h"))

    bot.send_message(call.message.chat.id, t["buy_title"], reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_"))
def send_invoice(call):
    plan_id = call.data.replace("pay_", "")
    plan = PLANS.get(plan_id)

    if not plan:
        return

    lang = get_lang(call.message.chat.id)
    t = TEXT[lang]

    prices = [types.LabeledPrice(label=f"{plan['hours']}h", amount=plan["stars"])]

    bot.send_invoice(
        call.message.chat.id,
        title=t["invoice_title"],
        description=f"{t['invoice_desc']} — {plan['hours']}h",
        invoice_payload=f"access_{plan_id}",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter=f"buy_{plan_id}",
    )


@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def payment(message):
    user_id = message.chat.id
    payload = message.successful_payment.invoice_payload

    if payload == "access_1h":
        give_access(user_id, 1)
    elif payload == "access_24h":
        give_access(user_id, 24)
    elif payload == "access_48h":
        give_access(user_id, 48)
    else:
        give_access(user_id, 24)

    bot.send_message(user_id, TEXT[get_lang(user_id)]["paid"], reply_markup=main_menu(user_id))


@app.route("/", methods=["GET"])
def home():
    return "OK"


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/check_access", methods=["GET"])
def check_access():
    user_id = request.args.get("user")

    if not user_id:
        return jsonify({"access": False, "until": 0})

    until = get_access_until(user_id)

    return jsonify({
        "access": until > int(time.time()),
        "until": until
    })


@app.before_request
def setup_webhook_once():
    if not getattr(app, "webhook_set", False):
        bot.remove_webhook()
        bot.set_webhook(url=f"{SERVICE_URL}/{TOKEN}")
        app.webhook_set = True
