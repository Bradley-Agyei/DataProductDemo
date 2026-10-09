CREATE TABLE dq_exceptions (
    exception_type VARCHAR(40) NOT NULL,
    member_id VARCHAR(10),
    account_id VARCHAR(10),
    transaction_id VARCHAR(12),
    detail VARCHAR(200) NOT NULL,
    dp_batch_id VARCHAR(36) NOT NULL
);
