# quoter

Your standard issue quote-bot. Use this to test our Studio EMS API.

## Usage

You need two API keys for to use this app: a [Studio API access-token](https://docs.clearstreet.io/studio/docs/authentication-1), and a Polygon PolyFeed API key.

To quote SPY in dev with `0.50` minimum difference vs. mid-point:
```
python3 app.py --symbol SPY --levels 5 --min-edge 0.50 --min-tick 0.05 --url api.co.clearstreet.io/studio --account 102396 --polygon-api-key <polygon-api-key> --auth <studio-access-token>
```