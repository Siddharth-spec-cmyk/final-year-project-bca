import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from keras.models import load_model
from flask import Flask, render_template, request, send_file
import datetime as dt
from alpha_vantage.timeseries import TimeSeries
from sklearn.preprocessing import MinMaxScaler
import os

plt.style.use("fivethirtyeight")

app = Flask(__name__)

model = load_model('stock_dl_model.h5')


API_KEY = "Z0L1887QSPBDDX2V"

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/tool', methods=['GET', 'POST'])
def tools():
    if request.method == 'POST':
        stock = request.form.get('stock', 'AAPL').upper().strip()  
        try:
           
            ts = TimeSeries(key=API_KEY, output_format='pandas')
            df, meta_data = ts.get_daily(symbol=stock, outputsize='full')

            if df.empty:
                raise ValueError(f"No data found for {stock}. Check the symbol.")

            df = df.rename(columns={"1. open": "Open", "2. high": "High", 
                                    "3. low": "Low", "4. close": "Close", 
                                    "5. volume": "Volume"})
            
            df = df.sort_index(ascending=True)  

        except Exception as e:
            return render_template('tools.html', error=f"Error fetching data: {e}")

        if 'Close' not in df:
            return render_template('tools.html', error="No 'Close' price data available.")

        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA100'] = df['Close'].ewm(span=100, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

        data_training = df[['Close']][:int(len(df) * 0.70)]
        data_testing = df[['Close']][int(len(df) * 0.70):]

       
        scaler = MinMaxScaler(feature_range=(0, 1))
        data_training_array = scaler.fit_transform(data_training)

        past_100_days = data_training.tail(100)
        final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
        input_data = scaler.transform(final_df)

        x_test, y_test = [], []
        for i in range(100, input_data.shape[0]):
            x_test.append(input_data[i - 100:i])
            y_test.append(input_data[i, 0])
        x_test, y_test = np.array(x_test), np.array(y_test)

        y_predicted = model.predict(x_test)

    
        scale_factor = 1 / scaler.scale_[0]
        y_predicted = y_predicted * scale_factor
        y_test = y_test * scale_factor

        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(df['Close'], 'y', label='Closing Price')
        ax1.plot(df['EMA20'], 'g', label='EMA 20')
        ax1.plot(df['EMA50'], 'r', label='EMA 50')
        ax1.set_title("Closing Price vs Time (EMA 20 & 50)")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Price")
        ax1.legend()
        ema_chart_path = "static/ema_20_50.png"
        fig1.savefig(ema_chart_path)
        plt.close(fig1)

      
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        ax2.plot(df['Close'], 'y', label='Closing Price')
        ax2.plot(df['EMA100'], 'g', label='EMA 100')
        ax2.plot(df['EMA200'], 'r', label='EMA 200')
        ax2.set_title("Closing Price vs Time (EMA 100 & 200)")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Price")
        ax2.legend()
        ema_chart_path_100_200 = "static/ema_100_200.png"
        fig2.savefig(ema_chart_path_100_200)
        plt.close(fig2)

        
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        ax3.plot(y_test, 'g', label="Original Price", linewidth=1)
        ax3.plot(y_predicted, 'r', label="Predicted Price", linewidth=1)
        ax3.set_title("Prediction vs Original Trend")
        ax3.set_xlabel("Time")
        ax3.set_ylabel("Price")
        ax3.legend()
        prediction_chart_path = "static/stock_prediction.png"
        fig3.savefig(prediction_chart_path)
        plt.close(fig3)

        dataset_link = f"static/{stock}_dataset.csv"
        df.to_csv(dataset_link)

        return render_template('tools.html',
                               plot_path_ema_20_50=ema_chart_path,
                               plot_path_ema_100_200=ema_chart_path_100_200,
                               plot_path_prediction=prediction_chart_path,
                               dataset_link=dataset_link)

    return render_template('tools.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(f"static/{filename}", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)