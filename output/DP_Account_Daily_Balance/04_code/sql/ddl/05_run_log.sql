CREATE TABLE run_log (
    table_name VARCHAR(50) NOT NULL,
    layer VARCHAR(10) NOT NULL,
    rows_in INT NOT NULL,
    rows_out INT NOT NULL,
    rows_rejected INT NOT NULL,
    status VARCHAR(10) NOT NULL,
    dp_batch_id VARCHAR(36) NOT NULL,
    run_ts TIMESTAMP NOT NULL
);
