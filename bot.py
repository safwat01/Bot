import telebot  
from telebot import types  
import sqlite3  
import os  

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Railway Variables থেকে নেবে  
bot = telebot.TeleBot(BOT_TOKEN)  

# ✅ Admin User ID  
ADMIN_ID = 6551628383    
REFERRAL_BONUS = 100  

# ✅ SQLite DB setup  
conn = sqlite3.connect("bot.db", check_same_thread=False)  
cursor = conn.cursor()  

# টেবিল তৈরি (একবারই হবে)  
cursor.execute("""  
CREATE TABLE IF NOT EXISTS users (  
    user_id INTEGER PRIMARY KEY,  
    balance INTEGER DEFAULT 0  
)  
""")  
conn.commit()  

# ব্যালেন্স যোগ করা  
def add_balance(user_id, amount):  
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))  
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))  
    conn.commit()  

# ব্যালেন্স চেক করা  
def get_balance(user_id):  
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))  
    row = cursor.fetchone()  
    return row[0] if row else 0  

# ব্যালেন্স কাটার ফাংশন  
def deduct_balance(user_id, amount):  
    bal = get_balance(user_id)  
    if bal >= amount:  
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))  
        conn.commit()  
        return True  
    return False  

# ✅ Start Command (Referral Support)  
@bot.message_handler(commands=['start'])  
def start(message):  
    user_id = message.from_user.id  
    args = message.text.split()  
    if len(args) > 1:  
        ref_id = args[1]  
        if str(user_id) != ref_id:  
            if get_balance(user_id) == 0:  
                add_balance(user_id, 0)  
                try:  
                    ref_id_int = int(ref_id)  
                    add_balance(ref_id_int, REFERRAL_BONUS)  
                    bot.send_message(ref_id_int, f"🎉 আপনি পেয়েছেন {REFERRAL_BONUS} কয়েন রেফারেল বোনাস!")  
                except:  
                    pass  
            bot.send_message(user_id, "🎉 রেফারেল কোড স্বীকার হয়েছে, স্বাগতম!")  
        else:  
            bot.send_message(user_id, "⚠️ আপনি নিজেকে রেফারেল করতে পারবেন না।")  
    else:  
        if get_balance(user_id) == 0:  
            add_balance(user_id, 0)  

    # ✅ Main Menu Buttons  
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  
    btn1 = types.KeyboardButton("📈 Views")  
    btn2 = types.KeyboardButton("❤️ Reactions")  
    btn3 = types.KeyboardButton("👥 Subscriber")  
    btn4 = types.KeyboardButton("💰 My Balance")  
    btn5 = types.KeyboardButton("🆘 Support")  
    btn6 = types.KeyboardButton("📤 Referral")  
    btn7 = types.KeyboardButton("💸 Transfer")  
    btn8 = types.KeyboardButton("💳 Buy Coins")  
    markup.add(btn1, btn2)  
    markup.add(btn3, btn4)  
    markup.add(btn5, btn6)  
    markup.add(btn7, btn8)  
    bot.send_message(user_id, "👋 স্বাগতম! নিচের মেনু থেকে একটি অপশন বেছে নিন:", reply_markup=markup)  

# ✅ Admin: Balance Add  
@bot.message_handler(commands=['addbalance'])  
def add_balance_command(message):  
    if message.from_user.id == ADMIN_ID:  
        try:  
            _, target_id, amount = message.text.split()  
            target_id = int(target_id)  
            amount = int(amount)  
            add_balance(target_id, amount)  
            bot.send_message(message.chat.id, f"✅ {target_id} কে {amount} কয়েন যোগ করা হয়েছে।")  
            bot.send_message(target_id, f"💰 আপনার ব্যালেন্সে {amount} কয়েন অ্যাড করা হয়েছে (Admin দ্বারা)।")  
        except:  
            bot.send_message(message.chat.id, "⚠️ ব্যবহার: /addbalance <user_id> <amount>")  
    else:  
        bot.send_message(message.chat.id, "❌ আপনি অনুমোদিত নন।")  

# ✅ Views  
@bot.message_handler(func=lambda message: message.text == "📈 Views")  
def views(message):  
    bot.send_message(message.chat.id, "🔗 আপনার পোস্টের লিংক দিন যেটাতে ভিউ বাড়াতে চান:")  

# ✅ Reactions  
@bot.message_handler(func=lambda message: message.text == "❤️ Reactions")  
def reactions(message):  
    bot.send_message(message.chat.id, "🔗 আপনার পোস্টের লিংক দিন যেটাতে রিঅ্যাকশন বাড়াতে চান:")  

# ✅ Subscriber  
@bot.message_handler(func=lambda message: message.text == "👥 Subscriber")  
def subscribers(message):  
    bot.send_message(message.chat.id, "🔗 আপনার চ্যানেল/গ্রুপ লিংক দিন সাবস্ক্রাইবার বাড়াতে:")  

# ✅ My Balance  
@bot.message_handler(func=lambda message: message.text == "💰 My Balance")  
def balance(message):  
    bal = get_balance(message.from_user.id)  
    bot.send_message(message.chat.id, f"🆔 Your UserID: `{message.from_user.id}`\n💰 আপনার ব্যালেন্স: {bal} Coins", parse_mode="Markdown")  

# ✅ Support  
@bot.message_handler(func=lambda message: message.text == "🆘 Support")  
def support(message):  
    bot.send_message(message.chat.id, "🆘 সাহায্যের জন্য যোগাযোগ করুন: @safwat01")  

# ✅ Referral  
@bot.message_handler(func=lambda message: message.text == "📤 Referral")  
def referral(message):  
    bot_username = "tgsbs_RoBot"  
    user_id = message.from_user.id  
    link = f"https://t.me/{bot_username}?start={user_id}"  
    bot.send_message(message.chat.id, f"📤 আপনার রেফারেল লিংক:\n{link}\n\nপ্রতি রেফারেল এ পাবেন {REFERRAL_BONUS} কয়েন।")  

# ✅ Transfer (Send Coins)  
@bot.message_handler(func=lambda message: message.text == "💸 Transfer")  
def transfer(message):  
    bot.send_message(message.chat.id, "💸 কয়েন পাঠাতে এই ফরম্যাটে লিখুন:\n`/transfer <user_id> <amount>`", parse_mode="Markdown")  

@bot.message_handler(commands=['transfer'])  
def transfer_command(message):  
    try:  
        _, target_id, amount = message.text.split()  
        sender_id = message.from_user.id  
        target_id = int(target_id)  
        amount = int(amount)  

        if sender_id == target_id:  
            bot.send_message(sender_id, "⚠️ নিজেকে কয়েন পাঠানো যাবে না।")  
            return  

        if deduct_balance(sender_id, amount):  
            add_balance(target_id, amount)  
            bot.send_message(sender_id, f"✅ আপনি সফলভাবে {target_id} ইউজারকে {amount} কয়েন পাঠিয়েছেন।")  
            bot.send_message(target_id, f"💰 আপনি {sender_id} থেকে {amount} কয়েন পেয়েছেন।")  
        else:  
            bot.send_message(sender_id, "❌ আপনার ব্যালেন্স পর্যাপ্ত নয়।")  
    except:  
        bot.send_message(message.chat.id, "⚠️ ব্যবহার: /transfer <user_id> <amount>")  

# ✅ Buy Coins  
@bot.message_handler(func=lambda message: message.text == "💳 Buy Coins")  
def buy_coins(message):  
    bot.send_message(message.chat.id, "💳 কয়েন কেনার জন্য /buy লিখুন অথবা আমাদের সাপোর্টে যোগাযোগ করুন।")  

# ✅ Fallback  
@bot.message_handler(func=lambda message: True)  
def fallback(message):  
    bot.send_message(message.chat.id, "⚠️ অনুগ্রহ করে মেনু থেকে একটি বৈধ অপশন বেছে নিন।")  

print("🤖 Bot is running...")  
bot.polling()
