import logging
import requests
from typing import Dict, List, Union
from polygon.websocket.models import EquityQuote, EquityAgg
from .models import Order, Trade, Position, EngineConfig


class BaseEngine:
    def __init__(self, config: EngineConfig):
        self.config = config
        self.position: int = 0
        self.open_orders: Dict[str, Order] = {}
        self.submitted_orders: List[str] = []
        self.ready = False
        self.num_rejects: int = 0
        self.quotes: Dict[str, EquityQuote] = {}
        self.agg_sec: Dict[str, EquityAgg] = {}
        self.agg_min: Dict[str, EquityAgg] = {}
        self.config.validate()
        self.cancel_all_orders()

    # invoked when all replayed data has been received
    def on_ready(self):
        self.ready = True
        logging.info(
            "%s engine ready, position = %d", self.config.symbol, self.position
        )

    # invoked when an order state updates from studio
    def on_order_update(self, timestamp: int, order: Order) -> None:
        if not order.order_id in self.submitted_orders:
            return

        if order.symbol != self.config.symbol:
            return

        if order.state == "rejected":
            logging.warn("Order %s rejected: %s", order.order_id, order.text)
            self.num_rejects += 1
            if self.num_rejects >= self.config.max_rejects:
                raise RuntimeError("Too many rejects")

        if order.state != "open":
            self.open_orders.pop(order.order_id, None)
        else:
            self.open_orders[order.order_id] = order

    # invoked when a trade occurs against an open order from studio
    def on_trade_notice(self, timestamp: int, trade: Trade) -> None:
        if trade.symbol != self.config.symbol:
            return

        logging.info(
            "%s trade: %s %s @ %s",
            self.config.symbol,
            trade.side,
            trade.quantity,
            trade.price,
        )

    # invoked when a position update occurs from studio
    def on_position_update(self, timestamp: int, position: Position) -> None:
        if position.symbol != self.config.symbol:
            return

        self.position = int(position.quantity)
        logging.info("%s position: %s", self.config.symbol, self.position)

    # invoked when a quote update occurs from polygon
    def on_quote_update(self, quote: EquityQuote) -> None:
        self.quotes[quote.symbol] = quote

    # invoked when a second aggregate update occurs from polygon
    def on_agg_sec_update(self, agg: EquityAgg) -> None:
        self.agg_sec[agg.symbol] = agg

    # invoked when a minute aggregate update occurs from polygon
    def on_agg_min_update(self, agg: EquityAgg) -> None:
        self.agg_min[agg.symbol] = agg

    def on_timer(self) -> None:
        pass

    def submit_order(self, side: str, quantity: int, price: str, tif: str) -> str:
        logging.info("Submitting order: %s %d @ %s...", side, quantity, price)

        if self.position > 0:
            if side == "buy":
                if self.position + quantity > self.config.max_position:
                    logging.info("Cannot submit order; max position will breach")
                    return
            else:
                quantity = min(quantity, self.position)
        elif self.position < 0:
            if side == "sell":
                if self.position - quantity < -self.config.max_position:
                    logging.info("Cannot submit order; max position will breach")
                    return
            else:
                quantity = min(quantity, -self.position)

        url = f"{self.config.url}/v2/accounts/{self.config.account}/orders"
        headers = {"Authorization": f"Bearer {self.config.auth}"}
        response = requests.post(
            url,
            headers=headers,
            json={
                "symbol": self.config.symbol,
                "side": side,
                "quantity": str(quantity),
                "price": price,
                "order_type": "limit",
                "time_in_force": tif,
                "strategy_type": "sor",
            },
        )
        if response.status_code != 201:
            raise RuntimeError(
                f"Failed submitting order: {response.status_code}, {response.text}"
            )

        order_id = response.json()["order_id"]
        self.submitted_orders.append(order_id)
        logging.info("Submitted order-id %s", order_id)

        return order_id

    def cancel_order(self, order: Order) -> None:
        url = f"{self.config.url}/v2/accounts/{self.config.account}/orders/{order.order_id}"
        headers = {"Authorization": f"Bearer {self.config.auth}"}
        response = requests.delete(url, headers=headers)
        if response.status_code != 201:
            raise RuntimeError(
                f"Failed cancelling order: {response.status_code}, {response.text}"
            )

        logging.info("Cancelled order: %s", order.order_id)

    def cancel_all_orders(self) -> None:
        url = f"{self.config.url}/v2/accounts/{self.config.account}/orders"
        headers = {"Authorization": f"Bearer {self.config.auth}"}
        response = requests.delete(url, headers=headers)
        if response.status_code != 201:
            raise RuntimeError(
                f"Failed cancelling all orders: {response.status_code}, {response.text}"
            )

        logging.info("Cancelled all orders")

    def to_tick(self, price: float) -> str:
        val = round(price / self.config.min_tick) * self.config.min_tick
        return "{:.2f}".format(val)
