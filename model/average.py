import pandas as pd
for i in range(1, 17):
    # Load your data
    data = pd.read_csv(f"data/activity_data_{i}.csv")

    # Convert the timestamp to datetime if needed
    data['timestamp'] = pd.to_datetime(data['timestamp'])

    # Replace 'pace_min_per_km' with its moving average
    # Adjust 'window' to define the number of periods for averaging
    window_size = 60  # Example: 5-period moving average
    data['pace_min_per_km'] = data['pace_min_per_km'].rolling(window=window_size).mean()

    # Optional: Drop NaN rows if the window creates them
    data = data.dropna()

    # Save or use the modified DataFrame
    data.to_csv(f"average_data/activity_data_{i}.csv", index=False)
