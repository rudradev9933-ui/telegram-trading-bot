"""
📊 SIGNAL PARSER MODULE
Extracts trading signals from Gemini AI response
"""

import re
import json

class SignalParser:
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
    
    def parse_gemini_response(self, text):
        """
        Parse Gemini AI response and extract trading signal
        
        Args:
            text (str): Gemini AI response text
            
        Returns:
            dict: Parsed signal data
        """
        print(f"\n📝 Gemini Response:\n{text}\n")
        
        signal = {
            "valid": False,
            "action": None,
            "risk_percent": self.config["bot_settings"]["default_risk_percent"],
            "stop_loss": None,
            "take_profit": None,
            "symbol": None
        }
        
        text_upper = text.upper()
        
        # Extract Action
        if "BUY" in text_upper:
            signal["action"] = "BUY"
        elif "SELL" in text_upper:
            signal["action"] = "SELL"
        
        # Extract Symbol
        symbol_match = re.search(r"(?:symbol|pair|asset)[:\s]*([A-Z]{3,10})", text, re.I)
        if symbol_match:
            signal["symbol"] = symbol_match.group(1).upper()
        
        # Extract Risk %
        risk_match = re.search(r"risk[:\s]*(\d+\.?\d*)%?", text, re.I)
        if risk_match:
            risk = float(risk_match.group(1))
            max_risk = self.config["bot_settings"]["max_risk_percent"]
            signal["risk_percent"] = min(risk, max_risk)
        
        # Extract Stop Loss
        sl_match = re.search(r"(?:sl|stop\s*loss)[:\s]*(\d+\.?\d+)", text, re.I)
        if sl_match:
            signal["stop_loss"] = float(sl_match.group(1))
        
        # Extract Take Profit
        tp_match = re.search(r"(?:tp|take\s*profit)[:\s]*(\d+\.?\d+)", text, re.I)
        if tp_match:
            signal["take_profit"] = float(tp_match.group(1))
        
        # Validate signal
        signal["valid"] = self.validate_signal(signal)
        
        return signal
    
    def validate_signal(self, signal):
        """
        Validate if signal has minimum required data
        
        Args:
            signal (dict): Signal data
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["action", "stop_loss", "take_profit"]
        
        for field in required_fields:
            if signal[field] is None:
                print(f"❌ Missing: {field}")
                return False
        
        # Check risk-reward ratio
        if signal["action"] and signal["stop_loss"] and signal["take_profit"]:
            # Calculate R:R (simplified)
            min_rr = self.config["risk_management"]["min_risk_reward_ratio"]
            # Add your R:R calculation logic here
            
        return True
    
    def format_signal_output(self, signal):
        """Pretty print signal data"""
        if signal["valid"]:
            return f"""
✅ VALID SIGNAL DETECTED
━━━━━━━━━━━━━━━━━━━━
📊 Action     : {signal['action']}
🎯 Symbol     : {signal['symbol'] or 'N/A'}
💰 Risk %     : {signal['risk_percent']}%
🛑 Stop Loss  : {signal['stop_loss']}
🎯 Take Profit: {signal['take_profit']}
━━━━━━━━━━━━━━━━━━━━
            """
        else:
            return "❌ Invalid signal - missing required data"
