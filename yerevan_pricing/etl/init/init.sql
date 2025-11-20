-- Initialize DB schema for ETL
-- (Copied from etl/database/init/init.sql)

-- DROP OLD TABLES (order matters)
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS fact_market_prices CASCADE;
DROP TABLE IF EXISTS dim_menu_item CASCADE;
DROP TABLE IF EXISTS dim_restaurant CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_category CASCADE;
DROP TABLE IF EXISTS dim_market CASCADE;
DROP TABLE IF EXISTS dim_time CASCADE;
DROP TABLE IF EXISTS dim_season CASCADE;

------------------------------------------------
-- DIM TABLES
------------------------------------------------

CREATE TABLE dim_category (
    category_id    INT PRIMARY KEY,
    category_name  VARCHAR(255)
);

CREATE TABLE dim_season (
    season   VARCHAR(50) PRIMARY KEY,
    months   VARCHAR(255)
);

CREATE TABLE dim_time (
    date         DATE PRIMARY KEY,
    year         INT,
    month        INT,
    day          INT,
    day_of_week  INT,
    season       VARCHAR(50) REFERENCES dim_season(season)
);

CREATE TABLE dim_market (
    market_id    INT PRIMARY KEY,
    admin1       VARCHAR(255),
    admin2       VARCHAR(255),
    market_name  VARCHAR(255),
    latitude     DOUBLE PRECISION,
    longitude    DOUBLE PRECISION
);

CREATE TABLE dim_restaurant (
    restaurant_id       INT PRIMARY KEY,
    name                VARCHAR(255),
    location            VARCHAR(255),
    type                VARCHAR(100),
    avg_customer_count  DOUBLE PRECISION,
    rating              DOUBLE PRECISION,
    owner_contact       VARCHAR(255)
);

CREATE TABLE dim_customer (
    customer_id      INT PRIMARY KEY,
    gender           VARCHAR(50),
    age_group        VARCHAR(50),
    avg_spending     DOUBLE PRECISION,
    visit_frequency  INT
);

CREATE TABLE dim_menu_item (
    product_id     INT PRIMARY KEY,
    restaurant_id  INT REFERENCES dim_restaurant(restaurant_id),
    product_name   VARCHAR(255),
    category_id    INT REFERENCES dim_category(category_id),
    base_price     NUMERIC(10,2),
    cost           NUMERIC(10,2),
    portion_size   VARCHAR(100),
    available      BOOLEAN
);

------------------------------------------------
-- FACT TABLES
------------------------------------------------

CREATE TABLE fact_sales (
    sale_id        INT PRIMARY KEY,
    product_id     INT REFERENCES dim_menu_item(product_id),
    restaurant_id  INT REFERENCES dim_restaurant(restaurant_id),
    customer_id    INT REFERENCES dim_customer(customer_id),
    date           DATE REFERENCES dim_time(date),
    units_sold     INT,
    price_sold     NUMERIC(10,2),
    revenue        NUMERIC(10,2)
);

CREATE TABLE fact_market_prices (
    price_id    INT PRIMARY KEY,
    date        DATE REFERENCES dim_time(date),
    market_id   INT REFERENCES dim_market(market_id),
    category    VARCHAR(255),
    commodity   VARCHAR(255),
    unit        VARCHAR(50),
    priceflag   VARCHAR(50),
    pricetype   VARCHAR(50),
    currency    VARCHAR(50),
    price       NUMERIC(10,2),
    usdprice    NUMERIC(10,2)
);
