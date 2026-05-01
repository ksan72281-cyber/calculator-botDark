import telebot
import math
import os
import re
from flask import Flask
import threading
from telebot.types import InlineQueryResultArticle, InputTextMessageContent

TOKEN = '8743380551:AAFRFCymI2vewEJ4H66WulrJcmlTl-Jscaw'
bot = telebot.TeleBot(TOKEN)

allowed_math_functions = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
allowed_math_functions['abs'] = abs
allowed_math_functions['round'] = round

# ✅ FIX: chat_id နဲ့ track လုပ်မယ် (group တစ်ခုလုံး balance share လုပ်နိုင်အောင်)
chat_totals = {}
chat_histories = {}

def get_tracking_id(message):
    """Group chat → chat_id သုံး | Private → user_id သုံး"""
    if message.chat.type == 'private':
        return message.from_user.id
    return message.chat.id

def get_total(tracking_id):
    return chat_totals.get(tracking_id, 0)

def add_amount(tracking_id, amount):
    if tracking_id not in chat_totals:
        chat_totals[tracking_id] = 0
    chat_totals[tracking_id] += amount
    return chat_totals[tracking_id]

def add_history(tracking_id, amount, total, username=""):
    if tracking_id not in chat_histories:
        chat_histories[tracking_id] = []
    sign = "+" if amount > 0 else ""
    name_str = f"[{username}] " if username else ""
    chat_histories[tracking_id].append(
        f"{name_str}{sign}{amount:,} Ks → စုစုပေါင်း: {total:,} Ks"
    )
    if len(chat_histories[tracking_id]) > 10:
        chat_histories[tracking_id] = chat_histories[tracking_id][-10:]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
        "🧮 *DarkCalculator Bot*\n\n"
        "*တွက်ချက်မှု:*\n"
        "`100+200*3` → တွက်ချက်ပေးမယ်\n\n"
        "*စုစုပေါင်း:*\n"
        "`+5000` → 5,000 ထည့်မယ်\n"
        "`-3000` → 3,000 နုတ်မယ်\n"
        "/total → စုစုပေါင်းကြည့်\n"
        "/edit → ပမာဏပြင်\n"
        "/reset → သုညပြန်သတ်\n"
        "/history → မှတ်တမ်းကြည့်",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['total'])
def show_total(message):
    tracking_id = get_tracking_id(message)
    total = get_total(tracking_id)
    bot.reply_to(message,
        f"💰 *စုစုပေါင်း:*\n`{total:,} Ks`",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['reset'])
def reset_total(message):
    tracking_id = get_tracking_id(message)
    chat_totals[tracking_id] = 0
    chat_histories[tracking_id] = []
    bot.reply_to(message, "✅ Reset လုပ်ပြီး။ စုစုပေါင်း = 0 Ks")

@bot.message_handler(commands=['edit'])
def edit_total(message):
    bot.reply_to(message,
        "✏️ *ပမာဏပြင်နည်း:*\n\n"
        "တိုက်ရိုက် ပမာဏ ထည့်ပါ:\n"
        "`=50000` → စုစုပေါင်းကို 50,000 အဖြစ် သတ်မှတ်မယ်",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['history'])
def show_history(message):
    tracking_id = get_tracking_id(message)
    history = chat_histories.get(tracking_id, [])
    if not history:
        bot.reply_to(message, "📋 မှတ်တမ်း မရှိသေးပါ")
        return
    text = "📋 *နောက်ဆုံး မှတ်တမ်းများ:*\n\n"
    for i, h in enumerate(reversed(history), 1):
        text += f"{i}. {h}\n"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    tracking_id = get_tracking_id(message)
    text = message.text.strip()
    username = message.from_user.first_name or message.from_user.username or ""

    # Reset (text အနေနဲ့ ရေးလျှင်လည်း အလုပ်လုပ်မယ်)
    if text.lower() == 'reset':
        chat_totals[tracking_id] = 0
        chat_histories[tracking_id] = []
        bot.reply_to(message, "✅ Reset လုပ်ပြီး။ စုစုပေါင်း = 0 Ks")
        return

    # =50000 → total ကို တိုက်ရိုက် သတ်မှတ်
    if re.match(r'^=\d+(\.\d+)?$', text.replace(',', '')):
        try:
            amount = float(text[1:].replace(',', ''))
            if amount.is_integer():
                amount = int(amount)
            chat_totals[tracking_id] = amount
            bot.reply_to(message,
                f"✏️ *စုစုပေါင်း ပြင်ပြီး:*\n`{amount:,} Ks`",
                parse_mode='Markdown'
            )
        except:
            bot.reply_to(message, "❌ ဂဏန်း မှားနေသည်")
        return

    # +5000 သို့မဟုတ် -3000 → group shared total ထဲ ထည့်/နုတ်
    match = re.match(r'^([+\-])(\d+(\.\d+)?)$', text.replace(',', ''))
    if match:
        sign = match.group(1)
        amount = float(match.group(2))
        if amount.is_integer():
            amount = int(amount)

        if sign == '+':
            total = add_amount(tracking_id, amount)
            add_history(tracking_id, amount, total, username)
            bot.reply_to(message,
                f"✅ *{amount:,} Ks ထည့်ပြီး*\n"
                f"💰 စုစုပေါင်း: `{total:,} Ks`",
                parse_mode='Markdown'
            )
        else:
            total = add_amount(tracking_id, -amount)
            add_history(tracking_id, -amount, total, username)
            bot.reply_to(message,
                f"✅ *{amount:,} Ks နုတ်ပြီး*\n"
                f"💰 စုစုပေါင်း: `{total:,} Ks`",
                parse_mode='Markdown'
            )
        return

    # သာမန် တွက်ချက်မှု
    try:
        text_to_calc = text.replace('^', '**').replace('x', '*').replace('×', '*').replace(',', '')

        if not re.match(r'^[\d+\-*/().\s]+$', text_to_calc):
            if message.chat.type == 'private':
                bot.reply_to(message,
                    "❓ မသိသောအမိန့်\n\n"
                    "/start နှိပ်ပြီး အသုံးပြုနည်း ကြည့်ပါ"
                )
            return

        result = eval(text_to_calc, {"__builtins__": None}, allowed_math_functions)

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        if isinstance(result, int):
            formatted_result = f"{result:,}"
        else:
            formatted_result = f"{result:,.4f}".rstrip('0').rstrip('.')

        bot.reply_to(message, f"`{text} = {formatted_result}`", parse_mode='Markdown')

    except ZeroDivisionError:
        if message.chat.type == 'private':
            bot.reply_to(message, "❌ သုညနဲ့ စားလို့မရပါ")
    except Exception:
        if message.chat.type == 'private':
            bot.reply_to(message, "For now I don't know how to calculate such things 😔")

@bot.inline_handler(lambda query: len(query.query) > 0)
def query_text(inline_query):
    try:
        query_str = inline_query.query.strip()
        calc_str = query_str.replace('^', '**').replace('x', '*').replace('×', '*').replace(',', '')
        result = eval(calc_str, {"__builtins__": None}, allowed_math_functions)

        if isinstance(result, float) and result.is_integer():
            result = int(result)
        if isinstance(result, int):
            formatted_result = f"{result:,}"
        else:
            formatted_result = f"{result:,.4f}".rstrip('0').rstrip('.')

        r = InlineQueryResultArticle(
            id='1',
            title=f"= {formatted_result}",
            description=f"{query_str} = {formatted_result}",
            input_message_content=InputTextMessageContent(f"{query_str} = {formatted_result}")
        )
        bot.answer_inline_query(inline_query.id, [r])
    except Exception:
        pass

app = Flask(__name__)

@app.route('/')
def home():
    return "DarkCalculator Bot is running 24/7!"

def run_bot():
    print("DarkCalculator Bot စတင်အလုပ်လုပ်နေပါပြီ...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    thread = threading.Thread(target=run_bot)
    thread.daemon = True
    thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
