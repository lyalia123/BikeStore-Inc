# data_generator.py
import psycopg2
import random
import time
from datetime import datetime, timedelta
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="bikestore",
            user="postgres",
            password="Alpieva2006"
        )
        self.cursor = self.conn.cursor()
        
    def get_random_customer(self):
        """Получить случайного клиента"""
        self.cursor.execute("SELECT customer_id FROM customers ORDER BY RANDOM() LIMIT 1")
        return self.cursor.fetchone()[0]
    
    def get_random_store(self):
        """Получить случайный магазин"""
        self.cursor.execute("SELECT store_id FROM stores ORDER BY RANDOM() LIMIT 1")
        return self.cursor.fetchone()[0]
    
    def get_random_staff(self, store_id):
        """Получить случайного сотрудника магазина"""
        self.cursor.execute("SELECT staff_id FROM staffs WHERE store_id = %s AND active = true ORDER BY RANDOM() LIMIT 1", (store_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_random_product(self):
        """Получить случайный товар"""
        self.cursor.execute("""
            SELECT product_id, list_price 
            FROM products 
            WHERE list_price > 0 
            ORDER BY RANDOM() LIMIT 1
        """)
        return self.cursor.fetchone()
    
    def generate_new_order(self):
        """Сгенерировать новый заказ с товарами"""
        try:
            # Создаем заказ
            customer_id = self.get_random_customer()
            store_id = self.get_random_store()
            staff_id = self.get_random_staff(store_id)
            
            if not staff_id:
                logger.warning("Не найден активный сотрудник для магазина")
                return
            
            order_date = datetime.now() - timedelta(days=random.randint(0, 30))
            required_date = order_date + timedelta(days=random.randint(5, 15))
            
            # Вставляем заказ
            self.cursor.execute("""
                INSERT INTO orders (customer_id, order_status, order_date, required_date, store_id, staff_id)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING order_id
            """, (customer_id, 1, order_date, required_date, store_id, staff_id))
            
            order_id = self.cursor.fetchone()[0]
            
            # Добавляем товары в заказ
            num_items = random.randint(1, 5)
            for item_num in range(num_items):
                product_id, list_price = self.get_random_product()
                quantity = random.randint(1, 3)
                discount = round(random.uniform(0, 0.3), 2) if random.random() > 0.7 else 0
                
                self.cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, list_price, discount)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_id, product_id, quantity, list_price, discount))
                
                # Обновляем остатки
                self.cursor.execute("""
                    UPDATE stocks 
                    SET quantity = GREATEST(0, quantity - %s)
                    WHERE store_id = %s AND product_id = %s
                """, (quantity, store_id, product_id))
            
            self.conn.commit()
            logger.info(f"Создан новый заказ #{order_id} с {num_items} товарами")
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при создании заказа: {e}")
    
    def update_product_prices(self):
        """Периодическое обновление цен товаров"""
        try:
            self.cursor.execute("""
                UPDATE products 
                SET list_price = list_price * (0.95 + random() * 0.1)
                WHERE product_id IN (
                    SELECT product_id FROM products ORDER BY RANDOM() LIMIT 3
                )
            """)
            self.conn.commit()
            logger.info("Обновлены цены для случайных товаров")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при обновлении цен: {e}")
    
    def run_continuous_generation(self, interval=15):
        """Запуск непрерывной генерации данных"""
        logger.info(f"Запуск генератора данных с интервалом {interval} секунд")
        price_update_counter = 0
        
        try:
            while True:
                # Основная генерация заказов
                self.generate_new_order()
                
                # Периодическое обновление цен (каждые 4-й раз)
                price_update_counter += 1
                if price_update_counter >= 4:
                    self.update_product_prices()
                    price_update_counter = 0
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Остановка генератора данных")
        finally:
            self.cursor.close()
            self.conn.close()

if __name__ == "__main__":
    generator = DataGenerator()
    generator.run_continuous_generation(interval=15)  # Обновление каждые 15 секунд