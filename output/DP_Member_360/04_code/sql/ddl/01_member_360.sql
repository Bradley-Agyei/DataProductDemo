CREATE TABLE member_360 (
    member_id VARCHAR(10) NOT NULL,
    member_since_date DATE NOT NULL,
    member_segment VARCHAR(20) NOT NULL,
    age_band VARCHAR(5),
    home_state CHAR(2) NOT NULL,
    digital_enrolled_flag BOOLEAN,
    kyc_status VARCHAR(20),
    risk_rating VARCHAR(10),
    relationship_status VARCHAR(15) NOT NULL,
    last_profile_update_ts TIMESTAMP,
    dp_load_ts TIMESTAMP NOT NULL,
    dp_batch_id VARCHAR(36) NOT NULL,
    PRIMARY KEY (member_id)
);
