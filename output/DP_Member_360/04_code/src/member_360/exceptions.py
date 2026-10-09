"""Exception report for risk & compliance: valid data that still needs a human look."""
from __future__ import annotations

import pandas as pd

from contracts.member_360 import DQ_EXCEPTIONS

COLUMNS = [c for c in DQ_EXCEPTIONS.column_names if c != "dp_batch_id"]


def negative_balances(transaction: pd.DataFrame, id_map: dict) -> list[dict]:
    rows = transaction[[v is not None and v < 0 for v in transaction["balance_after"]]]
    return [{
        "exception_type": "NEGATIVE_BALANCE",
        "member_id": id_map.get(r["member_id"]),
        "account_id": r["account_id"],
        "transaction_id": r["transaction_id"],
        "detail": f"balance_after {r['balance_after']} after {r['transaction_status']} transaction",
    } for r in rows.to_dict("records")]


def dormant_restricted_activity(member: pd.DataFrame, account: pd.DataFrame, transaction: pd.DataFrame,
                                id_map: dict) -> list[dict]:
    dormant = set(member.loc[member["member_status"] == "Dormant", "member_id"])
    accounts = set(account.loc[(account["account_status"] == "Restricted")
                               & account["member_id"].isin(list(dormant)), "account_id"])
    rows = transaction[transaction["account_id"].isin(list(accounts))]
    return [{
        "exception_type": "DORMANT_RESTRICTED_ACTIVITY",
        "member_id": id_map.get(r["member_id"]),
        "account_id": r["account_id"],
        "transaction_id": r["transaction_id"],
        "detail": f"{r['transaction_status']} transaction on Restricted account of Dormant member",
    } for r in rows.to_dict("records")]


def find_exceptions(staged: dict[str, pd.DataFrame], id_map: dict, batch_id: str) -> pd.DataFrame:
    rows = (negative_balances(staged["Transaction"], id_map)
            + dormant_restricted_activity(staged["Member"], staged["Account"], staged["Transaction"], id_map))
    return pd.DataFrame(rows, columns=COLUMNS, dtype=object).assign(dp_batch_id=batch_id)
