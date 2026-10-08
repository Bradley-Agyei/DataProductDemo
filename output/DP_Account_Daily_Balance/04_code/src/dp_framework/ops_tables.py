"""Operational tables every data product writes: rejects, DQ results and the run log."""
from .contract import Column as C, Table

REJECTS = Table("rejects", (
    C("table_name", "VARCHAR(50)", description="Table the row came from."),
    C("row_key", "VARCHAR(100)", description="Primary key value(s) of the rejected row."),
    C("column_name", "VARCHAR(64)", nullable=True, description="Column that failed, if column-level."),
    C("raw_value", "TEXT", nullable=True, description="Value as received."),
    C("reason", "VARCHAR(200)", description="Why the row was rejected."),
    C("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID."),
), grain="One row per rejected value or row")

DQ_RESULTS = Table("dq_results", (
    C("rule_id", "VARCHAR(10)", description="DQ rule ID."),
    C("description", "VARCHAR(200)", description="What the rule checks."),
    C("table_name", "VARCHAR(50)", description="Table checked."),
    C("severity", "VARCHAR(10)", allowed=("block", "reject", "warn"), description="Action on failure."),
    C("rows_checked", "INT", description="Rows evaluated."),
    C("rows_failed", "INT", description="Rows (or count difference) failing."),
    C("status", "VARCHAR(10)", allowed=("Pass", "Warn", "Reject", "Fail"), description="Outcome."),
    C("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID."),
    C("run_ts", "TIMESTAMP", description="When the rule ran."),
), grain="One row per rule per run")

RUN_LOG = Table("run_log", (
    C("table_name", "VARCHAR(50)", description="Table built."),
    C("layer", "VARCHAR(10)", description="staging or product."),
    C("rows_in", "INT", description="Rows read."),
    C("rows_out", "INT", description="Rows written."),
    C("rows_rejected", "INT", description="rows_in - rows_out."),
    C("status", "VARCHAR(10)", description="SUCCESS or BLOCKED."),
    C("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID."),
    C("run_ts", "TIMESTAMP", description="When the run happened."),
), grain="One row per table per run")
