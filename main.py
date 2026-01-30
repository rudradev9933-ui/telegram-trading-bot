"""
🤖 TELEGRAM TRADING BOT - MAIN ENTRY POINT
Automated trading signal processor with AI vision
"""

import asyncio
import os
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from dotenv import load_dotenv

# Import custom modules
from signal_parser import SignalParser
from api_integration import get_broker_api

# Load environment variables
load_dotenv()

# ================================
# 🔑 CONFIGURATION
# ================================
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Load config
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# Validate keys
if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ Missing API keys! Check .env file")

# ================================
# 🤖 INITIALIZE MODULES
# ================================
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

signal_parser = SignalParser()
broker_api = get_broker_api(CONFIG["broker"]["name"])

# ================================
# 📸 PHOTO HANDLER (CHANNEL)
# ================================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle photos posted in Telegram channel
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    try:
        print("\n" + "=" * 60)
        print("📸 New photo received from channel")
        print("=" * 60)
        
        # Download photo
        photo = await update.channel_post.photo[-1].get_file()
        photo_bytes = await photo.download_as_bytearray()
        caption = update.channel_post.caption or ""
        
        # Prepare Gemini prompt
        prompt = f"""
        You are a trading signal analyzer. Extract the following from this chart image:
        
        1. Trading action: BUY or SELL
        2. Symbol/Asset (e.g., XAUUSD, BTCUSD, EURUSD)
        3. Risk percentage (if mentioned)
        4. Stop Loss price
        5. Take Profit price
        
        Image caption: {caption}
        
        Respond in clear, structured text format.
        """
        
        print("⏳ Analyzing image with Gemini AI...")
        
        # Send to Gemini
        response = gemini_model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": photo_bytes}
        ])
        
        # Parse signal
        signal = signal_parser.parse_gemini_response(response.text)
        
        # Display result
        print(signal_parser.format_signal_output(signal))
        
        # Execute trade if auto-trade enabled and signal is valid
        if CONFIG["bot_settings"]["enable_auto_trade"] and signal["valid"]:
            print("\n🚀 Auto-trade ENABLED - Executing trade...")
            broker_api.execute_trade(signal)
        else:
            if not signal["valid"]:
                print("⚠️ Signal invalid - skipping execution")
            else:
                print("⚠️ Auto-trade DISABLED - manual execution required")
        
    except Exception as e:
        print(f"❌ ERROR in photo handler: {e}")
        import traceback
        traceback.print_exc()

# ================================
# 🚀 MAIN BOT START
# ================================
def main():
    """Initialize and start the bot"""
    
    print("""
╔════════════════════════════════════════╗
║  🤖 AI TRADING SIGNAL BOT v2.0        ║
║  📡 Listening to channel photos        ║
║  ⚡ Gemini Vision AI enabled           ║
║  💼 Broker API ready                   ║
╚════════════════════════════════════════╝
    """)
    
    print(f"⚙️  Auto-trade: {CONFIG['bot_settings']['enable_auto_trade']}")
    print(f"💰 Default risk: {CONFIG['bot_settings']['default_risk_percent']}%")
    print(f"🏦 Broker: {CONFIG['broker']['name']}\n")
    
    # Build application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add photo handler for channel posts
    app.add_handler(
        MessageHandler(
            filters.PHOTO & filters.ChatType.CHANNEL, 
            handle_photo
        )
    )
    
    print("⏳ Bot is now running... Press Ctrl+C to stop\n")
    
    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)

# ================================
# ▶️ RUN BOT
# ================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
