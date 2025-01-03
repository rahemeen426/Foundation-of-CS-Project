# -*- coding: utf-8 -*-
"""FCS_Project.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1zZ4zQ-L4vI-v6tMt4FRbWfzZDlr8jWHR
"""

from google.colab import drive
drive.mount('/content/drive')

import pandas as pd

df = pd.read_csv("/content/drive/MyDrive/Dataset/NYC_Trip_Fare.csv")
df.head()

"""**1. Extract all trips with trip_distance larger than 50**"""

trip1 = df[df['trip_distance']>50]
trip1

"""**2. Extract all trips where payment_type is missing**"""

trip2 = df[df['payment_type'].isnull()]
trip2

"""**3. For each (PULocationID, DOLocationID) pair, determine the number of trips**"""

number_of_trip = df.groupby(['PULocationID', 'DOLocationID']).size().reset_index(name='trip_counts')
number_of_trip

"""**4. Save all rows with missing VendorID, passenger_count, store_and_fwd_flag, payment_type in a new dataframe called bad, and remove those rows from the original dataframe.**"""

targeted_columns = ['VendorID', 'passenger_count', 'store_and_fwd_flag', 'payment_type']
bad = df[df[targeted_columns].isnull().any(axis=1)]

df = df.drop(bad.index)
print("Dataset After cleaning")
df

"""**5. Add a duration column storing how long each trip has taken (use tpep_pickup_datetime, tpep_dropoff_datetime)**"""

#Converting both columns into pandas datetime object
df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])

#Calculating the Duration, and converting it into seconds
df['Duration'] = (df['tpep_dropoff_datetime']-df['tpep_pickup_datetime']).dt.total_seconds()/60

print("Dataframe with Duration Column")
df

"""**6. For each pickup location, determine how many trips have started there.**"""

pickup_count = df.groupby('PULocationID').size().reset_index(name='Pickup Trip Count')
pickup_count

"""**7. Cluster the pickup time of the day into 30-minute intervals (e.g. from 02:00 to 02:30)**"""

df['Pickup Intreval'] = df['tpep_pickup_datetime'].dt.floor('30min')
df

"""**8. For each interval, determine the average number of passengers and the average fare amount.**"""

# Group by interval and calculate average passenger count and fare amount
Avg_passanger_fare_amount = df.groupby('Pickup Intreval')[['passenger_count', 'fare_amount']].mean().reset_index()
Avg_passanger_fare_amount

"""**9. For each payment type and each interval, determine the average fare amount**"""

# Group by interval and payment type, and calculate average fare amount
Avg_fare_amount = df.groupby(['Pickup Intreval', 'payment_type'])['fare_amount'].mean().reset_index()
Avg_fare_amount

"""**10. For each payment type, determine the interval when the average fare amount is maximum**"""

# Group by payment type and interval, and calculate the average fare amount
grouped_payment_interval = df.groupby(['Pickup Intreval', 'payment_type'])['fare_amount'].mean().reset_index()

# Find the interval with the maximum average fare amount for each payment type
max_fare_intervals = grouped_payment_interval.loc[grouped_payment_interval.groupby('payment_type')['fare_amount'].idxmax()]
max_fare_intervals

"""**11. For each payment type, determine the interval when the overall ratio between the tip and the fare amounts is maximum**"""

# Calculate the tip-to-fare ratio
df['tip_to_fare_ratio'] = df['tip_amount'] / df['fare_amount']

# Fix: Drop rows with NaN in relevant columns
df_cleaned = df.dropna(subset=['tip_to_fare_ratio'])


# Group by payment type and interval, and find the maximum ratio
grouped = df_cleaned.groupby(['payment_type', 'Pickup Intreval'])['tip_to_fare_ratio'].mean().reset_index()

# Find the interval with the maximum ratio for each payment type
max_ratio_intervals = grouped.loc[grouped.groupby('payment_type')['tip_to_fare_ratio'].idxmax()]

# Display the result
max_ratio_intervals

"""**12. Find the location with the highest average fare amount**"""

# Group by PULocationID and DOLocation and calculate the average fare amount
average_fare = df.groupby(['PULocationID', 'DOLocationID'])['fare_amount'].mean()

# Finding location with the highest average fare amount
highest_avg_location = average_fare.idxmax()
highest_avg_fare = average_fare.max()
print(f"The location pair with the highest average fare is {highest_avg_location} Pickup and Dropff location respectively, with an average fare of {highest_avg_fare:.2f}.")

"""**13. Build a new dataframe (called common) where, for each pickup location we keep all trips to the 5 most common destinations (i.e. each pickup location can have different common destinations).**"""

# Step 1: Count trips for each (PULocationID, DOLocationID) pair
trip_counts = df.groupby(['PULocationID', 'DOLocationID']).size().reset_index(name='Trip Count')

top_destinations = (
    trip_counts.groupby('PULocationID')
    .apply(lambda group: group[['DOLocationID', 'Trip Count']].nlargest(5, 'Trip Count'))
    .reset_index(drop=True)
)

# Ensure PULocationID remains in the final DataFrame
top_destinations = trip_counts.merge(top_destinations, on=['DOLocationID', 'Trip Count'])

print(top_destinations)

# Step 3: Merge with the original DataFrame to filter rows
common = df.merge(
    top_destinations[['PULocationID', 'DOLocationID']],
    on=['PULocationID', 'DOLocationID']
)

common

"""**14. On the common dataframe, for each payment type and each interval, determine the average fare amount**"""

# Group by interval and payment type, and calculate average fare amount on common dataframe
Avg_fare_amount_common = common.groupby(['Pickup Intreval', 'payment_type'])['fare_amount'].mean().reset_index()
Avg_fare_amount_common

"""**15. Compute the difference of the average fare amount computed in the previous point with those computed at point 9.**


"""

# Merge the two datasets on the interval column
merged_fares = Avg_fare_amount_common.merge(
    Avg_fare_amount,
    on='Pickup Intreval',
    suffixes=('', '_point_15'),
    how='left'  # Use left join as not all intervals from point 9 might exist in point 10
)

# Calculate the difference in average fare amounts
merged_fares['fare_difference'] = abs(
   Avg_fare_amount_common['fare_amount'] - Avg_fare_amount['fare_amount']
)

merged_fares[['Pickup Intreval','payment_type', 'fare_difference']]

# Difference_avg_fare = abs(Avg_fare_amount_common['fare_amount'] - Avg_fare_amount['fare_amount'])
# Difference_avg_fare.reset_index(name = 'Fare Difference')

"""**16. Compute the ratio between the differences computed in the previous point and those computed in point 9. Note: you have to compute a ratio for each pair (payment type, interval).**"""

import numpy as np

# Add the ratio computation to the merged DataFrame
merged_fares['fare_ratio'] = (
    merged_fares['fare_difference'] / Avg_fare_amount['fare_amount']
)

# Handle cases where division by zero or NaN occurs
merged_fares['fare_ratio'] = merged_fares['fare_ratio'].replace([np.inf, -np.inf], np.nan)

# Display the results
merged_fares[['Pickup Intreval', 'payment_type', 'fare_difference', 'fare_ratio']]

"""**17. Build chains of trips. Two trips are consecutive in a chain if
(a) they have the same VendorID,
(b) the pickup location of the second trip is also the dropoff location of the first trip,
(c) the pickup time of the second trip is after the dropoff time of the first trip, and
(d) the pickup time of the second trip is at most 2 minutes later than the dropoff time of the first trip.**
"""

df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
# Sort the DataFrame
df = df.sort_values(by=['VendorID', 'tpep_dropoff_datetime', 'tpep_pickup_datetime']).reset_index(drop=True)

# Add a chain column initialized to 0
df['chain'] = 0

# Loop through the trips to assign chain IDs
current_chain = 0
for i in range(1, len(df)):
    # Get current and previous trip
    prev_trip = df.iloc[i - 1]
    curr_trip = df.iloc[i]

    # Check the chaining conditions
    if (
        prev_trip['VendorID'] == curr_trip['VendorID'] and
        prev_trip['DOLocationID'] == curr_trip['PULocationID'] and
        curr_trip['tpep_pickup_datetime'] > prev_trip['tpep_dropoff_datetime'] and
        (curr_trip['tpep_pickup_datetime'] - prev_trip['tpep_dropoff_datetime']).total_seconds() <= 120
    ):
        # If conditions are met, assign the same chain ID
        df.loc[i, 'chain'] = current_chain
    else:
        # Otherwise, start a new chain
        current_chain += 1
        df.loc[i, 'chain'] = current_chain

# Display the resulting DataFrame with chains
df[['VendorID', 'PULocationID', 'DOLocationID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'chain']]