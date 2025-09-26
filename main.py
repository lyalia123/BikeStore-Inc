import psycopg2
import pandas as pd
import os
import numpy as np
from psycopg2 import extras

# Путь к папке с CSV файлами
DATA_DIR = r"C:/Users/Лейла/Desktop/BikeStore-Inc"

# Подключение к PostgreSQL
def get_connection(db_name="postgres"):
    return psycopg2.connect(
        host="localhost",
        port=5433,
        database=db_name,
        user="postgres",
        password="Alpieva2006"
    )

# Создаем базу данных
def create_database():
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DROP DATABASE IF EXISTS bikestore;")
    cur.execute("CREATE DATABASE bikestore;")
    cur.close()
    conn.close()
    print("Database 'bikestore' created")

# Создаем таблицы
def create_tables():
    conn = get_connection("bikestore")
    cur = conn.cursor()

    queries = [
        """
        CREATE TABLE brands (
            brand_id SERIAL PRIMARY KEY,
            brand_name VARCHAR(255) NOT NULL
        );
        """,
        """
        CREATE TABLE categories (
            category_id SERIAL PRIMARY KEY,
            category_name VARCHAR(255) NOT NULL
        );
        """,
        """
        CREATE TABLE products (
            product_id SERIAL PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            brand_id INT REFERENCES brands(brand_id),
            category_id INT REFERENCES categories(category_id),
            model_year INT,
            list_price NUMERIC
        );
        """,
        """
        CREATE TABLE customers (
            customer_id SERIAL PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            phone VARCHAR(25),
            email VARCHAR(100),
            street VARCHAR(100),
            city VARCHAR(50),
            state VARCHAR(25),
            zip_code VARCHAR(10)
        );
        """,
        """
        CREATE TABLE stores (
            store_id SERIAL PRIMARY KEY,
            store_name VARCHAR(255),
            phone VARCHAR(25),
            email VARCHAR(100),
            street VARCHAR(100),
            city VARCHAR(50),
            state VARCHAR(25),
            zip_code VARCHAR(10)
        );
        """,
        """
        CREATE TABLE staffs (
            staff_id SERIAL PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            email VARCHAR(100),
            phone VARCHAR(25),
            active BOOLEAN,
            store_id INT REFERENCES stores(store_id),
            manager_id INT
        );
        """,
        """
        CREATE TABLE orders (
            order_id SERIAL PRIMARY KEY,
            customer_id INT REFERENCES customers(customer_id),
            order_status INT,
            order_date DATE,
            required_date DATE,
            shipped_date DATE,
            store_id INT REFERENCES stores(store_id),
            staff_id INT REFERENCES staffs(staff_id)
        );
        """,
        """
        CREATE TABLE order_items (
            order_id INT REFERENCES orders(order_id),
            item_id SERIAL,
            product_id INT REFERENCES products(product_id),
            quantity INT,
            list_price NUMERIC,
            discount NUMERIC,
            PRIMARY KEY(order_id, item_id)
        );
        """,
        """
        CREATE TABLE stocks (
            store_id INT REFERENCES stores(store_id),
            product_id INT REFERENCES products(product_id),
            quantity INT,
            PRIMARY KEY (store_id, product_id)
        );
        """
    ]

    for q in queries:
        try:
            cur.execute(q)
        except Exception as e:
            print(f"Error creating table: {e}")
            continue

    conn.commit()
    cur.close()
    conn.close()
    print("Tables created")

# Функция для преобразования numpy типов в python типы
def convert_numpy_types(obj):
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj) if np.isnan(obj) else int(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

# Загружаем CSV в таблицы в правильном порядке с учетом зависимостей
def load_data():
    conn = get_connection("bikestore")
    cur = conn.cursor()

    # Таблицы в порядке зависимостей (от независимых к зависимым)
    tables = [
        ("brands", "brands.csv"),
        ("categories", "categories.csv"),
        ("products", "products.csv"),
        ("customers", "customers.csv"),
        ("stores", "stores.csv"),
        ("staffs", "staffs.csv"),
        ("orders", "orders.csv"),
        ("order_items", "order_items.csv"),
        ("stocks", "stocks.csv"),
    ]

    for table, filename in tables:
        file_path = os.path.join(DATA_DIR, filename)
        
        # Проверка существования файла
        if not os.path.exists(file_path):
            print(f"File {file_path} not found! Skipping...")
            continue
            
        try:
            # Пробуем разные кодировки
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin-1')
            
            # Заменяем NaN на None для PostgreSQL
            df = df.where(pd.notnull(df), None)
            
            # Специфичная обработка для каждой таблицы
            if table == "staffs":
                if "active" in df.columns:
                    df["active"] = df["active"].astype(bool)
                # Обработка manager_id - замена NaN на NULL
                if "manager_id" in df.columns:
                    df["manager_id"] = df["manager_id"].apply(lambda x: None if pd.isna(x) else int(x))
            
            # Обработка дат для orders
            elif table == "orders":
                date_columns = ["order_date", "required_date", "shipped_date"]
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
            
            # Преобразование всех числовых колонок к int
            for col in df.columns:
                if df[col].dtype in ['float64', 'int64']:
                    # Для ID колонок преобразуем в int, для цен оставляем float
                    if 'price' in col.lower() or 'discount' in col.lower():
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    else:
                        # Для ID колонок заменяем NaN на None и преобразуем в int где возможно
                        df[col] = df[col].apply(lambda x: int(x) if not pd.isna(x) else None)
            
            print(f"Loading {filename} into {table}...")
            print(f"Columns: {df.columns.tolist()}")
            print(f"First row: {[convert_numpy_types(x) for x in df.iloc[0].tolist()]}")
            
            # Преобразуем DataFrame в список кортежей с правильными типами
            tuples = []
            for _, row in df.iterrows():
                tuple_row = tuple(convert_numpy_types(x) for x in row)
                tuples.append(tuple_row)
            
            # Получаем названия колонок
            cols = ",".join(df.columns)
            placeholders = ",".join(["%s"] * len(df.columns))
            sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
            
            # Вставляем данные построчно с обработкой ошибок
            success_count = 0
            error_count = 0
            
            for i, tuple_row in enumerate(tuples):
                try:
                    cur.execute(sql, tuple_row)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # Показываем только первые 5 ошибок
                        print(f"Error in row {i}: {e}")
                        print(f"Problematic row: {tuple_row}")
                    continue
            
            conn.commit()
            print(f"Successfully loaded {success_count} rows into {table}")
            if error_count > 0:
                print(f"Failed to load {error_count} rows into {table}")
            
        except Exception as e:
            print(f"Error loading {filename} into {table}: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()

    cur.close()
    conn.close()
    print("Data loading completed")

def main():
    try:
        print("Starting database setup...")
        create_database()
        create_tables()
        load_data()
        print("Database setup complete. You can now run queries from queries.sql.")
    except Exception as e:
        print(f"Error during database setup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()