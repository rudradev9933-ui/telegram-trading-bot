import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import re

# ================================
# 🔑 DIRECT KEYS (TESTING ONLY)
# ================================
TELEGRAM_BOT_TOKEN = "8271751636:AAHUUMtC8pVtjoerPsEViTYxeUsD335MmOo"
GEMINI_API_KEY = "AIzaSyCCDc0a7cmWqgvhbpLEUyeNFfrbJHYfGz0"

# ================================
# 🤖 GEMINI SETUP
# ================================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ================================
# 📊 SIGNAL PARSER
# ================================
def parse_signal(text):
    print(f"\n📝 Gemini Response:\n{text}\n")

    signal = {
        "action": None,
        "risk_percent": 1.0,
        "stop_loss": None,
        "take_profit": None,
    }

    text_upper = text.upper()

    if "BUY" in text_upper:
        signal["action"] = "BUY"
    elif "SELL" in text_upper:
        signal["action"] = "SELL"

    risk_match = re.search(r"risk[:\s]*(\d+\.?\d*)%?", text, re.I)
    if risk_match:
        signal["risk_percent"] = float(risk_match.group(1))

    sl_match = re.search(r"(?:sl|stop\s*loss)[:\s]*(\d+\.?\d+)", text, re.I)
    if sl_match:
        signal["stop_loss"] = float(sl_match.group(1))

    tp_match = re.search(r"(?:tp|take\s*profit)[:\s]*(\d+\.?\d+)", text, re.I)
    if tp_match:
        signal["take_profit"] = float(tp_match.group(1))

    return signal

# ================================
# 📸 PHOTO HANDLER (CHANNEL)
# ================================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("\n" + "=" * 50)
        print("📸 Photo received from channel")
        print("=" * 50)

        photo = await update.channel_post.photo[-1].get_file()
        photo_bytes = await photo.download_as_bytearray()
        caption = update.channel_post.caption or ""

        prompt = f"""
        Analyze this trading signal image and extract clearly:
        1. BUY or SELL
        2. Risk percentage
        3. Stop Loss price
        4. Take Profit price

        Caption: {caption}

        Respond in simple text.
        """

        print("⏳ Sending image to Gemini AI...")
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": photo_bytes}
        ])

        signal = parse_signal(response.text)

        if signal["action"]:
            print(f"""
✅ SIGNAL FOUND
━━━━━━━━━━━━━━━━━━━━
📊 Action     : {signal['action']}
💰 Risk %     : {signal['risk_percent']}
🛑 Stop Loss : {signal['stop_loss']}
🎯 TakeProfit: {signal['take_profit']}
━━━━━━━━━━━━━━━━━━━━
            """)
        else:
            print("❌ No valid trade signal detected")

    except Exception as e:
        print(f"❌ ERROR: {e}")

# ================================
# 🚀 MAIN BOT START
# ================================
def main():
    print("""
╔════════════════════════════════════╗
║ 🤖 AI SIGNAL BOT STARTED           ║
║ 📡 Listening Channel Photos        ║
║ ⚡ Gemini Vision Enabled           ║
╚════════════════════════════════════╝
    """)

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(
        MessageHandler(filters.PHOTO & filters.ChatType.CHANNEL, handle_photo)
    )

    print("⏳ Bot polling started...\n")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

# ================================
# ▶️ RUN
# ================================
if __name__ == "__main__":
    main()
