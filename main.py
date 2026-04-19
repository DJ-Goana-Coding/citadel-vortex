import os
import asyncio
import logging
from contextlib import asynccontextmanager

import ccxt.pro as ccxt
import pandas as pd
import pandas_ta as ta
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from citadel.hub_publisher import publisher_from_env, ping_hub

logger = logging.getLogger(__name__)

# --- CONFIGURATION (ENV VARS) ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
HUB_URL = os.getenv("HUB_URL")
HUB_TOKEN = os.getenv("CITADEL_SECRET")
# SYMBOL_LIST should be comma-separated: "SOL/USDT,BTC/USDT"
SYMBOLS = os.getenv("SYMBOL_LIST", "SOL/USDT").split(",")

# Vercel HUD origin allowed to ping the scanner's health endpoints.
# Additional origins may be supplied via CORS_ALLOWED_ORIGINS (comma-separated).
DEFAULT_CORS_ORIGINS = ["https://citadel-nexus-private.vercel.app"]
_extra_origins = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
CORS_ORIGINS = list(dict.fromkeys(DEFAULT_CORS_ORIGINS + _extra_origins))

# Synapse: Vortex → mapping-and-inventory Hub publisher
hub_publisher = publisher_from_env()

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
            # Run the blocking HTTP call off the event loop.
            await asyncio.to_thread(
                requests.post,
                f"{HUB_URL}/vault/deposit",
                json=payload,
                headers=headers,
                timeout=5,
            )
            print(f"✅ VAULTED: ${amount:.2f}")
        except Exception as exc:
            # Log full detail server-side; never swallow KeyboardInterrupt/SystemExit.
            logger.warning("HUB_LINK_FRACTURED during vault_deposit: %s", exc)
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
                    # Synapse: forward the signal to the Hub for RAG awareness.
                    await hub_publisher.publish_signal(
                        symbol=symbol,
                        signal_type="momentum_breakout",
                        payload={
                            "close": float(last['c']),
                            "ema50": float(last['EMA50']),
                            "adx": float(last['ADX']),
                            "prev_high": float(prev['h']),
                            "timeframe": "15m",
                        },
                    )
        except Exception as e:
            print(f"Scanner Error ({symbol}): {e}")

    async def engine_loop(self):
        print(f"🚀 VORTEX ONLINE. HUNTING: {SYMBOLS}")
        while True:
            for symbol in SYMBOLS:
                await self.scan_market(symbol)
            await asyncio.sleep(20)


vortex = PhoenixVortex()


async def start_vortex():
    """Spawn the scanner engine loop and the hub publisher loop.

    Kept as a module-level coroutine so it can be invoked from the
    FastAPI ``lifespan`` and exercised directly by tests.
    """
    asyncio.create_task(vortex.engine_loop())
    asyncio.create_task(hub_publisher.run_forever())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_vortex()
    yield


app = FastAPI(lifespan=lifespan)

# CORS: allow the Vercel HUD (Command Face) to call health endpoints.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # Health endpoints are unauthenticated; no need to forward cookies/auth.
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/healthz")
def health():
    return {"status": "Vortex Spinning", "symbols": SYMBOLS}


@app.get("/healthz/hub")
def health_hub():
    """Verify connectivity to the central mapping-and-inventory Hub."""
    return ping_hub(HUB_URL)


if __name__ == "__main__":
    # Render uses port 10000 by default for web services
    uvicorn.run(app, host="0.0.0.0", port=10000)
