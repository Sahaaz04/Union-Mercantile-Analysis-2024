import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# Load
df = pd.read_csv(r"c:\Program Files\Analysis\Union Mercantile Sales 2011 (Clean).csv")
df['invoice_date'] = pd.to_datetime(df['invoice_date'])
observation_window_end = df['invoice_date'].max()

rfm = df.groupby('customer_id').agg({
    'invoice_date': [
        lambda x: (observation_window_end - x.max()).days,  # Recency
        lambda x: (x.max() - x.min()).days if len(x) > 1 else 0  # Customer Lifetime
    ],
    'invoice_no': 'nunique',                         # Frequency
    'unit_price': lambda x: (x * df.loc[x.index, 'quantity']).sum()  # Monetary
})

# Flatten multi-index columns
rfm.columns = ['recency', 'customer_lifetime_days', 'frequency', 'monetary']
rfm = rfm.reset_index()

# Segmenting buyers for churn
rfm['is_repeat_buyer'] = (rfm['frequency'] > 1).astype(int)

repeat_buyers_df = rfm[rfm['is_repeat_buyer'] == 1]   # For churn prediction
one_time_buyers_df = rfm[rfm['frequency'] == 1]        # For conversion prediction

# Define churn 
churn_threshold = 90
repeat_buyers_df['churn'] = (repeat_buyers_df['recency'] > churn_threshold).astype(int)

print(f"Churn Analysis Overview:")
print(f"Total customers: {len(rfm)}")
print(f"Repeat buyers: {len(repeat_buyers_df)}")
print(f"One-time buyers: {len(one_time_buyers_df)}")
print(f"Churn rate among repeat buyers: {repeat_buyers_df['churn'].mean():.1%}")

# Define features and target
X_rep = repeat_buyers_df[['frequency', 'monetary', 'customer_lifetime_days']]
y_rep = repeat_buyers_df['churn']

# Split and train the model
X_rep_train, X_rep_test, y_rep_train, y_rep_test = train_test_split(
    X_rep, y_rep, test_size=0.3, random_state=42
)
model_rep = RandomForestClassifier(random_state=42)
model_rep.fit(X_rep_train, y_rep_train)

# Evaluate the model for repeat buyers
y_rep_pred = model_rep.predict(X_rep_test)
print(classification_report(y_rep_test, y_rep_pred))

# Predict churn probability for CURRENT repeat buyers
repeat_buyers_df['churn_prob'] = model_rep.predict_proba(X_rep)[:, 1]

# Churn Status 
repeat_buyers_df['churn_status'] = np.select([
  repeat_buyers_df['churn_prob'] <= 0.3,
  repeat_buyers_df['churn_prob'] <= 0.7,
  repeat_buyers_df['churn_prob'] <= 0.9,
  repeat_buyers_df['churn_prob'] <= 1
], ['Low Risk', 'Medium Risk', 'High Risk', 'Churned'], default= 'Unknown'
  
)

# Show feature importance
feature_importance = pd.DataFrame({
    'feature': X_rep.columns,
    'importance': model_rep.feature_importances_
}).sort_values('importance', ascending=False)

print("\nFeature Importance:")
print(feature_importance)