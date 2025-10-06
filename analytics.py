import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from sqlalchemy import create_engine
from openpyxl import load_workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils import get_column_letter

# ========== 1. Конфигурация ==========
DB_URI = "postgresql+psycopg2://postgres:Alpieva2006@localhost:5433/bikestore"
engine = create_engine(DB_URI)

CHARTS_DIR = "charts"
EXPORTS_DIR = "exports"
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

# ========== 2. SQL-запросы (каждый с минимум 2 JOIN) ==========
queries = {
    # Pie chart: заказы по магазинам (с JOIN клиентов)
    "pie_orders_by_store": """
        SELECT s.store_name, COUNT(o.order_id) AS order_count
        FROM stores s
        JOIN orders o ON o.store_id = s.store_id
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY s.store_name
        ORDER BY order_count DESC;
    """,

    # Bar chart: средняя проданная цена по категориям (используем order_items.list_price)
    "bar_avg_price_category": """
        SELECT cat.category_name,
               ROUND(AVG(oi.list_price), 2) AS avg_price,
               COUNT(DISTINCT p.product_id) AS products_count
        FROM categories cat
        JOIN products p ON p.category_id = cat.category_id
        JOIN order_items oi ON oi.product_id = p.product_id
        JOIN orders o ON oi.order_id = o.order_id
        GROUP BY cat.category_name
        ORDER BY avg_price DESC;
    """,

    # Horizontal bar chart: суммарные чистые продажи по магазинам (учитываем discount)
    "hbar_sales_store": """
        SELECT s.store_name,
               ROUND(SUM(oi.quantity * oi.list_price * (1 - COALESCE(oi.discount, 0))), 2) AS total_sales
        FROM stores s
        JOIN orders o ON o.store_id = s.store_id
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY s.store_name
        ORDER BY total_sales DESC;
    """,

    # Line chart: динамика продаж по месяцам (PostgreSQL DATE_TRUNC)
    "line_sales_time": """
        SELECT DATE_TRUNC('month', o.order_date)::date AS month,
               ROUND(SUM(oi.quantity * oi.list_price * (1 - COALESCE(oi.discount,0))), 2) AS sales
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN stores s ON o.store_id = s.store_id
        GROUP BY month
        ORDER BY month;
    """,

    # Histogram: распределение прайс-уровней товаров (берём товары, которые есть в стоках)
    "hist_prices": """
        SELECT p.list_price
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        JOIN stocks st ON st.product_id = p.product_id
        JOIN stores s ON st.store_id = s.store_id
        WHERE p.list_price IS NOT NULL;
    """,

    # Scatter: средняя скидка по товару vs суммарные продажи по товару
    "scatter_discount_sales": """
        SELECT p.product_name,
               ROUND(AVG(COALESCE(oi.discount,0)), 4) AS avg_discount,
               ROUND(SUM(oi.quantity * oi.list_price * (1 - COALESCE(oi.discount,0))), 2) AS total_sales
        FROM products p
        JOIN order_items oi ON oi.product_id = p.product_id
        JOIN orders o ON oi.order_id = o.order_id
        JOIN categories c ON p.category_id = c.category_id
        GROUP BY p.product_id, p.product_name
        ORDER BY total_sales DESC;
    """
}

# ========== 3. Визуализации ==========
def run_query(sql):
    try:
        return pd.read_sql(sql, engine)
    except Exception as e:
        print(f"Ошибка выполнения SQL: {e}")
        return pd.DataFrame()

def build_charts():
    # ---------- Pie (top-10 stores + Other) ----------
    df = run_query(queries["pie_orders_by_store"])
    if df.empty:
        print("Pie chart: нет данных.")
    else:
        df = df.sort_values("order_count", ascending=False).reset_index(drop=True)
        top_n = 10
        if len(df) > top_n:
            top = df.head(top_n).copy()
            other_sum = df["order_count"].iloc[top_n:].sum()
            top = top.append({"store_name": "Other", "order_count": other_sum}, ignore_index=True)
        else:
            top = df.copy()

        top.set_index("store_name")["order_count"].plot.pie(
            autopct='%1.1f%%', figsize=(7,7), startangle=90
        )
        plt.title(" Распределение заказов по магазинам")
        plt.ylabel("")
        path = f"{CHARTS_DIR}/pie_orders_by_store_result.png"
        plt.savefig(path, bbox_inches="tight"); plt.close()
        print(f"Pie chart → {len(df)} строк (включая Other) → {path}")

    # ---------- Bar (avg price by category) ----------
    df = run_query(queries["bar_avg_price_category"])
    if df.empty:
        print("Bar chart: нет данных.")
    else:
        df.plot.bar(x="category_name", y="avg_price", legend=False)
        plt.title("Средняя проданная цена по категориям")
        plt.xlabel("Категория")
        plt.ylabel("Средняя цена (USD)")
        path = f"{CHARTS_DIR}/bar_avg_price_category2.png"
        plt.savefig(path, bbox_inches="tight"); plt.close()
        print(f"Bar chart → {len(df)} строк → {path}")

    # ---------- Horizontal bar (sales by store) ----------
    df = run_query(queries["hbar_sales_store"])
    if df.empty:
        print("Horizontal bar: нет данных.")
    else:
        df.plot.barh(x="store_name", y="total_sales", legend=False)
        plt.title("Суммарные чистые продажи по магазинам")
        plt.xlabel("Продажи (net, USD)")
        path = f"{CHARTS_DIR}/hbar_sales_store.png"
        plt.savefig(path, bbox_inches="tight"); plt.close()
        print(f"Horizontal bar → {len(df)} строк → {path}")

    # ---------- Line (sales over time) ----------
    df = run_query(queries["line_sales_time"])
    if df.empty:
        print("Line chart: нет данных.")
    else:
        # Убедимся, что month — datetime
        if not np.issubdtype(df['month'].dtype, np.datetime64):
            df['month'] = pd.to_datetime(df['month'])
        df.plot(x="month", y="sales", kind="line", marker='o')
        plt.title("Динамика чистых продаж по месяцам")
        plt.xlabel("Месяц")
        plt.ylabel("Продажи (USD)")
        path = f"{CHARTS_DIR}/line_sales_time.png"
        plt.savefig(path, bbox_inches="tight"); plt.close()
        print(f"Line chart → {len(df)} строк → {path}")

    # ---------- Histogram (distribution of list_price) ----------
    df = run_query(queries["hist_prices"])
    if df.empty:
        print("Histogram: нет данных.")
    else:
        # Column is 'list_price'
        if "list_price" not in df.columns:
            # если имя колонки другое — попробуем взять первый столбец
            col = df.columns[0]
        else:
            col = "list_price"
        df[col].dropna().plot.hist(bins=20)
        plt.title("Гистограмма цен товаров (list_price)")
        plt.xlabel("Цена")
        path = f"{CHARTS_DIR}/hist_prices.png"
        plt.savefig(path, bbox_inches="tight"); plt.close()
        print(f"Histogram → {len(df)} строк → {path}")

    # ---------- Scatter (avg discount vs total sales by product) ----------
    df = run_query(queries["scatter_discount_sales"])
    if df.empty:
        print("Scatter: нет данных.")
    else:
        # Сделаем интерактивный scatter с plotly (удобно смотреть product_name)
        fig = px.scatter(df.head(200), x="avg_discount", y="total_sales",
                         hover_data=["product_name"], title="Средняя скидка vs суммарные продажи (по товарам)",
                         labels={"avg_discount": "Средняя скидка", "total_sales": "Суммарные продажи"})
        # сохраняем статично также картинкой
        static_path = f"{CHARTS_DIR}/scatter_discount_sales.png"
        fig.write_image(static_path)  # requires kaleido; если не установлен — можно пропустить
        # Покажем в интерактивном окне (на защите удобно)
        try:
            fig.show()
        except Exception:
            pass
        print(f"Scatter → {len(df)} строк (показано top 200 интерактивно) → {static_path}")

# ========== 4. Интерактивный график (Plotly) ==========
def build_interactive_chart():
    df = run_query(queries["line_sales_time"])
    if df.empty:
        print("Interactive chart: нет данных.")
        return
    if not np.issubdtype(df['month'].dtype, np.datetime64):
        df['month'] = pd.to_datetime(df['month'])
    # Можно добавить animation_frame по году/месяцу — здесь просто интерактивный line
    fig = px.line(df, x="month", y="sales", title="📈 Продажи по месяцам (интерактивно)", markers=True)
    fig.show()

# ========== 5. Экспорт в Excel (множественные-листы + форматирование) ==========
def export_to_excel():
    dataframes = {
        "Orders by Store": run_query(queries["pie_orders_by_store"]),
        "Avg Price by Category": run_query(queries["bar_avg_price_category"]),
        "Sales by Store": run_query(queries["hbar_sales_store"]),
        "Sales by Month": run_query(queries["line_sales_time"]),
        "Prices": run_query(queries["hist_prices"]),
        "Discount vs Sales": run_query(queries["scatter_discount_sales"])
    }

    filename = f"{EXPORTS_DIR}/report.xlsx"
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        for sheet, df in dataframes.items():
            # Если пустой DF — создаём пустую таблицу с заголовком
            if df.empty:
                pd.DataFrame().to_excel(writer, sheet_name=sheet, index=False)
            else:
                df.to_excel(writer, sheet_name=sheet, index=False)

    wb = load_workbook(filename)
    total_rows = 0
    for ws_idx, ws in enumerate(wb.worksheets, start=1):
        ws.freeze_panes = "A2"
        # Собираем DataFrame, чтобы узнать числовые колонки
        sheet_name = ws.title
        df = dataframes.get(sheet_name, pd.DataFrame())
        total_rows += len(df)

        # Применяем градиент только к числовым колонкам
        num_cols = list(df.select_dtypes(include=[np.number]).columns) if not df.empty else []
        for col_name in num_cols:
            col_idx = list(df.columns).index(col_name)  # 0-based
            excel_col = get_column_letter(col_idx + 1)  # Excel columns start at 1
            cell_range = f"{excel_col}2:{excel_col}{ws.max_row}"
            rule = ColorScaleRule(start_type="min", start_color="FFAA0000",
                                  mid_type="percentile", mid_value=50, mid_color="FFFFFF00",
                                  end_type="max", end_color="FF00AA00")
            try:
                ws.conditional_formatting.add(cell_range, rule)
            except Exception:
                # если что-то не сработало — пропускаем и продолжаем
                pass

        # Добавляем автофильтр
        try:
            ws.auto_filter.ref = ws.dimensions
        except Exception:
            pass

    wb.save(filename)
    sheets_count = len(dataframes)
    print(f"📂 Создан файл {filename}, {sheets_count} листов, {total_rows} строк (в сумме по листам)")

# ========== MAIN ==========
def main():
    build_charts()
    # отдельно интерактивный график можно вызвать при защите
    try:
        build_interactive_chart()
    except Exception:
        pass
    export_to_excel()

if __name__ == "__main__":
    main()
