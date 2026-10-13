"""FR-06 (SCRUM-42): account attributes and the dormant-activity warning.

    roll-forward rows -> + member_id, account_status, product_code -> publish

account_status is the Account value on the run date, applied to every day (Q11).
product_code is looked up by product_id in the Product team's reference table
(Q6); while that table is absent it is NULL and the contract keeps it pending.

The warnings come out as exception-report rows and reach publish through
`upstream_warnings`: DQ-13 is reported once per member, which a product-row
Rule cannot express, and DQ-14 once per account.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from contracts.account_daily_balance import ACCOUNT_DAILY_BALANCE
from contracts.sources import PRODUCT_CODE_REF
from src.dp_framework.standardize import standardize

from . import config

PRODUCT = ACCOUNT_DAILY_BALANCE.name
ATTRIBUTES = ["member_id", "account_status", "product_code"]


def load_product_code_ref(path: Path = config.PRODUCT_CODE_MAP_PATH) -> pd.DataFrame | None:
    """The product code reference table, or None while it has not been supplied.

    A bad table stops the run: rejecting a row would silently NULL a whole product.
    """
    path = Path(path)
    if not path.exists():
        return None
    raw = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    typed, rejects = standardize(raw, PRODUCT_CODE_REF)
    if not rejects.empty:
        problems = "; ".join(f"{r['row_key']}: {r['reason']}" for r in rejects.to_dict("records"))
        raise ValueError(f"{path.name} is invalid: {problems}")
    return typed


def _warning(rule_id: str, row_key: str, detail: str) -> dict:
    return {"exception_type": "WARN", "rule_id": rule_id, "table_name": PRODUCT,
            "row_key": row_key, "detail": detail}


def account_attributes(balances: pd.DataFrame, accounts: pd.DataFrame,
                       product_ref: pd.DataFrame | None = None) -> tuple[pd.DataFrame, list[dict]]:
    """Add member_id, account_status and product_code to the roll-forward rows.

    `accounts`: standardized Account (account_id, member_id, product_id, account_status).
    Returns the rows and one DQ-14 warning per account whose product has no code;
    DQ-14 only applies once a reference table is supplied.
    """
    attrs = accounts[["account_id", "member_id", "product_id", "account_status"]]
    if attrs["account_id"].duplicated().any():
        raise ValueError("accounts has duplicate account_id")
    unknown = sorted(set(balances["account_id"]) - set(attrs["account_id"]))
    if unknown:
        raise ValueError(f"balance rows for accounts not in Account: {unknown[:5]}")

    codes = {} if product_ref is None else dict(zip(product_ref["product_id"], product_ref["product_code"]))
    attrs = attrs.assign(product_code=attrs["product_id"].map(lambda p: codes.get(p) if pd.notna(p) else None))

    warnings = []
    if product_ref is not None:
        for r in attrs[attrs["product_code"].isna()].sort_values("account_id").to_dict("records"):
            product = "no product_id" if pd.isna(r["product_id"]) else f"product_id {r['product_id']}"
            warnings.append(_warning("DQ-14", r["account_id"],
                                     f"product_id has no product_code in the reference table ({product})"))

    rows = balances.drop(columns=[c for c in ATTRIBUTES if c in balances.columns])
    rows = rows.merge(attrs[["account_id", *ATTRIBUTES]], on="account_id", how="left")
    rows["product_code"] = rows["product_code"].astype(object).where(rows["product_code"].notna(), None)
    order = [c for c in ACCOUNT_DAILY_BALANCE.column_names if c in rows.columns]
    return rows[order + [c for c in rows.columns if c not in order]], warnings


def dormant_activity(accounts: pd.DataFrame, members: pd.DataFrame,
                     transactions: pd.DataFrame) -> list[dict]:
    """DQ-13: one warning per Dormant member with any transaction in the run.

    Any status counts (Posted, Pending or Reversed): activity on a dormant
    member is the signal, whether or not it reaches the ledger (Q4, Q10).
    `members`: member_id, member_status only; no Member PII is read or written.
    """
    dormant = set(members.loc[members["member_status"] == "Dormant", "member_id"])
    owner = dict(zip(accounts["account_id"], accounts["member_id"]))
    activity = pd.DataFrame({"account_id": transactions["account_id"],
                             "member_id": transactions["account_id"].map(owner)})
    activity = activity[activity["member_id"].isin(dormant)]

    warnings = []
    for member_id, rows in activity.groupby("member_id", sort=True):
        n_accounts = rows["account_id"].nunique()
        warnings.append(_warning("DQ-13", member_id,
                                 f"Dormant member with activity: {len(rows)} transactions on "
                                 f"{n_accounts} account{'s' if n_accounts != 1 else ''}"))
    return warnings
