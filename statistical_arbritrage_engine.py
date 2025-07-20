from sklearn.linear_model import LinearRegression
from statsmodels.tsa.stattools import adfuller
import numpy as np
import yfinance as yf 
import pandas as pd 
import matplotlib.pyplot as plt 

#------CONFIGURATION------
TICKERS = ["PG", "XLP"]
START_DATE = "2020-07-01"
END_DATE = "2025-07-01"
WINDOW = 90
INITIAL_CASH = 100000
TAKE_PROFIT = 0.05
STOP_LOSS = -0.05


#------DATA DOWNLOAD------
def data_download(tickers, start, end):
	raw_data = yf.download(tickers, start=start, end=end)
	data = raw_data["Close"][tickers]
	#drop the rows with missing data
	data.dropna(inplace=True)
	return data


# b is hedge ratio that can be calculated using linear regression
#------ROLLING HEDGE RATIO------
def compute_rolling_hedge_ratios(data, window):
	hedge_ratios = []
	alphas = []
	for i in range(len(data)):
		if i < window:
			hedge_ratios.append(np.nan)
			alphas.append(np.nan)
		else:
			X = data['PG'].iloc[i-window:i].values.reshape(-1,1)
			y = data['XLP'].iloc[i-window:i].values.reshape(-1,1)
			model = LinearRegression()
			model.fit(X,y)
			hedge_ratios.append(model.coef_[0][0])
			alphas.append(model.intercept_[0])

	data['Hedge Ratio'] = hedge_ratios

	data['Alpha'] = alphas

	return data.dropna()

#---------- Spread & Stationarity ----------
def calculate_spread(data):
	spread = data['XLP'] - (data['Hedge Ratio'] * data['PG'] + data['Alpha'])
	spread = spread.replace([np.inf, -np.inf], np.nan).dropna()
	data['Spread'] = spread
	return spread

def test_stationarity(spread):
	adf_result = adfuller(spread)
	print("ADF statistic: ", adf_result[0])
	print("p-value: ", adf_result[1])
	print("Critical Values: ")
	for key,value in adf_result[4].items():
		print(f"{key}: {value}")
	print("---------------------------------")

#Plotting the spread



#---------- Signal Generation ----------
def calculate_z_score(spread):
	mean = spread.mean()
	std = spread.std()
	zscore = (spread-mean)/std
	return zscore

def generate_signals(data, zscore):
	data['Z-score'] = zscore
	data['Long Signal'] = data['Z-score'] < -2
	data['Short Signal'] = data['Z-score'] > 2
	data['Exit Signal'] = (data['Z-score'].abs() < 0.5)
	return data

#Plotting the signals


# Simulating Positions and PnL
def backtest_strategy(data):
    position = 0
    in_position = False
    entry_pg = entry_xlp = 0
    positions = []

    for i in range(len(data)):
        row = data.iloc[i]
        if not in_position:
            if row['Long Signal']:
                position = 1
                entry_pg, entry_xlp = row['PG'], row['XLP']
                in_position = True
            elif row['Short Signal']:
                position = -1
                entry_pg, entry_xlp = row['PG'], row['XLP']
                in_position = True
        else:
            curr_pg, curr_xlp = row['PG'], row['XLP']
            if position == 1:
                pnl = (curr_pg / entry_pg - 1) - (curr_xlp / entry_xlp - 1)
            else:
                pnl = (curr_xlp / entry_xlp - 1) - (curr_pg / entry_pg - 1)

            if pnl >= TAKE_PROFIT or pnl <= STOP_LOSS or row['Exit Signal']:
                position = 0
                in_position = False

        positions.append(position)

    data['Position'] = positions
    data['PG Return'] = data['PG'].pct_change()
    data['XLP Return'] = data['XLP'].pct_change()
    data['Strategy Return'] = data['Position'] * (data['PG Return'] - data['XLP Return'])
    data['Cumulative Return'] = (1 + data['Strategy Return']).cumprod()
    data['Portfolio Value'] = INITIAL_CASH * data['Cumulative Return']
    return data

# ---------- Plotting ----------
def plot_price(data):
	data[["PG", "XLP"]].plot(figsize=(12, 6), title="PG vs XLP Prices")
	plt.grid(True)
	plt.show()

def plot_spread(spread):
	plt.figure(figsize=(12,6))
	plt.plot(spread)
	plt.title("Spread")
	plt.axhline(spread.mean(), color='red', linestyle="--", label="mean")
	plt.legend()
	plt.show()

def plot_zscore_signals(data):
	plt.figure(figsize=(14,6))
	plt.plot(data['Z-score'], label="Z-score", color="blue")
	plt.axhline(2, color="red", linestyle="--", label="Sell Threshold")
	plt.axhline(-2, color="green", linestyle="--", label="Buy Threshold")
	plt.axhline(0, color="black", linestyle="--")
	plt.plot(data[data['Long Signal']].index, data['Z-score'][data['Long Signal']], '^', markersize=10, color='g', label='Long')
	plt.plot(data[data['Short Signal']].index, data['Z-score'][data['Short Signal']], 'v', markersize=10, color='r', label='Short')
	plt.plot(data[data['Exit Signal']].index, data['Z-score'][data['Exit Signal']], 'o', markersize=6, color='black', label='Exit')
	plt.title("Trading Signals Based on Z-score")
	plt.legend()
	plt.grid(True)
	plt.show()

def plot_portfolio(data):
	plt.figure(figsize=(14, 6))
	plt.plot(data.index, data['Portfolio Value'], label="Portfolio Value", color='purple')
	plt.title("Backtested Portfolio Value")
	plt.xlabel("Date")
	plt.ylabel("Portfolio Value ($)")
	plt.grid(True)
	plt.legend()
	plt.show()


def main():
	data = data_download(TICKERS, START_DATE, END_DATE)
	plot_price(data)

	data = compute_rolling_hedge_ratios(data, WINDOW)
	spread = calculate_spread(data)

	plot_spread(spread)
	test_stationarity(spread)

	zscore = calculate_z_score(spread)
	data['Spread'] = spread
	data = generate_signals(data, zscore)

	plot_zscore_signals(data)
	data = backtest_strategy(data)
	plot_portfolio(data)

	final_value = data['Portfolio Value'].iloc[-1]

	total_return = (final_value / INITIAL_CASH - 1) * 100
	print(f"\nFinal Portfolio Value: ${final_value:,.2f}")
	print(f"Total Return: {total_return:.2f}%")

if __name__ == "__main__":
	main()
