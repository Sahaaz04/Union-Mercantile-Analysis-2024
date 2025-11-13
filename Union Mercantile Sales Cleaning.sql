DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
    invoice_no TEXT,
    stock_code TEXT,
    item_description TEXT,
    quantity FLOAT,
    invoice_date TIMESTAMP,
    unit_price FLOAT,
    customer_id TEXT,
    country TEXT
);

-- Fix Datetime Format
SET datestyle = 'ISO, MDY';

COPY transactions (
    invoice_no,
    stock_code, 
    item_description,
    quantity,
    invoice_date,
    unit_price,
    customer_id,
    country
)
FROM 'C:\Program Files\OnlineRetail.csv'
DELIMITER ','
CSV HEADER
ENCODING 'LATIN1'; -- Fix Encoding

-- Turning all empty ' ' strings into null values and removing spaces in front or back of strings.
UPDATE transactions
SET
    invoice_no = NULLIF(TRIM(invoice_no), ''),
    stock_code = NULLIF(TRIM(stock_code), ''),
    item_description = NULLIF(TRIM(item_description), ''),
    customer_id = NULLIF(TRIM(customer_id), ''),
    country = NULLIF(TRIM(country), '');

-- Deleting Negative Quantities and Deleting Null values of Invoice Date and Customer ID.
DELETE FROM transactions WHERE quantity < 0;
DELETE FROM transactions WHERE invoice_date IS NULL;
DELETE FROM transactions WHERE customer_id IS NULL;

-- Updating Location names.
UPDATE transactions
SET country = CASE
    WHEN country = 'RSA' THEN 'South Africa'
    WHEN country = 'EIRE' THEN 'Ireland'
    WHEN country = 'European Community' THEN 'Unspecified'
    ELSE country
    END;

-- Deleting non-product transactions.
DELETE FROM transactions 
WHERE stock_code IN ('POST', 'DOT', 'C2', 'MISC', 'BANK CHARGES', 'PADS', 'M');


-- Cleaning summary.
-- Fixed Datetime Format
-- Fixed Encoding
-- Turned all empty ' ' strings into null values and removing spaces in front or back of strings.
-- Deleted Negative Quantities and Deleting Null values of Invoice Date and Customer ID.
-- Updated Location names.
-- Deleted non-product transactions.


-- Exporting cleaned Data.
COPY transactions TO 'C:/Users/Public/UCI_Retail_Cleaned.csv' DELIMITER ',' CSV HEADER;







