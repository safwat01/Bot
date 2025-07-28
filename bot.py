import telebot
from telebot import types
import sqlite3
import os
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Railway Variables থেকে নেবে
bot = telebot.TeleBot(BOT_TOKEN)

# ✅ Admin User ID
ADMIN_ID = 6551628383
REFERRAL_BONUS = 100

# ✅ SQLite DB setup
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# টেবিল তৈরি
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    user_id INTEGER,
    order_type TEXT,
    order_link TEXT,
    order_quantity INTEGER,
    order_time TEXT
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

# অর্ডার সেভ করার ফাংশন
def save_order(order_id, user_id, order_type, order_link, order_quantity, order_time):
    cursor.execute("""
    INSERT INTO orders (order_id, user_id, order_type, order_link, order_quantity, order_time)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (order_id, user_id, order_type, order_link, order_quantity, order_time))
    conn.commit()

# অর্ডার আইডি জেনারেটর
def generate_order_id():
    return str(int(time.time()))

# অর্ডার প্রসেস করার ফাংশন
def process_order(user_id, order_type, link, quantity, price_per_unit):
    total_cost = quantity * price_per_unit
    if deduct_balance(user_id, total_cost):
        order_id = generate_order_id()
        order_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # ডাটাবেজে সেভ করা
        save_order(order_id, user_id, order_type, link, quantity, order_time)

        # ইউজারের কাছে মেসেজ
        bot.send_message(user_id, f"✅ অর্ডার নিশ্চিত হয়েছে!\n\n"
                                  f"Order ID: {order_id}\n"
                                  f"Order Type: {order_type}\n"
                                  f"Order Link: {link}\n"
                                  f"Order Quantity: {quantity}\n"
                                  f"Order Time: {order_time}")

        # অ্যাডমিনের কাছে মেসেজ
        bot.send_message(ADMIN_ID, f"## নতুন অর্ডার ##\n\n"
                                   f"User ID: {user_id}\n"
                                   f"Order ID: {order_id}\n"
                                   f"Order Type: {order_type}\n"
                                   f"Order Link: {link}\n"
                                   f"Order Quantity: {quantity}\n"
                                   f"Order Time: {order_time}")
    else:
        bot.send_message(user_id, "❌ আপনার পর্যাপ্ত কয়েন নেই!")

# অর্ডার ডাটা টেম্পোরারি স্টোরেজ
order_data = {}

# অর্ডার শুরু (Views, Reactions, Subscriber)
@bot.message_handler(func=lambda msg: msg.text in ["📈 Views", "❤️ Reactions", "👥 Subscriber"])
def order_start(message):
    user_id = message.from_user.id
    order_type = message.text
    order_data[user_id] = {"type": order_type}
    bot.send_message(user_id, "🔗 অর্ডারের লিংক দিন:")

# লিংক ইনপুট নেওয়া
@bot.message_handler(func=lambda msg: msg.from_user.id in order_data and "link" not in order_data[msg.from_user.id])
def get_link(message):
    user_id = message.from_user.id
    order_data[user_id]["link"] = message.text
    bot.send_message(user_id, "📌 কত সংখ্যক অর্ডার চান তা লিখুন:")

# কোয়ান্টিটি ইনপুট নেওয়া এবং অর্ডার প্রসেস
@bot.message_handler(func=lambda msg: msg.from_user.id in order_data and "link" in order_data[msg.from_user.id])
def get_quantity(message):
    user_id = message.from_user.id
    try:
        quantity = int(message.text)
        order_type = order_data[user_id]["type"]
        link = order_data[user_id]["link"]

        price_per_unit = 1 if order_type == "📈 Views" else 3 if order_type == "❤️ Reactions" else 5
        process_order(user_id, order_type, link, quantity, price_per_unit)

        del order_data[user_id]
    except:
        bot.send_message(user_id, "⚠️ সঠিক সংখ্যা লিখুন।")

# Start কমান্ড (Referral সাপোর্ট)
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

    # মেনু বোতাম
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📈 Views"), types.KeyboardButton("❤️ Reactions"))
    markup.add(types.KeyboardButton("👥 Subscriber"), types.KeyboardButton("💰 My Balance"))
    markup.add(types.KeyboardButton("🆘 Support"), types.KeyboardButton("📤 Referral"))
    markup.add(types.KeyboardButton("💸 Transfer"), types.KeyboardButton("💳 Buy Coins"))
    bot.send_message(user_id, "👋 স্বাগতম! নিচের মেনু থেকে একটি অপশন বেছে নিন:", reply_markup=markup)

# Admin: Balance Add
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

# ব্যালেন্স দেখানো
@bot.message_handler(func=lambda m: m.text == "💰 My Balance")
def balance(message):
    bal = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"🆔 UserID: `{message.from_user.id}`\n💰 ব্যালেন্স: {bal} Coins", parse_mode="Markdown")

# Support মেসেজ
@bot.message_handler(func=lambda m: m.text == "🆘 Support")
def support(message):
    bot.send_message(message.chat.id, "🆘 সাহায্যের জন্য যোগাযোগ করুন: @safwat01")

# Referral লিংক
@bot.message_handler(func=lambda m: m.text == "📤 Referral")
def referral(message):
    bot_username = "tgsbs_RoBot"
    user_id = message.from_user.id
    link = f"https://t.me/{bot_username}?start={user_id}"
    bot.send_message(message.chat.id, f"📤 রেফারেল লিংক:\n{link}\n\nপ্রতি রেফারেল এ পাবেন {REFERRAL_BONUS} কয়েন।")

# Transfer
@bot.message_handler(func=lambda m: m.text == "💸 Transfer")
def transfer(message):
    bot.send_message(message.chat.id, "💸 কয়েন পাঠাতে:\n`/transfer <user_id> <amount>`", parse_mode="Markdown")

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
            bot.send_message(sender_id, f"✅ সফলভাবে {target_id} কে {amount} কয়েন পাঠানো হয়েছে।")
            bot.send_message(target_id, f"💰 আপনি {sender_id} থেকে {amount} কয়েন পেয়েছেন।")
        else:
            bot.send_message(sender_id, "❌ পর্যাপ্ত কয়েন নেই।")
    except:
        bot.send_message(message.chat.id, "⚠️ ব্যবহার: /transfer <user_id> <amount>")

# Buy Coins
@bot.message_handler(func=lambda m: m.text == "💳 Buy Coins")
def buy_coins(message):
    bot.send_message(message.chat.id, "💳 কয়েন কেনার জন্য /buy লিখুন অথবা সাপোর্টে যোগাযোগ করুন।")

# Admin কমান্ড: সব অর্ডার দেখানো
@bot.message_handler(commands=['orders'])
def show_orders(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ আপনি অনুমোদিত নন।")
        return

    cursor.execute("SELECT * FROM orders ORDER BY order_time DESC")
    orders = cursor.fetchall()
    if not orders:
        bot.send_message(message.chat.id, "কোনো অর্ডার পাওয়া যায়নি।")
        return

    text = "📋 সকল অর্ডার:\n\n"
    for order in orders:
        order_id, user_id, order_type, order_link, order_quantity, order_time = order
        text += (f"Order ID: {order_id}\nUser ID: {user_id}\nType: {order_type}\n"
                 f"Link: {order_link}\nQuantity: {order_quantity}\nTime: {order_time}\n\n")
        if len(text) > 3500:  # Telegram message limit workaround
            bot.send_message(message.chat.id, text)
            text = ""
    if text:
        bot.send_message(message.chat.id, text)

# Fallback
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "⚠️ মেনু থেকে একটি বৈধ অপশন বেছে নিন।")

print("🤖 Bot is running...")
bot.polling()
