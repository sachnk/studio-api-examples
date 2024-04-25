import logging
import math
import random

from polygon.websocket.models import EquityQuote
from common import BaseEngine
from common.models import Order, EngineConfig


class Engine(BaseEngine):
    def __init__(self, config: EngineConfig, min_edge: float, num_levels: int):
        super().__init__(config)
        self.min_edge = min_edge
        self.num_levels = num_levels
        self.theo: float = math.nan
        self.dirty = False

        if self.min_edge < 0:
            raise ValueError("min_edge must be greater than 0")

        if self.min_edge < self.config.min_tick:
            raise ValueError("min_tick must be greater than min_edge")

    def on_order_update(self, order: Order) -> None:
        super().on_order_update(order)
        self.dirty = True

    def on_quote_update(self, quote: EquityQuote) -> None:
        super().on_quote_update(quote)

        theo = (quote.bid_price + quote.ask_price) / 2.0
        if math.fabs(theo - self.theo) < 0.01:
            return

        self.theo = theo
        self.dirty = True

    def on_timer(self) -> None:
        if not self.dirty:
            return

        if self.eval():
            self.dirty = False

    def eval(self) -> bool:
        if not self.ready:
            return False

        logging.info("---- begin eval: theo = %.2f", self.theo)

        if math.isnan(self.theo):
            logging.info("no theo; cancelling all orders")
            self.cancel_all_orders()
            return True

        # cancel orders with insufficient edge
        for order in self.open_orders.values():
            price = float(order.price)
            edge = (
                math.fabs(self.theo - price)
                if order.side == "buy"
                else math.fabs(price - self.theo)
            )
            if edge < self.config.min_edge:
                logging.info(
                    "%s @ %.2f, edge=%.3f, cancelling...", order.side, price, edge
                )
                self.cancel_order(order)
            else:
                logging.info("%s @ %.2f, edge=%.3f", order.side, price, edge)

        # fill in missing levels
        price = (
            float(self.open_buys[-1].price) - self.config.min_tick
            if len(self.open_buys) > 0
            else self.theo - self.config.min_edge
        )
        for i in range(self.num_levels - len(self.open_buys)):
            if price < self.config.min_tick:
                break
            size = random.randint(self.config.min_size, self.config.max_size)
            self.submit_order("buy", size, self.to_tick(price))
            price -= self.config.min_tick

        price = (
            float(self.open_sells[-1].price) - self.config.min_tick
            if len(self.open_sells) > 0
            else self.theo + self.config.min_edge
        )
        for i in range(self.num_levels - len(self.open_sells)):
            size = random.randint(self.config.min_size, self.config.max_size)
            self.submit_order("sell", size, self.to_tick(price))
            price += self.config.min_tick

        logging.info("---- end eval: theo = %.2f", self.theo)
        return True
