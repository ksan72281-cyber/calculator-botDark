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

# User တိုင်းအတွက် total သိမ်းမယ်
user_totals = {}

def get_total(user_id):
    return user_totals.get(user_id, 0)

def add_amount(user_id, amount):
    if user_id not in user_totals:
        user_totals[user_id] = 0
    user_totals[user_id] += amount
    return user_totals[user_id]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
        "🧮 *Kiwii Calculator Bot*\n\n"
        "*တွက်ချက်မှု:*\n"
        "`100+200*3` → တွက်ချက်ပေးမယ်\n\n"
        "*KBZPay စုစုပေါင်း:*\n"
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
    user_id = message.from_user.id
    total = get_total(user_id)
    bot.reply_to(message,
        f"💰 *စုစုပေါင်း:*\n`{total:,} Ks`",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['reset'])
def reset_total(message):
    user_id = message.from_user.id
    user_totals[user_id] = 0
    user_histories[user_id] = []
    bot.reply_to(message, "✅ Reset လုပ်ပြီး။ စုစုပေါင်း = 0 Ks")

@bot.message_handler(commands=['edit'])
def edit_total(message):
    bot.reply_to(message,
        "✏️ *ပမာဏပြင်နည်း:*\n\n"
        "တိုက်ရိုက် ပမာဏ ထည့်ပါ:\n"
        "`=50000` → စုစုပေါင်းကို 50,000 အဖြစ် သတ်မှတ်မယ်",
        parse_mode='Markdown'
    )

# History သိမ်းမယ်
user_histories = {}

def add_history(user_id, amount, total):
    if user_id not in user_histories:
        user_histories[user_id] = []
    sign = "+" if amount > 0 else ""
    user_histories[user_id].append(f"{sign}{amount:,} Ks → စုစုပေါင်း: {total:,} Ks")
    # နောက်ဆုံး 10 ခုသာ သိမ်း
    if len(user_histories[user_id]) > 10:
        user_histories[user_id] = user_histories[user_id][-10:]

@bot.message_handler(commands=['history'])
def show_history(message):
    user_id = message.from_user.id
    history = user_histories.get(user_id, [])
    if not history:
        bot.reply_to(message, "📋 မှတ်တမ်း မရှိသေးပါ")
        return
    text = "📋 *နောက်ဆုံး မှတ်တမ်းများ:*\n\n"
    for i, h in enumerate(reversed(history), 1):
        text += f"{i}. {h}\n"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # =50000 → total ကို တိုက်ရိုက် သတ်မှတ်
    if re.match(r'^=\d+(\.\d+)?$', text):
        try:
            amount = float(text[1:].replace(',', ''))
            if amount.is_integer():
                amount = int(amount)
            user_totals[user_id] = amount
            bot.reply_to(message,
                f"✏️ *စုစုပေါင်း ပြင်ပြီး:*\n`{amount:,} Ks`",
                parse_mode='Markdown'
            )
        except:
            bot.reply_to(message, "❌ ဂဏန်း မှားနေသည်")
        return

    # +5000 သို့မဟုတ် -3000 → total ထဲ ထည့်/နုတ်
    match = re.match(r'^([+\-])(\d+(\.\d+)?)$', text.replace(',', ''))
    if match:
        sign = match.group(1)
        amount = float(match.group(2))
        if amount.is_integer():
            amount = int(amount)

        if sign == '+':
            total = add_amount(user_id, amount)
            add_history(user_id, amount, total)
            bot.reply_to(message,
                f"✅ *{amount:,} Ks ထည့်ပြီး*\n"
                f"💰 စုစုပေါင်း: `{total:,} Ks`",
                parse_mode='Markdown'
            )
        else:
            total = add_amount(user_id, -amount)
            add_history(user_id, -amount, total)
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
        else:
            pass

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
    return "Kiwii Calculator Bot is running 24/7!"

def run_bot():
    print("Kiwii Calculator Bot စတင်အလုပ်လုပ်နေပါပြီ...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    thread = threading.Thread(target=run_bot)
    thread.daemon = True
    thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
