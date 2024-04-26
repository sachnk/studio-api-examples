# Studio API Examples

This project contains examples of using Clear Street Studio's [API](https://docs.clearstreet.io/studio). These examples are for illustrative purposes only, and not intended for production use.

The strategies here are toy examples.

## Prequisites 

You need at least python 3.12 and poetry 1.8.2 to run the examples. In addition, for market-data, you need an API key from [polygon.io](https://polygon.io).

## Maker Usage

```
$ poetry install
$ cd maker-example
$ poetry run python3 app.py AAPL --url api.clearstreet.io/studio --account <your-account> --polygon-api-key <polygon-api-key> --auth <studio-access-token>
```

This will launch a quoting engine for `AAPL`. It will maintain 5 price-levels on both buy/sell sides.

## Taker Example

```
$ poetry install
$ cd taker-example
$ poetry run python3 app.py MSFT NVDA --url api.clearstreet.io/studio --account <your-account> --polygon-api-key <polygon-api-key> --auth <studio-access-token>
```

This will launch a taker engine that looks triggers IOC orders on `MSFT` based on the exponential moving-average of `NVDA` 1-second bars. If the EMA on `NVDA`, linearly priced to `MSFT`, exceeds `MSFT`'s current BBO, the engine will take liquidity.