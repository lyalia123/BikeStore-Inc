# export_orders_to_csv.py
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import os

def export_orders_data():
    """Экспортирует данные о заказах по дням в CSV"""
    
    conn = psycopg2.connect(
        host="localhost", port=5433, database="bikestore",
        user="postgres", password="Alpieva2006"
    )
    
    # Данные за последние 30 дней
    query = """
    SELECT 
        DATE(o.order_date) as order_day,
        COUNT(o.order_id) as daily_orders
    FROM orders o
    WHERE o.order_date IS NOT NULL
        AND o.order_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY DATE(o.order_date)
    ORDER BY order_day;
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Сохраняем в CSV
    csv_path = "daily_orders.csv"
    df.to_csv(csv_path, index=False)
    
    print(f"✅ Данные экспортированы в {csv_path}")
    print(f"📊 Количество дней: {len(df)}")
    print(f"📅 Период: {df['order_day'].min()} - {df['order_day'].max()}")
    print(f"📈 Всего заказов: {df['daily_orders'].sum()}")
    
    return csv_path

if __name__ == "__main__":
    export_orders_data()