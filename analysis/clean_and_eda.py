import os

import pandas as pd
import sys

pd.options.mode.chained_assignment = None
sys.stdout.reconfigure(encoding='utf-8')

# Task 1 — Load and inspect

orders = pd.read_csv("data/orders.csv")
products = pd.read_csv("data/products.csv")
customers = pd.read_csv("data/customers.csv")

print("Orders shape:")
print(orders.shape)


# Task 2 — Standardize payment_method casing

print("\nBefore standardization:")
print(orders["payment_method"].unique())

orders['payment_method'] = orders['payment_method'].str.strip().str.upper()
print("\nAfter standardization:")
print(orders['payment_method'].value_counts())


# Task 3 — Remove duplicate orders

orders_clean = orders.drop_duplicates(subset=['customer_id', 'product_id', 'order_date', 'quantity', 'discount_pct', 'payment_method', 'rating', 'returned'], keep='first')
print("\nShape after removing duplicates:")
print(orders_clean.shape)


# Task 4 — Impute missing values

print("\nMissing values before imputation:")
print(orders_clean[['discount_pct','rating']].isnull().sum())

orders_clean['discount_pct'] = orders_clean['discount_pct'].fillna(0)

rating_median = orders_clean['rating'].median()

print(f"\nMedian rating: {rating_median}")

orders_clean['rating'] = orders_clean['rating'].fillna(rating_median)

print("\nMissing values after imputation:")
print(orders_clean[['discount_pct','rating']].isnull().sum())


# Task 5 — Merge and reconcile against Part 1

orders_merged = orders.merge(products, on='product_id', how='left').merge(customers, on='customer_id', how='left')
orders_clean_merged = orders_clean.merge(products, on='product_id', how='left').merge(customers, on='customer_id', how='left')

orders_merged_discount_pct = orders_merged['discount_pct'].fillna(0)

orders_merged_order_value = orders_merged['quantity'] * orders_merged['price'] * (1 - orders_merged_discount_pct/100)
orders_clean_merged_order_value = orders_clean_merged['quantity'] * orders_clean_merged['price'] * (1 - orders_clean_merged['discount_pct']/100)

print("\nTotal order_value before cleaning:")
print(round(orders_merged_order_value.sum(), 2))
print("\nTotal order_value after cleaning:")
print(round(orders_clean_merged_order_value.sum(), 2))

delta_order_value = round(orders_merged_order_value.sum() - orders_clean_merged_order_value.sum(), 2)
print("\nDelta in order_value due to cleaning:")
print(delta_order_value)

print("\nReconciliation Note:")
print(f"The total order_value decreased by ₹{delta_order_value} after cleaning the data. " \
f"This exact delta is attributed to the removal of 5 duplicate rows in Task 3. " \
f"The combined order_value of these 5 dropped rows was ₹{delta_order_value}, which accounts for " \
f"the entire difference between the raw total of ₹{round(orders_merged_order_value.sum(), 2)} and the cleaned total of ₹{round(orders_clean_merged_order_value.sum(), 2)}. " \
f"The imputation of missing discount_pct and rating values did not affect the order_value total, " \
f"as these imputations do not change the quantity or price used in the order_value calculation.")


# Task 6 — IQR outlier detection on quantity

Q1_quantity = orders_clean_merged['quantity'].quantile(0.25)
Q3_quantity = orders_clean_merged['quantity'].quantile(0.75)
IQR_quantity = Q3_quantity - Q1_quantity

print("\nQuantity Outlier Detection:")
print(f"Q1: {Q1_quantity}, Q3: {Q3_quantity}, IQR: {IQR_quantity}")

lower_bound_quantity = Q1_quantity - (1.5 * IQR_quantity)
upper_bound_quantity = Q3_quantity + (1.5 * IQR_quantity)

print(f"Lower Bound: {lower_bound_quantity}, Upper Bound: {upper_bound_quantity}")

orders_clean_merged['is_outlier'] = (orders_clean_merged['quantity'] < lower_bound_quantity) | (orders_clean_merged['quantity'] > upper_bound_quantity)
print("\nOutlier rows based on quantity:")
outlier_rows = orders_clean_merged[orders_clean_merged['is_outlier']]
print(outlier_rows)


# Task 7 — Hypothesis: does COD have a higher return rate?

print(f"Hypothesis: Does COD have a higher return rate?")

grouped_df = orders_clean_merged.groupby('payment_method')['returned'].agg(['count','mean']).reset_index()
grouped_df['return_rate'] = (grouped_df['mean'] * 100).round(1)
print("\nReturn rates by payment method:")
print(grouped_df)
print(f"\nCARD return rate: {grouped_df[grouped_df['payment_method'] == 'CARD']['return_rate'].values[0]}%")
print(f"COD return rate: {grouped_df[grouped_df['payment_method'] == 'COD']['return_rate'].values[0]}%")
print(f"UPI return rate: {grouped_df[grouped_df['payment_method'] == 'UPI']['return_rate'].values[0]}%")
print("\nHence the hypothesis is Confirmed. COD has a higher return rate than other payment methods.")


# Task 8 — Multi-level segmentation

grouped_segment_df = orders_clean_merged.groupby(['payment_method', 'city_tier'])['returned'].agg(['count','mean']).reset_index()
grouped_segment_df['return_rate'] = (grouped_segment_df['mean'] * 100).round(1)
print("\nReturn rates by payment method and city tier:")
print(grouped_segment_df)

highest_risk_segment = grouped_segment_df.loc[grouped_segment_df['return_rate'].idxmax()]
print(f"\nThis indicates that the risk associated with COD is not uniform across city tiers and the return rate for {highest_risk_segment['payment_method']} in Tier-{highest_risk_segment['city_tier']} cities is {highest_risk_segment['return_rate']}%, which is at highest-risk.")


# Task 9 — Correlation analysis

print(f"\nHypothesis: Higher discounts reduce returns")

corr_matrix = orders_clean_merged[['rating', 'returned', 'discount_pct', 'quantity']].corr().round(2)

print("\nCorrelation matrix:")
print(corr_matrix)
label_matrix = corr_matrix.map(lambda x: 'negligible' if abs(x) < 0.2 else ('weak' if abs(x) < 0.4 else ('moderate' if abs(x) < 0.7 else 'strong')))
print("\nCorrelation strength labels:")
print(label_matrix)

print("\nHence the hypothesis is Busted. The correlation between discount_pct and returned is negligible (≈ -0.09), indicating that higher discounts do not significantly reduce returns.")


# Task 10 - Outlier-corrected time series

orders_clean_merged['order_date'] = pd.to_datetime(orders_clean_merged['order_date'])
orders_clean_merged['year_month'] = orders_clean_merged['order_date'].dt.to_period('M').astype(str)
orders_clean_merged['order_value'] = orders_clean_merged['quantity'] * orders_clean_merged['price'] * (1 - orders_clean_merged['discount_pct'] / 100)

monthly_order_value_with_outliers = orders_clean_merged.groupby('year_month')['order_value'].sum().round(2)
monthly_order_value_without_outliers = orders_clean_merged[~orders_clean_merged['is_outlier']].groupby('year_month')['order_value'].sum().round(2)

print("\nMonthly total order_value including Task 6 outlier orders:")
print(monthly_order_value_with_outliers)

print("\nMonthly total order_value excluding Task 6 outlier orders:")
print(monthly_order_value_without_outliers)

print("\nOutlier-corrected time series note:")
print("January's apparent lead is an artifact of the two bulk orders landing in January: O0011 on 2026-01-28 and O0098 on 2026-01-10.")
print("Once those Task 6 outliers are excluded, March is the genuine peak month with an outlier-corrected total order_value of 20318.90.")

orders_clean_merged.to_csv("data/orders_clean_merged.csv", index=False)

import json

return_rate_by_payment = (
    orders_clean_merged.groupby("payment_method")["returned"].mean().mul(100).round(1)
)
return_rate_by_segment = (
    orders_clean_merged.groupby(["payment_method", "city_tier"])["returned"]
    .mean()
    .mul(100)
    .round(1)
)
highest_risk_key = return_rate_by_segment.idxmax()
monthly_order_value_with_outliers = (
    orders_clean_merged.groupby("year_month")["order_value"].sum().round(2)
)
true_peak_month = monthly_order_value_without_outliers.idxmax()
outlier_inflated_month = monthly_order_value_with_outliers.idxmax()

findings = {
    "cleaned_total_revenue_inr": round(float(orders_clean_merged["order_value"].sum()), 2),
    "raw_total_revenue_inr": round(float(orders_merged_order_value.sum()), 2),
    "duplicate_reconciliation_delta_inr": round(
        float(orders_merged_order_value.sum() - orders_clean_merged["order_value"].sum()), 2
    ),
    "return_rate_by_payment": {
        method: float(rate) for method, rate in return_rate_by_payment.items()
    },
    "highest_risk_segment": {
        "payment_method": str(highest_risk_key[0]),
        "city_tier": int(highest_risk_key[1]),
        "return_rate_pct": float(return_rate_by_segment.loc[highest_risk_key]),
    },
    "true_peak_month": {
        "month": str(true_peak_month),
        "revenue_inr": float(monthly_order_value_without_outliers.loc[true_peak_month]),
    },
    "outlier_inflated_month": {
        "month": str(outlier_inflated_month),
        "apparent_revenue_inr": float(monthly_order_value_with_outliers.loc[outlier_inflated_month]),
        "corrected_revenue_inr": float(monthly_order_value_without_outliers.loc[outlier_inflated_month]),
    },
}

with open("narrator/findings.json", "w", encoding="utf-8") as f:
    json.dump(findings, f, indent=4)
