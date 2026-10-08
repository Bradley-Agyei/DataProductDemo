CREATE TABLE rejects (
    table_name VARCHAR(50) NOT NULL,
    row_key VARCHAR(100) NOT NULL,
    column_name VARCHAR(64),
    raw_value TEXT,
    reason VARCHAR(200) NOT NULL,
    dp_batch_id VARCHAR(36) NOT NULL
);
