import telebot
import math
import os
from flask import Flask
import threading
from telebot.types import InlineQueryResultArticle, InputTextMessageContent # ဒီ line ကို အပေါ်ဆုံးမှာ Import လုပ်ပေးပါ

# သင့်ရဲ့ Bot API Token 
TOKEN = 'TOKEN = '8787754774:AAEOPMrAfMhHFviaEHWFUSE_2P6RIVlmUxM'
bot = telebot.TeleBot(TOKEN)

# သင်္ချာတွက်ချက်မှုများအတွက်
allowed_math_functions = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
allowed_math_functions['abs'] = abs
allowed_math_functions['round'] = round

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello from Kiwii calculations bot!")

@bot.message_handler(func=lambda message: True)
def calculate(message):
    try:
        text_to_calc = message.text.lower() 
        text_to_calc = text_to_calc.replace('^', '**') 
        text_to_calc = text_to_calc.replace('x', '*')  
        text_to_calc = text_to_calc.replace('×', '*')  
        text_to_calc = text_to_calc.replace(',', '')   
        
        result = eval(text_to_calc, {"__builtins__": None}, allowed_math_functions)
        
        bot.reply_to(message, f"{message.text} = {result}")
    except Exception:
        # GP ထဲမှာဆိုရင် Error စာသားမပို့ဘဲ ငြိမ်နေရန် (Spam မဖြစ်စေရန် ပြင်ဆင်ချက်)
        if message.chat.type == 'private':
            bot.reply_to(message, "For now I don't know how to calculate such things 😔")
        else:
            pass

@bot.inline_handler(lambda query: len(query.query) > 0)
def query_text(inline_query):
    try:
        query_str = inline_query.query.lower()
        # တွက်ချက်မှုဆိုင်ရာ ပြင်ဆင်ချက်များ
        calc_str = query_str.replace('^', '**').replace('x', '*').replace('×', '*').replace(',', '')
        
        # တွက်ချက်ခြင်း
        result = eval(calc_str, {"__builtins__": None}, allowed_math_functions)
        
        # ပြသမည့် ရလဒ် Format
        r = InlineQueryResultArticle(
            id='1',
            title=f"Result: {result}",
            description=f"{query_str} ကို တွက်ချက်ရန် နှိပ်ပါ",
            input_message_content=InputTextMessageContent(f"{query_str} = {result}")
        )
        
        bot.answer_inline_query(inline_query.id, [r])
    except Exception:
        # Error ဖြစ်နေရင် ဘာမှမပြရန် သို့မဟုတ် Error ပြရန်
        pass

# --- အောက်ပါအပိုင်းသည် 24/7 Run နိုင်ရန် Flask Web Server ထည့်ထားခြင်းဖြစ်သည် ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_bot():
    print("calculations bot စတင်အလုပ်လုပ်နေပါပြီ...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    # Bot ကို သီးသန့် Thread တစ်ခုခွဲပြီး Run မည်
    thread = threading.Thread(target=run_bot)
    thread.start()
    
    # Web Server ကို Run မည်
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
