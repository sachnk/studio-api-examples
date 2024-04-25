import logging
import requests
from typing import Dict, List
from polygon.websocket.models import EquityQuote, EquityAgg
from .models import Order, Trade, Position, EngineConfig

class BaseEngine:
    def __init__(self, config: EngineConfig):
        self.config = config
        self.position: int = 0
        self.open_orders: Dict[str, Order] = {}
        self.open_buys: List[Order] = []
        self.open_sells: List[Order] = []
        self.submitted_orders: List[str] = []
        self.ready = False
        self.num_rejects: int = 0
        self.quote: EquityQuote = None
        self.agg_sec: EquityAgg = None
        self.agg_min: EquityAgg = None
        self.config.validate()
        self.cancel_all_orders()

    # invoked when all replayed data has been received
    def on_ready(self):
        self.ready = True
        logging.info("%s engine ready, position = %d", self.config.symbol, self.position)

    # invoked when an order state updates from studio
    def on_order_update(self, order: Order) -> None:
        if not order.order_id in self.submitted_orders:
            return

        if order.symbol != self.config.symbol:
            return

        if order.state == "rejected":
            logging.warn("Order %s rejected: %s", order.order_id, order.text)
            self.num_rejects += 1
            if (self.num_rejects >= self.config.max_rejects):
                raise RuntimeError("Too many rejects")

        if order.state != "open":
            removed = self.open_orders.pop(order.order_id, None)
            if removed is not None:
                self.open_buys.remove(removed) if removed.side == "buy" else self.open_sells.remove(removed)
        else:
            self.open_orders[order.order_id] = order
            if order.side == "buy":
                self.open_buys.append(order)
                self.open_buys.sort(key=lambda x: float(x.price), reverse=True)
            else:
                self.open_sells.append(order)
                self.open_sells.sort(key=lambda x: float(x.price))

    # invoked when a trade occurs against an open order from studio
    def on_trade_notice(self, trade: Trade) -> None:
        if trade.symbol != self.config.symbol:
            return

        logging.info("%s trade: %s %s @ %s", self.config.symbol, trade.side, trade.quantity, trade.price)

    # invoked when a position update occurs from studio
    def on_position_update(self, position: Position) -> None:
        if position.symbol != self.config.symbol:
            return

        self.position = int(position.quantity)
        logging.info("%s position: %s", self.config.symbol, self.position)

    # invoked when a quote update occurs from polygon
    def on_quote_update(self, quote: EquityQuote) -> None:
        if quote.symbol != self.config.symbol:
            return

        self.quote = quote

    # invoked when a second aggregate update occurs from polygon
    def on_agg_sec_update(self, agg: EquityAgg) -> None:
        if agg.symbol != self.config.symbol:
            return
        
        self.agg_sec = agg
    
    # invoked when a minute aggregate update occurs from polygon
    def on_agg_min_update(self, agg: EquityAgg) -> None:
        if agg.symbol != self.config.symbol:
            return
        
        self.agg_min = agg

    def submit_order(self, side: str, quantity: int, price: str) -> None:
        logging.info("Submitting order: %s %d @ %s...", side, quantity, price)

        if side == "buy" and abs(self.position + quantity) > self.config.max_position:
            logging.info("Cannot submit order; max position will breach")
            return
        
        if side == "sell" and abs(self.position - quantity) > self.config.max_position:
            logging.info("Cannot submit order; max position will breach")
            return

        url = f"{self.config.url}/v2/accounts/{self.config.account}/orders"
        headers = {"Authorization": f"Bearer {self.config.auth}"}
        response = requests.post(url, headers=headers, json={
            "symbol": self.config.symbol,
            "side": side,
            "quantity": str(quantity),
            "price": price,
            "order_type": "limit",
            "time_in_force": "day",
            "strategy_type": "sor"
        })
        if (response.status_code != 201):
            raise RuntimeError(f"Failed submitting order: {response.status_code}, {response.text}")

        order_id = response.json()["order_id"]
        self.submitted_orders.append(order_id)
        logging.info("Submitted order-id %s", order_id)

    def cancel_order(self, order: Order) -> None:
        url = f"{self.config.url}/v2/accounts/{self.config.account}/orders/{order.order_id}"
        headers = {"Authorization": f"Bearer {self.config.auth}"}
        response = requests.delete(url, headers=headers)
        if (response.status_code != 201):
            raise RuntimeError(f"Failed cancelling order: {response.status_code}, {response.text}")

        logging.info("Cancelled order: %s", order.order_id)

    def cancel_all_orders(self) -> None:
        url = f"{self.config.url}/v2/accounts/{self.config.account}/orders"
        headers = {"Authorization": f"Bearer {self.config.auth}"}
        response = requests.delete(url, headers=headers)
        if (response.status_code != 201):
            raise RuntimeError(f"Failed cancelling all orders: {response.status_code}, {response.text}")

        logging.info("Cancelled all orders")

    def to_tick(self, price: float) -> str:
        val = round(price / self.config.min_tick) * self.config.min_tick
        return "{:.2f}".format(val)
