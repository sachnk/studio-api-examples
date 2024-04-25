import sys

sys.path.append("..")

import argparse
import asyncio
import logging
import os

from maker.engine import Engine
from common.models import EngineConfig
from common import ws_polgon_task, ws_studio_task, timer_task


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
    engine = Engine(config=config, min_edge=args.min_edge, num_levels=args.levels)

    task1 = asyncio.create_task(
        ws_polgon_task(
            engine=engine, symbols=[args.symbol], api_key=args.polygon_api_key
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
        description="A sample maker bot for using Clear Street Studio's APIs"
    )
    parser.add_argument("symbol", type=str, help="The symbol to quote")
    parser.add_argument(
        "--levels", type=int, help="Number of levels to quote", default=5
    )
    parser.add_argument(
        "--max-position",
        type=int,
        help="Maximum position to hold, long or short",
        default=100,
    )
    parser.add_argument(
        "--min-size", type=int, help="Minimum size for orders", default=1
    )
    parser.add_argument(
        "--max-size", type=int, help="Maximum size for orders", default=10
    )
    parser.add_argument(
        "--min-edge", type=float, help="Minimum edge around theo", default=0.50
    )
    parser.add_argument(
        "--min-tick", type=float, help="Minimum price tick", default=0.05
    )

    url = os.environ.get("STUDIO_URL", "https://api.co.clearstreet.io/studio")
    parser.add_argument(
        "--url",
        type=str,
        help="Base URL for Studio API",
        required=url is None,
        default=url,
    )

    auth = os.environ.get("STUDIO_AUTH")
    parser.add_argument(
        "--auth",
        type=str,
        help="Studio API access-token",
        required=auth is None,
        default=auth,
    )

    account = os.environ.get("STUDIO_ACCOUNT")
    parser.add_argument(
        "--account",
        type=str,
        help="Studio account",
        required=account is None,
        default=account,
    )

    polygon = os.environ.get("POLYGON_API_KEY")
    parser.add_argument(
        "--polygon-api-key",
        type=str,
        help="Polygon API key",
        required=polygon is None,
        default=polygon,
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
