"""
💼 BROKER API INTEGRATION MODULE
Handles connections to trading platforms
"""

import os
import json
from abc import ABC, abstractmethod
import requests
import time

class BrokerAPI(ABC):
    """Abstract base class for broker integrations"""
    
    @abstractmethod
    def connect(self):
        """Establish connection to broker"""
        pass
    
    @abstractmethod
    def execute_trade(self, signal):
        """Execute a trade based on signal"""
        pass
    
    @abstractmethod
    def get_account_balance(self):
        """Get current account balance"""
        pass


class CTraderIntegration(BrokerAPI):
    """cTrader (Shift C Trader) integration via Open API"""
    
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # cTrader API credentials from environment
        self.client_id = os.getenv('CTRADER_CLIENT_ID')
        self.client_secret = os.getenv('CTRADER_CLIENT_SECRET')
        self.access_token = os.getenv('CTRADER_ACCESS_TOKEN')
        self.account_id = self.config["broker"]["account_id"]
        
        # API endpoints
        self.base_url = "https://openapi.ctrader.com"
        self.connection = None
    
    def connect(self):
        """Connect to cTrader API"""
        try:
            print("🔌 Connecting to cTrader API...")
            
            # Test connection by getting account info
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/v1/accounts/{self.account_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ cTrader API connected")
                self.connection = True
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def execute_trade(self, signal):
        """
        Execute trade on cTrader
        
        Args:
            signal (dict): Parsed signal data
        """
        if not signal["valid"]:
            print("❌ Cannot execute invalid signal")
            return False
        
        if not self.connection:
            print("❌ Not connected to cTrader")
            return False
        
        try:
            print(f"\n🔄 Executing {signal['action']} trade on cTrader...")
            
            # Calculate lot size
            volume = self.calculate_lot_size(signal["risk_percent"])
            
            # Prepare order payload
            order_payload = {
                "accountId": self.account_id,
                "symbolName": signal["symbol"] or "XAUUSD",
                "tradeSide": "BUY" if signal["action"] == "BUY" else "SELL",
                "volume": volume,  # in units (1 lot = 100,000 units for Forex)
                "stopLoss": signal["stop_loss"],
                "takeProfit": signal["take_profit"],
                "orderType": "MARKET",
                "label": "TelegramBot"
            }
            
            print(f"📊 Trade Parameters: {order_payload}")
            
            # Execute order via cTrader API
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/v1/orders",
                headers=headers,
                json=order_payload
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ Trade executed successfully")
                print(f"📋 Order ID: {result.get('orderId', 'N/A')}")
                return True
            else:
                print(f"❌ Trade execution failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
        except Exception as e:
            print(f"❌ Trade execution error: {e}")
            return False
    
    def calculate_lot_size(self, risk_percent):
        """
        Calculate lot size based on account balance and risk %
        
        Args:
            risk_percent (float): Risk percentage
            
        Returns:
            int: Volume in units (cTrader uses units, not lots)
        """
        balance = self.get_account_balance()
        risk_amount = balance * (risk_percent / 100)
        
        # Basic calculation (customize based on your risk model)
        # For Forex: 1 lot = 100,000 units
        # For Gold (XAUUSD): 1 lot = 100 units
        
        # Example: Risk $100 on XAUUSD with $10 per pip
        # Volume = risk_amount / pip_value
        
        volume = int(risk_amount * 10)  # Simplified - adjust formula
        volume = max(volume, 1000)  # Minimum 0.01 lot (1000 units)
        
        print(f"💰 Calculated volume: {volume} units ({volume/100000:.2f} lots)")
        return volume
    
    def get_account_balance(self):
        """Get account balance from cTrader"""
        try:
            if not self.connection:
                return 10000.0  # Default test balance
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/v1/accounts/{self.account_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                balance = data.get('balance', 0)
                print(f"💰 Account balance: ${balance:.2f}")
                return balance
            else:
                print("⚠️ Could not fetch balance, using default")
                return 10000.0
                
        except Exception as e:
            print(f"⚠️ Balance fetch error: {e}")
            return 10000.0
    
    def close_position(self, position_id):
        """Close an open position"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.delete(
                f"{self.base_url}/v1/positions/{position_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"✅ Position {position_id} closed")
                return True
            else:
                print(f"❌ Failed to close position: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Close position error: {e}")
            return False


class MetaAPIIntegration(BrokerAPI):
    """MetaTrader integration via MetaAPI (kept for reference)"""
    
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.api_token = os.getenv('METAAPI_TOKEN')
        self.account_id = self.config["broker"]["account_id"]
        self.connection = None
    
    def connect(self):
        print("🔌 MetaAPI - use cTrader instead")
        return False
    
    def execute_trade(self, signal):
        print("⚠️ MetaAPI not active - use cTrader")
        return False
    
    def get_account_balance(self):
        return 0.0


def get_broker_api(broker_name="ctrader"):
    """
    Factory function to get broker API instance
    
    Args:
        broker_name (str): Name of broker
        
    Returns:
        BrokerAPI: Broker API instance
    """
    brokers = {
        "ctrader": CTraderIntegration,
        "shiftc": CTraderIntegration,  # Alias
        "metaapi": MetaAPIIntegration
    }
    
    broker_class = brokers.get(broker_name.lower())
    if broker_class:
        return broker_class()
    else:
        raise ValueError(f"❌ Unsupported broker: {broker_name}")
