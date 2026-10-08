CREATE TABLE account_daily_balance (
    balance_date DATE NOT NULL,
    account_id VARCHAR(10) NOT NULL,
    member_id VARCHAR(10) NOT NULL,
    product_code VARCHAR(12),
    account_status VARCHAR(12) NOT NULL,
    opening_balance DECIMAL(15,2) NOT NULL,
    total_credits DECIMAL(15,2) NOT NULL,
    total_debits DECIMAL(15,2) NOT NULL,
    closing_balance DECIMAL(15,2) NOT NULL,
    available_balance DECIMAL(15,2),
    overdraft_flag BOOLEAN NOT NULL,
    transaction_count INT NOT NULL,
    pending_debits DECIMAL(15,2) NOT NULL,
    dp_load_ts TIMESTAMP NOT NULL,
    dp_batch_id VARCHAR(36) NOT NULL,
    PRIMARY KEY (balance_date, account_id)
);
