import asyncio
import random
import json
import os
import hmac
import hashlib
import base64
import time
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# =====================================================================
# 👑 الإعدادات السيادية (بوت اللغة الإنجليزية فقط)
# =====================================================================
ADMIN_ID = 8859538798  # معرف المسؤول الخاص بك
BOT_TOKEN = "8859538798:AAHmJ0NM0-M9MZSfHLvZx27zzbjukQTF1dc"  # تم إضافة التوكن الخاص بك هنا بنجاح

SECRET_KEY = "V40_ENGLISH_SECURE_2026"
USERS_FILE = "english_users_database.json"

STORE_LINK = "https://t.me/your_store"  
SUPPORT_LINK = "https://t.me/your_support"

# =====================================================================
# 💾 إدارة قاعدة البيانات والذاكرة
# =====================================================================
def load_db():
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE, "r", encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(USERS_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True
    db = load_db()
    return str(user_id) in db and time.time() < float(db[str(user_id)])

# =====================================================================
# 🔐 محرك التشفير والتحقق للأكواد
# =====================================================================
def verify_code(code):
    try:
        clean = code.replace("ENG-", "").strip()
        missing_padding = len(clean) % 4
        if missing_padding: clean += '=' * (4 - missing_padding)
        decoded = base64.urlsafe_b64decode(clean).decode()
        expiry, sig = decoded.split(":")
        check = hmac.new(SECRET_KEY.encode(), f"ENGLISH:{expiry}".encode(), hashlib.sha256).hexdigest()[:12]
        if sig == check and time.time() < int(expiry): return True, int(expiry)
        return False, "❌ الكود غير صالح أو منتهي الصلاحية."
    except: return False, "⚠️ خطأ في تنسيق الكود."

def generate_code(days):
    expiry = int(time.time()) + (days * 86400)
    sig = hmac.new(SECRET_KEY.encode(), f"ENGLISH:{expiry}".encode(), hashlib.sha256).hexdigest()[:12]
    token = base64.urlsafe_b64encode(f"{expiry}:{sig}".encode()).decode().replace("=", "")
    return f"ENG-{token}"

# =====================================================================
# 🇬🇧 قوائم الأوامر والوظائف الأساسية
# =====================================================================
MAIN_MENU = [
    ["📝 اختبار تحديد المستوى", "📖 الكلمات اليومية"],
    ["🗣️ محادثة تفاعلية", "🧠 نصيحة اليوم"],
    ["⚙️ الدعم والاشتراك"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_subscribed(uid):
        await update.message.reply_text(f"⚠️ **Subscription not active.**\nPlease activate your subscription: {STORE_LINK}")
        return
        
    menu = MAIN_MENU.copy()
    if uid == ADMIN_ID: menu.insert(0, ["🛠 Admin Control"])
    
    welcome_msg = (
        "🇬🇧 **Welcome to the English Learning Platform!**\n\n"
        "مرحباً بك في منصتك المتطورة لتعلم وتطوير اللغة الإنجليزية! "
        "اختر أحد الخيارات من القائمة بالأسفل لبدء رحلتك التعليمية:"
    )
    await update.message.reply_text(welcome_msg, reply_markup=ReplyKeyboardMarkup(menu, resize_keyboard=True), parse_mode="Markdown")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    uid = update.effective_user.id

    # استقبال وتفعيل كود الاشتراك للعملاء
    if text.startswith("ENG-"):
        ok, exp = verify_code(text)
        if ok:
            db = load_db()
            db[str(uid)] = exp
            save_db(db)
            await update.message.reply_text("✅ **Subscription activated successfully!**\nاضغط /start لتحديث القائمة.")
        else:
            await update.message.reply_text(exp)
        return

    if not is_subscribed(uid): return

    # تنفيذ الأوامر من القائمة
    if text == "📖 الكلمات اليومية":
        words = [
            ("Persistent", "مستمر / مُصرّ"),
            ("Acquire", "يكتسب / يحصل على"),
            ("Fluency", "الطلاقة في التحدث"),
            ("Enhance", "يُحسّن / يُطوّر"),
            ("Simultaneously", "في نفس الوقت / بالتزامن")
        ]
        w = random.choice(words)
        await update.message.reply_text(f"💡 **Word of the Day:**\n\n🇬🇧 **Word:** `{w[0]}`\n🇸🇦 **Meaning:** {w[1]}")

    elif text == "🧠 نصيحة اليوم":
        tips = [
            "Practice speaking out loud for at least 15 minutes daily.",
            "Try to watch movies with English subtitles, not Arabic ones.",
            "Don't be afraid to make mistakes; it's the only way to learn!",
            "Surround your daily environment with English (change your phone language)."
        ]
        await update.message.reply_text(f"🗣️ **Learning Tip:**\n\n`{random.choice(tips)}`")

    elif text == "📝 اختبار تحديد المستوى":
        await update.message.reply_text("📝 **Placement Test Coming Soon!**\nيجري حالياً إعداد تحديث شامل للاختبار التفاعلي، ترقبه قريباً.")

    elif text == "🗣️ محادثة تفاعلية":
        await update.message.reply_text("🗣️ **Interactive Conversation:**\nأهلاً بك! ابدأ كتابة أي جملة بالإنجليزية وسأقوم بمساعدتك وتصحيحها لك فوراً.")

    elif text == "⚙️ الدعم والاشتراك":
        await update.message.reply_text(f"🛒 **Subscription Link:** {STORE_LINK}\n💬 **Technical Support:** {SUPPORT_LINK}")

    # لوحة تحكم الأدمن لتوليد الأكواد
    elif uid == ADMIN_ID and text == "🛠 Admin Control":
        count = len(load_db())
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎫 Code 1 Month", callback_data="gen_1m"), 
             InlineKeyboardButton("🎫 Code 1 Year", callback_data="gen_1y")]
        ])
        await update.message.reply_text(
            f"👥 **Admin Control Panel:**\n\nActive Subscribers: `{count}`\n\nGenerate validation codes for customers:", 
            reply_markup=kb, 
            parse_mode="Markdown"
        )

# =====================================================================
# 🎫 معالج الأزرار التفاعلية للأدمن (توليد الأكواد)
# =====================================================================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID: return

    days = 30 if q.data == "gen_1m" else 365
    code = generate_code(days)
    await context.bot.send_message(
        chat_id=ADMIN_ID, 
        text=f"🎫 **New English Code Generated ({days} Days):**\n\n`{code}`\n\nCopy and send it to the user."
    )

# =====================================================================
# 🚀 محرك التشغيل الرئيسي
# =====================================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("🚀 بوت اللغة الإنجليزية يعمل الآن بنجاح واستقرار تام!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
