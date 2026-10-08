CREATE TABLE dq_exceptions (
    exception_type VARCHAR(10) NOT NULL,
    rule_id VARCHAR(10) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    row_key VARCHAR(100) NOT NULL,
    detail VARCHAR(200) NOT NULL,
    dp_batch_id VARCHAR(36) NOT NULL
);
