CREATE TABLE member_id_xref (
    source_member_id VARCHAR(10) NOT NULL,
    member_id VARCHAR(10) NOT NULL,
    source_system VARCHAR(30) NOT NULL,
    dp_load_ts TIMESTAMP NOT NULL,
    PRIMARY KEY (source_member_id)
);
