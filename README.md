# 📈 Statistical Arbitrage Engine: PG vs XLP

This project implements a **statistical arbitrage strategy** (pairs trading) using **Procter & Gamble (PG)** and the **Consumer Staples ETF (XLP)**. It identifies trading opportunities based on statistical relationships and mean reversion in price spreads.

The strategy includes:
-  ADF test for stationarity
-  Z-score threshold-based trade signals
-  Rolling hedge ratio using linear regression
-  Stop-loss and take-profit logic
-  Portfolio backtesting simulation

---

## Strategy Logic

The assumption is that PG and XLP move together over time (co-integrated). The engine:

1. Fetches historical price data using `yfinance`
2. Computes a **rolling hedge ratio** via linear regression
3. Calculates the **spread** between the two assets
4. Uses the **Z-score of the spread** to generate trading signals:
   -  Go Long PG & Short XLP if Z-score < -entry threshold
   -  Go Short PG & Long XLP if Z-score > +entry threshold
   -  Exit positions when Z-score crosses the exit threshold
5. Enforces **stop-loss** and **take-profit** for risk management
6. Simulates PnL based on position returns over time

---

##  Installation

```bash
git clone https://github.com/your-username/statistical-arbitrage-engine.git
cd statistical-arbitrage-engine
pip install -r requirements.txt
```

## Usage
```
python statistical_arbitrage_engine.py
```

## Sample Output
```
Final Portfolio Value: $101,473.77
Total Return: 1.47%
```


