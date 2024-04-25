import sys

sys.path.append("..")

import argparse
import asyncio
import logging
import os

from taker.engine import Engine
from common.models import EngineConfig
from common import add_common_args, ws_polgon_task, ws_studio_task, timer_task


async def main(args):
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )

    config = EngineConfig(
        url=args.url,
        auth=args.auth,
        account=args.account,
        symbol=args.symbol,
        max_position=args.max_position,
        min_tick=args.min_tick,
        min_size=args.min_size,
        max_size=args.max_size,
        max_rejects=4,
    )
    engine = Engine(config=config, trigger_symbol=args.trigger_symbol, min_edge=args.min_edge)

    task1 = asyncio.create_task(
        ws_polgon_task(
            engine=engine,
            symbols=[args.symbol, args.trigger_symbol],
            api_key=args.polygon_api_key,
        )
    )
    task2 = asyncio.create_task(
        ws_studio_task(
            engine=engine, url=args.url, auth=args.auth, account=args.account
        )
    )
    task3 = asyncio.create_task(timer_task(engine=engine))
    await asyncio.gather(task1, task2, task3)


def parse_args():
    parser = argparse.ArgumentParser(
        description="An example taker bot using Clear Street Studio's APIs"
    )
    parser.add_argument("symbol", type=str, help="The symbol to trade")
    parser.add_argument("trigger_symbol", type=str, help="The symbol to trigger off of")
    parser.add_argument("--min-edge", type=float, help="Minimum edge", default=1.00)
    add_common_args(parser)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
