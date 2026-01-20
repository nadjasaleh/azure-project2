BEGIN;

CREATE TABLE IF NOT EXISTS consultant (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS customer (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS shift (
    id SERIAL PRIMARY KEY,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    lunch_break BOOLEAN DEFAULT TRUE,
    consultant_id INT NOT NULL,
    customer_id INT NOT NULL,
    CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE CASCADE,
    CONSTRAINT fk_consultant FOREIGN KEY (consultant_id) REFERENCES consultant(id) ON DELETE CASCADE,
    CONSTRAINT shift_end_after_start CHECK (end_time > start_time)
);

COMMIT;
