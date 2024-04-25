import os
from argparse import ArgumentParser


def add_common_args(parser: ArgumentParser) -> None:
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
