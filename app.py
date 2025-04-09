from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import io
import base64
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
matplotlib.use('agg')

app = Flask(__name__)

# Load the dataset (replace with your actual loading and cleaning)
df = pd.read_csv('dataset/london_bike_cleaned.csv')

df['time'] = pd.to_datetime(df['time'])
df.set_index('time', inplace=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    moving_average_window = request.form.get('moving_average_window', 14, type=int)

    if start_date_str and end_date_str:
        start_date = pd.to_datetime(start_date_str)
        end_date = pd.to_datetime(end_date_str)
        filtered_df = df[(df.index >= start_date) & (df.index <= end_date)].copy()
    else:
        filtered_df = df.copy()
        # Set default start and end dates for the slider
        start_date = filtered_df.index.min()
        end_date = filtered_df.index.max()

    # Dynamic Moving Average Plot
    if not filtered_df.empty:
        filtered_df['moving_average'] = filtered_df['count'].rolling(window=moving_average_window, min_periods=1).mean()
        plt.figure(figsize=(15, 6))
        plt.plot(filtered_df.index, filtered_df['count'], label='Total Rides', alpha=0.6)
        plt.plot(filtered_df.index, filtered_df['moving_average'], label=f'{moving_average_window}-Day Moving Average', color='red')
        plt.xlabel('Date')
        plt.ylabel('Number of Bike Rides')
        plt.title(f'Total Bike Rides and {moving_average_window}-Day Moving Average ({start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")})')
        plt.legend()
        plt.grid(True)
        img_ma = io.BytesIO()
        plt.savefig(img_ma, format='png')
        img_ma.seek(0)
        plot_url_ma = base64.b64encode(img_ma.read()).decode('utf-8')
        plt.close()
    else:
        plot_url_ma = None

    # Total Number of Bike Rides
    total_rides = len(filtered_df)

    # Total Number of Bike Rides Split by Weather
    weather_counts = filtered_df['weather'].value_counts().to_dict()
    weather_labels = {
        1: 'Clear/Sunny',
        2: 'Scattered Clouds',
        3: 'Broken Clouds',
        4: 'Cloudy',
        7: 'Rain/Light Snow/Thunderstorm',
        10: 'Freezing Rain/Heavy Snow',
        26: 'Snowfall',
        94: 'Fog'
    }
    weather_data = {weather_labels.get(code, f'Code {code}'): count for code, count in weather_counts.items()}

    # Total Number of Bike Rides Split by Hour
    hourly_counts = filtered_df.groupby(filtered_df.index.hour)['count'].sum().to_dict()

    # Temperature vs Wind Speed Heat Map
    if not filtered_df.empty:
        plt.figure(figsize=(20, 20))
        # Define a custom colormap
        colors = ["blue", "cyan", "lightgreen", "yellow", "orange", "red"]
        cmap = LinearSegmentedColormap.from_list("mycmap", colors)
        heatmap_data = filtered_df.pivot_table(index='temp_real_C', columns='wind_speed_kph', values='count', aggfunc='mean').fillna(0)
        sns.heatmap(heatmap_data, cmap=cmap, cbar_kws={'label': 'Average Bike Rides'})
        plt.xlabel('Wind Speed (km/h)')
        plt.ylabel('Temperature (°C)')
        plt.title('Temperature vs Wind Speed (Average Bike Rides)')
        img_heatmap = io.BytesIO()
        plt.savefig(img_heatmap, format='png')
        img_heatmap.seek(0)
        plot_url_heatmap = base64.b64encode(img_heatmap.read()).decode('utf-8')
        plt.close()
    else:
        plot_url_heatmap = None

    # Get available date range for the slider
    min_date = df.index.min().strftime('%Y-%m-%d')
    max_date = df.index.max().strftime('%Y-%m-%d')

    return render_template('index.html',
                           plot_url_ma=plot_url_ma,
                           total_rides=total_rides,
                           weather_data=weather_data,
                           hourly_counts=hourly_counts,
                           plot_url_heatmap=plot_url_heatmap,
                           min_date=min_date,
                           max_date=max_date,
                           default_start_date=start_date.strftime('%Y-%m-%d') if not filtered_df.empty else min_date,
                           default_end_date=end_date.strftime('%Y-%m-%d') if not filtered_df.empty else max_date,
                           default_window=moving_average_window)

if __name__ == '__main__':
    app.run(debug=True)