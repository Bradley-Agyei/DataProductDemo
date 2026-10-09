CREATE TABLE dq_results (
    rule_id VARCHAR(10) NOT NULL,
    description VARCHAR(200) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    rows_checked INT NOT NULL,
    rows_failed INT NOT NULL,
    status VARCHAR(10) NOT NULL,
    dp_batch_id VARCHAR(36) NOT NULL,
    run_ts TIMESTAMP NOT NULL
);
