from typing import Optional
from dataclasses import dataclass


@dataclass
class Order:
    created_at: int
    updated_at: int
    order_id: str
    version: int
    account_id: str
    state: str
    status: str
    symbol: str
    order_type: str
    side: str
    quantity: str
    time_in_force: str
    average_price: str
    filled_quantity: str
    price: Optional[str] = None
    strategy_type: Optional[str] = None
    order_update_reason: Optional[str] = None
    reference_id: Optional[str] = None
    text: Optional[str] = None


@dataclass
class Trade:
    created_at: int
    account_id: str
    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: str
    price: str


@dataclass
class Position:
    account_id: str
    symbol: str
    quantity: str


@dataclass
class EngineConfig:
    url: str
    auth: str
    account: str
    symbol: str
    max_position: int
    min_size: int
    max_size: int
    min_tick: float
    max_rejects: int

    def validate(self):
        if self.min_tick < 0:
            raise ValueError("min_tick must be greater than 0")
        if self.max_position < 0:
            raise ValueError("min_position must be greater than 0")
