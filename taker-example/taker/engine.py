import logging
import ta
import pandas as pd

from typing import Dict
from polygon.websocket.models import EquityAgg, EquityQuote
from common import BaseEngine
from common.models import Order, EngineConfig

MIN_BARS = 32

def midpt(quote: EquityQuote) -> float:
    return (quote.ask_price + quote.bid_price) / 2.0

class Engine(BaseEngine):
    def __init__(self, config: EngineConfig, trigger_symbol: str, min_edge: float):
        super().__init__(config)
        self.symbol = self.config.symbol
        self.trigger_symbol = trigger_symbol
        self.min_edge = min_edge
        self.df = pd.DataFrame(columns=["timestamp", "symbol", "open", "high", "close"])

    def on_quote_update(self, quote: EquityQuote) -> None:
        super().on_quote_update(quote)
        if quote.symbol == self.symbol:
            self.eval()

    def on_agg_sec_update(self, agg: EquityAgg) -> None:
        super().on_agg_sec_update(agg)
        self.df = self.df._append(
            {
                "timestamp": agg.end_timestamp,
                "symbol": agg.symbol,
                "open": agg.open,
                "high": agg.high,
                "low": agg.low,
                "close": agg.close,
            },
            ignore_index=True,
        )

        self.eval()
    
    def eval(self):
        if not self.ready:
            return

        quote = self.quotes[self.symbol]
        if quote is None:
            return
        
        trigger_quote =  self.quotes[self.trigger_symbol]
        if trigger_quote is None:
            return
        
        df = self.df[self.df["symbol"] == self.trigger_symbol]
        if len(df) < MIN_BARS:
            return
        
        if len(self.open_orders) > 0:
            return

        mid = midpt(quote)
        trigger_mid = midpt(trigger_quote)
        trigger_ema = ta.trend.EMAIndicator(close=df['close'], window=15, fillna=False).ema_indicator().iloc[-1]

        theo = (trigger_ema * mid) / trigger_mid
        if theo > quote.ask_price:
            edge = theo - quote.ask_price
            logging.info("%s_mid=%.2f, %s_mid=%.2f, %s_ema=%.2f, theo=%.3f, edge=%.2f", self.symbol, mid, self.trigger_symbol, trigger_mid, self.trigger_symbol, trigger_ema, theo, edge)
            if edge > self.min_edge:
                self.submit_order("buy", 1, quote.ask_price, "ioc")
        elif theo < quote.bid_price:
            edge =  quote.bid_price - theo
            logging.info("%s_mid=%.2f, %s_mid=%.2f, %s_ema=%.2f, theo=%.3f, edge=%.2f", self.symbol, mid, self.trigger_symbol, trigger_mid, self.trigger_symbol, trigger_ema, theo, edge)
            if edge > self.min_edge:
                self.submit_order("sell", 1, quote.bid_price, "ioc")

