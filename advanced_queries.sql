-- advanced_queries.sql

-- Для Heatmap: количество заказов по категориям и магазинам
SELECT 
    cat.category_name,
    s.store_name,
    COUNT(DISTINCT o.order_id) as order_count
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN categories cat ON p.category_id = cat.category_id
JOIN stores s ON o.store_id = s.store_id
GROUP BY cat.category_name, s.store_name;

-- Для Sunburst Chart: иерархия бренд -> категория -> продукт -> продажи
SELECT 
    b.brand_name,
    cat.category_name,
    p.product_name,
    SUM(oi.quantity * oi.list_price * (1 - oi.discount)) as total_sales
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN brands b ON p.brand_id = b.brand_id
JOIN categories cat ON p.category_id = cat.category_id
GROUP BY b.brand_name, cat.category_name, p.product_name;

-- Для Treemap: вклад категорий в общие продажи
SELECT 
    cat.category_name,
    SUM(oi.quantity * oi.list_price * (1 - oi.discount)) as total_sales,
    COUNT(DISTINCT o.order_id) as order_count
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN categories cat ON p.category_id = cat.category_id
GROUP BY cat.category_name;

-- Для Word Cloud: популярные слова в названиях продуктов
SELECT 
    UNNEST(STRING_TO_ARRAY(LOWER(product_name), ' ')) as word,
    COUNT(*) as frequency
FROM products
WHERE LENGTH(UNNEST(STRING_TO_ARRAY(LOWER(product_name), ' '))) > 3
GROUP BY word
ORDER BY frequency DESC;

-- Для географической визуализации (добавляем координаты)
ALTER TABLE stores ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 6);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS longitude DECIMAL(10, 6);

-- Обновляем координаты для существующих магазинов
UPDATE stores SET 
    latitude = CASE store_id
        WHEN 1 THEN 40.7128  -- Нью-Йорк
        WHEN 2 THEN 34.0522  -- Лос-Анджелес  
        WHEN 3 THEN 41.8781  -- Чикаго
        ELSE 39.8283 END,    -- Произвольные
    longitude = CASE store_id
        WHEN 1 THEN -74.0060
        WHEN 2 THEN -118.2437
        WHEN 3 THEN -87.6298
        ELSE -98.5795 END;

-- Запрос для карты
SELECT 
    store_name,
    city,
    state,
    latitude,
    longitude,
    COUNT(o.order_id) as order_count,
    SUM(oi.quantity * oi.list_price * (1 - oi.discount)) as total_sales
FROM stores s
LEFT JOIN orders o ON s.store_id = o.store_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY s.store_id, store_name, city, state, latitude, longitude;

-- Для нормализации данных (Calculated Column пример)
SELECT 
    product_id,
    product_name,
    list_price,
    (list_price - MIN(list_price) OVER()) / (MAX(list_price) OVER() - MIN(list_price) OVER()) as normalized_price
FROM products;

-- Для категоризации (Calculated Column пример)
SELECT 
    product_id,
    product_name,
    list_price,
    CASE 
        WHEN list_price < 500 THEN 'Budget'
        WHEN list_price BETWEEN 500 AND 1500 THEN 'Standard' 
        WHEN list_price BETWEEN 1500 AND 3000 THEN 'Premium'
        ELSE 'Luxury'
    END as price_category
FROM products;