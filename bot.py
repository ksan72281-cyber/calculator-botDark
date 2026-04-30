import telebot
import math
import os
from flask import Flask
import threading
from telebot.types import InlineQueryResultArticle, InputTextMessageContent

TOKEN = '8787754774:AAEOPMrAfMhHFviaEHWFUSE_2P6RIVlmUxM'
bot = telebot.TeleBot(TOKEN)

allowed_math_functions = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
allowed_math_functions['abs'] = abs
allowed_math_functions['round'] = round

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
        "🧮 Calculator Bot မှ ကြိုဆိုပါသည်!\n\n"
        "တွက်ချက်မှုများ တိုက်ရိုက်ရိုက်ပို့ပါ:\n\n"
        "➕ ပေါင်း: 3529000+2699600+956800\n"
        "➖ နုတ်: 10000-2500\n"
        "✖️ မြှောက်: 500*12\n"
        "➗ စား: 9000/3\n"
        "🔢 ရှုပ်ထွေးသော: (100+200)*3-50/2"
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message,
        "📖 အသုံးပြုနည်း\n\n"
        "+ ပေါင်း\n"
        "- နုတ်\n"
        "* မြှောက်\n"
        "/ စား\n"
        "^ အမြင့်\n\n"
        "ဥပမာ:\n"
        "100000+200000+300000 = 600,000\n"
        "1000000-250000 = 750,000\n"
        "2500*4 = 10,000\n"
        "9000/3 = 3,000"
    )

@bot.message_handler(func=lambda message: True)
def calculate(message):
    try:
        text_to_calc = message.text.strip()
        text_to_calc = text_to_calc.replace('^', '**')
        text_to_calc = text_to_calc.replace('x', '*')
        text_to_calc = text_to_calc.replace('×', '*')
        text_to_calc = text_to_calc.replace(',', '')

        result = eval(text_to_calc, {"__builtins__": None}, allowed_math_functions)

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        if isinstance(result, int):
            formatted_result = f"{result:,}"
        else:
            formatted_result = f"{result:,.4f}".rstrip('0').rstrip('.')

        bot.reply_to(message, f"{message.text} = {formatted_result}")

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
    return "Bot is running 24/7!"

def run_bot():
    print("Calculator Bot စတင်အလုပ်လုပ်နေပါပြီ...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    thread = threading.Thread(target=run_bot)
    thread.daemon = True
    thread.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
