import tkinter as tk
from tkinter import ttk, PhotoImage, Label
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplfinance as mpf
import pandas as pd
from binance import Client
from sklearn.linear_model import LinearRegression
from tradingview_ta import TA_Handler, Interval


def analyze_and_plot():
    # Получение значений из полей ввода
    symbol = symbol_entry.get().upper()
    interval = interval_combobox.get()

    # Анализ данных и построение графика
    try:
        client = Client()
        binance_df = client.get_historical_klines(symbol, interval)

        binance_df = [[float(i) for i in row[:6]] for row in binance_df]
        binance_df = pd.DataFrame(binance_df, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
        binance_df['Time'] = pd.to_datetime(binance_df['Time'], unit='ms')
        binance_df = binance_df.set_index('Time')

        output = TA_Handler(
            symbol=symbol,
            screener='Crypto',
            exchange='Binance',
            interval=interval
        )
        data = output.get_analysis().indicators

        tradingview_df = pd.DataFrame([data])

        features = ['RSI', 'Stoch.K', 'Stoch.D', 'CCI20', 'ADX', 'AO', 'Mom', 'MACD.macd', 'volume']
        target = 'change'

        X = tradingview_df[features]
        y = tradingview_df[target]

        model = LinearRegression()
        model.fit(X, y)

        future_data = X.iloc[0].values.reshape(1, -1)
        predicted_change = model.predict(future_data)

        future_price = binance_df['Close'].iloc[-1] + predicted_change[0]
        predict_label1 = Label(frame, text=f'Рекомендация: {output.get_analysis().summary['RECOMMENDATION']}', bg=bg_color, fg=fg_color, font=font_base).grid(row=4,column=0,pady=10)
        predict_label2 = Label(frame, text=f'~цена в будущем: {future_price}', bg=bg_color, fg=fg_color, font=font_base).grid(row=5,column=0,pady=10)
        binance_df['SMA20'] = binance_df['Close'].rolling(window=20).mean()
        binance_df['SMA50'] = binance_df['Close'].rolling(window=50).mean()

        trend_direction = binance_df['SMA20'].iloc[-1] - binance_df['SMA20'].iloc[-2]
        if trend_direction > 0:
            future_price_direction = 'up'
        elif trend_direction < 0:
            future_price_direction = 'down'
        else:
            future_price_direction = 'horizontal'

        if future_price_direction == 'up':
            future_price = binance_df['High'].iloc[-1] + predicted_change[0]
        elif future_price_direction == 'down':
            future_price = binance_df['Low'].iloc[-1] + predicted_change[0]
        else:
            future_price = binance_df['Close'].iloc[-1] + predicted_change[0]

        fig, axlist = mpf.plot(binance_df, type='candle', style='charles', volume=True, returnfig=True, mav=(20, 50), datetime_format='%b %d, %H:%M', title=f'График пары {symbol}')

        for ax in axlist:
            ax.axhline(y=future_price, color='blue', linestyle='solid', linewidth=2)

        plt.show()
    except Exception as e:
        print('нет такой пары', e, end='\n')

# Создание главного окна Tkinter
root = tk.Tk()
root.title("Asota Trade")

bg_color = '#0a0130'
fg_color = '#05c1ff'
font_base = ('Helvetica', 12, 'bold')

# Создание фрейма для размещения виджетов
frame = tk.Frame(root, bg=bg_color)
frame.grid(row=0, column=0, padx=60, pady=0)

# Надпись "Asota Trade"
title_label = tk.Label(frame, text="Asota Trade", font=('Helvetica', 40, 'bold'), bg=bg_color, fg='White')
title_label.grid(row=0, columnspan=2, pady=10)

# Метка и поле ввода для пары
symbol_label = tk.Label(frame, text="Пара:", bg=bg_color, fg=fg_color, font=font_base)
symbol_label.grid(row=1, column=0, pady=5, sticky='w')
symbol_entry = tk.Entry(frame, bg=bg_color, font=font_base, fg=fg_color)
symbol_entry.grid(row=1, column=1, pady=5, sticky='w')

# Метка и выпадающий список для интервала
interval_label = tk.Label(frame, text="Интервал:", bg=bg_color, fg=fg_color, font=font_base)
interval_label.grid(row=2, column=0, pady=5, sticky='w')
intervals = ["1m", "5m", "15m", "1h", "4h", "1d"]
interval_combobox = ttk.Combobox(frame, values=intervals, font=font_base)
interval_combobox.grid(row=2, column=1, pady=5, sticky='w')
interval_combobox.current(0)

# Кнопка для анализа и построения графика
button = tk.Button(frame, text="Анализировать и построить график", command=analyze_and_plot, bg=bg_color, highlightthickness=0, font=font_base, fg=fg_color)
button.grid(row=3, columnspan=2, pady=10)

# Поднимаем рамку с виджетами на передний план
frame.lift()

# Запуск основного цикла Tkinter
root.mainloop()
