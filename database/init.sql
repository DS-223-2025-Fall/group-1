-- ================================
-- DIMENSION TABLES
-- ================================

-- 1. Restaurant Dimension
CREATE TABLE dim_restaurant (
    restaurant_id      SERIAL PRIMARY KEY,
    restaurant_name    VARCHAR(255),
    city               VARCHAR(100),
    state              VARCHAR(50),
    country            VARCHAR(50)
);

-- 2. Category Dimension
CREATE TABLE dim_category (
    category_id        SERIAL PRIMARY KEY,
    category_name      VARCHAR(100)
);

-- 3. Menu Item Dimension
CREATE TABLE dim_menu_item (
    product_id         SERIAL PRIMARY KEY,
    product_name       VARCHAR(255),
    price              NUMERIC(10,2),
    restaurant_id      INT,
    category_id        INT,
    CONSTRAINT fk_menu_restaurant
        FOREIGN KEY (restaurant_id) REFERENCES dim_restaurant (restaurant_id),
    CONSTRAINT fk_menu_category
        FOREIGN KEY (category_id) REFERENCES dim_category (category_id)
);

-- 4. Customer Dimension
CREATE TABLE dim_customer (
    customer_id        SERIAL PRIMARY KEY,
    customer_name      VARCHAR(255),
    email              VARCHAR(255),
    phone_number       VARCHAR(50)
);

-- 5. Season Dimension
CREATE TABLE dim_season (
    season             VARCHAR(20) PRIMARY KEY
);

-- 6. Time Dimension
CREATE TABLE dim_time (
    date               DATE PRIMARY KEY,
    year               INT,
    month              INT,
    day                INT,
    season             VARCHAR(20),
    CONSTRAINT fk_time_season
        FOREIGN KEY (season) REFERENCES dim_season (season)
);

-- 7. Market Dimension
CREATE TABLE dim_market (
    market_id          SERIAL PRIMARY KEY,
    region             VARCHAR(255)
);

-- ================================
-- FACT TABLES
-- ================================

-- 8. Sales Fact Table
CREATE TABLE fact_sales (
    sale_id            SERIAL PRIMARY KEY,
    product_id         INT,
    restaurant_id      INT,
    customer_id        INT,
    date               DATE,
    units_sold         INT,
    amount             NUMERIC(10,2),

    CONSTRAINT fk_sales_product
        FOREIGN KEY (product_id) REFERENCES dim_menu_item (product_id),

    CONSTRAINT fk_sales_restaurant
        FOREIGN KEY (restaurant_id) REFERENCES dim_restaurant (restaurant_id),

    CONSTRAINT fk_sales_customer
        FOREIGN KEY (customer_id) REFERENCES dim_customer (customer_id),

    CONSTRAINT fk_sales_date
        FOREIGN KEY (date) REFERENCES dim_time (date)
);

-- 9. Market Prices Fact Table
CREATE TABLE fact_market_prices (
    price_id           SERIAL PRIMARY KEY,
    market_id          INT,
    date               DATE,
    price              NUMERIC(10,2),

    CONSTRAINT fk_market_price_market
        FOREIGN KEY (market_id) REFERENCES dim_market (market_id),

    CONSTRAINT fk_market_price_date
        FOREIGN KEY (date) REFERENCES dim_time (date)
);
