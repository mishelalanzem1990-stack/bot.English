import asyncio
import random
import json
import os
import hmac
import hashlib
import base64
import time
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ================== الإعدادات السيادية ==================
BOT_TOKEN = "8859538798:AAHmJ0NM0-M9MZSfHLvZx27zzbjukQTF1dc"
ADMIN_ID = 892901952  
SECRET_KEY = "V40_ENGLISH_SECURE_2026"
USERS_FILE = "english_users_database.json"

STORE_LINK = "https://t.me/your_store"  # ضع رابط متجرك هنا

# ✨ بنك الجمل المتكامل ذو المظهر الجميل والتصنيفات المتنوعة ✨
ENGLISH_PHRASES = [
    {"en": "How have you been?", "ar": "كيف كانت أحوالك مؤخراً؟", "type": "🗣️ ممارسات يومية"},
    {"en": "Keep up the good work!", "ar": "استمر في هذا العمل الرائع!", "type": "🔥 جرعة تحفيزية"},
    {"en": "I will get back to you soon.", "ar": "سأرد عليك في أقرب وقت.", "type": "💼 لغة الأعمال"},
    {"en": "Let's call it a day.", "ar": "فلنكتفِ بهذا القدر اليوم (لننهي العمل).", "type": "💼 لغة الأعمال"},
    {"en": "Could you please clarify this?", "ar": "هل يمكنك توضيح هذا من فضلك؟", "type": "💼 لغة الأعمال"},
    {"en": "Never give up on your dreams.", "ar": "لا تتخلى عن أحلامك أبداً.", "type": "🔥 جرعة تحفيزية"},
    {"en": "It is not worth it.", "ar": "الأمر لا يستحق كل هذا العناء.", "type": "🗣️ ممارسات يومية"},
    {"en": "Can you handle this task?", "ar": "هل تستطيع تولي هذه المهمة؟", "type": "💼 لغة الأعمال"},
    {"en": "What do you recommend?", "ar": "ماذا تقترح أو توصي به؟", "type": "✈️ سياحة وسفر"},
    {"en": "Action speaks louder than words.", "ar": "الأفعال أبلغ من الأقوال.", "type": "💎 حكمة اليوم"},
    {"en": "Better late than never.", "ar": "أن تأتي متأخراً خير من أن لا تأتي أبداً.", "type": "💎 حكمة اليوم"},
    {"en": "I'm looking forward to it.", "ar": "أنا أتطلع بشوق لحدوث ذلك.", "type": "🗣️ ممارسات يومية"},
    {"en": "Don't take it to heart.", "ar": "لا تأخذ الأمر على محمل شخصي (لا تزعل).", "type": "🗣️ ممارسات يومية"},
    {"en": "Where is the nearest pharmacy?", "ar": "أين تقع أقرب صيدلية؟", "type": "✈️ سياحة وسفر"},
    {"en": "Could you take a picture of me?", "ar": "هل يمكنك التقاط صورة لي؟", "type": "✈️ سياحة وسفر"},
    {"en": "Hard work always pays off.", "ar": "العمل الجاد يؤتي ثماره دائماً.", "type": "🔥 جرعة تحفيزية"}
]

# ================== نظام الذاكرة وتخزين المشتركين ==================
def load_users():
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except: return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================== محرك تشفير وفحص الأكواد ==================
def verify_secure_code(code):
    try:
        clean = code.replace("STK-", "").strip()
        missing_padding = len(clean) % 4
        if missing_padding: clean += '=' * (4 - missing_padding)
        decoded = base64.urlsafe_b64decode(clean).decode()
        expiry, sig = decoded.split(":")
        check = hmac.new(SECRET_KEY.encode(), f"ENGLISH:{expiry}".encode(), hashlib.sha256).hexdigest()[:12]
        if sig == check and time.time() < int(expiry): return True, int(expiry)
        return False, "❌ الكود غير صالح أو منتهي الصلاحية."
    except: return False, "⚠️ خطأ في تنسيق الكود."

def generate_secure_code(days):
    expiry = int(time.time()) + (days * 86400)
    sig = hmac.new(SECRET_KEY.encode(), f"ENGLISH:{expiry}".encode(), hashlib.sha256).hexdigest()[:12]
    token = base64.urlsafe_b64encode(f"{expiry}:{sig}".encode()).decode().replace("=", "")
    return f"STK-{token}"

def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True
    users = load_users()
    return str(user_id) in users and time.time() < float(users[str(user_id)])

# ================== معالجة الأوامر والرسائل ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name

    # لو كان المستخدم هو الآدمن (أبو فهد) تظهر له لوحة التحكم بالأكواد تلقائياً
    if uid == ADMIN_ID:
        count = len(load_users())
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎫 كود شهر (30 يوم)", callback_data="gen_1m")],
            [InlineKeyboardButton("🎫 كود سنة (365 يوم)", callback_data="gen_1y")]
        ])
        await update.message.reply_text(
            f"👑 **مرحباً بك يا أبو فهد في لوحة تحكم بوت الإنجليزية!**\n\n"
            f"👥 عدد الطلاب المشتركين حالياً: `{count}`\n\n"
            f"إليك أدوات توليد أكواد تفعيل الاشتراكات الجديدة لعملائك:", 
            reply_markup=kb, parse_mode="Markdown"
        )
        return

    # للجمهور العادي: فحص الاشتراك
    if not is_subscribed(uid):
        await update.message.reply_text(
            f"⚠️ **أهلاً بك يا {name}، الاشتراك غير مفعّل لديك حالياً.**\n\n"
            f"🔐 للحصول على كود التفعيل والبدء في تلقي الجمل التعليمية كل ساعة تلقائياً، "
            f"يرجى التواصل أو الشراء من المتجر: {STORE_LINK}\n\n"
            f"📥 بعد الحصول على الكود، أرسله هنا مباشرة في المحادثة لتفعيل حسابك.",
            disable_web_page_preview=True
        )
        return

    await update.message.reply_text(
        f"👋 **أهلاً بك مجدداً يا {name}!**\n\n"
        f"⏰ نظام التلقين الآلي مفعّل على حسابك بنجاح. البوت يرسل لك جرعتك اللغوية المنسقة "
        f"تلقائياً كل ساعة دون أي تدخل منك. طوّر لغتك بذكاء!",
        parse_mode="Markdown"
    )

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    uid = update.effective_user.id

    # معالجة إدخال أكواد التفعيل من قبل المستخدمين
    if text.startswith("STK-"):
        ok, exp = verify_secure_code(text)
        if ok:
            users = load_users()
            users[str(uid)] = exp
            save_users(users)
            await update.message.reply_text(
                "🎉 **ممتاز! تم تفعيل اشتراكك بنجاح.**\n\n"
                "⏱️ سيبدأ البوت ببث جملتين مترجمتين ومنسقتين لك كل ساعة تلقائياً من الآن وصاعداً. بالتوفيق في رحلتك التعليمية! \n"
                "اضغط /start لتحديث حالة النظام."
            )
        else:
            await update.message.reply_text(exp)
        return

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.from_user.id == ADMIN_ID:
        days = 30 if q.data == "gen_1m" else 365
        code = generate_secure_code(days)
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=f"🎫 **تم توليد كود اشتراك جديد بنجاح ({days} يوم):**\n\n`{code}`\n\nقم بنسخه وإرساله للعميل لتفعيل اشتراكه فوراً."
        )

# ================== محرك الإرسال الآلي والديكور ==================
async def auto_broadcast_job(context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    if not users: return
    
    # اختيار جملتين عشوائيتين مميزتين
    selected = random.sample(ENGLISH_PHRASES, 2)
    
    # 🎨 تنسيق الرسالة الجمالي الفاخر
    msg_text = (
        "⏰ **جرعتك اللغوية التلقائية لهذه الساعة:**\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"🟢 **الجملة الأولى** | {selected[0]['type']}\n"
        f"🇺🇸 ` {selected[0]['en']} `\n"
        f"🇸🇦 {selected[0]['ar']}\n\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔵 **الجملة الثانية** | {selected[1]['type']}\n"
        f"🇺🇸 ` {selected[1]['en']} `\n"
        f"🇸🇦 {selected[1]['ar']}\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "💡 *نصيحة: اضغط على الجملة الإنجليزية لنسخها وممارستها!*"
    )
    
    # البوت يرسل تلقائياً فقط لمن لديه اشتراك ساري المفعول حالياً
    current_time = time.time()
    for user_id, expiry in users.items():
        if current_time < float(expiry):
            try:
                await context.application.bot.send_message(chat_id=int(user_id), text=msg_text, parse_mode="Markdown")
            except:
                continue

# ================== تشغيل وإدارة البوت ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # جدولة البث التلقائي كل ساعة (3600 ثانية) للمشتركين النشطين
    scheduler = AsyncIOScheduler()
    scheduler.add_job(auto_broadcast_job, 'interval', seconds=3600)
    scheduler.start()
    
    # الأوامر والمعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("🚀 بوت التلقين الآلي والمشفر يعمل الآن تحت إشراف أبو فهد.. جاري الإرسال للمشتركين!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
