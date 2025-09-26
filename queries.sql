-- 1. Вывести 10 первых клиентов
SELECT * FROM customers LIMIT 10;

-- 2. Количество заказов по городам
SELECT c.city, COUNT(o.order_id) AS order_count
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.city
ORDER BY order_count DESC;

-- 3. Средняя цена товаров по категориям
SELECT cat.category_name, AVG(p.list_price) AS avg_price
FROM products p
JOIN categories cat ON p.category_id = cat.category_id
GROUP BY cat.category_name
ORDER BY avg_price DESC;

-- 4. Минимальная и максимальная цена товаров по брендам
SELECT b.brand_name, MIN(p.list_price) AS min_price, MAX(p.list_price) AS max_price
FROM products p
JOIN brands b ON p.brand_id = b.brand_id
GROUP BY b.brand_name
ORDER BY b.brand_name;

-- 5. Суммарные продажи по каждому магазину
SELECT s.store_name, SUM(oi.quantity * oi.list_price) AS total_sales
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN stores s ON o.store_id = s.store_id
GROUP BY s.store_name
ORDER BY total_sales DESC;

-- 6. Количество заказанных товаров по категориям
SELECT cat.category_name, SUM(oi.quantity) AS total_quantity
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN categories cat ON p.category_id = cat.category_id
GROUP BY cat.category_name
ORDER BY total_quantity DESC;

-- 7. Средняя скидка по товарам
SELECT p.product_name, AVG(oi.discount) AS avg_discount
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_name
ORDER BY avg_discount DESC;

-- 8. Количество активных и неактивных сотрудников по магазинам
SELECT s.store_name, 
       SUM(CASE WHEN st.active THEN 1 ELSE 0 END) AS active_staff,
       SUM(CASE WHEN NOT st.active THEN 1 ELSE 0 END) AS inactive_staff
FROM staffs st
JOIN stores s ON st.store_id = s.store_id
GROUP BY s.store_name
ORDER BY active_staff DESC;

-- 9. Общая сумма покупок по клиентам
SELECT 
    c.first_name || ' ' || c.last_name AS customer_name, 
    SUM(oi.quantity * oi.list_price * (1 - oi.discount)) AS total_spent
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_spent DESC;

-- 10. Остатки товаров на складах
SELECT s.store_name, p.product_name, st.quantity
FROM stocks st
JOIN stores s ON st.store_id = s.store_id
JOIN products p ON st.product_id = p.product_id
ORDER BY s.store_name, p.product_name;