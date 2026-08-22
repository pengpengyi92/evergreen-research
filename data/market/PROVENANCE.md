# Market data fixture — provenance

`spx_daily.csv` is the only data the harness needs, and it is fully public.

| Field | Value |
|---|---|
| Series | S&P 500 index (^GSPC), daily OHLCV |
| Source | Yahoo Finance chart API `query2.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=5y&interval=1d` |
| Retrieved | 2026-08-23 |
| Range | 2021-08-23 → 2026-08-21 (1255 bars) |
| SHA-256 | `5b6e7115779b8027a9b613b64ba6731c77c3dfe6c5f9019fbc8f5e9672fdb61d` |
| License | Index prices are factual market data; redistribution of OHLC quotes for research is standard practice. If you require a fully license-clean series, replace with any public OHLCV CSV with the same header (`date,open,high,low,close,volume`). |

Verify:

```bash
shasum -a 256 data/market/spx_daily.csv   # must match the SHA-256 above
```

Re-derive: the harness (`harness/market.py`) is deterministic — same CSV in,
same regimes, same scores out.
