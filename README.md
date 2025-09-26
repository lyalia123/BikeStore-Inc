# BikeStore Analytics

## Company
BikeStore Inc. – это сеть магазинов велосипедов, где ведется аналитика продаж, остатков на складах и работы сотрудников.

## Project Overview
Проект включает создание базы данных `bikestore`, загрузку данных из CSV файлов и выполнение аналитических SQL-запросов для оценки продаж, остатков, заказов и работы персонала.

## ERD (Entity-Relationship Diagram)

```mermaid
erDiagram
    BRANDS ||--o{ PRODUCTS : "brand_id"
    CATEGORIES ||--o{ PRODUCTS : "category_id"
    PRODUCTS ||--o{ ORDER_ITEMS : "product_id"
    CUSTOMERS ||--o{ ORDERS : "customer_id"
    STORES ||--o{ STAFFS : "store_id"
    STORES ||--o{ ORDERS : "store_id"
    STAFFS ||--o{ ORDERS : "staff_id"
    ORDERS ||--o{ ORDER_ITEMS : "order_id"
    STORES ||--o{ STOCKS : "store_id"
    PRODUCTS ||--o{ STOCKS : "product_id"
    
    BRANDS {
        SERIAL brand_id PK
        VARCHAR brand_name
    }
    CATEGORIES {
        SERIAL category_id PK
        VARCHAR category_name
    }
    PRODUCTS {
        SERIAL product_id PK
        VARCHAR product_name
        INT brand_id FK
        INT category_id FK
        INT model_year
        NUMERIC list_price
    }
    CUSTOMERS {
        SERIAL customer_id PK
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR phone
        VARCHAR email
        VARCHAR street
        VARCHAR city
        VARCHAR state
        VARCHAR zip_code
    }
    STORES {
        SERIAL store_id PK
        VARCHAR store_name
        VARCHAR phone
        VARCHAR email
        VARCHAR street
        VARCHAR city
        VARCHAR state
        VARCHAR zip_code
    }
    STAFFS {
        SERIAL staff_id PK
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR email
        VARCHAR phone
        BOOLEAN active
        INT store_id FK
        INT manager_id
    }
    ORDERS {
        SERIAL order_id PK
        INT customer_id FK
        INT order_status
        DATE order_date
        DATE required_date
        DATE shipped_date
        INT store_id FK
        INT staff_id FK
    }
    ORDER_ITEMS {
        INT order_id FK
        SERIAL item_id PK
        INT product_id FK
        INT quantity
        NUMERIC list_price
        NUMERIC discount
    }
    STOCKS {
        INT store_id FK
        INT product_id FK
        INT quantity
    }
