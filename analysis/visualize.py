import os
import pandas as pd
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

orders_df = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "orders_clean_merged.csv"))

# return_rate_by_payment.png
grouped_df = orders_df.groupby('payment_method')['returned'].agg(['count','mean']).reset_index()
grouped_df['return_rate'] = (grouped_df['mean'] * 100).round(1)
grouped_df = grouped_df.sort_values(by='return_rate', ascending=False)

plt.figure(figsize=(8, 6))
bars = plt.bar(grouped_df['payment_method'], grouped_df['return_rate'], color=['#FF9999', '#66B2FF', '#99FF99'])
plt.title(f"COD Returns at 44.4% — 3x Card", fontsize=14)
plt.xlabel("Payment Method")
plt.ylabel("Return Rate (%)")
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2, height, f'{height}%', ha='center', va='bottom')
plt.savefig(os.path.join(PROJECT_ROOT, "visualizations", "return_rate_by_payment.png"))

# monthly_revenue_trend.png
monthly_order_value_without_outliers = orders_df[~orders_df['is_outlier']].groupby('year_month')['order_value'].sum().round(2)
plt.figure(figsize=(10, 6))
plt.plot(monthly_order_value_without_outliers.index, monthly_order_value_without_outliers.values, marker='o', color='#FF5733')
plt.title("Outlier-Corrected Monthly Revenue Trend — March Peak", fontsize=14)
plt.xlabel("Year-Month")
plt.ylabel("Total Order Value")
plt.xticks(rotation=45)
for i, value in enumerate(monthly_order_value_without_outliers.values):
    plt.text(monthly_order_value_without_outliers.index[i], value, f'{value}', ha='center', va='bottom')
plt.tight_layout()
plt.savefig(os.path.join(PROJECT_ROOT, "visualizations", "monthly_revenue_trend.png"))