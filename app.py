import calendar
import json
import math
import os
import time
import uuid
from copy import deepcopy
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

try:
    from supabase import Client, create_client
except ModuleNotFoundError:
    Client = None
    create_client = None


# -----------------------------
# Page config & theme setup
# -----------------------------
st.set_page_config(
    page_title="Monthly Tracker for TyShawn & Lexi",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS theme with dark mode support
CUSTOM_CSS = """
<style>
:root {
    --primary-color: #3498db;
    --primary-dark: #2980b9;
    --secondary-color: #2ecc71;
    --danger-color: #e74c3c;
    --warning-color: #f39c12;
    --info-color: #3498db;
    --success-color: #27ae60;
    --neutral-light: #ecf0f1;
    --neutral-dark: #34495e;
    --text-primary: #2c3e50;
    --text-secondary: #7f8c8d;
    --border-color: #bdc3c7;
    --bg-primary: #ffffff;
    --bg-secondary: #f5f7fa;
}

@media (prefers-color-scheme: dark) {
    :root {
        --primary-color: #3498db;
        --primary-dark: #2980b9;
        --secondary-color: #2ecc71;
        --danger-color: #e74c3c;
        --warning-color: #f39c12;
        --info-color: #3498db;
        --success-color: #27ae60;
        --neutral-light: #2a2a2a;
        --neutral-dark: #d0d0d0;
        --text-primary: #e0e0e0;
        --text-secondary: #a0a0a0;
        --border-color: #404040;
        --bg-primary: #1e1e1e;
        --bg-secondary: #2d2d2d;
    }
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
    min-height: 100vh;
    color: var(--text-primary);
}

/* Headings */
h1, h2, h3 {
    color: var(--text-primary);
    font-weight: 700;
    letter-spacing: -0.5px;
}

h1 { font-size: 2.5rem; margin-bottom: 0.5rem; color: #3498db; }
h2 { font-size: 2rem; margin-bottom: 0.3rem; margin-top: 1.5rem; }
h3 { font-size: 1.4rem; margin-bottom: 0.2rem; margin-top: 1rem; }

@media (prefers-color-scheme: dark) {
    h1 { color: #3498db; }
    h2 { color: #e0e0e0; }
    h3 { color: #e0e0e0; }
}

/* Buttons */
[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%) !important;
    box-shadow: 0 4px 6px rgba(52, 152, 219, 0.3) !important;
    transition: all 0.3s ease !important;
}

[data-testid="baseButton-primary"]:hover {
    box-shadow: 0 6px 12px rgba(52, 152, 219, 0.4) !important;
    transform: translateY(-1px) !important;
}

[data-testid="baseButton-secondary"] {
    background: var(--neutral-light) !important;
    border: 2px solid var(--primary-color) !important;
    color: var(--primary-color) !important;
    transition: all 0.3s ease !important;
}

[data-testid="baseButton-secondary"]:hover {
    background: var(--primary-color) !important;
    color: white !important;
}

/* Forms and inputs */
input:not([role="combobox"]), textarea {
    border: 2px solid var(--border-color) !important;
    border-radius: 8px !important;
    padding: 10px 12px !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

input:not([role="combobox"]):focus, textarea:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1) !important;
}

@media (prefers-color-scheme: dark) {
    input:not([role="combobox"]), textarea {
        background-color: #2a2a2a !important;
        color: #e0e0e0 !important;
        border: 2px solid #404040 !important;
    }
    input::placeholder, textarea::placeholder {
        color: #808080 !important;
    }
}

/* Dataframes */
.stDataFrame {
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
}

@media (prefers-color-scheme: dark) {
    .stDataFrame {
        border: 1px solid #404040 !important;
    }
}

/* Containers */
[data-testid="stVerticalBlock"] > [data-testid="stContainer"] {
    border-radius: 12px;
    overflow: hidden;
}

/* Dividers */
hr {
    border: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-color), transparent);
    margin: 2rem 0;
}

/* Metric cards styling */
.metric-card {
    background: linear-gradient(135deg, white 0%, var(--neutral-light) 100%);
    border: 2px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    border-color: var(--primary-color);
}

/* Success/Error messages */
.stAlert {
    border-radius: 8px;
    border-left: 5px solid;
}

.stSuccess { border-left-color: var(--success-color); }
.stError { border-left-color: var(--danger-color); }
.stWarning { border-left-color: var(--warning-color); }
.stInfo { border-left-color: var(--info-color); }

/* Tabs */
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--primary-color) !important;
    border-bottom: 3px solid var(--primary-color) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, white 0%, var(--neutral-light) 100%);
    border-right: 1px solid var(--border-color);
}

[data-testid="stSidebar"] h1 {
    color: var(--primary-color);
    margin-bottom: 0.3rem;
}

@media (prefers-color-scheme: dark) {
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #252525 0%, #1e1e1e 100%);
        border-right: 1px solid #404040;
    }
    [data-testid="stSidebar"] h1 {
        color: #3498db;
    }
}

/* Captions and small text */
.stCaption {
    color: var(--text-secondary);
    font-size: 0.85rem;
    line-height: 1.5;
}

@media (prefers-color-scheme: dark) {
    .stCaption {
        color: #a0a0a0;
    }
}

/* Selection styles */
::selection {
    background: var(--primary-color);
    color: white;
}

/* App-like mode: keep sidebar toggle, hide extra chrome */
#MainMenu,
footer,
[data-testid="stStatusWidget"],
[data-testid="stDecoration"],
[data-testid="stAppToolbar"],
[data-testid="stToolbarActions"] {
    display: none !important;
}

/* Hide bottom-right Streamlit floating controls/badges */
[data-testid="stToastContainer"],
[data-testid="stException"],
a[title*="Streamlit" i],
a[aria-label*="Streamlit" i],
button[title*="Streamlit" i],
button[aria-label*="Streamlit" i] {
    display: none !important;
}

/* ---------------------------------
   Responsive layout by device size
   --------------------------------- */

/* Phones */
@media (max-width: 768px) {
    h1 { font-size: 1.7rem !important; }
    h2 { font-size: 1.35rem !important; }
    h3 { font-size: 1.1rem !important; }

    [data-testid="stAppViewContainer"] {
        padding-left: 0.4rem;
        padding-right: 0.4rem;
    }

    [data-testid="stMetric"] {
        padding: 0.5rem 0.6rem !important;
    }

    .metric-card {
        padding: 0.9rem !important;
        border-radius: 10px !important;
    }

    [data-testid="baseButton-primary"],
    [data-testid="baseButton-secondary"] {
        width: 100% !important;
        min-height: 44px !important;
    }

    [data-testid="stTabs"] button {
        font-size: 0.86rem !important;
        padding: 0.45rem 0.5rem !important;
    }

    .stDataFrame {
        font-size: 0.85rem !important;
    }

    /* Stack all multi-column layouts on phones */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.6rem !important;
    }

    [data-testid="column"] {
        min-width: 100% !important;
        width: 100% !important;
        flex: 1 1 100% !important;
    }

    /* Better tab usability on smaller screens */
    [data-testid="stTabs"] [role="tablist"] {
        gap: 0.25rem !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
    }
}

/* Tablets */
@media (min-width: 769px) and (max-width: 1024px) {
    h1 { font-size: 2rem !important; }
    h2 { font-size: 1.6rem !important; }
    h3 { font-size: 1.2rem !important; }

    .metric-card {
        padding: 1.1rem !important;
    }

    [data-testid="stTabs"] button {
        font-size: 0.92rem !important;
    }
}

/* Desktop and larger */
@media (min-width: 1400px) {
    [data-testid="stAppViewContainer"] {
        max-width: 1600px;
        margin: 0 auto;
    }
}

/* Touch-first devices */
@media (pointer: coarse) {
    [data-testid="baseButton-primary"],
    [data-testid="baseButton-secondary"] {
        min-height: 44px !important;
    }

    input:not([role="combobox"]), textarea {
        min-height: 42px !important;
    }
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def hide_streamlit_floating_ui() -> None:
    components.html(
        """
        <script>
        const hideFloatingUi = () => {
            const targetDoc = window.parent?.document || document;
            const targetWindow = window.parent || window;
            const selectors = [
                '[data-testid="stAppToolbar"]',
                '[data-testid="stToolbarActions"]',
                '[data-testid="stStatusWidget"]',
                '[data-testid="stToastContainer"]',
                '[data-testid="stProfileButton"]',
                '[data-testid="stProfileContainer"]',
                'a[title*="Streamlit" i]',
                'a[aria-label*="Streamlit" i]',
                'button[title*="Streamlit" i]',
                'button[aria-label*="Streamlit" i]',
                'button[title*="Profile" i]',
                'button[aria-label*="Profile" i]',
                'img[alt*="profile" i]',
                'img[alt*="avatar" i]',
                'iframe[src*="streamlit" i]'
            ];

            selectors.forEach((selector) => {
                targetDoc.querySelectorAll(selector).forEach((element) => {
                    element.style.display = 'none';
                    element.style.visibility = 'hidden';
                    element.style.pointerEvents = 'none';
                });
            });

            targetDoc.querySelectorAll('a, button, div, img, iframe').forEach((element) => {
                const text = [
                    element.getAttribute('title') || '',
                    element.getAttribute('aria-label') || '',
                    element.getAttribute('alt') || '',
                    element.getAttribute('src') || '',
                    element.getAttribute('href') || '',
                    element.textContent || ''
                ].join(' ');

                const rect = element.getBoundingClientRect();
                const nearBottomRight = (
                    rect.width > 0 && rect.height > 0 &&
                    rect.right >= targetWindow.innerWidth - 40 &&
                    rect.bottom >= targetWindow.innerHeight - 40 &&
                    rect.width <= 260 &&
                    rect.height <= 140
                );

                if (nearBottomRight && /streamlit|profile|avatar/i.test(text)) {
                    element.style.display = 'none';
                    element.style.visibility = 'hidden';
                    element.style.pointerEvents = 'none';
                }
            });
        };

        hideFloatingUi();
        setTimeout(hideFloatingUi, 500);
        setTimeout(hideFloatingUi, 1500);
        setInterval(hideFloatingUi, 3000);
        </script>
        """,
        height=0,
        width=0,
    )


hide_streamlit_floating_ui()


# -----------------------------
# Constants
# -----------------------------
APP_TITLE = "Monthly Budget + Tracker"
DATA_FILE = Path(__file__).parent / "monthly_tracker_data.json"
USER_CREDENTIALS = {
    "tyshawn": os.getenv("TYSHAWN_PASSWORD", "lexi"),
    "lexi": os.getenv("LEXI_PASSWORD", "tyshawn"),
}
DISPLAY_NAMES = {
    "tyshawn": "TyShawn",
    "lexi": "Lexi",
}
OWNERS = ["tyshawn", "lexi"]
OWNER_LABELS = {
    "tyshawn": "TyShawn",
    "lexi": "Lexi",
    "shared": "Carryover",
}
TRANSACTION_OWNERS = ["tyshawn", "lexi"]
RECURRENCE_FREQUENCIES = ["None", "Monthly"]
ENTRY_TYPE_LABELS = {
    "expense": "Expense",
    "revenue": "Revenue",
    "savings": "Savings",
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
    "Loan Payment",
    "Credit Card Payment",
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
    "Savings Transfer",
    "Other",
]
SAVINGS_CATEGORIES = [
    "Savings Deposit",
]
CARRYOVER_CATEGORY = "Carryover Balance"
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
        "savings": {category: 0.0 for category in SAVINGS_CATEGORIES},
    }


def get_user_categories(data: dict, entry_type: str) -> list[str]:
    """Return custom categories if available, otherwise return defaults."""
    custom = data.get("custom_categories", {}).get(entry_type, [])
    if custom:
        return custom
    
    if entry_type == "expense":
        return EXPENSE_CATEGORIES
    elif entry_type == "revenue":
        return REVENUE_CATEGORIES
    else:
        return SAVINGS_CATEGORIES


def get_all_tags(data: dict) -> list[str]:
    """Return all existing transaction tags from the data."""
    all_tags = set()
    for txn in data.get("transactions", []):
        tags = txn.get("tags", "")
        if tags:
            for tag in tags.split(","):
                all_tags.add(tag.strip())
    return sorted(list(all_tags))


def get_transaction_templates(data: dict) -> dict:
    """Get saved transaction templates."""
    if "templates" not in data:
        data["templates"] = {}
    return data.get("templates", {})


def save_transaction_template(data: dict, template_name: str, template_data: dict) -> None:
    """Save a transaction as a template for quick reuse."""
    if "templates" not in data:
        data["templates"] = {}
    data["templates"][template_name] = template_data
    save_json_dict(DATA_FILE, data)


def get_data_integrity_issues(data: dict, month_key: str) -> dict:
    """Check for data integrity issues like unset budgets, unusual amounts, etc."""
    issues = {
        "budget_not_set": [],
        "missing_descriptions": [],
        "unusual_amounts": [],
        "no_transactions": False
    }
    
    df = transaction_dataframe(data, month_key)
    
    # Check if budgets are set
    budget_record = data.get("budgets", {}).get(month_key)
    if budget_record:
        for owner in OWNERS:
            owner_budget = budget_record.get(owner, empty_budget_block())
            if not any(owner_budget.get("expense", {}).values()):
                issues["budget_not_set"].append(owner)
    
    # Check for transactions without descriptions
    for _, row in df.iterrows():
        if not row.get("description", "").strip():
            issues["missing_descriptions"].append(row["id"])
    
    # Check for unusual amounts (outliers > 3x the median)
    if not df.empty:
        expenses = df[df["entry_type"] == "expense"]
        if not expenses.empty:
            median = expenses["amount"].median()
            for _, row in expenses.iterrows():
                if median > 0 and row["amount"] > median * 3:
                    issues["unusual_amounts"].append({
                        "amount": row["amount"],
                        "category": row["category"],
                        "median": median
                    })
    
    if df.empty:
        issues["no_transactions"] = True
    
    return issues


def show_category_growth_alerts(data: dict, month_key: str) -> None:
    """Flag categories where spending increased 20%+ vs previous month."""
    prev_month = previous_month_key(month_key)
    
    curr_df = transaction_dataframe(data, month_key)
    prev_df = transaction_dataframe(data, prev_month) if prev_month in data.get("budgets", {}) else pd.DataFrame()
    
    if curr_df.empty or prev_df.empty:
        return
    
    curr_expenses = curr_df[curr_df["entry_type"] == "expense"].groupby("category")["amount"].sum()
    prev_expenses = prev_df[prev_df["entry_type"] == "expense"].groupby("category")["amount"].sum()
    
    alerts = []
    for cat in curr_expenses.index:
        prev_val = float(prev_expenses.get(cat, 0))
        curr_val = float(curr_expenses.get(cat, 0))
        
        if prev_val > 0:
            pct_change = ((curr_val - prev_val) / prev_val) * 100
            if pct_change >= 20:
                alerts.append({
                    'category': cat,
                    'current': curr_val,
                    'previous': prev_val,
                    'pct_change': pct_change
                })
    
    if alerts:
        st.warning("🚨 **Category Growth Alerts**")
        for alert in alerts:
            st.write(f"⬆️ **{alert['category']}**: {alert['pct_change']:.1f}% increase "
                    f"({format_currency(alert['previous'])} → {format_currency(alert['current'])})")


def show_cash_flow_forecast(data: dict, month_key: str) -> None:
    """Project cash balance 3 months ahead based on recurring transactions."""
    year, month = map(int, month_key.split("-"))
    
    # Get current month summary
    curr_df = transaction_dataframe(data, month_key)
    curr_summary = monthly_summary(curr_df)
    
    # Find recurring transactions
    recurring = [txn for txn in data.get("transactions", []) 
                if txn.get("recurrence_frequency") == "Monthly"]
    
    if not recurring:
        st.info("No recurring transactions found for forecast.")
        return
    
    # Calculate recurring monthly total
    recurring_monthly = sum(float(txn.get("amount", 0)) for txn in recurring 
                           if txn.get("entry_type") == "revenue") - \
                       sum(float(txn.get("amount", 0)) for txn in recurring 
                           if txn.get("entry_type") == "expense")
    
    # Project 3 months
    forecast_data = []
    current_balance = curr_summary["net"]
    
    for i in range(3):
        future_month = month + i
        if future_month > 12:
            future_month -= 12
        
        projected_balance = current_balance + recurring_monthly
        forecast_data.append({
            'month': ALL_MONTHS[future_month - 1],
            'projected_balance': projected_balance,
            'monthly_net': recurring_monthly
        })
        current_balance = projected_balance
    
    # Display forecast
    st.markdown("**3-Month Cash Flow Forecast**")
    forecast_df = pd.DataFrame(forecast_data)
    forecast_df['projected_balance'] = forecast_df['projected_balance'].apply(format_currency)
    forecast_df['monthly_net'] = forecast_df['monthly_net'].apply(format_currency)
    forecast_df = forecast_df.rename(columns={
        'month': 'Month',
        'projected_balance': 'Projected Balance',
        'monthly_net': 'Monthly Net (Recurring)'
    })
    st.dataframe(forecast_df, use_container_width=True, hide_index=True)


def show_spending_by_owner(data: dict, month_key: str) -> None:
    """Display comparison of spending between TyShawn and Lexi."""
    df = transaction_dataframe(data, month_key)
    
    if df.empty:
        st.info("No transaction data yet.")
        return
    
    personal_df = df[df["owner"].isin(["tyshawn", "lexi"])]
    
    if personal_df.empty:
        st.info("No personal transactions yet.")
        return
    
    # Create comparison chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), facecolor='#1e1e1e')
    
    for ax in [ax1, ax2]:
        ax.set_facecolor('#1e1e1e')
    
    # Revenue vs Expense comparison
    owner_summary = personal_df.groupby("owner").apply(
        lambda x: {
            'revenue': float(x[x["entry_type"] == "revenue"]["amount"].sum()),
            'expense': float(x[x["entry_type"] == "expense"]["amount"].sum()),
            'savings': float(x[x["entry_type"] == "savings"]["amount"].sum())
        }
    )
    
    owners = list(owner_summary.index)
    owner_labels = [OWNER_LABELS[o] for o in owners]
    
    x = range(len(owners))
    width = 0.25
    
    revenue_vals = [owner_summary[o]['revenue'] for o in owners]
    expense_vals = [owner_summary[o]['expense'] for o in owners]
    savings_vals = [owner_summary[o]['savings'] for o in owners]
    
    ax1.bar([i - width for i in x], revenue_vals, width, label='Revenue', color='#2ecc71', edgecolor='white', linewidth=1.5)
    ax1.bar(x, expense_vals, width, label='Expenses', color='#e74c3c', edgecolor='white', linewidth=1.5)
    ax1.bar([i + width for i in x], savings_vals, width, label='Savings', color='#3498db', edgecolor='white', linewidth=1.5)
    
    ax1.set_ylabel('Amount ($)', fontsize=11, fontweight='bold', color='#e0e0e0')
    ax1.set_title('Revenue vs Expenses vs Savings', fontsize=12, fontweight='bold', color='#e0e0e0')
    ax1.set_xticks(x)
    ax1.set_xticklabels(owner_labels, color='#e0e0e0')
    ax1.legend(fontsize=9, facecolor='#2a2a2a', edgecolor='#555', labelcolor='#e0e0e0')
    ax1.grid(axis='y', alpha=0.2, linestyle='--')
    ax1.set_axisbelow(True)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#555')
    ax1.spines['bottom'].set_color('#555')
    ax1.tick_params(colors='#e0e0e0')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}' if x >= 0 else f'-${abs(x):,.0f}'))
    
    # Net comparison
    net_vals = [revenue_vals[i] - expense_vals[i] for i in range(len(owners))]
    colors = ['#2ecc71' if val > 0 else '#e74c3c' for val in net_vals]
    bars = ax2.bar(owner_labels, net_vals, color=colors, edgecolor='white', linewidth=2, alpha=0.8)
    
    ax2.set_ylabel('Amount ($)', fontsize=11, fontweight='bold', color='#e0e0e0')
    ax2.set_title('Net Balance Comparison', fontsize=12, fontweight='bold', color='#e0e0e0')
    ax2.axhline(y=0, color='#999', linestyle='-', linewidth=1)
    ax2.grid(axis='y', alpha=0.2, linestyle='--')
    ax2.set_axisbelow(True)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color('#555')
    ax2.spines['bottom'].set_color('#555')
    ax2.tick_params(colors='#e0e0e0')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}' if x >= 0 else f'-${abs(x):,.0f}'))
    
    # Add value labels
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:.0f}', ha='center', va='bottom' if height > 0 else 'top',
                fontsize=10, color='#e0e0e0', weight='bold')
    
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def add_custom_category(data: dict, entry_type: str, category_name: str) -> None:
    """Add a custom category to the data store."""
    if "custom_categories" not in data:
        data["custom_categories"] = {"expense": [], "revenue": [], "savings": []}
    
    if category_name not in data["custom_categories"].get(entry_type, []):
        data["custom_categories"][entry_type].append(category_name)
        save_json_dict(DATA_FILE, data)


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


@st.cache_resource
def get_supabase_client():
    """Return a cached Supabase client if credentials are configured, else None."""
    if create_client is None:
        return None
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        if not url or not key or "YOUR_PROJECT_ID" in url:
            return None
        return create_client(url, key)
    except Exception:
        return None


def load_json_dict(file_path: Path) -> dict:
    # ── Try Supabase first ──────────────────────────────────────
    client = get_supabase_client()
    if client:
        try:
            response = (
                client.table("tracker_data")
                .select("payload")
                .eq("id", 1)
                .maybe_single()
                .execute()
            )
            raw = response.data
            if raw and isinstance(raw.get("payload"), dict):
                data = raw["payload"]
                data.setdefault("budgets", {})
                data.setdefault("transactions", [])
                if not isinstance(data["budgets"], dict):
                    data["budgets"] = {}
                if not isinstance(data["transactions"], list):
                    data["transactions"] = []
                return data
        except Exception:
            pass  # fall through to local file

    # ── Fallback: local JSON file ───────────────────────────────
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
    # ── Try Supabase first ──────────────────────────────────────
    client = get_supabase_client()
    if client:
        try:
            client.table("tracker_data").upsert({"id": 1, "payload": data}).execute()
            return  # success — no need to write locally
        except Exception:
            pass  # fall through to local file

    # ── Fallback: local JSON file ───────────────────────────────
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    # Auto-backup: create timestamped backup
    backup_dir = file_path.parent / ".backups"
    backup_dir.mkdir(exist_ok=True)
    today = date.today().isoformat()
    backup_file = backup_dir / f"backup_{today}.json"
    if not backup_file.exists():
        with open(backup_file, "w", encoding="utf-8") as file:
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


def next_month_key(month_key: str) -> str:
    year, month = [int(part) for part in month_key.split("-")]
    if month == 12:
        return f"{year + 1}-01"
    return f"{year}-{month + 1:02d}"


def previous_existing_budget_month_key(data: dict, month_key: str) -> str | None:
    if not isinstance(data.get("budgets"), dict):
        return None

    prior_keys = [key for key in data["budgets"].keys() if key < month_key]
    return max(prior_keys) if prior_keys else None


def sorted_month_keys(data: dict) -> list[str]:
    month_keys = set(data.get("budgets", {}).keys())
    for transaction in data.get("transactions", []):
        month_key = transaction.get("month_key")
        if month_key:
            month_keys.add(month_key)
    month_keys.add(month_key_from_date(date.today()))
    return sorted(month_keys)


def carryover_from_prior_month(data: dict, new_month_key: str, prior_month_key: str) -> bool:
    """Create or update the carryover transaction for each owner from the prior month.
    Returns True if any transaction was added or updated, False otherwise."""
    year, month = map(int, new_month_key.split("-"))
    carryover_date = date(year, month, 1)

    prior_df = transaction_dataframe(data, prior_month_key)
    carryover_description = f"Carryover from {month_label(prior_month_key)}"

    changed = False
    for owner in OWNERS:
        owner_prior_df = owner_filtered_df(prior_df, owner)
        owner_prior_net = float(monthly_summary(owner_prior_df)["net"])

        # Find any existing carryover transaction for this owner/month
        existing_txn = next(
            (
                txn for txn in data.get("transactions", [])
                if txn.get("month_key") == new_month_key
                and txn.get("owner") == owner
                and txn.get("category") == CARRYOVER_CATEGORY
                and txn.get("description", "") == carryover_description
            ),
            None,
        )

        if owner_prior_net == 0:
            # Prior month net is now zero — remove stale carryover if present
            if existing_txn:
                data["transactions"].remove(existing_txn)
                changed = True
            continue

        new_entry_type = "revenue" if owner_prior_net > 0 else "expense"
        new_amount = round(abs(owner_prior_net), 2)

        if existing_txn:
            # Update only if the amount or direction changed
            if (
                round(existing_txn.get("amount", 0), 2) != new_amount
                or existing_txn.get("entry_type") != new_entry_type
            ):
                existing_txn["amount"] = new_amount
                existing_txn["entry_type"] = new_entry_type
                existing_txn["updated_at"] = datetime.now().isoformat(timespec="seconds")
                changed = True
            continue

        # No existing carryover — create one
        carryover_txn = {
            "id": str(uuid.uuid4()),
            "month_key": new_month_key,
            "date": carryover_date.isoformat(),
            "entry_type": new_entry_type,
            "owner": owner,
            "category": CARRYOVER_CATEGORY,
            "amount": new_amount,
            "description": carryover_description,
            "created_by": current_username() or "system",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": "",
            "recurrence_frequency": "None",
            "recurrence_count": 1,
            "tags": "",
        }
        data.setdefault("transactions", []).append(carryover_txn)
        changed = True

    return changed


def apply_prior_month_actuals_to_budget(data: dict, new_month_key: str, prior_month_key: str) -> None:
    """Set new month budgets to rolling average of prior 2-3 months by owner/category."""
    category_map = {
        "expense": EXPENSE_CATEGORIES,
        "revenue": REVENUE_CATEGORIES,
        "savings": SAVINGS_CATEGORIES,
    }
    
    # Collect prior 2 months of data
    prior_months = [prior_month_key]
    temp_key = prior_month_key
    for _ in range(1):
        temp_key = previous_month_key(temp_key)
        if temp_key in data.get("budgets", {}):
            prior_months.append(temp_key)

    for owner in OWNERS:
        owner_budget = data["budgets"][new_month_key].get(owner, empty_budget_block())

        for entry_type, categories in category_map.items():
            category_actuals = {cat: [] for cat in categories}
            
            # Gather actuals from prior months
            for month in prior_months:
                month_df = transaction_dataframe(data, month)
                owner_df = owner_filtered_df(month_df, owner)
                actuals = (
                    owner_df[owner_df["entry_type"] == entry_type]
                    .groupby("category", dropna=False)["amount"]
                    .sum()
                    .to_dict()
                    if not owner_df.empty
                    else {}
                )
                for cat in categories:
                    category_actuals[cat].append(float(actuals.get(cat, 0.0)))
            
            # Calculate average
            owner_budget[entry_type] = {
                category: sum(category_actuals[category]) / len(category_actuals[category]) if category_actuals[category] else 0.0
                for category in categories
            }

        data["budgets"][new_month_key][owner] = owner_budget


def ensure_month_exists(data: dict, month_key: str) -> str | None:
    data.setdefault("budgets", {})
    if month_key in data["budgets"]:
        prior_key = previous_month_key(month_key)
        if prior_key not in data["budgets"]:
            prior_key = previous_existing_budget_month_key(data, month_key)
        if prior_key and prior_key in data["budgets"]:
            changed = carryover_from_prior_month(data, month_key, prior_key)
            if changed:
                return "updated"
        return None

    prior_key = previous_month_key(month_key)
    if prior_key not in data["budgets"]:
        prior_key = previous_existing_budget_month_key(data, month_key)

    if prior_key and prior_key in data["budgets"]:
        data["budgets"][month_key] = deepcopy(data["budgets"][prior_key])
        apply_prior_month_actuals_to_budget(data, month_key, prior_key)
        carryover_from_prior_month(data, month_key, prior_key)
        return "copied"

    data["budgets"][month_key] = empty_month_record()
    return "created"


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
        "recurrence_frequency": str(record.get("recurrence_frequency", "None")),
        "recurrence_count": int(record.get("recurrence_count", 1)),
    }

    if normalized["entry_type"] not in ["expense", "revenue", "savings"]:
        return None
    allowed_owners = set(TRANSACTION_OWNERS)
    if normalized["category"] == CARRYOVER_CATEGORY:
        allowed_owners.add("shared")
    if normalized["owner"] not in allowed_owners:
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
                        month_clean[owner]["savings"] = normalize_budget_section(
                            owner_record.get("savings", {}), SAVINGS_CATEGORIES
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
def detect_mobile_client() -> bool:
    """Best-effort mobile detection from request user-agent."""
    user_agent = ""
    try:
        headers = getattr(st.context, "headers", {})
        if headers:
            user_agent = str(headers.get("User-Agent", ""))
    except Exception:
        user_agent = ""

    ua = user_agent.lower()
    mobile_tokens = ["iphone", "android", "mobile", "ipad", "ipod"]
    return any(token in ua for token in mobile_tokens)


def init_session_state() -> None:
    default_mobile = detect_mobile_client()
    defaults = {
        "logged_in": False,
        "current_user": None,
        "page": "dashboard",
        "selected_month": month_key_from_date(date.today()),
        "editing_transaction_id": None,
        "search_query": "",
        "search_category": "All",
        "search_min_amount": 0.0,
        "search_max_amount": float('inf'),
        "search_start_date": date.today(),
        "search_end_date": date.today(),
        "undo_action": None,
        "auto_closeout_notice": [],
        "is_mobile_client": default_mobile,
        "compact_dashboard_mode": default_mobile,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def show_mobile_toolbar(data: dict) -> None:
    """Top toolbar for phone users with same navigation and month controls."""
    if not st.session_state.get("is_mobile_client", False):
        return

    st.markdown("### 📱 Phone Quick Controls")
    nav_items = [
        ("dashboard", "🏠 Dashboard"),
        ("quick_add", "⚡ Quick Add"),
        ("tracker", "🧾 Monthly Tracker"),
        ("budget", "📘 Budget Planner"),
        ("analytics", "📊 Analytics"),
        ("goals", "🎯 Savings Goals"),
        ("settings", "⚙️ Settings"),
    ]
    nav_labels = [label for _, label in nav_items]
    current_page = st.session_state.get("page", "dashboard")
    current_page_label = next((label for page, label in nav_items if page == current_page), nav_labels[0])

    col1, col2 = st.columns(2)
    with col1:
        selected_page_label = st.selectbox(
            "Page",
            options=nav_labels,
            index=nav_labels.index(current_page_label),
            key="mobile_page_switcher_select",
        )
    with col2:
        month_keys = sorted_month_keys(data)
        month_labels = [month_label(month_key) for month_key in month_keys]
        selected_month_key = st.session_state.get("selected_month", month_key_from_date(date.today()))
        if selected_month_key not in month_keys:
            ensure_month_exists(data, selected_month_key)
            save_json_dict(DATA_FILE, data)
            month_keys = sorted_month_keys(data)
            month_labels = [month_label(month_key) for month_key in month_keys]
        selected_month_label = st.selectbox(
            "Month",
            options=month_labels,
            index=month_keys.index(st.session_state["selected_month"]),
            key="mobile_month_switcher_select",
        )

    selected_page = next((page for page, label in nav_items if label == selected_page_label), current_page)
    selected_month = label_to_month_key(selected_month_label)

    page_changed = selected_page != st.session_state["page"]
    month_changed = selected_month != st.session_state["selected_month"]

    if month_changed:
        st.session_state["selected_month"] = selected_month
        ensure_month_exists(data, selected_month)
        save_json_dict(DATA_FILE, data)

    if page_changed:
        st.session_state["page"] = selected_page

    if page_changed or month_changed:
        st.rerun()

    st.divider()


# -----------------------------
# Helpers: transaction logic
# -----------------------------
def current_username() -> str:
    return str(st.session_state.get("current_user", "")).lower()


def can_edit_transaction(transaction: dict) -> bool:
    username = current_username()
    return transaction["created_by"] == username


def set_undo_action(action_type: str, payload: dict, message: str) -> None:
    st.session_state["undo_action"] = {
        "type": action_type,
        "payload": deepcopy(payload),
        "message": message,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def undo_last_action(data: dict) -> bool:
    action = st.session_state.get("undo_action")
    if not action:
        return False

    payload = action.get("payload", {})
    action_type = action.get("type")

    if action_type == "add":
        transaction_id = payload.get("transaction_id")
        data["transactions"] = [txn for txn in data.get("transactions", []) if txn.get("id") != transaction_id]
    elif action_type == "delete":
        transaction = payload.get("transaction")
        index = int(payload.get("index", len(data.get("transactions", []))))
        if transaction:
            data.setdefault("transactions", [])
            data["transactions"].insert(min(index, len(data["transactions"])), transaction)
    elif action_type == "edit":
        previous_transaction = payload.get("transaction")
        if previous_transaction:
            for idx, transaction in enumerate(data.get("transactions", [])):
                if transaction.get("id") == previous_transaction.get("id"):
                    data["transactions"][idx] = previous_transaction
                    break
    else:
        return False

    save_json_dict(DATA_FILE, data)
    st.session_state["undo_action"] = None
    return True


def auto_closeout_months(data: dict) -> list[str]:
    data.setdefault("budgets", {})
    current_key = month_key_from_date(date.today())
    if current_key not in data["budgets"] and not data["budgets"]:
        ensure_month_exists(data, current_key)
        return [current_key]

    created_months: list[str] = []
    if not data["budgets"]:
        return created_months

    latest_key = max(data["budgets"].keys())
    while latest_key < current_key:
        latest_key = next_month_key(latest_key)
        ensure_month_exists(data, latest_key)
        created_months.append(latest_key)

    return created_months


def build_notifications(data: dict, month_key: str) -> list[dict]:
    notifications: list[dict] = []
    integrity = get_data_integrity_issues(data, month_key)
    current_key = month_key_from_date(date.today())
    previous_key = previous_month_key(current_key)

    if month_key == previous_key and date.today().day <= 10:
        current_df = transaction_dataframe(data, month_key)
        current_summary = monthly_summary(current_df)
        personal_df = current_df[current_df["owner"].isin(["tyshawn", "lexi"])].copy()
        top_category = get_top_spending_category(personal_df)
        top_category_text = (
            f"{top_category[0]} ({format_currency(top_category[1])})"
            if top_category
            else "No spending yet"
        )
        notifications.append({
            "level": "info",
            "title": "Monthly recap",
            "detail": f"Spent {format_currency(current_summary['expense'])}, saved {format_currency(current_summary['savings'])}, top category: {top_category_text}.",
        })

    for closed_month in st.session_state.get("auto_closeout_notice", []):
        notifications.append({
            "level": "success",
            "title": "Month auto-closed",
            "detail": f"Prepared {month_label(closed_month)} with carried-over budgets.",
        })

    for owner in OWNERS:
        owner_status = get_budget_status(data, month_key, owner)
        over_count = len([warning for warning in owner_status["warnings"] if warning["status"] == "over"])
        near_count = len([warning for warning in owner_status["warnings"] if warning["status"] != "over"])
        if over_count:
            notifications.append({
                "level": "error",
                "title": f"{OWNER_LABELS[owner]} over budget",
                "detail": f"{over_count} category(s) already over budget.",
            })
        elif near_count:
            notifications.append({
                "level": "warning",
                "title": f"{OWNER_LABELS[owner]} budget watch",
                "detail": f"{near_count} category(s) are above 80% of budget.",
            })

    if integrity["budget_not_set"]:
        notifications.append({
            "level": "info",
            "title": "Budgets need setup",
            "detail": ", ".join(OWNER_LABELS[owner] for owner in integrity["budget_not_set"]),
        })
    if integrity["missing_descriptions"]:
        notifications.append({
            "level": "warning",
            "title": "Descriptions missing",
            "detail": f"{len(integrity['missing_descriptions'])} transaction(s) need clearer notes.",
        })
    if integrity["unusual_amounts"]:
        notifications.append({
            "level": "info",
            "title": "Large transactions detected",
            "detail": f"{len(integrity['unusual_amounts'])} transaction(s) look unusually high.",
        })

    recurring_count = len([
        txn for txn in data.get("transactions", [])
        if txn.get("month_key") == month_key and txn.get("recurrence_frequency") == "Monthly"
    ])
    if recurring_count:
        notifications.append({
            "level": "info",
            "title": "Recurring items due",
            "detail": f"{recurring_count} recurring bill/income item(s) tracked this month.",
        })

    return notifications[:6]


def show_notifications_panel(data: dict, month_key: str) -> None:
    notifications = build_notifications(data, month_key)
    st.markdown("### 🔔 Notifications")
    if not notifications:
        st.success("All clear — no urgent updates right now.")
        return

    styles = {
        "success": ("#1f7a4d", "✅"),
        "info": ("#2563eb", "ℹ️"),
        "warning": ("#b7791f", "⚠️"),
        "error": ("#c53030", "🚨"),
    }
    for item in notifications:
        border_color, icon = styles.get(item["level"], ("#2563eb", "ℹ️"))
        st.markdown(
            f"""
            <div style="border-left: 4px solid {border_color}; padding: 0.75rem 1rem; margin-bottom: 0.6rem; background: rgba(255,255,255,0.03); border-radius: 0.5rem;">
                <div style="font-weight: 700;">{icon} {item['title']}</div>
                <div style="opacity: 0.85; font-size: 0.92rem;">{item['detail']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def show_recent_activity_panel(data: dict) -> None:
    action = st.session_state.get("undo_action")
    if not action:
        return

    st.markdown("### ↩️ Recent Activity")
    panel_col1, panel_col2 = st.columns([4, 1])
    with panel_col1:
        st.info(action.get("message", "Recent change available to undo."))
    with panel_col2:
        if st.button("Undo", key="undo_recent_activity_btn", use_container_width=True):
            if undo_last_action(data):
                st.success("✅ Last change undone.")
                st.rerun()


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
    recurrence_frequency: str = "None",
    recurrence_count: int = 1,
    tags: str = "",
) -> dict:
    ensure_month_exists(data, month_key)
    transaction = {
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
        "recurrence_frequency": recurrence_frequency,
        "recurrence_count": int(recurrence_count),
        "tags": tags,
    }
    data["transactions"].append(transaction)
    return transaction


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
    return df[df["owner"] == owner].copy()


def monthly_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "revenue": 0.0,
            "expense": 0.0,
            "savings": 0.0,
            "net": 0.0,
        }

    revenue_df = df[df["entry_type"] == "revenue"]
    expense_df = df[df["entry_type"] == "expense"]
    savings_df = df[df["entry_type"] == "savings"]

    savings_transfer_out = float(expense_df.loc[expense_df["category"] == "Savings Transfer", "amount"].sum())
    savings_transfer_in = float(revenue_df.loc[revenue_df["category"] == "Savings Transfer", "amount"].sum())

    revenue = float(revenue_df["amount"].sum()) - savings_transfer_out
    expense = float(expense_df.loc[expense_df["category"] != "Savings Transfer", "amount"].sum())
    carryover_amount = float(savings_df.loc[savings_df["category"] == CARRYOVER_CATEGORY, "amount"].sum())
    savings = float(savings_df["amount"].sum()) - carryover_amount + savings_transfer_out - savings_transfer_in

    return {
        "revenue": revenue,
        "expense": expense,
        "savings": savings,
        "net": revenue - expense,
    }


def total_savings(data: dict) -> float:
    transactions = data.get("transactions", [])
    if not transactions:
        return 0.0

    df = pd.DataFrame(transactions)
    if df.empty:
        return 0.0

    savings_df = df[df["entry_type"] == "savings"].copy()
    return float(savings_df["amount"].sum())


def budget_totals_for_owner(data: dict, month_key: str, owner: str) -> dict:
    ensure_month_exists(data, month_key)
    record = data["budgets"][month_key][owner]
    return {
        "revenue_budget": sum(record["revenue"].values()),
        "expense_budget": sum(record["expense"].values()),
        "savings_budget": sum(record["savings"].values()),
    }


def combined_budget_totals(data: dict, month_key: str) -> dict:
    totals = {"revenue_budget": 0.0, "expense_budget": 0.0, "savings_budget": 0.0}
    for owner in OWNERS:
        owner_totals = budget_totals_for_owner(data, month_key, owner)
        totals["revenue_budget"] += owner_totals["revenue_budget"]
        totals["expense_budget"] += owner_totals["expense_budget"]
        totals["savings_budget"] += owner_totals["savings_budget"]
    return totals


# Spending insights helper functions
def get_top_spending_category(df: pd.DataFrame) -> tuple[str, float] | None:
    """Return the category with highest spending and the amount."""
    if df.empty:
        return None
    expenses = df[df["entry_type"] == "expense"].copy()
    if expenses.empty:
        return None
    by_category = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
    return (by_category.index[0], float(by_category.iloc[0]))


def get_highest_transaction(df: pd.DataFrame) -> dict | None:
    """Return details of the highest single transaction."""
    if df.empty:
        return None
    highest = df.loc[df["amount"].idxmax()]
    return {
        "category": highest["category"],
        "amount": float(highest["amount"]),
        "type": highest["entry_type"],
        "description": highest["description"],
    }


def get_daily_average_spending(df: pd.DataFrame, month_key: str) -> float:
    """Calculate average daily spending for the month."""
    if df.empty:
        return 0.0
    expenses = df[df["entry_type"] == "expense"].copy()
    if expenses.empty:
        return 0.0
    total_expenses = float(expenses["amount"].sum())
    # Get number of days in the month
    year, month = map(int, month_key.split("-"))
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    days_in_month = (next_month - date(year, month, 1)).days
    return total_expenses / days_in_month


def get_budget_warnings(data: dict, month_key: str, owner: str) -> list[dict]:
    """Return list of budget alerts for expenses at 80%+ of budget."""
    df = transaction_dataframe(data, month_key)
    owner_df = owner_filtered_df(df, owner)
    budget_record = data["budgets"].get(month_key, {}).get(owner, empty_budget_block())
    
    warnings = []
    expenses = owner_df[owner_df["entry_type"] == "expense"].groupby("category")["amount"].sum().to_dict()
    
    for category, budget_amount in budget_record["expense"].items():
        if budget_amount > 0:
            actual = float(expenses.get(category, 0.0))
            percentage = (actual / budget_amount) * 100
            if percentage >= 80:
                warnings.append({
                    "category": category,
                    "actual": actual,
                    "budget": budget_amount,
                    "percentage": percentage,
                })
    return warnings


def detect_duplicate_transactions(data: dict, new_txn: dict, tolerance_minutes: int = 5) -> list[dict]:
    """Check for potential duplicate transactions (same amount, category, owner within N minutes)."""
    new_date = datetime.strptime(new_txn["date"], "%Y-%m-%d").date()
    duplicates = []
    
    for txn in data.get("transactions", []):
        if txn["id"] == new_txn.get("id"):
            continue
        if (txn["category"] == new_txn["category"] and
            txn["owner"] == new_txn["owner"] and
            txn["entry_type"] == new_txn["entry_type"] and
            abs(float(txn["amount"]) - float(new_txn["amount"])) < 0.01):
            txn_date = datetime.strptime(txn["date"], "%Y-%m-%d").date()
            if abs((txn_date - new_date).days) <= 1:
                duplicates.append(txn)
    return duplicates


def calculate_savings_rate(df: pd.DataFrame) -> float:
    """Return savings rate as percentage of revenue."""
    if df.empty:
        return 0.0
    revenue = float(df[df["entry_type"] == "revenue"]["amount"].sum())
    if revenue <= 0:
        return 0.0
    savings = float(df[df["entry_type"] == "savings"]["amount"].sum())
    return (savings / revenue) * 100


def get_budget_status(data: dict, month_key: str, owner: str) -> dict:
    """Check budget status for an owner - returns dict with warnings."""
    df = transaction_dataframe(data, month_key)
    owner_df = owner_filtered_df(df, owner) if owner != "total" else df[df["owner"].isin(["tyshawn", "lexi"])].copy()
    
    budget_record = data["budgets"].get(month_key, {}).get(owner, empty_budget_block())
    expenses_actual = owner_df[owner_df["entry_type"] == "expense"].groupby("category")["amount"].sum().to_dict()
    
    warnings = []
    for category, budget_amount in budget_record["expense"].items():
        if budget_amount > 0:
            actual = float(expenses_actual.get(category, 0.0))
            percentage = (actual / budget_amount) * 100
            if actual > budget_amount:
                warnings.append({"category": category, "status": "over", "percentage": percentage, "actual": actual, "budget": budget_amount})
            elif percentage >= 80:
                warnings.append({"category": category, "status": "warning", "percentage": percentage, "actual": actual, "budget": budget_amount})
    
    return {"warnings": warnings, "has_issues": len(warnings) > 0}


def get_most_used_categories(data: dict) -> dict[str, list[str]]:
    """Get most frequently used categories by type."""
    df = pd.DataFrame(data.get("transactions", []))
    if df.empty:
        return {"expense": EXPENSE_CATEGORIES, "revenue": REVENUE_CATEGORIES, "savings": SAVINGS_CATEGORIES}
    
    most_used = {}
    for entry_type in ["expense", "revenue", "savings"]:
        type_df = df[df["entry_type"] == entry_type]
        if not type_df.empty:
            category_counts = type_df["category"].value_counts()
            sorted_categories = category_counts.index.tolist()
            # Add categories not yet used
            if entry_type == "expense":
                all_cats = EXPENSE_CATEGORIES
            elif entry_type == "revenue":
                all_cats = REVENUE_CATEGORIES
            else:
                all_cats = SAVINGS_CATEGORIES
            for cat in all_cats:
                if cat not in sorted_categories:
                    sorted_categories.append(cat)
            most_used[entry_type] = sorted_categories
        else:
            if entry_type == "expense":
                most_used[entry_type] = EXPENSE_CATEGORIES
            elif entry_type == "revenue":
                most_used[entry_type] = REVENUE_CATEGORIES
            else:
                most_used[entry_type] = SAVINGS_CATEGORIES
    
    return most_used


def plot_monthly_budget_trend(month_keys: list[str], actual: pd.DataFrame, budget: pd.DataFrame) -> None:
    colors = {
        "expense": "#e74c3c",
        "revenue": "#2ecc71",
        "savings": "#3498db",
    }
    categories = ["expense", "revenue", "savings"]
    x = [i for i in range(len(month_keys))]
    width = 0.12

    fig, ax = plt.subplots(figsize=(11, 5.5), facecolor='white')
    for i, category in enumerate(categories):
        actual_values = actual[category].tolist()
        budget_values = budget[f"{category}_budget"].tolist()
        offset = i * 2 * width
        
        # Actual bars (solid)
        ax.bar([pos + offset for pos in x], actual_values, width=width, 
               color=colors[category], label=f"Actual {category.title()}", 
               edgecolor='white', linewidth=1)
        
        # Budget bars (hatched)
        ax.bar([pos + offset + width for pos in x], budget_values, width=width, 
               color=colors[category], alpha=0.5, hatch="//", 
               label=f"Budget {category.title()}", 
               edgecolor='white', linewidth=0.5)

    ax.set_xticks([pos + width for pos in x])
    ax.set_xticklabels([month_label(key) for key in month_keys], rotation=45, ha="right", fontsize=10)
    ax.set_ylabel("Amount ($)", fontsize=11, fontweight='600')
    ax.set_title("Monthly Budget vs Actual Trend", fontsize=14, fontweight='bold', pad=15)
    
    # Add grid for better readability
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.7)
    ax.set_axisbelow(True)
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}' if x >= 0 else f'-${abs(x):,.0f}'))
    
    # Create custom legend
    category_handles = [plt.Rectangle((0, 0), 1, 1, color=colors[c], label=c.title(), edgecolor='white', linewidth=1) for c in categories]
    budget_handle = plt.Rectangle((0, 0), 1, 1, color="gray", alpha=0.5, hatch="//", label="Budget", edgecolor='white', linewidth=0.5)
    actual_handle = plt.Rectangle((0, 0), 1, 1, color="gray", label="Actual", edgecolor='white', linewidth=1)
    legend1 = ax.legend(handles=category_handles, title="Category", loc="upper left", fontsize=10, title_fontsize=11)
    ax.add_artist(legend1)
    ax.legend(handles=[actual_handle, budget_handle], title="Line Type", loc="upper right", fontsize=10, title_fontsize=11)
    
    # Clean up spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# -----------------------------
# UI helpers
# -----------------------------
def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def create_excel_bytes(df: pd.DataFrame) -> bytes | None:
    try:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Transactions')
        return buffer.getvalue()
    except ImportError:
        return None
    except Exception:
        return None


def metric_card(title: str, value: str, caption: str = "") -> None:
    """Enhanced metric card with gradient backgrounds and better styling."""
    # Determine color based on entry type or keyword
    color_class = "neutral"
    if "revenue" in title.lower():
        light_bg = "#e8f8f5"
        dark_bg = "#1a3a35"
        border_color = "#27ae60"
        icon = "📈"
    elif "expense" in title.lower() or "cost" in title.lower():
        light_bg = "#fadbd8"
        dark_bg = "#3a1a1a"
        border_color = "#e74c3c"
        icon = "💰"
    elif "saving" in title.lower():
        light_bg = "#d6eaf8"
        dark_bg = "#1a2a3a"
        border_color = "#3498db"
        icon = "🎯"
    elif "net" in title.lower() or "balance" in title.lower():
        light_bg = "#fef5e7"
        dark_bg = "#3a3220"
        border_color = "#f39c12"
        icon = "💵"
    else:
        light_bg = "#ecf0f1"
        dark_bg = "#2a2a2a"
        border_color = "#95a5a6"
        icon = "📊"
    
    html_content = f"""
    <div style="
        background: linear-gradient(135deg, {light_bg} 0%, #ffffff 100%);
        border: 2px solid {border_color};
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    ">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-size: 0.9rem; font-weight: 600; color: #7f8c8d;">{icon} {title.upper()}</span>
        </div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #2c3e50; margin-bottom: 0.3rem;">{value}</div>
        {f'<div style="font-size: 0.8rem; color: #7f8c8d;">{caption}</div>' if caption else ''}
    </div>
    
    <style>
    @media (prefers-color-scheme: dark) {{
        div[style*="background: linear-gradient"] {{
            background: linear-gradient(135deg, {dark_bg} 0%, #252525 100%) !important;
            color: #e0e0e0;
        }}
        div[style*="background: linear-gradient"] div[style*="font-size: 1.8rem"] {{
            color: #e0e0e0 !important;
        }}
        div[style*="background: linear-gradient"] span {{
            color: #b0b0b0 !important;
        }}
    }}
    </style>
    """
    st.markdown(html_content, unsafe_allow_html=True)


def budget_progress_bar(category: str, actual: float, budget: float) -> None:
    """Display a visual progress bar for budget utilization with color coding."""
    if budget <= 0:
        return
    
    percentage = (actual / budget) * 100
    percentage = min(percentage, 200)  # Cap at 200% for display
    
    # Determine color based on percentage
    if percentage > 100:
        bar_color = "#e74c3c"  # Red - over budget
        status = "Over Budget"
    elif percentage >= 80:
        bar_color = "#f39c12"  # Orange - warning
        status = "Warning"
    else:
        bar_color = "#2ecc71"  # Green - on track
        status = "On Track"
    
    # Build percentage display
    percentage_display = f'{percentage:.0f}%' if percentage > 10 else ''
    
    # Build remaining/overage display
    if actual > budget:
        remaining_display = f'<span style="font-size: 0.75rem; color: #e74c3c; font-weight: 600;">Over by {format_currency(actual - budget)}</span>'
    else:
        remaining_display = f'<span style="font-size: 0.75rem; color: #27ae60;">Remaining: {format_currency(budget - actual)}</span>'
    
    html_content = f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-weight: 600; color: #2c3e50;">{category}</span>
            <span style="font-size: 0.9rem; color: #7f8c8d;">{format_currency(actual)} / {format_currency(budget)}</span>
        </div>
        <div style="width: 100%; height: 24px; background: #ecf0f1; border-radius: 12px; overflow: hidden; border: 1px solid #bdc3c7;">
            <div style="width: {min(percentage, 100)}%; height: 100%; background: {bar_color}; display: flex; align-items: center; justify-content: center; transition: width 0.3s ease;">
                <span style="color: white; font-weight: 600; font-size: 0.75rem;">{percentage_display}</span>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 0.3rem;">
            <span style="font-size: 0.75rem; color: #95a5a6;">{status}</span>
            {remaining_display}
        </div>
    </div>
    
    <style>
    @media (prefers-color-scheme: dark) {{
        div[style*="display: flex"] {{
            color: #e0e0e0 !important;
        }}
    }}
    </style>
    """
    st.markdown(html_content, unsafe_allow_html=True)


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
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📅 This Month", key="nav_jump_current_month_btn", use_container_width=True):
            ensure_month_exists(data, current_key)
            save_json_dict(DATA_FILE, data)
            st.session_state["selected_month"] = current_key
            st.rerun()
    with col2:
        prev_key = previous_month_key(current_key)
        if st.button("⬅️ Previous", key="nav_jump_prev_month_btn", use_container_width=True):
            if prev_key not in month_keys:
                ensure_month_exists(data, prev_key)
                save_json_dict(DATA_FILE, data)
            st.session_state["selected_month"] = prev_key
            st.rerun()
    with col3:
        next_key = f"{int(current_key[:4])}-{int(current_key[5:]) + 1:02d}" if int(current_key[5:]) < 12 else f"{int(current_key[:4]) + 1}-01"
        if st.button("➡️ Next", key="nav_jump_next_month_btn", use_container_width=True):
            if next_key not in month_keys:
                ensure_month_exists(data, next_key)
                save_json_dict(DATA_FILE, data)
            st.session_state["selected_month"] = next_key
            st.rerun()


# -----------------------------
# Login page
# -----------------------------
def show_login_page() -> None:
    if st.session_state.get("logout_success"):
        st.success("✅ Logged out successfully.")
        st.session_state["logout_success"] = False

    # Create centered layout for login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 3rem 0;">
                <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">💸 Monthly Budget Tracker</h1>
                <p style="font-size: 1.1rem; color: #7f8c8d; margin-bottom: 2rem;">
                    Track revenues, expenses, budgets, and savings together
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        with st.container(border=True):
            st.markdown("""
                <div style="text-align: center; margin-bottom: 1.5rem;">
                    <h3 style="margin: 0; color: #2c3e50;">Sign In</h3>
                    <p style="color: #7f8c8d; font-size: 0.9rem; margin-top: 0.5rem;">Enter your username and password</p>
                </div>
            """, unsafe_allow_html=True)
            
            username = st.text_input(
                "👤 Username",
                placeholder="tyshawn or lexi",
                key="login_username",
            )
            password = st.text_input(
                "🔐 Password",
                type="password",
                key="login_password",
            )

            if st.button(
                "Sign In",
                key="auth_login_btn",
                type="primary",
                use_container_width=True,
            ):
                if not username or not password:
                    st.error("⚠️ Please enter both username and password.")
                    st.stop()

                if validate_credentials(username, password):
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = username.strip().lower()
                    st.session_state["page"] = "dashboard"
                    st.session_state["login_success"] = True
                    st.rerun()
                else:
                    st.error("❌ Invalid login. Check your username and password.")
        
        st.markdown("""
            <div style="text-align: center; color: #95a5a6; font-size: 0.85rem; margin-top: 2rem;">
                <p>🔒 Your financial data is stored locally and securely</p>
            </div>
        """, unsafe_allow_html=True)


# -----------------------------
# Sidebar
# -----------------------------
def show_sidebar(data: dict) -> None:
    with st.sidebar:
        name = DISPLAY_NAMES.get(current_username(), current_username().title())
        
        # Sidebar header with better styling
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0; border-bottom: 2px solid #e0e0e0; margin-bottom: 1.5rem;">
                <h1 style="margin: 0; color: #3498db; font-size: 1.8rem;">💸 Budget Tracker</h1>
                <p style="margin: 0.5rem 0 0 0; color: #7f8c8d; font-size: 0.85rem;">Logged in as <strong>{}</strong></p>
            </div>
        """.format(name), unsafe_allow_html=True)

        show_month_selector(data)
        st.divider()

        st.markdown("### 📍 Navigation")
        nav_items = [
            ("dashboard", "🏠 Dashboard", "nav_dashboard_btn"),
            ("quick_add", "⚡ Quick Add", "nav_quick_add_btn"),
            ("tracker", "🧾 Monthly Tracker", "nav_tracker_btn"),
            ("budget", "📘 Budget Planner", "nav_budget_btn"),
            ("analytics", "📊 Analytics", "nav_analytics_btn"),
            ("goals", "🎯 Savings Goals", "nav_goals_btn"),
            ("settings", "⚙️ Settings", "nav_settings_btn"),
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
            st.session_state["logout_success"] = True
            st.rerun()
        
        st.divider()
        st.markdown("""
            <div style="text-align: center; color: #95a5a6; font-size: 0.75rem; padding-top: 1rem;">
                <p style="margin: 0.3rem 0;">💡 Manage your money together</p>
                <p style="margin: 0.3rem 0; font-style: italic;">Version 1.0</p>
            </div>
        """, unsafe_allow_html=True)


# -----------------------------

def plot_spending_by_category(df: pd.DataFrame, title: str = "Spending by Category") -> None:
    """Display pie chart of spending by category."""
    if df.empty:
        st.info("No spending data yet.")
        return
    
    expenses = df[df["entry_type"] == "expense"]
    if expenses.empty:
        st.info("No expenses yet.")
        return
    
    spending = expenses.groupby("category")["amount"].sum().sort_values(ascending=False).head(10)
    
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#1e1e1e')
    ax.set_facecolor('#1e1e1e')
    
    # Enhanced color palette
    colors = ['#FF6B6B', '#FFA500', '#FFD93D', '#6BCB77', '#4D96FF', '#9D84B7', '#FF85B3', '#FFB84D', '#A8E6CF', '#FFB3BA']
    
    wedges, texts, autotexts = ax.pie(
        spending.values, 
        labels=spending.index, 
        autopct='%1.1f%%',
        colors=colors[:len(spending)],
        startangle=90,
        textprops={'fontsize': 10, 'weight': 'bold'},
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )
    
    # Style percentage text
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(9)
        autotext.set_weight('bold')
    
    # Style labels
    for text in texts:
        text.set_color('#e0e0e0')
        text.set_fontsize(9)
        text.set_weight('bold')
    
    ax.set_title(title, fontsize=13, fontweight='bold', color='#e0e0e0', pad=20)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def show_spending_velocity(df: pd.DataFrame, month_key: str) -> None:
    """Show projected end-of-month spending based on current pace."""
    if df.empty:
        st.info("No spending data yet.")
        return
    
    expenses = df[df["entry_type"] == "expense"]
    if expenses.empty:
        return
    
    year, month = map(int, month_key.split("-"))
    days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30 if month != 2 else 28
    days_elapsed = max(1, (date.today() - date(year, month, 1)).days + 1)
    
    if days_elapsed < days_in_month:
        total_spent = float(expenses["amount"].sum())
        daily_avg = total_spent / days_elapsed
        projected = daily_avg * days_in_month
        days_remaining = days_in_month - days_elapsed
        
        # Create visual metrics with better styling
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "💰 Daily Average",
                format_currency(daily_avg),
                delta=f"{days_remaining} days left",
                delta_color="off"
            )
        
        with col2:
            st.metric(
                "📈 Projected Total",
                format_currency(projected),
                delta=f"{days_elapsed}/{days_in_month} days",
                delta_color="off"
            )
        
        with col3:
            budget_comparison = f"+{format_currency(total_spent)}" if total_spent > 0 else format_currency(total_spent)
            st.metric(
                "✓ Current Spending",
                format_currency(total_spent),
                delta=f"~{format_currency(daily_avg)}/day",
                delta_color="off"
            )
        
        # Add a progress bar showing month progress
        progress = days_elapsed / days_in_month
        st.progress(progress, text=f"Month {progress*100:.0f}% complete")


def show_budget_vs_actual(data: dict, month_key: str, owner: str) -> None:
    """Display side-by-side comparison of budgeted vs actual spending by category."""
    df = transaction_dataframe(data, month_key)
    owner_df = owner_filtered_df(df, owner)
    
    if owner_df.empty:
        st.info("No transaction data yet.")
        return
    
    budget_record = data.get("budgets", {}).get(month_key, {}).get(owner, empty_budget_block())
    expenses_df = owner_df[owner_df["entry_type"] == "expense"]
    
    if expenses_df.empty:
        st.info("No expense data yet.")
        return
    
    # Get actual spending by category
    actual_by_cat = expenses_df.groupby("category")["amount"].sum()
    
    # Get budgeted amounts
    budgeted_by_cat = budget_record.get("expense", {})
    
    # Merge and prepare for comparison
    categories = sorted(set(list(actual_by_cat.index) + list(budgeted_by_cat.keys())))
    actual_vals = [float(actual_by_cat.get(cat, 0)) for cat in categories]
    budget_vals = [float(budgeted_by_cat.get(cat, 0)) for cat in categories]
    
    # Create comparison chart
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#1e1e1e')
    ax.set_facecolor('#1e1e1e')
    
    x = range(len(categories))
    width = 0.35
    
    bars1 = ax.bar([i - width/2 for i in x], budget_vals, width, label='Budgeted', color='#3498db', edgecolor='white', linewidth=1.5, alpha=0.8)
    bars2 = ax.bar([i + width/2 for i in x], actual_vals, width, label='Actual', color='#e74c3c', edgecolor='white', linewidth=1.5, alpha=0.8)
    
    # Styling
    ax.set_ylabel('Amount ($)', fontsize=11, fontweight='bold', color='#e0e0e0')
    ax.set_title(f'Budget vs Actual Spending - {OWNER_LABELS[owner]}', fontsize=13, fontweight='bold', color='#e0e0e0', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha='right', color='#e0e0e0', fontsize=9)
    ax.legend(fontsize=10, facecolor='#2a2a2a', edgecolor='#555', labelcolor='#e0e0e0')
    ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.7)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}' if x >= 0 else f'-${abs(x):,.0f}'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#555')
    ax.spines['bottom'].set_color('#555')
    ax.tick_params(colors='#e0e0e0')
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${height:.0f}',
                       ha='center', va='bottom', fontsize=8, color='#e0e0e0', weight='bold')
    
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def show_category_trends(data: dict, month_key: str) -> None:
    """Show which categories are trending up/down month-over-month."""
    prev_month = previous_month_key(month_key)
    
    curr_df = transaction_dataframe(data, month_key)
    prev_df = transaction_dataframe(data, prev_month) if prev_month in data.get("budgets", {}) else pd.DataFrame()
    
    if curr_df.empty or prev_df.empty:
        st.info("Not enough data to show trends yet.")
        return
    
    curr_expenses = curr_df[curr_df["entry_type"] == "expense"].groupby("category")["amount"].sum()
    prev_expenses = prev_df[prev_df["entry_type"] == "expense"].groupby("category")["amount"].sum()
    
    # Calculate changes
    categories = sorted(set(list(curr_expenses.index) + list(prev_expenses.index)))
    trends = []
    
    for cat in categories:
        curr_val = float(curr_expenses.get(cat, 0))
        prev_val = float(prev_expenses.get(cat, 0))
        
        if prev_val > 0:
            pct_change = ((curr_val - prev_val) / prev_val) * 100
            change_amount = curr_val - prev_val
        else:
            pct_change = 100 if curr_val > 0 else 0
            change_amount = curr_val
        
        trends.append({
            'category': cat,
            'current': curr_val,
            'previous': prev_val,
            'change': change_amount,
            'pct_change': pct_change
        })
    
    # Sort by percentage change descending
    trends.sort(key=lambda x: x['pct_change'], reverse=True)
    
    st.markdown("**Category Spending Trends (Month-over-Month)**")
    
    for trend in trends:
        if trend['previous'] > 0 or trend['current'] > 0:
            icon = "📈" if trend['pct_change'] > 0 else "📉" if trend['pct_change'] < 0 else "➡️"
            color = "#e74c3c" if trend['pct_change'] > 0 else "#2ecc71" if trend['pct_change'] < 0 else "#f39c12"
            
            col1, col2 = st.columns([3, 1])
            with col1:
                current_display = format_currency(trend['current']).replace("$", "\\$")
                previous_display = format_currency(trend['previous']).replace("$", "\\$")
                st.markdown(
                    f"{icon} **{trend['category']}**: {current_display} (was {previous_display})"
                )
            with col2:
                st.write(f"<span style='color:{color}; font-weight:bold;'>{trend['pct_change']:+.1f}%</span>", 
                        unsafe_allow_html=True)


def compare_with_previous_month(data: dict, month_key: str) -> None:
    """Show side-by-side comparison with previous month."""
    prev_key = previous_month_key(month_key)
    
    curr_df = transaction_dataframe(data, month_key)
    prev_df = transaction_dataframe(data, prev_key) if prev_key in data.get("budgets", {}) else pd.DataFrame()
    
    curr_sum = monthly_summary(curr_df)
    prev_sum = monthly_summary(prev_df) if not prev_df.empty else {k: 0.0 for k in ["revenue", "expense", "savings", "net"]}
    revenue_delta = curr_sum["revenue"] - prev_sum["revenue"]
    expense_delta = curr_sum["expense"] - prev_sum["expense"]
    net_delta = curr_sum["net"] - prev_sum["net"]

    revenue_delta_text = f"{'+' if revenue_delta >= 0 else '-'}${abs(revenue_delta):,.2f} vs prev"
    expense_delta_text = f"{'+' if expense_delta >= 0 else '-'}${abs(expense_delta):,.2f} vs prev"
    net_delta_text = f"{'+' if net_delta >= 0 else '-'}${abs(net_delta):,.2f} vs prev"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Revenue")
        st.metric(
            "This Month",
            format_currency(curr_sum["revenue"]),
            revenue_delta_text,
            delta_color="normal",
        )
    with col2:
        st.subheader("Expenses")
        st.metric(
            "This Month",
            format_currency(curr_sum["expense"]),
            expense_delta_text,
            delta_color="inverse",
        )
    with col3:
        st.subheader("Net")
        st.metric(
            "This Month",
            format_currency(curr_sum["net"]),
            net_delta_text,
            delta_color="normal",
        )


def get_seasonal_comparison(data: dict, month_key: str) -> dict:
    """Compare current month to same month last year."""
    year, month = map(int, month_key.split("-"))
    prev_year_key = f"{year - 1}-{month:02d}"
    
    curr_df = transaction_dataframe(data, month_key)
    prev_year_df = transaction_dataframe(data, prev_year_key) if prev_year_key in data.get("budgets", {}) else pd.DataFrame()
    
    curr_sum = monthly_summary(curr_df)
    prev_year_sum = monthly_summary(prev_year_df) if not prev_year_df.empty else {k: 0.0 for k in ["revenue", "expense", "savings", "net"]}
    
    return {
        "current": curr_sum,
        "previous_year": prev_year_sum,
        "has_prev_year": not prev_year_df.empty
    }


def show_bill_reminders(data: dict, month_key: str) -> None:
    """Display recurring transactions (bills) for the month."""
    df = transaction_dataframe(data, month_key)
    recurring = df[df["recurrence_frequency"] != "None"].copy()
    
    if recurring.empty:
        st.info("No recurring bills set up yet.")
        return
    
    st.subheader("Recurring Bills & Income")
    for _, row in recurring.iterrows():
        icon = "📥" if row["entry_type"] == "revenue" else "📤"
        st.write(f"{icon} **{row['category']}** • {OWNER_LABELS[row['owner']]} • {format_currency(row['amount'])}")
        st.caption(f"Added by {DISPLAY_NAMES.get(row['created_by'], row['created_by'])}")


def show_savings_goals(data: dict) -> None:
    """Track and display savings goals."""
    if "savings_goals" not in data:
        data["savings_goals"] = {}
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Savings Goals")
    with col2:
        if st.button("Add Goal", key="add_goal_btn"):
            st.session_state["adding_goal"] = True
    
    if st.session_state.get("adding_goal"):
        with st.form("add_goal_form"):
            goal_name = st.text_input("Goal Name", placeholder="Emergency Fund")
            target_amount = st.number_input("Target Amount", min_value=0.0, step=100.0)
            submit = st.form_submit_button("Create Goal")
            
            if submit and goal_name:
                data["savings_goals"][goal_name] = {
                    "target": target_amount,
                    "created": date.today().isoformat(),
                    "current": 0.0
                }
                save_json_dict(DATA_FILE, data)
                st.session_state["adding_goal"] = False
                st.rerun()
    
    for goal_name, goal_data in data.get("savings_goals", {}).items():
        target = goal_data.get("target", 0.0)
        current = goal_data.get("current", 0.0)
        pct = (current / target * 100) if target > 0 else 0
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(min(pct / 100, 1.0), text=f"{goal_name}: {format_currency(current)}/{format_currency(target)} ({pct:.0f}%)")
        with col2:
            if st.button("✏️", key=f"edit_goal_{goal_name}", help="Edit goal"):
                st.session_state[f"edit_goal_{goal_name}"] = True
    
    save_json_dict(DATA_FILE, data)


# Dashboard page
# -----------------------------
def show_dashboard(data: dict) -> None:
    if st.session_state.get("login_success"):
        st.success("✅ Logged in successfully!")
        st.session_state["login_success"] = False

    month_key = st.session_state["selected_month"]
    df = transaction_dataframe(data, month_key)
    overall = monthly_summary(df)
    cumulative_savings = total_savings(data)
    ty_df = owner_filtered_df(df, "tyshawn")
    lexi_df = owner_filtered_df(df, "lexi")
    personal_df = df[df["owner"].isin(["tyshawn", "lexi"])].copy()
    budget_totals = combined_budget_totals(data, month_key)

    # Enhanced header
    st.markdown(f"""
        <div style="padding: 2rem 0 1rem 0;">
            <h1 style="margin: 0; color: #2c3e50;">📊 Dashboard</h1>
            <p style="margin: 0.5rem 0 0 0; color: #7f8c8d; font-size: 1rem;">{month_label(month_key)} Overview</p>
        </div>
    """, unsafe_allow_html=True)
    st.caption("Quick overview of your financial activity this month.")
    st.divider()

    panel_col1, panel_col2 = st.columns([1.3, 1])
    with panel_col1:
        show_notifications_panel(data, month_key)
    with panel_col2:
        show_recent_activity_panel(data)

    st.divider()

    st.toggle("Compact mobile mode", key="compact_dashboard_mode", help="Collapse the heavier dashboard sections into expanders for easier phone use.")

    compact_mode = st.session_state.get("compact_dashboard_mode", False)

    def render_summary_and_core() -> None:
        st.markdown("### 📈 Monthly Summary")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            metric_card("Revenue", format_currency(overall["revenue"]))
        with col2:
            metric_card("Expenses", format_currency(overall["expense"]))
        with col3:
            metric_card("Monthly Savings", format_currency(overall["savings"]))
        with col4:
            metric_card("Lifetime Savings", format_currency(cumulative_savings))
        with col5:
            metric_card("Net Balance", format_currency(overall["net"]))

    def render_insights_and_budget() -> None:
        st.markdown("### 💡 Spending Insights")
        insights_col1, insights_col2, insights_col3 = st.columns(3)

        with insights_col1:
            top_category = get_top_spending_category(personal_df)
            if top_category:
                metric_card("Top Category", top_category[0], f"{format_currency(top_category[1])}")
            else:
                st.info("📭 No spending data yet")

        with insights_col2:
            highest = get_highest_transaction(personal_df)
            if highest:
                metric_card("Highest Transaction", format_currency(highest["amount"]), f"{highest['category']}")
            else:
                st.info("📭 No transactions yet")

        with insights_col3:
            daily_avg = get_daily_average_spending(personal_df, month_key)
            metric_card("Daily Avg Spending", format_currency(daily_avg), "per day")

        st.divider()
        st.markdown("### 🎯 Budget Overview")
        budget_col1, budget_col2 = st.columns(2)
        with budget_col1:
            metric_card("Budgeted Expenses", format_currency(budget_totals["expense_budget"]))
        with budget_col2:
            metric_card("Budgeted Revenue", format_currency(budget_totals["revenue_budget"]))

        st.divider()
        st.markdown("### 👥 Individual Breakdown")
        left, middle, right = st.columns(3)
        with left:
            summary = monthly_summary(ty_df)
            metric_card("TyShawn Net", format_currency(summary["net"]))
        with middle:
            summary = monthly_summary(lexi_df)
            metric_card("Lexi Net", format_currency(summary["net"]))
        with right:
            summary = monthly_summary(personal_df)
            metric_card("Total Net", format_currency(summary["net"]))

    def render_visual_sections() -> None:
        st.markdown("### 📊 Category Breakdown")
        viz_col1, viz_col2 = st.columns(2)
        with viz_col1:
            plot_spending_by_category(personal_df, f"Spending by Category - {month_label(month_key)}")
        with viz_col2:
            st.markdown("### ⚡ Spending Velocity")
            show_spending_velocity(personal_df, month_key)

        st.divider()
        show_category_growth_alerts(data, month_key)

        st.divider()
        st.markdown("### 👥 Spending Comparison: TyShawn vs Lexi")
        show_spending_by_owner(data, month_key)

        st.divider()
        st.markdown("### 💼 Budget vs Actual Spending")
        budget_viz_col1, budget_viz_col2 = st.columns(2)
        with budget_viz_col1:
            show_budget_vs_actual(data, month_key, "tyshawn")
        with budget_viz_col2:
            show_budget_vs_actual(data, month_key, "lexi")

        st.divider()
        st.markdown("### 📈 Month Comparison")
        compare_with_previous_month(data, month_key)

        st.divider()
        st.markdown("### 📊 Category Spending Trends")
        show_category_trends(data, month_key)

        st.divider()
        st.markdown("### 🔮 3-Month Cash Flow Forecast")
        show_cash_flow_forecast(data, month_key)

        st.divider()
        seasonal = get_seasonal_comparison(data, month_key)
        if seasonal["has_prev_year"]:
            st.markdown("### 📅 Year-over-Year Comparison")
            col1, col2, col3 = st.columns(3)
            prev_year = seasonal["previous_year"]
            with col1:
                st.metric(
                    "Revenue vs Last Year",
                    format_currency(seasonal["current"]["revenue"]),
                    f"{format_currency(seasonal['current']['revenue'] - prev_year['revenue'])}",
                )
            with col2:
                st.metric(
                    "Expenses vs Last Year",
                    format_currency(seasonal["current"]["expense"]),
                    f"{format_currency(seasonal['current']['expense'] - prev_year['expense'])}",
                )
            with col3:
                st.metric(
                    "Savings vs Last Year",
                    format_currency(seasonal["current"]["savings"]),
                    f"{format_currency(seasonal['current']['savings'] - prev_year['savings'])}",
                )

    def render_recent_entries() -> None:
        st.markdown("### 📝 Recent Entries")
        if df.empty:
            st.info("📭 No entries yet")
            if st.button("⚡ Add your first transaction", key="dashboard_quick_add_btn"):
                st.session_state["page"] = "quick_add"
                st.rerun()
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

    render_summary_and_core()
    st.divider()

    if compact_mode:
        with st.expander("💡 Insights & budget", expanded=False):
            render_insights_and_budget()
        with st.expander("📊 Charts, trends & comparisons", expanded=False):
            render_visual_sections()
        with st.expander("📝 Recent entries", expanded=False):
            render_recent_entries()
    else:
        render_insights_and_budget()
        st.divider()
        render_visual_sections()
        st.divider()
        render_recent_entries()


# -----------------------------
# Quick Add page
# -----------------------------
def render_entry_form(data: dict, month_key: str, form_prefix: str) -> None:
    # Get most used categories for quick access
    most_used = get_most_used_categories(data)

    form_date_key = f"{form_prefix}_date_{month_key}"
    form_type_key = f"{form_prefix}_type_{month_key}"
    form_owner_key = f"{form_prefix}_owner_{month_key}"
    form_category_key = f"{form_prefix}_category_{month_key}"
    form_amount_key = f"{form_prefix}_amount_{month_key}"
    form_desc_key = f"{form_prefix}_desc_{month_key}"
    form_recurrence_freq_key = f"{form_prefix}_recurrence_frequency_{month_key}"
    form_recurrence_count_key = f"{form_prefix}_recurrence_count_{month_key}"
    pending_template_key = f"{form_prefix}_pending_template_{month_key}"

    pending_template = st.session_state.pop(pending_template_key, None)
    if isinstance(pending_template, dict):
        pending_type = str(pending_template.get("entry_type", "expense")).strip().lower()
        if pending_type not in ["expense", "revenue", "savings"]:
            pending_type = "expense"
        st.session_state[form_type_key] = pending_type
        st.session_state[form_owner_key] = pending_template.get("owner", current_username() or TRANSACTION_OWNERS[0])
        st.session_state[form_category_key] = pending_template.get("category", "")
        st.session_state[form_amount_key] = float(pending_template.get("amount", 0.0) or 0.0)
        st.session_state[form_desc_key] = str(pending_template.get("description", ""))

    if form_date_key not in st.session_state:
        st.session_state[form_date_key] = date.today() if month_key == month_key_from_date(date.today()) else datetime.strptime(month_key + "-01", "%Y-%m-%d").date()

    if st.session_state.get(form_type_key) not in ["expense", "revenue", "savings"]:
        st.session_state[form_type_key] = "expense"

    if st.session_state.get(form_owner_key) not in TRANSACTION_OWNERS:
        st.session_state[form_owner_key] = current_username() or TRANSACTION_OWNERS[0]

    st.markdown("### 📝 Enter Transaction Details")

    col1, col2 = st.columns([1, 1])
    with col1:
        selected_date = st.date_input(
            "📅 Date",
            key=form_date_key,
        )
    with col2:
        entry_type = st.selectbox(
            "📊 Entry Type",
            options=["expense", "revenue", "savings"],
            format_func=lambda value: ENTRY_TYPE_LABELS[value],
            key=form_type_key,
        )

    col3, col4 = st.columns([1, 1])
    with col3:
        owner = st.selectbox(
            "👤 Who does this belong to?",
            options=TRANSACTION_OWNERS,
            format_func=lambda value: OWNER_LABELS[value],
            key=form_owner_key,
        )
    with col4:
        if entry_type == "expense":
            categories = most_used.get("expense", EXPENSE_CATEGORIES)
        elif entry_type == "revenue":
            categories = most_used.get("revenue", REVENUE_CATEGORIES)
        else:
            categories = most_used.get("savings", SAVINGS_CATEGORIES)

        current_category = st.session_state.get(form_category_key, categories[0] if categories else "")
        if current_category not in categories:
            st.session_state[form_category_key] = categories[0] if categories else ""

        category = st.selectbox(
            "🏷️ Category",
            options=categories,
            key=form_category_key,
        )

    col5, col6 = st.columns([1, 1])
    with col5:
        amount = st.number_input(
            "💰 Amount",
            min_value=0.0,
            step=1.0,
            format="%.2f",
            key=form_amount_key,
        )
    with col6:
        description = st.text_input(
            "📝 Description",
            placeholder="Required - what was this for?",
            key=form_desc_key,
        )

    submitted = st.button("➕ Add Entry", key=f"{form_prefix}_submit_btn_{month_key}", type="primary", use_container_width=True)
    if submitted:
        if amount <= 0:
            st.error("❌ Amount must be greater than $0.01")
            st.stop()
        if not description.strip():
            st.error("❌ Please provide a description of the transaction")
            st.stop()

        transaction = add_transaction(
            data=data,
            month_key=month_key,
            entry_date=selected_date,
            entry_type=entry_type,
            owner=owner,
            category=category,
            amount=amount,
            description=description,
            created_by=current_username(),
            recurrence_frequency="None",
            recurrence_count=1,
        )
        set_undo_action(
            "add",
            {"transaction_id": transaction["id"]},
            f"Added {ENTRY_TYPE_LABELS[entry_type]}: {category} for {format_currency(amount)}.",
        )
        save_json_dict(DATA_FILE, data)
        st.success("✅ Entry added successfully! 🎉")
        st.session_state["page"] = "tracker"
        st.rerun()


def show_quick_add(data: dict) -> None:
    month_key = st.session_state["selected_month"]
    form_prefix = "quick_add"
    form_type_key = f"{form_prefix}_type_{month_key}"
    form_owner_key = f"{form_prefix}_owner_{month_key}"
    form_category_key = f"{form_prefix}_category_{month_key}"
    form_amount_key = f"{form_prefix}_amount_{month_key}"
    form_desc_key = f"{form_prefix}_desc_{month_key}"
    pending_template_key = f"{form_prefix}_pending_template_{month_key}"
    
    st.markdown(f"""
        <div style="padding: 2rem 0 1rem 0;">
            <h1 style="margin: 0; color: #2c3e50;">⚡ Quick Add</h1>
            <p style="margin: 0.5rem 0 0 0; color: #7f8c8d; font-size: 1rem;">{month_label(month_key)}</p>
        </div>
    """, unsafe_allow_html=True)
    st.caption("Quick Add stays available for manual entry only — templates just prefill the form and do not create automatic recurring payments.")
    st.divider()

    st.markdown("### 📋 Quick Templates")
    current_owner = current_username() or TRANSACTION_OWNERS[0]
    quick_templates = {
        "💰 Paycheck": {
            "entry_type": "revenue",
            "owner": current_owner,
            "category": "Paycheck",
            "amount": 0.0,
            "description": "Paycheck",
        },
        "🏠 Rent": {
            "entry_type": "expense",
            "owner": current_owner,
            "category": "Rent + Utilities",
            "amount": 0.0,
            "description": "Rent Payment",
        },
        "🛒 Groceries": {
            "entry_type": "expense",
            "owner": current_owner,
            "category": "Groceries",
            "amount": 0.0,
            "description": "Grocery Shopping",
        },
        "🚗 Gas": {
            "entry_type": "expense",
            "owner": current_owner,
            "category": "Gas",
            "amount": 0.0,
            "description": "Gas",
        },
    }
    saved_templates = get_transaction_templates(data)
    template_buttons = list(quick_templates.items()) + list(saved_templates.items())

    if template_buttons:
        template_cols = st.columns(min(4, len(template_buttons)))
        for index, (label, template) in enumerate(template_buttons[:8]):
            with template_cols[index % len(template_cols)]:
                if st.button(label, key=f"quick_template_{index}_{month_key}", use_container_width=True):
                    st.session_state[pending_template_key] = template
                    st.rerun()

    st.divider()

    show_recent_activity_panel(data)

    with st.container(border=True):
        render_entry_form(data, month_key, "quick_add")


# -----------------------------
# Monthly tracker page
# -----------------------------
def editable_transaction_table(data: dict, df: pd.DataFrame, section_title: str) -> None:
    st.markdown(f"### {section_title}")
    if df.empty:
        st.info("📭 No entries in this section yet.")
        return

    section_key = section_title.lower().replace(" ", "_")

    sorted_df = df.sort_values(["date", "created_at"], ascending=[False, False])
    for _, row in sorted_df.iterrows():
        transaction = next((item for item in data["transactions"] if item["id"] == row["id"]), None)
        if not transaction:
            continue

        # Color code based on entry type
        if row['entry_type'] == 'revenue':
            border_color = "#27ae60"
            icon = "📈"
        elif row['entry_type'] == 'expense':
            border_color = "#e74c3c"
            icon = "💸"
        else:
            border_color = "#3498db"
            icon = "🎯"

        with st.container(border=True):
            left, right = st.columns([4, 1.2])
            with left:
                st.markdown(f"<div style='font-size: 0.95rem;'><strong>{icon} {row['date'].strftime('%Y-%m-%d')} · {ENTRY_TYPE_LABELS[row['entry_type']]} · {OWNER_LABELS[row['owner']]}</strong></div>", unsafe_allow_html=True)
                st.markdown(f"**{row['category']}** · {format_currency(float(row['amount']))}")
                if row.get("description"):
                    st.caption(f"📝 {row['description']}")
                if row.get("recurrence_frequency", "None") != "None" and int(row.get("recurrence_count", 1)) > 1:
                    st.caption(f"🔁 Recurs {row['recurrence_frequency'].lower()} for {int(row['recurrence_count'])} months")
                st.caption(f"Added by {DISPLAY_NAMES.get(row['created_by'], row['created_by'])}")
            with right:
                can_edit = can_edit_transaction(transaction)
                if can_edit:
                    if st.button("✏️ Edit", key=f"edit_txn_btn_{section_title}_{row['id']}", use_container_width=True):
                        st.session_state["editing_transaction_id"] = row["id"]
                        st.rerun()
                    if st.button("🗑️ Delete", key=f"delete_txn_btn_{section_title}_{row['id']}", use_container_width=True):
                        st.session_state[f"confirm_delete_{section_key}_{row['id']}"] = True
                        st.rerun()
                
                if st.session_state.get(f"confirm_delete_{section_key}_{row['id']}"):
                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("✅ Confirm Delete", key=f"confirm_delete_btn_{section_key}_{row['id']}", use_container_width=True):
                            delete_index = next((idx for idx, item in enumerate(data["transactions"]) if item["id"] == row["id"]), len(data["transactions"]))
                            set_undo_action(
                                "delete",
                                {"transaction": deepcopy(transaction), "index": delete_index},
                                f"Deleted {transaction['category']} for {format_currency(float(transaction['amount']))}.",
                            )
                            data["transactions"] = [item for item in data["transactions"] if item["id"] != row["id"]]
                            save_json_dict(DATA_FILE, data)
                            success_placeholder = st.empty()
                            success_placeholder.success("✅ Entry deleted.")
                            if st.session_state.get("editing_transaction_id") == row["id"]:
                                st.session_state["editing_transaction_id"] = None
                            st.session_state[f"confirm_delete_{section_key}_{row['id']}"] = False
                            st.rerun()
                    with col_confirm2:
                        if st.button("❌ Cancel", key=f"cancel_delete_btn_{section_key}_{row['id']}", use_container_width=True):
                            st.session_state[f"confirm_delete_{section_key}_{row['id']}"] = False
                            st.rerun()
                elif not can_edit:
                    st.caption("🔒 Only the creator can edit this entry.")

            if st.session_state.get("editing_transaction_id") == row["id"] and can_edit:
                st.divider()
                with st.container(border=True):
                    st.markdown("#### ✏️ Update Entry")
                    entry_type = st.selectbox(
                        "Entry Type",
                        ["expense", "revenue", "savings"],
                        index=["expense", "revenue", "savings"].index(transaction["entry_type"]),
                        format_func=lambda value: ENTRY_TYPE_LABELS[value],
                        key=f"edit_type_{section_title}_{row['id']}",
                    )
                    owner = st.selectbox(
                        "Owner",
                        TRANSACTION_OWNERS,
                        index=TRANSACTION_OWNERS.index(transaction["owner"]) if transaction["owner"] in TRANSACTION_OWNERS else 0,
                        format_func=lambda value: OWNER_LABELS.get(value, value),
                        key=f"edit_owner_{section_title}_{row['id']}",
                    )
                    if entry_type == "expense":
                        categories = EXPENSE_CATEGORIES
                    elif entry_type == "revenue":
                        categories = REVENUE_CATEGORIES
                    else:
                        categories = SAVINGS_CATEGORIES
                    category = st.selectbox(
                        "Category",
                        categories,
                        index=categories.index(transaction["category"]) if transaction["category"] in categories else 0,
                        key=f"edit_category_{section_title}_{row['id']}",
                    )
                    amount = st.number_input(
                        "Amount",
                        min_value=0.0,
                        value=float(transaction["amount"]),
                        step=1.0,
                        format="%.2f",
                        key=f"edit_amount_{section_title}_{row['id']}",
                    )
                    entry_date = st.date_input(
                        "Date",
                        value=datetime.strptime(transaction["date"], "%Y-%m-%d").date(),
                        key=f"edit_date_{section_title}_{row['id']}",
                    )
                    description = st.text_input(
                        "Description",
                        value=transaction.get("description", ""),
                        key=f"edit_desc_{section_title}_{row['id']}",
                    )
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Save Changes", key=f"save_txn_btn_{section_title}_{row['id']}", type="primary", use_container_width=True):
                            if amount <= 0:
                                st.error("❌ Amount must be greater than zero.")
                                st.stop()
                            previous_snapshot = deepcopy(transaction)
                            transaction["entry_type"] = entry_type
                            transaction["owner"] = owner
                            transaction["category"] = category
                            transaction["amount"] = float(amount)
                            transaction["date"] = entry_date.isoformat()
                            transaction["month_key"] = month_key_from_date(entry_date)
                            transaction["description"] = description.strip()
                            transaction["updated_at"] = datetime.now().isoformat(timespec="seconds")
                            set_undo_action(
                                "edit",
                                {"transaction": previous_snapshot},
                                f"Updated {transaction['category']} to {format_currency(float(transaction['amount']))}.",
                            )
                            save_json_dict(DATA_FILE, data)
                            st.session_state["editing_transaction_id"] = None
                            st.success("✅ Entry updated.")
                            st.rerun()
                    with col_b:
                        if st.button("❌ Cancel", key=f"cancel_txn_btn_{section_title}_{row['id']}", use_container_width=True):
                            st.session_state["editing_transaction_id"] = None
                            st.rerun()


def show_tracker(data: dict) -> None:
    month_key = st.session_state["selected_month"]
    df = transaction_dataframe(data, month_key)

    st.markdown(f"""
        <div style="padding: 2rem 0 1rem 0;">
            <h1 style="margin: 0; color: #2c3e50;">🧾 Monthly Tracker</h1>
            <p style="margin: 0.5rem 0 0 0; color: #7f8c8d; font-size: 1rem;">{month_label(month_key)}</p>
        </div>
    """, unsafe_allow_html=True)
    st.caption("View all entries, organized by type and person. Use filters to search transactions.")
    st.divider()

    show_recent_activity_panel(data)

    overall = monthly_summary(df)
    cumulative_savings = total_savings(data)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        metric_card("Total Revenue", format_currency(overall["revenue"]))
    with col2:
        metric_card("Total Expenses", format_currency(overall["expense"]))
    with col3:
        metric_card("Monthly Savings", format_currency(overall["savings"]))
    with col4:
        metric_card("Lifetime Savings", format_currency(cumulative_savings))
    with col5:
        metric_card("Net Balance", format_currency(overall["net"]))

    st.divider()
    
    # Search and Filter Section
    st.markdown("### 🔍 Search & Filter")
    
    # Cross-month search toggle
    cross_month = st.checkbox("🔎 Search all months (not just current)", value=st.session_state.get("cross_month_search", False), key="cross_month_toggle")
    st.session_state["cross_month_search"] = cross_month
    
    # Get appropriate dataframe for search
    if cross_month:
        df = pd.DataFrame(data.get("transactions", []))
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["entry_type_label"] = df["entry_type"].map(ENTRY_TYPE_LABELS)
            df["owner_label"] = df["owner"].map(OWNER_LABELS)
    
    search_col1, search_col2, search_col3 = st.columns(3)
    
    with search_col1:
        st.session_state["search_query"] = st.text_input(
            "📝 Search by description",
            value=st.session_state.get("search_query", ""),
            placeholder="Type to search...",
            key="tracker_search_input"
        )
    
    with search_col2:
        categories = ["All"] + sorted(set(df["category"].tolist())) if not df.empty else ["All"]
        st.session_state["search_category"] = st.selectbox(
            "🏷️ Category",
            options=categories,
            index=0,
            key="tracker_category_filter"
        )
    
    with search_col3:
        amount_range = st.slider(
            "💰 Amount Range",
            min_value=0.0,
            max_value=float(df["amount"].max()) if not df.empty else 1000.0,
            value=(0.0, float(df["amount"].max()) if not df.empty else 1000.0),
            step=10.0,
            key="tracker_amount_filter"
        )
        st.session_state["search_min_amount"] = amount_range[0]
        st.session_state["search_max_amount"] = amount_range[1]

    date_col1, date_col2 = st.columns([3, 1])
    year, month = map(int, month_key.split("-"))
    month_start = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])
    if st.session_state.get("tracker_date_range_month") != month_key:
        st.session_state["search_start_date"] = month_start
        st.session_state["search_end_date"] = month_end
        st.session_state["tracker_date_range_month"] = month_key

    with date_col1:
        selected_range = st.date_input(
            "📅 Date Range",
            value=(st.session_state["search_start_date"], st.session_state["search_end_date"]),
            key="tracker_date_range_input",
        )
        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            st.session_state["search_start_date"], st.session_state["search_end_date"] = selected_range

    with date_col2:
        st.caption("Filter by a specific date range for the selected month.")

    # Apply filters
    filtered_df = df.copy()
    
    if st.session_state["search_query"]:
        filtered_df = filtered_df[filtered_df["description"].str.contains(st.session_state["search_query"], case=False, na=False)]
    
    if st.session_state["search_category"] != "All":
        filtered_df = filtered_df[filtered_df["category"] == st.session_state["search_category"]]
    
    filtered_df = filtered_df[
        (filtered_df["amount"] >= st.session_state["search_min_amount"]) &
        (filtered_df["amount"] <= st.session_state["search_max_amount"])
    ]

    if st.session_state.get("search_start_date") and st.session_state.get("search_end_date"):
        filtered_df = filtered_df[
            (filtered_df["date"] >= pd.to_datetime(st.session_state["search_start_date"])) &
            (filtered_df["date"] <= pd.to_datetime(st.session_state["search_end_date"]))
        ]

    if not df.empty:
        st.caption(f"Showing {len(filtered_df)} of {len(df)} entries")

    if not filtered_df.empty:
        export_df = filtered_df.loc[:, [
            "date",
            "entry_type_label",
            "owner_label",
            "category",
            "amount",
            "description",
            "created_by_label",
            "recurrence_frequency",
            "recurrence_count",
        ]].copy()
        export_df = export_df.rename(columns={
            "date": "Date",
            "entry_type_label": "Type",
            "owner_label": "Owner",
            "category": "Category",
            "amount": "Amount",
            "description": "Description",
            "created_by_label": "Added By",
            "recurrence_frequency": "Repeats",
            "recurrence_count": "Times",
        })
        excel_bytes = create_excel_bytes(export_df)
        if excel_bytes is not None:
            st.download_button(
                label="Download current view as Excel",
                data=excel_bytes,
                file_name=f"{month_key}_transactions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_button",
            )
        st.download_button(
            label="Download current view as CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{month_key}_transactions.csv",
            mime="text/csv",
            key="download_csv_button",
        )

    st.divider()

    st.markdown("### 📅 Recurring Bills & Income")
    show_bill_reminders(data, month_key)
    
    st.divider()
    
    tab_all, tab_ty, tab_lexi = st.tabs([
        "📋 All Entries",
        "👤 TyShawn",
        "👤 Lexi",
    ])

    with tab_all:
        if filtered_df.empty:
            st.info("📭 No entries match your search criteria. Try adjusting your filters.")
        else:
            editable_transaction_table(data, filtered_df, "All Entries")
    with tab_ty:
        ty_filtered = owner_filtered_df(filtered_df, "tyshawn")
        if ty_filtered.empty:
            st.info("📭 No entries found for TyShawn. Try adjusting your filters.")
        else:
            editable_transaction_table(data, ty_filtered, "TyShawn Entries")
    with tab_lexi:
        lexi_filtered = owner_filtered_df(filtered_df, "lexi")
        if lexi_filtered.empty:
            st.info("📭 No entries found for Lexi. Try adjusting your filters.")
        else:
            editable_transaction_table(data, lexi_filtered, "Lexi Entries")


# -----------------------------
# Budget planner page
# -----------------------------
def render_budget_editor(data: dict, month_key: str, owner: str) -> None:
    ensure_month_exists(data, month_key)
    budget_record = data["budgets"][month_key][owner]

    st.markdown(f"### 💵 {OWNER_LABELS[owner]} Budgets")
    st.caption("💡 Tip: Budgets auto-adjust to your actual spending from the previous month to keep them realistic.")
    expense_tab, revenue_tab, savings_tab = st.tabs(["💸 Expenses", "📈 Revenue", "🎯 Savings"])

    with expense_tab:
        with st.form(key=f"budget_expense_form_{owner}_{month_key}"):
            st.markdown("**Set expense budgets for each category:**")
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

            if st.form_submit_button("💾 Save Expense Budgets", type="primary", use_container_width=True):
                data["budgets"][month_key][owner]["expense"] = {k: float(v) for k, v in expense_values.items()}
                save_json_dict(DATA_FILE, data)
                st.success("✅ Expense budgets saved.")
                st.rerun()

    with revenue_tab:
        with st.form(key=f"budget_revenue_form_{owner}_{month_key}"):
            st.markdown("**Set revenue budgets for each category:**")
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

            if st.form_submit_button("💾 Save Revenue Budgets", type="primary", use_container_width=True):
                data["budgets"][month_key][owner]["revenue"] = {k: float(v) for k, v in revenue_values.items()}
                save_json_dict(DATA_FILE, data)
                st.success("✅ Revenue budgets saved.")
                st.rerun()

    with savings_tab:
        with st.form(key=f"budget_savings_form_{owner}_{month_key}"):
            st.markdown("**Set savings budgets for each category:**")
            savings_values = {}
            for category in SAVINGS_CATEGORIES:
                savings_values[category] = st.number_input(
                    category,
                    min_value=0.0,
                    value=float(budget_record["savings"].get(category, 0.0)),
                    step=1.0,
                    format="%.2f",
                    key=f"budget_{owner}_savings_{category}_{month_key}",
                )

            if st.form_submit_button("💾 Save Savings Budgets", type="primary", use_container_width=True):
                data["budgets"][month_key][owner]["savings"] = {k: float(v) for k, v in savings_values.items()}
                save_json_dict(DATA_FILE, data)
                st.success("✅ Savings budgets saved.")
                st.rerun()


def show_budget_page(data: dict) -> None:
    month_key = st.session_state["selected_month"]
    budget_status = ensure_month_exists(data, month_key)
    if budget_status == "copied":
        save_json_dict(DATA_FILE, data)
        st.success("📋 Budget initialized from the prior month.")
    elif budget_status == "created":
        save_json_dict(DATA_FILE, data)
        st.success("✨ New monthly budget created.")
    df = transaction_dataframe(data, month_key)

    st.markdown(f"""
        <div style="padding: 2rem 0 1rem 0;">
            <h1 style="margin: 0; color: #2c3e50;">📘 Budget Planner</h1>
            <p style="margin: 0.5rem 0 0 0; color: #7f8c8d; font-size: 1rem;">{month_label(month_key)}</p>
        </div>
    """, unsafe_allow_html=True)
    st.caption("Set and monitor budgets for both TyShawn and Lexi.")
    st.divider()

    compare_tab, budget_tab = st.tabs(["📊 Budget vs Actual", "💵 Budget Editor"])

    with compare_tab:
        compare_owner = st.selectbox(
            "📊 Compare For",
            options=["total", "tyshawn", "lexi"],
            format_func=lambda value: "Total" if value == "total" else OWNER_LABELS[value],
            key="budget_compare_owner_select",
        )

        if compare_owner == "total":
            filtered_df = df[df["owner"].isin(["tyshawn", "lexi"])].copy()
        else:
            filtered_df = owner_filtered_df(df, compare_owner)
        expense_actual = (
            filtered_df[filtered_df["entry_type"] == "expense"].groupby("category", dropna=False)["amount"].sum().to_dict()
            if not filtered_df.empty else {}
        )
        revenue_actual = (
            filtered_df[filtered_df["entry_type"] == "revenue"].groupby("category", dropna=False)["amount"].sum().to_dict()
            if not filtered_df.empty else {}
        )

        def get_budget_value(category_type: str, category: str) -> float:
            if compare_owner == "total":
                ty_budget = float(data["budgets"][month_key].get("tyshawn", {}).get(category_type, {}).get(category, 0.0))
                lexi_budget = float(data["budgets"][month_key].get("lexi", {}).get(category_type, {}).get(category, 0.0))
                return ty_budget + lexi_budget
            owner_data = data["budgets"][month_key].get(compare_owner, {})
            return float(owner_data.get(category_type, {}).get(category, 0.0))

        expense_rows = []
        for category in EXPENSE_CATEGORIES:
            budget = get_budget_value("expense", category)
            actual = float(expense_actual.get(category, 0.0))
            expense_rows.append({
                "Category": category,
                "Budget": budget,
                "Actual": actual,
                "Difference": budget - actual,
            })

        revenue_rows = []
        for category in REVENUE_CATEGORIES:
            budget = get_budget_value("revenue", category)
            actual = float(revenue_actual.get(category, 0.0))
            revenue_rows.append({
                "Category": category,
                "Budget": budget,
                "Actual": actual,
                "Difference": actual - budget,
            })

        # Savings actual should include both direct savings deposits and transfer-based savings.
        savings_actual = (
            filtered_df[filtered_df["entry_type"] == "savings"].groupby("category", dropna=False)["amount"].sum().to_dict()
            if not filtered_df.empty else {}
        )
        savings_transfer_out = float(
            filtered_df.loc[
                (filtered_df["entry_type"] == "expense") & (filtered_df["category"] == "Savings Transfer"),
                "amount",
            ].sum()
        ) if not filtered_df.empty else 0.0
        savings_transfer_in = float(
            filtered_df.loc[
                (filtered_df["entry_type"] == "revenue") & (filtered_df["category"] == "Savings Transfer"),
                "amount",
            ].sum()
        ) if not filtered_df.empty else 0.0

        # Net transfer contribution to savings (positive means adding to savings).
        net_transfer_to_savings = savings_transfer_out - savings_transfer_in

        savings_rows = []
        primary_savings_category = SAVINGS_CATEGORIES[0] if SAVINGS_CATEGORIES else "Savings Deposit"
        for category in SAVINGS_CATEGORIES:
            budget = get_budget_value("savings", category)
            direct_actual = float(savings_actual.get(category, 0.0))
            transfer_actual = net_transfer_to_savings if category == primary_savings_category else 0.0
            actual = direct_actual + transfer_actual
            savings_rows.append({
                "Category": category,
                "Budget": budget,
                "Actual": actual,
                "Difference": actual - budget,
            })

        st.markdown("### 💸 Expense Budget vs Actual")
        expense_df_display = pd.DataFrame(expense_rows)
        total_budget_expense = float(expense_df_display["Budget"].sum())
        total_actual_expense = float(expense_df_display["Actual"].sum())
        if total_budget_expense > 0:
            st.markdown("**Total Expense Progress:**")
            budget_progress_bar("Total Expenses", total_actual_expense, total_budget_expense)
        if not expense_df_display.empty and expense_df_display[expense_df_display["Budget"] > 0].shape[0] > 0:
            st.markdown("**Visual Progress:**")
            for _, row in expense_df_display[expense_df_display["Budget"] > 0].iterrows():
                budget_progress_bar(row["Category"], row["Actual"], row["Budget"])
            st.markdown("**Detailed Table:**")
        st.dataframe(expense_df_display, use_container_width=True, hide_index=True)
        
        st.markdown("### 📈 Revenue Budget vs Actual")
        revenue_df_display = pd.DataFrame(revenue_rows)
        total_budget_revenue = float(revenue_df_display["Budget"].sum())
        total_actual_revenue = float(revenue_df_display["Actual"].sum())
        if total_budget_revenue > 0:
            st.markdown("**Total Revenue Progress:**")
            budget_progress_bar("Total Revenue", total_actual_revenue, total_budget_revenue)
        if not revenue_df_display.empty and revenue_df_display[revenue_df_display["Budget"] > 0].shape[0] > 0:
            st.markdown("**Visual Progress:**")
            for _, row in revenue_df_display[revenue_df_display["Budget"] > 0].iterrows():
                budget_progress_bar(row["Category"], row["Actual"], row["Budget"])
            st.markdown("**Detailed Table:**")
        st.dataframe(revenue_df_display, use_container_width=True, hide_index=True)
        
        st.markdown("### 🎯 Savings Budget vs Actual")
        savings_df_display = pd.DataFrame(savings_rows)
        total_budget_savings = float(savings_df_display["Budget"].sum())
        total_actual_savings = float(savings_df_display["Actual"].sum())
        if total_budget_savings > 0:
            st.markdown("**Total Savings Progress:**")
            budget_progress_bar("Total Savings", total_actual_savings, total_budget_savings)
        if not savings_df_display.empty and savings_df_display[savings_df_display["Budget"] > 0].shape[0] > 0:
            st.markdown("**Visual Progress:**")
            for _, row in savings_df_display[savings_df_display["Budget"] > 0].iterrows():
                budget_progress_bar(row["Category"], row["Actual"], row["Budget"])
            st.markdown("**Detailed Table:**")
        st.dataframe(savings_df_display, use_container_width=True, hide_index=True)

    with budget_tab:
        owner_tabs = st.tabs(["📊 Totals", "👤 TyShawn", "👤 Lexi"])
        with owner_tabs[0]:
            st.markdown("### 📈 Combined Budget Totals")
            total_budget = combined_budget_totals(data, month_key)
            metric_card("Total Budgeted Expenses", format_currency(total_budget["expense_budget"]))
            metric_card("Total Budgeted Revenue", format_currency(total_budget["revenue_budget"]))
            metric_card("Total Budgeted Savings", format_currency(total_budget["savings_budget"]))
            if any(total_budget.values()):
                totals_rows = []
                for category in EXPENSE_CATEGORIES:
                    totals_rows.append({
                        "Category": category,
                        "Budget": float(data["budgets"][month_key]["tyshawn"]["expense"].get(category, 0.0)) + float(data["budgets"][month_key]["lexi"]["expense"].get(category, 0.0)),
                    })
                st.dataframe(pd.DataFrame(totals_rows), use_container_width=True, hide_index=True)
            else:
                st.info("📭 No budgeted categories yet.")
        with owner_tabs[1]:
            render_budget_editor(data, month_key, "tyshawn")
        with owner_tabs[2]:
            render_budget_editor(data, month_key, "lexi")


# -----------------------------
# Analytics page
# -----------------------------
def plot_bar_chart(series: pd.Series, title: str, x_label: str = "", y_label: str = "Amount ($)") -> None:
    if series.empty:
        st.info("Not enough data to build this chart yet.")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor='white')
    
    # Use a modern color palette
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#e67e22']
    bars = ax.bar(range(len(series)), series.values, color=colors[:len(series)], edgecolor='white', linewidth=1.5)
    
    # Styling
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    if x_label:
        ax.set_xlabel(x_label, fontsize=11, fontweight='600')
    if y_label:
        ax.set_ylabel(y_label, fontsize=11, fontweight='600')
    
    # Set x-axis labels
    ax.set_xticks(range(len(series)))
    ax.set_xticklabels(series.index, rotation=45, ha='right', fontsize=10)
    ax.tick_params(axis='y', labelsize=10)
    
    # Add grid for better readability
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.7)
    ax.set_axisbelow(True)
    
    # Format y-axis as currency if it looks like money
    if y_label and ('$' in y_label or 'Amount' in title or 'Total' in title):
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}' if x >= 0 else f'-${abs(x):,.0f}'))
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:,.0f}' if height > 0 else f'${height:,.0f}',
                ha='center', va='bottom', fontsize=9, fontweight='600')
    
    # Clean up spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def show_analytics(data: dict) -> None:
    month_key = st.session_state["selected_month"]
    current_df = transaction_dataframe(data, month_key)
    all_transactions = pd.DataFrame(data["transactions"])

    st.markdown(f"""
        <div style="padding: 2rem 0 1rem 0;">
            <h1 style="margin: 0; color: #2c3e50;">📊 Analytics</h1>
            <p style="margin: 0.5rem 0 0 0; color: #7f8c8d; font-size: 1rem;">{month_label(month_key)}</p>
        </div>
    """, unsafe_allow_html=True)
    st.caption("Deep dive into spending patterns, category breakdowns, and trends.")
    st.divider()

    # Monthly Comparison Section
    st.markdown("### 📊 Month-to-Month Comparison")
    prev_month_key = previous_month_key(month_key)
    if prev_month_key in sorted_month_keys(data):
        prev_df = transaction_dataframe(data, prev_month_key)
        curr_summary = monthly_summary(current_df)
        prev_summary = monthly_summary(prev_df)
        
        comparison_col1, comparison_col2, comparison_col3 = st.columns(3)
        
        with comparison_col1:
            revenue_change = curr_summary["revenue"] - prev_summary["revenue"]
            change_pct = (revenue_change / prev_summary["revenue"]) * 100 if prev_summary["revenue"] != 0 else 0
            revenue_change_text = f"{'+' if revenue_change >= 0 else '-'}${abs(revenue_change):,.2f} ({change_pct:+.1f}%)"
            st.metric(
                "Revenue Comparison",
                format_currency(curr_summary["revenue"]),
                revenue_change_text,
                delta_color="normal",
            )
        
        with comparison_col2:
            expense_change = curr_summary["expense"] - prev_summary["expense"]
            change_pct = (expense_change / prev_summary["expense"]) * 100 if prev_summary["expense"] != 0 else 0
            expense_change_text = f"{'+' if expense_change >= 0 else '-'}${abs(expense_change):,.2f} ({change_pct:+.1f}%)"
            st.metric(
                "Expense Comparison",
                format_currency(curr_summary["expense"]),
                expense_change_text,
                delta_color="inverse",
            )
        
        with comparison_col3:
            net_change = curr_summary["net"] - prev_summary["net"]
            change_pct = (net_change / abs(prev_summary["net"])) * 100 if prev_summary["net"] != 0 else 0
            net_change_text = f"{'+' if net_change >= 0 else '-'}${abs(net_change):,.2f} ({change_pct:+.1f}%)"
            st.metric(
                "Net Balance Comparison",
                format_currency(curr_summary["net"]),
                net_change_text,
                delta_color="normal",
            )
        
        # Comparison Chart
        comparison_data = {
            "Month": [month_label(prev_month_key), month_label(month_key)],
            "Revenue": [prev_summary["revenue"], curr_summary["revenue"]],
            "Expenses": [prev_summary["expense"], curr_summary["expense"]],
            "Savings": [prev_summary["savings"], curr_summary["savings"]],
        }
        comparison_df = pd.DataFrame(comparison_data)
        
        fig, ax = plt.subplots(figsize=(10, 5), facecolor='white')
        x = range(len(comparison_df))
        width = 0.25
        
        ax.bar([i - width for i in x], comparison_df["Revenue"], width=width, label="Revenue", color="#2ecc71", edgecolor='white', linewidth=1)
        ax.bar(x, comparison_df["Expenses"], width=width, label="Expenses", color="#e74c3c", edgecolor='white', linewidth=1)
        ax.bar([i + width for i in x], comparison_df["Savings"], width=width, label="Savings", color="#3498db", edgecolor='white', linewidth=1)
        
        ax.set_ylabel("Amount ($)", fontsize=11, fontweight='600')
        ax.set_title(f"Monthly Comparison: {month_label(prev_month_key)} vs {month_label(month_key)}", fontsize=14, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(comparison_df["Month"])
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.7)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}' if x >= 0 else f'-${abs(x):,.0f}'))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("📭 Not enough data for month-to-month comparison yet.")
    
    st.divider()

    owner_tabs = st.tabs(["📊 Total", "👤 TyShawn", "👤 Lexi"])
    for owner, owner_tab in zip(["total", "tyshawn", "lexi"], owner_tabs):
        with owner_tab:
            if owner == "total":
                owner_month_df = current_df[current_df["owner"].isin(["tyshawn", "lexi"])].copy()
                owner_trend_df = all_transactions[all_transactions["owner"].isin(["tyshawn", "lexi"])].copy()
                owner_label = "Total"
            else:
                owner_month_df = current_df[current_df["owner"] == owner].copy()
                owner_trend_df = all_transactions[all_transactions["owner"] == owner].copy()
                owner_label = OWNER_LABELS[owner]

            if owner_month_df.empty:
                st.info(f"📭 No data yet for {owner_label}.")
                continue

            owner_month_df["amount"] = pd.to_numeric(owner_month_df["amount"], errors="coerce").fillna(0.0)

            st.markdown(f"### 💸 {owner_label} Spending by Category")
            expenses = owner_month_df[owner_month_df["entry_type"] == "expense"]
            if expenses.empty:
                st.info("📭 No expense data yet.")
            else:
                by_category = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
                plot_bar_chart(by_category, "Expenses by Category")

            st.markdown(f"### 📈 {owner_label} Income vs Expenses")
            owner_summary_values = monthly_summary(owner_month_df)
            summary = pd.Series(
                {
                    "Revenue": owner_summary_values["revenue"],
                    "Expense": owner_summary_values["expense"],
                    "Savings": owner_summary_values["savings"],
                }
            )
            plot_bar_chart(summary, "Income vs Expenses vs Savings", y_label="Total ($)")

            if owner == "total":
                st.markdown("### 👥 TyShawn vs Lexi Comparison")
                person_df = owner_month_df[owner_month_df["owner"].isin(["tyshawn", "lexi"])]
                if person_df.empty:
                    st.info("📭 No personal entries yet for this month.")
                else:
                    compare = person_df.groupby(["owner", "entry_type"])["amount"].sum().unstack(fill_value=0.0)
                    compare.index = [DISPLAY_NAMES.get(idx, idx.title()) for idx in compare.index]
                    compare.columns = [ENTRY_TYPE_LABELS.get(idx, idx.title()) for idx in compare.columns]
                    st.dataframe(compare, use_container_width=True)
                    net_series = compare.get("Revenue", pd.Series(0.0, index=compare.index)) - compare.get("Expense", pd.Series(0.0, index=compare.index))
                    plot_bar_chart(net_series, "TyShawn vs Lexi Net Comparison", y_label="Net ($)")
            else:
                st.markdown(f"### 🎯 {owner_label} Entry Type Breakdown")
                breakdown = owner_month_df.groupby("entry_type")["amount"].sum()
                breakdown.index = [ENTRY_TYPE_LABELS.get(idx, idx.title()) for idx in breakdown.index]
                plot_bar_chart(breakdown, f"{owner_label} Entry Type Breakdown")

            st.markdown(f"### 💰 {owner_label} Savings Overview")
            savings_df = owner_month_df[owner_month_df["entry_type"] == "savings"]
            savings_transfer_in = owner_month_df[(owner_month_df["entry_type"] == "revenue") & (owner_month_df["category"] == "Savings Transfer")]["amount"].sum()
            savings_transfer_out = owner_month_df[(owner_month_df["entry_type"] == "expense") & (owner_month_df["category"] == "Savings Transfer")]["amount"].sum()
            direct_savings = savings_df.groupby("category")["amount"].sum().sort_values(ascending=False)

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                metric_card("Direct Savings", format_currency(direct_savings.sum()))
            with col_b:
                metric_card("Transfer In", format_currency(savings_transfer_out))
            with col_c:
                metric_card("Transfer Out", format_currency(savings_transfer_in))

            savings_by_category_chart = direct_savings.copy()
            net_transfer_to_savings = savings_transfer_out - savings_transfer_in
            if abs(net_transfer_to_savings) > 0:
                savings_by_category_chart.loc["Savings Transfer (Net)"] = net_transfer_to_savings

            if not savings_by_category_chart.empty:
                plot_bar_chart(savings_by_category_chart.sort_values(ascending=False), "Savings by Category")
            else:
                st.info("📭 No direct savings entries yet.")

            st.markdown(f"### 📉 {owner_label} Monthly Trend")
            if owner_trend_df.empty:
                st.info(f"📭 No trend data yet for {owner_label}.")
            else:
                owner_trend_df["amount"] = pd.to_numeric(owner_trend_df["amount"], errors="coerce").fillna(0.0)
                month_keys = sorted(owner_trend_df["month_key"].dropna().unique().tolist())

                monthly_actual_rows = []
                for trend_month_key in month_keys:
                    trend_month_df = owner_trend_df[owner_trend_df["month_key"] == trend_month_key]
                    trend_summary = monthly_summary(trend_month_df)
                    monthly_actual_rows.append(
                        {
                            "month_key": trend_month_key,
                            "expense": trend_summary["expense"],
                            "revenue": trend_summary["revenue"],
                            "savings": trend_summary["savings"],
                        }
                    )

                monthly_actual = pd.DataFrame(monthly_actual_rows).set_index("month_key").sort_index()

                month_keys = list(monthly_actual.index)
                if not month_keys:
                    st.info(f"📭 No trend data yet for {owner_label}.")
                    continue

                if owner == "total":
                    monthly_budget = pd.DataFrame(
                        [combined_budget_totals(data, month_key) for month_key in month_keys],
                        index=month_keys,
                    )
                else:
                    monthly_budget = pd.DataFrame(
                        [budget_totals_for_owner(data, month_key, owner) for month_key in month_keys],
                        index=month_keys,
                    )

                st.dataframe(
                    pd.concat(
                        [monthly_actual.add_prefix("Actual "), monthly_budget.rename(columns={
                            "expense_budget": "Budget Expense",
                            "revenue_budget": "Budget Revenue",
                            "savings_budget": "Budget Savings",
                        })],
                        axis=1,
                    ),
                    use_container_width=True,
                )

                plot_monthly_budget_trend(month_keys, monthly_actual, monthly_budget)
    
    st.divider()
    st.markdown("### 🎯 Savings Goals (Track your progress)")
    show_savings_goals(data)


def show_savings_goals_page(data: dict) -> None:
    """Display savings goals management page."""
    st.markdown("""
        <div style="padding: 2rem 0 1rem 0;">
            <h1 style="margin: 0; color: #2c3e50;">🎯 Savings Goals</h1>
            <p style="margin: 0.5rem 0 0 0; color: #7f8c8d; font-size: 1rem;">Track your long-term savings objectives</p>
        </div>
    """, unsafe_allow_html=True)
    st.caption("Set and monitor your savings goals to stay motivated and on track.")
    st.divider()
    
    show_savings_goals(data)


def show_settings_page(data: dict) -> None:
    """Display settings and customization page."""
    st.markdown("""
        <div style="padding: 2rem 0 1rem 0;">
            <h1 style="margin: 0; color: #2c3e50;">⚙️ Settings</h1>
            <p style="margin: 0.5rem 0 0 0; color: #7f8c8d; font-size: 1rem;">Customize your tracker experience</p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### 📚 Custom Categories")
    st.caption("Add your own categories for expenses, revenue, and savings.")
    
    if "custom_categories" not in data:
        data["custom_categories"] = {"expense": [], "revenue": [], "savings": []}
    
    # Tabs for each category type
    expense_tab, revenue_tab, savings_tab = st.tabs(["💸 Expenses", "📈 Revenue", "🎯 Savings"])
    
    with expense_tab:
        st.markdown("**Custom Expense Categories**")
        custom_expenses = data["custom_categories"].get("expense", [])
        
        # Display existing custom categories
        if custom_expenses:
            st.markdown("**Your Custom Categories:**")
            for i, cat in enumerate(custom_expenses):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"• {cat}")
                with col2:
                    if st.button("🗑️", key=f"delete_exp_{i}", help="Delete"):
                        data["custom_categories"]["expense"].remove(cat)
                        save_json_dict(DATA_FILE, data)
                        st.rerun()
        else:
            st.info("No custom expense categories yet.")
        
        # Add new category
        new_cat = st.text_input("Add new expense category", key="new_expense_cat", placeholder="e.g., Pet Care")
        if st.button("Add Expense Category", key="add_expense_cat_btn"):
            if new_cat and new_cat not in custom_expenses:
                data["custom_categories"]["expense"].append(new_cat)
                save_json_dict(DATA_FILE, data)
                st.success(f"✅ Added '{new_cat}' to expense categories")
                st.rerun()
    
    with revenue_tab:
        st.markdown("**Custom Revenue Categories**")
        custom_revenue = data["custom_categories"].get("revenue", [])
        
        # Display existing custom categories
        if custom_revenue:
            st.markdown("**Your Custom Categories:**")
            for i, cat in enumerate(custom_revenue):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"• {cat}")
                with col2:
                    if st.button("🗑️", key=f"delete_rev_{i}", help="Delete"):
                        data["custom_categories"]["revenue"].remove(cat)
                        save_json_dict(DATA_FILE, data)
                        st.rerun()
        else:
            st.info("No custom revenue categories yet.")
        
        # Add new category
        new_cat = st.text_input("Add new revenue category", key="new_revenue_cat", placeholder="e.g., Freelance Work")
        if st.button("Add Revenue Category", key="add_revenue_cat_btn"):
            if new_cat and new_cat not in custom_revenue:
                data["custom_categories"]["revenue"].append(new_cat)
                save_json_dict(DATA_FILE, data)
                st.success(f"✅ Added '{new_cat}' to revenue categories")
                st.rerun()
    
    with savings_tab:
        st.markdown("**Custom Savings Categories**")
        custom_savings = data["custom_categories"].get("savings", [])
        
        # Display existing custom categories
        if custom_savings:
            st.markdown("**Your Custom Categories:**")
            for i, cat in enumerate(custom_savings):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"• {cat}")
                with col2:
                    if st.button("🗑️", key=f"delete_sav_{i}", help="Delete"):
                        data["custom_categories"]["savings"].remove(cat)
                        save_json_dict(DATA_FILE, data)
                        st.rerun()
        else:
            st.info("No custom savings categories yet.")
        
        # Add new category
        new_cat = st.text_input("Add new savings category", key="new_savings_cat", placeholder="e.g., Vacation Fund")
        if st.button("Add Savings Category", key="add_savings_cat_btn"):
            if new_cat and new_cat not in custom_savings:
                data["custom_categories"]["savings"].append(new_cat)
                save_json_dict(DATA_FILE, data)
                st.success(f"✅ Added '{new_cat}' to savings categories")
                st.rerun()
    
    st.divider()
    st.markdown("### 💾 Backup & Export")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Download Full Backup", key="download_backup_btn"):
            backup_data = json.dumps(data, indent=2, default=str)
            st.download_button(
                label="Download Backup JSON",
                data=backup_data.encode("utf-8"),
                file_name=f"budget_tracker_backup_{date.today().isoformat()}.json",
                mime="application/json",
                key="download_backup_file"
            )
    
    with col2:
        st.caption("💡 Tip: Save your data regularly for safekeeping.")


# -----------------------------
# App runner
# -----------------------------
def main() -> None:
    init_session_state()
    data = sanitize_loaded_data(load_json_dict(DATA_FILE))
    auto_closed_months = auto_closeout_months(data)
    if auto_closed_months:
        save_json_dict(DATA_FILE, data)
        st.session_state["auto_closeout_notice"] = auto_closed_months
    else:
        st.session_state["auto_closeout_notice"] = []
    ensure_result = ensure_month_exists(data, st.session_state["selected_month"])

    # Also keep the *next* month's carryover fresh so adding a transaction to the
    # current month immediately reflects in the following month, even before the
    # user navigates there.
    next_key = next_month_key(st.session_state["selected_month"])
    next_result = ensure_month_exists(data, next_key)

    if ensure_result == "updated" or next_result == "updated":
        save_json_dict(DATA_FILE, data)

    if not st.session_state["logged_in"]:
        show_login_page()
        return

    show_sidebar(data)
    show_mobile_toolbar(data)

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
    elif st.session_state["page"] == "goals":
        show_savings_goals_page(data)
    elif st.session_state["page"] == "settings":
        show_settings_page(data)
    else:
        st.session_state["page"] = "dashboard"
        st.rerun()


if __name__ == "__main__":
    main()
