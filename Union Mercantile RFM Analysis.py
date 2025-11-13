import pandas as pd
import numpy as np
from datetime import datetime

# Load data
df = pd.read_csv(r"c:\Program Files\Analysis\Union Mercantile Sales 2011 (Clean).csv")
df['invoice_date'] = pd.to_datetime(df['invoice_date'])

# Calculate RFM metrics
observation_window_end = df['invoice_date'].max()
rfm = df.groupby('customer_id').agg({
    'invoice_date': [
        lambda x: (observation_window_end - x.max()).days,  # Recency
    ],
    'invoice_no': 'nunique',                         # Frequency
    'unit_price': lambda x: (x * df.loc[x.index, 'quantity']).sum()  # Monetary
})

# Flatten multi-index columns
rfm.columns = ['recency', 'frequency', 'monetary']
rfm = rfm.reset_index()

# Create monetary status with custom cutoffs
rfm['monetary_status'] = np.select([
    rfm['monetary'] >= 5000,
    rfm['monetary'] >= 1000,
    rfm['monetary'] >= 300
], ['High Value', 'Average Value', 'Low Value'], default='Very Low Value')

rfm['frequency_status'] = np.select([
    rfm['frequency'] == 1,       
    rfm['frequency'] <= 3,       
    rfm['frequency'] <= 5       
], ['One-Time', 'Few', 'Occasional'], default='Frequent')

# Create recency status
rfm['recency_status'] = np.select([
    rfm['recency'] <= 30,
    rfm['recency'] <= 90, 
    rfm['recency'] <= 180
], ['Recent', 'Needs Attention', 'At Risk'], default='Churned')

# Create the final segmentation summary
segmentation_summary = rfm[['customer_id', 'recency_status', 'monetary_status', 'frequency_status']]

# print("=== SEGMENTATION RESULTS ===")
# print(f"Total customers: {len(segmentation_summary)}")
# print("\nRecency Status Distribution:")
# print(segmentation_summary['recency_status'].value_counts())
# print("\nMonetary Status Distribution:")
# print(segmentation_summary['monetary_status'].value_counts())
# print("\nFrequency Status Distribution:")
# print(segmentation_summary['frequency_status'].value_counts())

# Show some examples
# print("\n=== SAMPLE CUSTOMER SEGMENTS ===")
# print(segmentation_summary.head(10))