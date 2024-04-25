import json
import asyncio
import websockets
import logging

from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage, EquityQuote, EquityAgg
from polygon.websocket.models.common import Feed
from .models import Order, Trade, Position
from .base_engine import BaseEngine
from typing import List

async def polygon_processor(engine: BaseEngine, msgs: List[WebSocketMessage]):
    for msg in msgs:
        if msg.event_type == "Q":
            msg: EquityQuote = msg
            engine.on_quote_update(msg)
        elif msg.event_type == "A":
            msg: EquityAgg = msg
            engine.on_agg_sec_update(msg)
        elif msg.event_type == "AM":
            msg: EquityAgg = msg
            engine.on_agg_min_update(msg)

async def ws_polgon_task(engine: BaseEngine, symbols: List[str], api_key: str):
    subscriptions = [f"Q.{symbol}" for symbol in symbols] + [f"A.{symbol}" for symbol in symbols] + [f"AM.{symbol}" for symbol in symbols]
    ws = WebSocketClient(api_key=api_key, feed=Feed.PolyFeed, subscriptions=subscriptions, verbose=True)
    await ws.connect(processor=lambda msgs: polygon_processor(engine, msgs))

async def ws_studio_task(engine: BaseEngine, url: str, auth: str, account: str):
    msg = {
        "authorization": auth,
        "payload": {
            "type": "subscribe-activity",
            "account_id": account
        }
    }
    url = url.replace("http://", "ws://").replace("https://", "wss://")
    url = f"{url}/v2/ws"
    logging.info("connect: %s", url)

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps(msg))
        logging.info("studio websocket connected")
        while True:
            msg = await ws.recv()
            payload = json.loads(msg)["payload"]
            if payload["type"] == "order-update":
                engine.on_order_update(Order(**payload["data"]))
            elif payload["type"] == "trade-notice":
                engine.on_trade_notice(Trade(**payload["data"]))
            elif payload["type"] == "position-update":
                engine.on_position_update(Position(**payload["data"]))
            elif payload["type"] == "replay-complete":
                engine.on_ready()

async def timer_task(engine: BaseEngine):
    while True:
        engine.on_timer()
        await asyncio.sleep(1)