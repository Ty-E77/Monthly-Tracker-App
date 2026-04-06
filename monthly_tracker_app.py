import json
import math
import uuid
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Monthly Tracker for TyShawn & Lexi",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------
# Constants
# -----------------------------
APP_TITLE = "Monthly Budget + Tracker"
DATA_FILE = Path("monthly_tracker_data.json")
USER_CREDENTIALS = {
    "tyshawn": "lexi",
    "lexi": "tyshawn",
}
DISPLAY_NAMES = {
    "tyshawn": "TyShawn",
    "lexi": "Lexi",
}
OWNERS = ["shared", "tyshawn", "lexi"]
OWNER_LABELS = {
    "shared": "Both / Shared",
    "tyshawn": "TyShawn",
    "lexi": "Lexi",
}
ENTRY_TYPE_LABELS = {
    "expense": "Expense",
    "revenue": "Revenue",
}
EXPENSE_CATEGORIES = [
    "Rent + Utilities",
    "Groceries",
    "Gas",
    "Car Insurance",
    "Toiletries",
    "Eating Out",
    "Phone Bill",
    "Subscriptions",
    "Shopping",
    "Health",
    "Entertainment",
    "Debt Payment",
    "Savings Transfer",
    "Travel",
    "Other",
]
REVENUE_CATEGORIES = [
    "Paycheck",
    "Side Hustle",
    "Cash Gift",
    "Refund",
    "Bonus",
    "Other",
]
ALL_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


# -----------------------------
# Helpers: data storage
# -----------------------------
def empty_budget_block():
    return {
        "expense": {category: 0.0 for category in EXPENSE_CATEGORIES},
        "revenue": {category: 0.0 for category in REVENUE_CATEGORIES},
    }


def empty_month_record():
    return {
        owner: empty_budget_block() for owner in OWNERS
    }


def default_data_store():
    current_key = month_key_from_date(date.today())
    return {
        "budgets": {current_key: empty_month_record()},
        "transactions": [],
    }


def load_json_dict(file_path: Path) -> dict:
    if not file_path.exists():
        return default_data_store()

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return default_data_store()

    if not isinstance(data, dict):
        return default_data_store()

    data.setdefault("budgets", {})
    data.setdefault("transactions", [])

    if not isinstance(data["budgets"], dict):
        data["budgets"] = {}
    if not isinstance(data["transactions"], list):
        data["transactions"] = []

    return data


def save_json_dict(file_path: Path, data: dict) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


# -----------------------------
# Helpers: month handling
# -----------------------------
def month_key_from_date(value: date) -> str:
    return value.strftime("%Y-%m")


def month_label(month_key: str) -> str:
    year, month = month_key.split("-")
    return f"{ALL_MONTHS[int(month) - 1]} {year}"


def label_to_month_key(label: str) -> str:
    month_name, year = label.rsplit(" ", 1)
    month_num = ALL_MONTHS.index(month_name) + 1
    return f"{year}-{month_num:02d}"


def previous_month_key(month_key: str) -> str:
    year, month = [int(part) for part in month_key.split("-")]
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"


def sorted_month_keys(data: dict) -> list[str]:
    month_keys = set(data.get("budgets", {}).keys())
    for transaction in data.get("transactions", []):
        month_key = transaction.get("month_key")
        if month_key:
            month_keys.add(month_key)
    month_keys.add(month_key_from_date(date.today()))
    return sorted(month_keys)


def ensure_month_exists(data: dict, month_key: str) -> None:
    data.setdefault("budgets", {})
    if month_key in data["budgets"]:
        return

    prior_key = previous_month_key(month_key)
    if prior_key in data["budgets"]:
        data["budgets"][month_key] = deepcopy(data["budgets"][prior_key])
    else:
        data["budgets"][month_key] = empty_month_record()


# -----------------------------
# Helpers: validation + parsing
# -----------------------------
def validate_credentials(username: str, password: str) -> bool:
    return USER_CREDENTIALS.get(username.lower().strip()) == password.strip()


def normalize_transaction(record: dict) -> dict | None:
    required_keys = {
        "id",
        "month_key",
        "date",
        "entry_type",
        "owner",
        "category",
        "amount",
        "description",
        "created_by",
        "created_at",
    }
    if not isinstance(record, dict) or not required_keys.issubset(record.keys()):
        return None

    try:
        amount = float(record["amount"])
    except (TypeError, ValueError):
        return None

    normalized = {
        "id": str(record["id"]),
        "month_key": str(record["month_key"]),
        "date": str(record["date"]),
        "entry_type": str(record["entry_type"]),
        "owner": str(record["owner"]),
        "category": str(record["category"]),
        "amount": amount,
        "description": str(record.get("description", "")),
        "created_by": str(record["created_by"]),
        "created_at": str(record["created_at"]),
        "updated_at": str(record.get("updated_at", "")),
    }

    if normalized["entry_type"] not in ["expense", "revenue"]:
        return None
    if normalized["owner"] not in OWNERS:
        return None

    return normalized


def normalize_budget_section(section: dict, categories: list[str]) -> dict:
    normalized = {category: 0.0 for category in categories}
    if isinstance(section, dict):
        for category in categories:
            try:
                normalized[category] = float(section.get(category, 0.0) or 0.0)
            except (TypeError, ValueError):
                normalized[category] = 0.0
    return normalized


def sanitize_loaded_data(data: dict) -> dict:
    clean = default_data_store()

    if isinstance(data.get("budgets"), dict):
        clean["budgets"] = {}
        for month_key, month_record in data["budgets"].items():
            month_clean = empty_month_record()
            if isinstance(month_record, dict):
                for owner in OWNERS:
                    owner_record = month_record.get(owner, {})
                    if isinstance(owner_record, dict):
                        month_clean[owner]["expense"] = normalize_budget_section(
                            owner_record.get("expense", {}), EXPENSE_CATEGORIES
                        )
                        month_clean[owner]["revenue"] = normalize_budget_section(
                            owner_record.get("revenue", {}), REVENUE_CATEGORIES
                        )
            clean["budgets"][month_key] = month_clean

    clean_transactions = []
    for transaction in data.get("transactions", []):
        normalized = normalize_transaction(transaction)
        if normalized:
            clean_transactions.append(normalized)
    clean["transactions"] = clean_transactions

    ensure_month_exists(clean, month_key_from_date(date.today()))
    return clean


# -----------------------------
# Helpers: session state
# -----------------------------
def init_session_state() -> None:
    defaults = {
        "logged_in": False,
        "current_user": None,
        "page": "dashboard",
        "selected_month": month_key_from_date(date.today()),
        "editing_transaction_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# -----------------------------
# Helpers: transaction logic
# -----------------------------
def current_username() -> str:
    return str(st.session_state.get("current_user", "")).lower()


def can_edit_transaction(transaction: dict) -> bool:
    username = current_username()
    if transaction["owner"] == "shared":
        return True
    return transaction["created_by"] == username


def add_transaction(
    data: dict,
    month_key: str,
    entry_date: date,
    entry_type: str,
    owner: str,
    category: str,
    amount: float,
    description: str,
    created_by: str,
) -> None:
    ensure_month_exists(data, month_key)
    data["transactions"].append(
        {
            "id": str(uuid.uuid4()),
            "month_key": month_key,
            "date": entry_date.isoformat(),
            "entry_type": entry_type,
            "owner": owner,
            "category": category,
            "amount": float(amount),
            "description": description.strip(),
            "created_by": created_by,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": "",
        }
    )


def transactions_for_month(data: dict, month_key: str) -> list[dict]:
    return [
        transaction for transaction in data["transactions"]
        if transaction.get("month_key") == month_key
    ]


def transaction_dataframe(data: dict, month_key: str) -> pd.DataFrame:
    month_transactions = transactions_for_month(data, month_key)
    if not month_transactions:
        return pd.DataFrame(
            columns=[
                "id",
                "date",
                "entry_type",
                "owner",
                "category",
                "amount",
                "description",
                "created_by",
            ]
        )

    df = pd.DataFrame(month_transactions)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["entry_type_label"] = df["entry_type"].map(ENTRY_TYPE_LABELS)
    df["owner_label"] = df["owner"].map(OWNER_LABELS)
    df["created_by_label"] = df["created_by"].map(DISPLAY_NAMES).fillna(df["created_by"])
    return df


# -----------------------------
# Helpers: summary calculations
# -----------------------------
def owner_filtered_df(df: pd.DataFrame, owner: str) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    if owner == "shared":
        return df[df["owner"] == "shared"].copy()
    return df[df["owner"] == owner].copy()


def monthly_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "revenue": 0.0,
            "expense": 0.0,
            "net": 0.0,
        }
    revenue = float(df.loc[df["entry_type"] == "revenue", "amount"].sum())
    expense = float(df.loc[df["entry_type"] == "expense", "amount"].sum())
    return {
        "revenue": revenue,
        "expense": expense,
        "net": revenue - expense,
    }


def budget_totals_for_owner(data: dict, month_key: str, owner: str) -> dict:
    ensure_month_exists(data, month_key)
    record = data["budgets"][month_key][owner]
    return {
        "revenue_budget": sum(record["revenue"].values()),
        "expense_budget": sum(record["expense"].values()),
    }


def combined_budget_totals(data: dict, month_key: str) -> dict:
    totals = {"revenue_budget": 0.0, "expense_budget": 0.0}
    for owner in OWNERS:
        owner_totals = budget_totals_for_owner(data, month_key, owner)
        totals["revenue_budget"] += owner_totals["revenue_budget"]
        totals["expense_budget"] += owner_totals["expense_budget"]
    return totals


# -----------------------------
# UI helpers
# -----------------------------
def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def metric_card(title: str, value: str, caption: str = "") -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.markdown(f"### {value}")
        if caption:
            st.caption(caption)


def show_month_selector(data: dict) -> None:
    month_keys = sorted_month_keys(data)
    labels = [month_label(month_key) for month_key in month_keys]

    if st.session_state["selected_month"] not in month_keys:
        st.session_state["selected_month"] = month_key_from_date(date.today())
        ensure_month_exists(data, st.session_state["selected_month"])
        save_json_dict(DATA_FILE, data)
        month_keys = sorted_month_keys(data)
        labels = [month_label(month_key) for month_key in month_keys]

    selected_label = st.selectbox(
        "Month",
        options=labels,
        index=month_keys.index(st.session_state["selected_month"]),
        key="month_switcher_select",
    )
    selected_key = label_to_month_key(selected_label)
    if selected_key != st.session_state["selected_month"]:
        st.session_state["selected_month"] = selected_key
        ensure_month_exists(data, selected_key)
        save_json_dict(DATA_FILE, data)
        st.rerun()

    current_key = month_key_from_date(date.today())
    if st.session_state["selected_month"] != current_key:
        if st.button("Jump to Current Month", key="nav_jump_current_month_btn", use_container_width=True):
            ensure_month_exists(data, current_key)
            save_json_dict(DATA_FILE, data)
            st.session_state["selected_month"] = current_key
            st.rerun()


# -----------------------------
# Login page
# -----------------------------
def show_login_page() -> None:
    st.markdown(f"# {APP_TITLE}")
    st.caption("Track shared and personal revenues, expenses, budgets, and monthly trends together.")
    st.divider()

    left, right = st.columns([1.2, 0.8])

    with left:
        with st.container(border=True):
            st.markdown("### What this app does")
            st.markdown(
                """
                - track **shared and personal** income + expenses
                - manage **joint and separate monthly budgets**
                - use **Quick Add** for on-the-go entries
                - switch between **previous months**
                - review **analytics and trends**
                """
            )

    with right:
        with st.container(border=True):
            st.markdown("### Log In")
            username = st.text_input("Username", placeholder="tyshawn or lexi", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")

            if st.button("Log In", key="auth_login_btn", type="primary", use_container_width=True):
                if not username or not password:
                    st.error("Please enter both username and password.")
                    st.stop()

                if validate_credentials(username, password):
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = username.strip().lower()
                    st.session_state["page"] = "dashboard"
                    st.rerun()
                else:
                    st.error("Invalid login. Use the usernames/passwords you gave me.")

        with st.container(border=True):
            st.markdown("### Login Info")
            st.markdown("**TyShawn login** → username: `tyshawn`, password: `lexi`")
            st.markdown("**Lexi login** → username: `lexi`, password: `tyshawn`")


# -----------------------------
# Sidebar
# -----------------------------
def show_sidebar(data: dict) -> None:
    with st.sidebar:
        name = DISPLAY_NAMES.get(current_username(), current_username().title())
        st.markdown(f"# 💸 {APP_TITLE}")
        st.caption(f"Logged in as **{name}**")
        st.divider()

        show_month_selector(data)
        st.divider()

        nav_items = [
            ("dashboard", "🏠 Dashboard", "nav_dashboard_btn"),
            ("quick_add", "⚡ Quick Add", "nav_quick_add_btn"),
            ("tracker", "🧾 Monthly Tracker", "nav_tracker_btn"),
            ("budget", "📘 Budget Planner", "nav_budget_btn"),
            ("analytics", "📊 Analytics", "nav_analytics_btn"),
        ]

        for page_name, label, key in nav_items:
            button_type = "primary" if st.session_state["page"] == page_name else "secondary"
            if st.button(label, key=key, type=button_type, use_container_width=True):
                st.session_state["page"] = page_name
                st.rerun()

        st.divider()
        if st.button("🚪 Log Out", key="nav_logout_btn", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["current_user"] = None
            st.session_state["page"] = "dashboard"
            st.rerun()


# -----------------------------
# Dashboard
# -----------------------------
def show_dashboard(data: dict) -> None:
    month_key = st.session_state["selected_month"]
    df = transaction_dataframe(data, month_key)

    st.markdown(f"## Dashboard · {month_label(month_key)}")
    st.caption("See this month at a glance across shared and personal finances.")
    st.divider()

    overall = monthly_summary(df)
    ty_df = owner_filtered_df(df, "tyshawn")
    lexi_df = owner_filtered_df(df, "lexi")
    shared_df = owner_filtered_df(df, "shared")
    budget_totals = combined_budget_totals(data, month_key)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Revenue", format_currency(overall["revenue"]), "All entries this month")
    with col2:
        metric_card("Expenses", format_currency(overall["expense"]), "All entries this month")
    with col3:
        metric_card("Net", format_currency(overall["net"]), "Revenue minus expenses")
    with col4:
        metric_card("Budgeted Expenses", format_currency(budget_totals["expense_budget"]), "Shared + personal budgets")

    st.divider()

    left, middle, right = st.columns(3)
    with left:
        summary = monthly_summary(ty_df)
        metric_card("TyShawn Net", format_currency(summary["net"]), "Personal entries only")
    with middle:
        summary = monthly_summary(lexi_df)
        metric_card("Lexi Net", format_currency(summary["net"]), "Personal entries only")
    with right:
        summary = monthly_summary(shared_df)
        metric_card("Shared Net", format_currency(summary["net"]), "Shared entries only")

    st.divider()
    st.markdown("### Recent Entries")
    if df.empty:
        st.info("No entries yet for this month. Use Quick Add to start tracking.")
    else:
        display_df = df.sort_values("date", ascending=False).head(10).copy()
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        display_df = display_df[
            ["date", "entry_type_label", "owner_label", "category", "amount", "description", "created_by_label"]
        ].rename(
            columns={
                "date": "Date",
                "entry_type_label": "Type",
                "owner_label": "Owner",
                "category": "Category",
                "amount": "Amount",
                "description": "Description",
                "created_by_label": "Added By",
            }
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)


# -----------------------------
# Quick Add page
# -----------------------------
def render_entry_form(data: dict, month_key: str, form_prefix: str) -> None:
    selected_date = st.date_input(
        "Date",
        value=date.today() if month_key == month_key_from_date(date.today()) else datetime.strptime(month_key + "-01", "%Y-%m-%d").date(),
        key=f"{form_prefix}_date",
    )
    entry_type = st.selectbox(
        "Entry Type",
        options=["expense", "revenue"],
        format_func=lambda value: ENTRY_TYPE_LABELS[value],
        key=f"{form_prefix}_type",
    )
    owner = st.selectbox(
        "Who does this belong to?",
        options=OWNERS,
        format_func=lambda value: OWNER_LABELS[value],
        key=f"{form_prefix}_owner",
    )

    categories = EXPENSE_CATEGORIES if entry_type == "expense" else REVENUE_CATEGORIES
    category = st.selectbox(
        "Category",
        options=categories,
        key=f"{form_prefix}_category",
    )
    amount = st.number_input(
        "Amount",
        min_value=0.0,
        step=1.0,
        format="%.2f",
        key=f"{form_prefix}_amount",
    )
    description = st.text_input(
        "Description",
        placeholder="Optional note",
        key=f"{form_prefix}_description",
    )

    if st.button("Add Entry", key=f"{form_prefix}_submit_btn", type="primary", use_container_width=True):
        if amount <= 0:
            st.error("Amount must be greater than zero.")
            st.stop()

        add_transaction(
            data=data,
            month_key=month_key,
            entry_date=selected_date,
            entry_type=entry_type,
            owner=owner,
            category=category,
            amount=amount,
            description=description,
            created_by=current_username(),
        )
        save_json_dict(DATA_FILE, data)
        st.success("Entry added successfully.")
        st.rerun()


def show_quick_add(data: dict) -> None:
    month_key = st.session_state["selected_month"]
    st.markdown(f"## Quick Add · {month_label(month_key)}")
    st.caption("Add a revenue or expense fast while you are on the go.")
    st.divider()

    with st.container(border=True):
        render_entry_form(data, month_key, "quick_add")


# -----------------------------
# Monthly tracker page
# -----------------------------
def editable_transaction_table(data: dict, df: pd.DataFrame, section_title: str) -> None:
    st.markdown(f"### {section_title}")
    if df.empty:
        st.info("No entries in this section yet.")
        return

    sorted_df = df.sort_values(["date", "created_at"], ascending=[False, False])
    for _, row in sorted_df.iterrows():
        transaction = next((item for item in data["transactions"] if item["id"] == row["id"]), None)
        if not transaction:
            continue

        with st.container(border=True):
            left, right = st.columns([4, 1.2])
            with left:
                st.markdown(f"**{row['date'].strftime('%Y-%m-%d')} · {ENTRY_TYPE_LABELS[row['entry_type']]} · {OWNER_LABELS[row['owner']]}**")
                st.markdown(f"{row['category']} — {format_currency(float(row['amount']))}")
                if row.get("description"):
                    st.caption(row["description"])
                st.caption(f"Added by {DISPLAY_NAMES.get(row['created_by'], row['created_by'])}")
            with right:
                can_edit = can_edit_transaction(transaction)
                if can_edit:
                    if st.button("Edit", key=f"edit_txn_btn_{row['id']}", use_container_width=True):
                        st.session_state["editing_transaction_id"] = row["id"]
                        st.rerun()
                    if st.button("Delete", key=f"delete_txn_btn_{row['id']}", use_container_width=True):
                        data["transactions"] = [item for item in data["transactions"] if item["id"] != row["id"]]
                        save_json_dict(DATA_FILE, data)
                        st.success("Entry deleted.")
                        if st.session_state.get("editing_transaction_id") == row["id"]:
                            st.session_state["editing_transaction_id"] = None
                        st.rerun()
                else:
                    st.caption("Only the creator can edit this personal entry.")

            if st.session_state.get("editing_transaction_id") == row["id"] and can_edit:
                st.divider()
                with st.container(border=True):
                    st.markdown("#### Update Entry")
                    entry_type = st.selectbox(
                        "Entry Type",
                        ["expense", "revenue"],
                        index=["expense", "revenue"].index(transaction["entry_type"]),
                        format_func=lambda value: ENTRY_TYPE_LABELS[value],
                        key=f"edit_type_{row['id']}",
                    )
                    owner = st.selectbox(
                        "Owner",
                        OWNERS,
                        index=OWNERS.index(transaction["owner"]),
                        format_func=lambda value: OWNER_LABELS[value],
                        key=f"edit_owner_{row['id']}",
                    )
                    categories = EXPENSE_CATEGORIES if entry_type == "expense" else REVENUE_CATEGORIES
                    category = st.selectbox(
                        "Category",
                        categories,
                        index=categories.index(transaction["category"]) if transaction["category"] in categories else 0,
                        key=f"edit_category_{row['id']}",
                    )
                    amount = st.number_input(
                        "Amount",
                        min_value=0.0,
                        value=float(transaction["amount"]),
                        step=1.0,
                        format="%.2f",
                        key=f"edit_amount_{row['id']}",
                    )
                    entry_date = st.date_input(
                        "Date",
                        value=datetime.strptime(transaction["date"], "%Y-%m-%d").date(),
                        key=f"edit_date_{row['id']}",
                    )
                    description = st.text_input(
                        "Description",
                        value=transaction.get("description", ""),
                        key=f"edit_desc_{row['id']}",
                    )
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Save Changes", key=f"save_txn_btn_{row['id']}", type="primary", use_container_width=True):
                            if amount <= 0:
                                st.error("Amount must be greater than zero.")
                                st.stop()
                            transaction["entry_type"] = entry_type
                            transaction["owner"] = owner
                            transaction["category"] = category
                            transaction["amount"] = float(amount)
                            transaction["date"] = entry_date.isoformat()
                            transaction["month_key"] = month_key_from_date(entry_date)
                            transaction["description"] = description.strip()
                            transaction["updated_at"] = datetime.now().isoformat(timespec="seconds")
                            save_json_dict(DATA_FILE, data)
                            st.session_state["editing_transaction_id"] = None
                            st.success("Entry updated.")
                            st.rerun()
                    with col_b:
                        if st.button("Cancel", key=f"cancel_txn_btn_{row['id']}", use_container_width=True):
                            st.session_state["editing_transaction_id"] = None
                            st.rerun()


def show_tracker(data: dict) -> None:
    month_key = st.session_state["selected_month"]
    df = transaction_dataframe(data, month_key)

    st.markdown(f"## Monthly Tracker · {month_label(month_key)}")
    st.caption("See all entries together, or break them out by shared, TyShawn, and Lexi.")
    st.divider()

    overall = monthly_summary(df)
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Total Revenue", format_currency(overall["revenue"]))
    with col2:
        metric_card("Total Expenses", format_currency(overall["expense"]))
    with col3:
        metric_card("Left Over", format_currency(overall["net"]))

    st.divider()
    tab_all, tab_shared, tab_ty, tab_lexi = st.tabs([
        "All Entries",
        "Shared",
        "TyShawn",
        "Lexi",
    ])

    with tab_all:
        editable_transaction_table(data, df, "All Entries")
    with tab_shared:
        editable_transaction_table(data, owner_filtered_df(df, "shared"), "Shared Entries")
    with tab_ty:
        editable_transaction_table(data, owner_filtered_df(df, "tyshawn"), "TyShawn Entries")
    with tab_lexi:
        editable_transaction_table(data, owner_filtered_df(df, "lexi"), "Lexi Entries")


# -----------------------------
# Budget planner page
# -----------------------------
def render_budget_editor(data: dict, month_key: str, owner: str) -> None:
    ensure_month_exists(data, month_key)
    budget_record = data["budgets"][month_key][owner]

    st.markdown(f"### {OWNER_LABELS[owner]} Budgets")
    expense_tab, revenue_tab = st.tabs(["Expense Budgets", "Revenue Budgets"])

    with expense_tab:
        with st.form(key=f"budget_expense_form_{owner}_{month_key}"):
            expense_values = {}
            left, right = st.columns(2)
            midpoint = math.ceil(len(EXPENSE_CATEGORIES) / 2)
            left_categories = EXPENSE_CATEGORIES[:midpoint]
            right_categories = EXPENSE_CATEGORIES[midpoint:]

            with left:
                for category in left_categories:
                    expense_values[category] = st.number_input(
                        category,
                        min_value=0.0,
                        value=float(budget_record["expense"].get(category, 0.0)),
                        step=1.0,
                        format="%.2f",
                        key=f"budget_{owner}_expense_{category}_{month_key}",
                    )
            with right:
                for category in right_categories:
                    expense_values[category] = st.number_input(
                        category,
                        min_value=0.0,
                        value=float(budget_record["expense"].get(category, 0.0)),
                        step=1.0,
                        format="%.2f",
                        key=f"budget_{owner}_expense_{category}_{month_key}",
                    )

            if st.form_submit_button("Save Expense Budgets", type="primary", use_container_width=True):
                data["budgets"][month_key][owner]["expense"] = {k: float(v) for k, v in expense_values.items()}
                save_json_dict(DATA_FILE, data)
                st.success("Expense budgets saved.")
                st.rerun()

    with revenue_tab:
        with st.form(key=f"budget_revenue_form_{owner}_{month_key}"):
            revenue_values = {}
            for category in REVENUE_CATEGORIES:
                revenue_values[category] = st.number_input(
                    category,
                    min_value=0.0,
                    value=float(budget_record["revenue"].get(category, 0.0)),
                    step=1.0,
                    format="%.2f",
                    key=f"budget_{owner}_revenue_{category}_{month_key}",
                )

            if st.form_submit_button("Save Revenue Budgets", type="primary", use_container_width=True):
                data["budgets"][month_key][owner]["revenue"] = {k: float(v) for k, v in revenue_values.items()}
                save_json_dict(DATA_FILE, data)
                st.success("Revenue budgets saved.")
                st.rerun()


def show_budget_page(data: dict) -> None:
    month_key = st.session_state["selected_month"]
    ensure_month_exists(data, month_key)
    df = transaction_dataframe(data, month_key)

    st.markdown(f"## Budget Planner · {month_label(month_key)}")
    st.caption("Adjust separate and joint budgets inspired by your workbook, then compare budget vs actual.")
    st.divider()

    budget_tab, compare_tab = st.tabs(["Budget Editor", "Budget vs Actual"])

    with budget_tab:
        owner_tabs = st.tabs(["Shared", "TyShawn", "Lexi"])
        with owner_tabs[0]:
            render_budget_editor(data, month_key, "shared")
        with owner_tabs[1]:
            render_budget_editor(data, month_key, "tyshawn")
        with owner_tabs[2]:
            render_budget_editor(data, month_key, "lexi")

    with compare_tab:
        compare_owner = st.selectbox(
            "Compare For",
            options=OWNERS,
            format_func=lambda value: OWNER_LABELS[value],
            key="budget_compare_owner_select",
        )

        filtered_df = owner_filtered_df(df, compare_owner)
        expense_actual = (
            filtered_df[filtered_df["entry_type"] == "expense"].groupby("category", dropna=False)["amount"].sum().to_dict()
            if not filtered_df.empty else {}
        )
        revenue_actual = (
            filtered_df[filtered_df["entry_type"] == "revenue"].groupby("category", dropna=False)["amount"].sum().to_dict()
            if not filtered_df.empty else {}
        )

        expense_rows = []
        for category in EXPENSE_CATEGORIES:
            budget = float(data["budgets"][month_key][compare_owner]["expense"].get(category, 0.0))
            actual = float(expense_actual.get(category, 0.0))
            expense_rows.append({
                "Category": category,
                "Budget": budget,
                "Actual": actual,
                "Difference": budget - actual,
            })

        revenue_rows = []
        for category in REVENUE_CATEGORIES:
            budget = float(data["budgets"][month_key][compare_owner]["revenue"].get(category, 0.0))
            actual = float(revenue_actual.get(category, 0.0))
            revenue_rows.append({
                "Category": category,
                "Budget": budget,
                "Actual": actual,
                "Difference": actual - budget,
            })

        st.markdown("### Expense Budget vs Actual")
        st.dataframe(pd.DataFrame(expense_rows), use_container_width=True, hide_index=True)
        st.markdown("### Revenue Budget vs Actual")
        st.dataframe(pd.DataFrame(revenue_rows), use_container_width=True, hide_index=True)


# -----------------------------
# Analytics page
# -----------------------------
def plot_bar_chart(series: pd.Series, title: str, x_label: str = "", y_label: str = "Amount ($)") -> None:
    if series.empty:
        st.info("Not enough data to build this chart yet.")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5))
    series.plot(kind="bar", ax=ax)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def show_analytics(data: dict) -> None:
    month_key = st.session_state["selected_month"]
    current_df = transaction_dataframe(data, month_key)
    all_transactions = pd.DataFrame(data["transactions"])

    st.markdown(f"## Analytics · {month_label(month_key)}")
    st.caption("Compare categories, people, shared spending, and month-over-month trends.")
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Spending by Category",
        "Income vs Expenses",
        "Shared vs Personal",
        "TyShawn vs Lexi",
        "Monthly Trend",
    ])

    with tab1:
        if current_df.empty:
            st.info("No data yet for this month.")
        else:
            expenses = current_df[current_df["entry_type"] == "expense"]
            by_category = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
            plot_bar_chart(by_category, "Expenses by Category")

    with tab2:
        if current_df.empty:
            st.info("No data yet for this month.")
        else:
            summary = current_df.groupby("entry_type")["amount"].sum()
            summary.index = [ENTRY_TYPE_LABELS.get(idx, idx.title()) for idx in summary.index]
            plot_bar_chart(summary, "Income vs Expenses", y_label="Total ($)")

    with tab3:
        if current_df.empty:
            st.info("No data yet for this month.")
        else:
            grouped = current_df.groupby(["owner", "entry_type"])["amount"].sum().reset_index()
            grouped["Owner"] = grouped["owner"].map(OWNER_LABELS)
            grouped["Type"] = grouped["entry_type"].map(ENTRY_TYPE_LABELS)
            pivot = grouped.pivot(index="Owner", columns="Type", values="amount").fillna(0.0)
            st.dataframe(pivot, use_container_width=True)
            shared_series = current_df.groupby("owner")["amount"].sum()
            shared_series.index = [OWNER_LABELS.get(idx, idx) for idx in shared_series.index]
            plot_bar_chart(shared_series, "Shared vs Personal Totals")

    with tab4:
        if current_df.empty:
            st.info("No data yet for this month.")
        else:
            person_df = current_df[current_df["owner"].isin(["tyshawn", "lexi"])]
            if person_df.empty:
                st.info("No personal entries yet for this month.")
            else:
                compare = person_df.groupby(["owner", "entry_type"])["amount"].sum().unstack(fill_value=0.0)
                compare.index = [DISPLAY_NAMES.get(idx, idx.title()) for idx in compare.index]
                compare.columns = [ENTRY_TYPE_LABELS.get(idx, idx.title()) for idx in compare.columns]
                st.dataframe(compare, use_container_width=True)
                net_series = compare.get("Revenue", pd.Series(0.0, index=compare.index)) - compare.get("Expense", pd.Series(0.0, index=compare.index))
                plot_bar_chart(net_series, "TyShawn vs Lexi Net Comparison", y_label="Net ($)")

    with tab5:
        if all_transactions.empty:
            st.info("No trend data yet.")
        else:
            trend_df = all_transactions.copy()
            trend_df["amount"] = pd.to_numeric(trend_df["amount"], errors="coerce").fillna(0.0)
            monthly = trend_df.groupby(["month_key", "entry_type"])["amount"].sum().unstack(fill_value=0.0)
            monthly = monthly.sort_index()
            monthly.index = [month_label(idx) for idx in monthly.index]
            st.dataframe(monthly, use_container_width=True)
            if "revenue" in monthly.columns and "expense" in monthly.columns:
                net = monthly["revenue"] - monthly["expense"]
                plot_bar_chart(net, "Monthly Net Trend", y_label="Net ($)")
            else:
                combined = monthly.sum(axis=1)
                plot_bar_chart(combined, "Monthly Totals")


# -----------------------------
# App runner
# -----------------------------
def main() -> None:
    init_session_state()
    data = sanitize_loaded_data(load_json_dict(DATA_FILE))
    ensure_month_exists(data, st.session_state["selected_month"])

    if not st.session_state["logged_in"]:
        show_login_page()
        return

    show_sidebar(data)

    if st.session_state["page"] == "dashboard":
        show_dashboard(data)
    elif st.session_state["page"] == "quick_add":
        show_quick_add(data)
    elif st.session_state["page"] == "tracker":
        show_tracker(data)
    elif st.session_state["page"] == "budget":
        show_budget_page(data)
    elif st.session_state["page"] == "analytics":
        show_analytics(data)
    else:
        st.session_state["page"] = "dashboard"
        st.rerun()


if __name__ == "__main__":
    main()
