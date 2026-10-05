CREATE TABLE dq_exceptions (
    exception_type VARCHAR(40) NOT NULL,
    case_id VARCHAR(10) NOT NULL,
    member_id VARCHAR(10),
    detail VARCHAR(200) NOT NULL,
    dp_batch_id VARCHAR(36) NOT NULL
);
