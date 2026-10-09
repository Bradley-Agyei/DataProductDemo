CREATE TABLE fraud_case_status_snapshot (
    snapshot_date DATE NOT NULL,
    case_id VARCHAR(10) NOT NULL,
    case_status VARCHAR(15) NOT NULL,
    priority VARCHAR(10) NOT NULL,
    assigned_queue VARCHAR(30) NOT NULL,
    dp_batch_id VARCHAR(36) NOT NULL,
    PRIMARY KEY (snapshot_date, case_id)
);
