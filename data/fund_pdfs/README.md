# Fund Fact Sheet PDFs — Upload Guide

Place your downloaded fund fact sheet PDFs in the appropriate subfolder below.

## Folder Structure

```
data/fund_pdfs/
├── equity/        ← Large Cap, Mid Cap, Small Cap, Flexi Cap, Multi Cap
├── debt/          ← Low Duration, Bond, Short Duration, FMPs
├── hybrid/        ← Balanced Advantage, Conservative Hybrid, Aggressive Hybrid
├── index/         ← Nifty 50, Sensex, Nifty Next 50 Index Funds
├── liquid/        ← Liquid Funds, Overnight Funds, Savings Funds
└── others/        ← ELSS, Sectoral, Thematic, or any others
```

## Suggested Downloads (Matching Arjun's Portfolio)

| Fund Name | Category | Download From |
|-----------|----------|---------------|
| SBI Bluechip Fund | equity | sbimf.com |
| ICICI Prudential Technology Fund | equity | icicipruamc.com |
| Axis Midcap Fund | equity | axismf.com |
| HDFC Sensex Index Fund | index | hdfcfund.com |
| Motilal Oswal Multicap Fund | equity | motilaloswalmf.com |
| HDFC Low Duration Fund | debt | hdfcfund.com |
| SBI Savings Fund | liquid | sbimf.com |
| Aditya Birla Sun Life Savings Fund | liquid | adityabirlacapital.com |
| ICICI Prudential Liquid Fund | liquid | icicipruamc.com |
| UTI Nifty 50 Index Fund | index | utimf.com |
| Parag Parikh Flexi Cap Fund | equity | ppfas.com |

## How to Download

1. Go to the AMC website (e.g., hdfcfund.com)
2. Search for the fund name
3. Look for **"Fund Fact Sheet"** or **"Monthly Factsheet"** download link
4. Download the PDF and drop it in the correct subfolder above

> **Tip**: The ingestion pipeline will recursively scan all subfolders, so even if you put a PDF in the wrong folder, it will still be picked up.
