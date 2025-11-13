import pandas as pd
import datetime
import numpy as np
from lifetimes.utils import calibration_and_holdout_data, summary_data_from_transaction_data
from lifetimes import BetaGeoFitter, GammaGammaFitter

# Load data
df = pd.read_csv(r"c:\Program Files\Analysis\Union Mercantile Sales 2011 (Clean).csv")
df['invoice_date'] = pd.to_datetime(df['invoice_date'])

# Calculate total spend per transaction (quantity * unit_price)
df['total_spend'] = df['quantity'] * df['unit_price']

# Set time windows for retail data
observation_window_end = df['invoice_date'].max()
calibration_end = observation_window_end - datetime.timedelta(days=180)

# Prepare data
df = df[['customer_id', 'invoice_no', 'invoice_date', 'total_spend']]
df = df[df['invoice_date'] <= observation_window_end]

# Create RFM summary for calibration period
rfm_cal = summary_data_from_transaction_data(
    transactions=df[df['invoice_date'] <= calibration_end],
    customer_id_col='customer_id',
    datetime_col='invoice_date', 
    monetary_value_col='total_spend',
    observation_period_end=calibration_end,
    freq='D'
)

# Remove outliers and invalid values
rfm_cal = rfm_cal[
    (rfm_cal['monetary_value'] > 0.1) &
    (rfm_cal['monetary_value'] < 10000) &
    (rfm_cal['frequency'] > 0)
]

# Split data for calibration/holdout
summary_cal_holdout = calibration_and_holdout_data(
    transactions=df,
    customer_id_col='customer_id',
    datetime_col='invoice_date',
    calibration_period_end=calibration_end,
    observation_period_end=observation_window_end,
    freq='D'
)
summary_cal_holdout = summary_cal_holdout[summary_cal_holdout.index.isin(rfm_cal.index)]

# Fit BG/NBD model
bgf = BetaGeoFitter(penalizer_coef=0.001)
bgf.fit(
    summary_cal_holdout['frequency_cal'],
    summary_cal_holdout['recency_cal'], 
    summary_cal_holdout['T_cal']
)

# Fit Gamma-Gamma model
ggf = GammaGammaFitter(penalizer_coef=0.01)
ggf.fit(rfm_cal['frequency'], rfm_cal['monetary_value'])

# Calculate 6-month CLV
clv_6mo = ggf.customer_lifetime_value(
    transaction_prediction_model=bgf,
    frequency=rfm_cal['frequency'],
    recency=rfm_cal['recency'],
    T=rfm_cal['T'],
    monetary_value=rfm_cal['monetary_value'],
    time=180,
    freq='D'
)

# Create results
clv_results = rfm_cal.copy()
clv_results['clv_6mo'] = clv_6mo.round(2)
clv_results = clv_results.reset_index()

# SEGMENTATION: Top 20% = High, Next 30% = Average, Bottom 50% = Low
high_cutoff = clv_results['clv_6mo'].quantile(0.80)  # Top 20%
avg_cutoff = clv_results['clv_6mo'].quantile(0.50)   # Next 30% (50th to 80th percentile)

clv_results['clv_status'] = np.select([
    clv_results['clv_6mo'] >= high_cutoff,
    clv_results['clv_6mo'] >= avg_cutoff
], ['High Value', 'Average Value'], default='Low Value')

# Calculate CAC 
cac = 50  # £50 customer acquisition cost
clv_to_cac_ratio = clv_results['clv_6mo'].mean() / cac

# print(f"Total Customers with Predictions: {len(clv_results)}")
# print(f"Average 6-month CLV: £{clv_results['clv_6mo'].mean():.2f}")
# print(clv_results['clv_status'].value_counts())
# print(f"Assumed CAC: £{cac:.2f}")
# print(f"CLV:CAC Ratio: {clv_to_cac_ratio:.2f}:1")
