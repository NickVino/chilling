# Imports
import openmeteo_requests
import requests_cache
from retry_requests import retry

import pandas as pd
import numpy as np
from windrose import WindroseAxes
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Your Variables
loc_latitude = 42.8795
loc_longitude = -78.8757
loc_timezone = "America/New_York"
loc_wind_speed_unit = "mph"
run_date = "2026-06-18"

graph_title = "A Windy Day at Seneca One: 06-19-26"
file_save_dir = r'C:\Users\nickp\OneDrive\Desktop\Home Data Projects\Viz\mtb-viz-challenge\\'
file_save_name = 'seneca_one_wind_rose.png'

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make api call
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": loc_latitude,
    "longitude": loc_longitude,
    "start_date": run_date,
    "end_date": run_date,
    "hourly": ["wind_direction_10m", "wind_gusts_10m","wind_speed_10m"],
    "timezone": loc_timezone,
    "wind_speed_unit": loc_wind_speed_unit
}
responses = openmeteo.weather_api(url, params = params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_wind_direction_10m = hourly.Variables(0).ValuesAsNumpy()
hourly_wind_gusts_10m = hourly.Variables(1).ValuesAsNumpy()
hourly_wind_speed_10m = hourly.Variables(2).ValuesAsNumpy()

hourly_data = {
    "date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    ).tz_convert(response.Timezone().decode())
}

hourly_data["wind_direction_10m"] = hourly_wind_direction_10m
hourly_data["wind_gusts_10m"] = hourly_wind_gusts_10m
hourly_data["wind_speed_10m"] = hourly_wind_speed_10m

hourly_dataframe = pd.DataFrame(data = hourly_data)

# Add label columns to df
labels = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
hourly_dataframe['bin_idx'] = (((hourly_dataframe['wind_direction_10m'] / 22.5) + 0.5).astype(int) % 16)
hourly_dataframe['sector'] = [labels[i] for i in hourly_dataframe['bin_idx']]

# Create wind rose plot
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']

ax = WindroseAxes.from_ax()
ax.bar(
    hourly_dataframe['wind_direction_10m'], 
    hourly_dataframe['wind_gusts_10m'], 
    normed=True, # Converts raw counts to percentages (highly recommended for multi-year data)
    opening=0.8, 
    edgecolor='white', 
    nsector=16, # Automatically handles the 16-sector binning
)

# 4. Format legend to show percentage frequencies
ax.set_legend(
    title="Wind Speed (m/s)", 
    loc="lower left", 
    bbox_to_anchor=(1, 0),
    prop={'family': 'Arial', 'size': 11} 
)

# Ensure the title also respects the font choice
plt.title(graph_title, fontname="Arial", fontsize=14, weight='bold')
plt.savefig(
    file_save_dir + file_save_name, 
    dpi=300,               # High resolution suitable for print and presentations
    bbox_inches='tight',   # Prevents the legend or titles from being cut off
    transparent=False      # Saves with a solid white background instead of clear
)