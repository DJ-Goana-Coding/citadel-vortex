import os
import asyncio
import ccxt.pro as ccxt
import pandas as pd
import pandas_ta as ta
import requests
from fastapi import FastAPI
import uvicorn
from datetime import datetime

# --- CONFIGURATION (ENV VARS) ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
HUB_URL = os.getenv("HUB_URL")
HUB_TOKEN = os.getenv("CITADEL_SECRET")
# SYMBOL_LIST should be comma-separated: "SOL/USDT,BTC/USDT"
SYMBOLS = os.getenv("SYMBOL_LIST", "SOL/USDT").split(",")

app = FastAPI()
exchange = ccxt.binance({
    'apiKey': API_KEY, 'secret': API_SECRET,
    'enableRateLimit': True, 'options': {'defaultType': 'future'}
})

class PhoenixVortex:
    def __init__(self):
        self.active_trades = {}

    async def vault_deposit(self, amount):
        """Sends 30% Iron Ratchet cut to District 01 Hub"""
        try:
            headers = {"x-citadel-token": HUB_TOKEN}
            payload = {"amount": float(amount), "source": "Vortex_v2", "signature": "G04NNA_RATCHET"}
            requests.post(f"{HUB_URL}/vault/deposit", json=payload, headers=headers, timeout=5)
            print(f"✅ VAULTED: ${amount:.2f}")
        except:
            print("❌ HUB_LINK_FRACTURED")

    async def scan_market(self, symbol):
        try:
            ohlcv = await exchange.fetch_ohlcv(symbol, '15m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
            
            # Indicators
            df['EMA50'] = df.ta.ema(length=50)
            df['ADX'] = df.ta.adx(length=14)['ADX_14']
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Entry: Price > EMA50 AND ADX Strength > 25 AND Breakout
            if not self.active_trades.get(symbol) and last['c'] > last['EMA50'] and last['ADX'] > 25:
                if last['c'] > prev['h']:
                    print(f"🔥 SIGNAL: {symbol} Momentum Detected.")
                    # Logic for creating order goes here
                    self.active_trades[symbol] = True 
        except Exception as e:
            print(f"Scanner Error ({symbol}): {e}")

    async def engine_loop(self):
        print(f"🚀 VORTEX ONLINE. HUNTING: {SYMBOLS}")
        while True:
            for symbol in SYMBOLS:
                await self.scan_market(symbol)
            await asyncio.sleep(20)

vortex = PhoenixVortex()

@app.on_event("startup")
async def start_vortex():
    asyncio.create_task(vortex.engine_loop())

@app.get("/healthz")
def health():
    return {"status": "Vortex Spinning", "symbols": SYMBOLS}

if __name__ == "__main__":
    # Render uses port 10000 by default for web services
    uvicorn.run(app, host="0.0.0.0", port=10000)
