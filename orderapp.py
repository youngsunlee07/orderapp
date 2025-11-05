import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="💰 Order · Promo · Free", layout="wide")

# ---------- 스타일 ----------
st.markdown("""
<style>
    /* 모바일 대응 - 폰트와 여백 최소화 */
    .block-container {padding: 0.3rem 0.5rem;}
    html, body, [class*="css"] {font-size: 0.85rem !important;}
    input, button, select, textarea {font-size: 0.9rem !important;}
    .main-title {font-weight: 800; font-size: 1.1rem; margin-bottom: 0.3rem;}
    .section-title {font-weight: 700; font-size: 0.95rem; margin-top: 0.5rem; margin-bottom: 0.25rem;}
    .subtext {font-size: 0.8rem; color: #555; margin-bottom: 0.6rem;}

    /* 모바일 테이블 스크롤 최소화 */
    [data-testid="stDataFrame"] div[data-testid="stHorizontalBlock"] {
        overflow-x: auto;
    }
    table {
        font-size: 0.8rem;
        white-space: nowrap;
        min-width: 600px;
    }

    /* Summary Box */
    .summary-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #ccc;
        border-radius: 6px;
        padding: 3px 6px;
        margin-bottom: 8px;
        background-color: #f8f9fb;
    }
    .summary-item {
        flex: 1;
        text-align: center;
        border-right: 1px solid #ddd;
        padding: 2px 4px;
    }
    .summary-item:last-child {border-right: none;}
    .summary-title {font-weight: 600; font-size: 0.75rem; color: #444;}
    .summary-value {font-weight: 700; font-size: 0.9rem; color: #000;}
</style>
""", unsafe_allow_html=True)

# ---------- (이하 기존 코드 동일) ----------
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("backyard_list.xlsx")
    except FileNotFoundError:
        st.error("❌ 'backyard_list.xlsx' 파일을 찾을 수 없습니다.")
        return pd.DataFrame(columns=["Product Category", "Product Name", "Price", "Item Number"])
    
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0)
    df.rename(columns={"Product Name": "Item", "Price": "box_price"}, inplace=True)
    return df

df = load_data()
if df.empty:
    st.stop()

if "category_dfs" not in st.session_state:
    st.session_state["category_dfs"] = {}

discount_rules = {
    "30 WEAVE WONDER WRAP": 10,
    "30 EYELASH GLUE 1DZ DISPLAY": 16,
    "30 CHIC BOND & REMOVER": 50,
    "VIA TUBE OIL 24PC": 10,
    "SMOOTH MOISTURE SILKENING SYSTEM": 30
}

def update_discount(category, index, matched_discount, toggle_key_str):
    toggle_value = st.session_state[toggle_key_str]
    new_discount = matched_discount if toggle_value else 0
    st.session_state["category_dfs"][category].loc[index, "Discount %"] = new_discount

def update_qty(category, index, field, key):
    value = st.session_state[key]
    st.session_state["category_dfs"][category].loc[index, field] = value

st.markdown("<div class='main-title'>💰 Order · Promo · Free</div>", unsafe_allow_html=True)
st.markdown("<div class='subtext'>Input Order, Promo, and Free quantities. Discounts can be toggled for eligible products.</div>", unsafe_allow_html=True)

summary_placeholder = st.empty()
st.markdown("<div class='section-title'>🗂️ Category</div>", unsafe_allow_html=True)
categories = df["Product Category"].unique()
selected_category = st.selectbox("", categories, label_visibility="collapsed")

if selected_category not in st.session_state["category_dfs"]:
    cat_df = df[df["Product Category"] == selected_category].copy()
    cat_df["Order Qty"] = 0
    cat_df["Promo Qty"] = 0
    cat_df["Free Qty"] = 0
    cat_df["Discount %"] = 0
    st.session_state["category_dfs"][selected_category] = cat_df
else:
    cat_df = st.session_state["category_dfs"][selected_category]

for key, val in discount_rules.items():
    mask = cat_df["Item"].str.contains(key, case=False, na=False)
    cat_df.loc[mask & (cat_df["Discount %"] == 0), "Discount %"] = val

st.markdown("<div class='section-title'>📋 Products</div>", unsafe_allow_html=True)
header = st.columns([3, 1, 1, 1, 1, 1])
for c, title in zip(header, ["Product", "Price", "Order", "Promo", "Free", "Discount"]):
    c.markdown(f"**{title}**")

for idx, row in cat_df.iterrows():
    cols = st.columns([3, 1, 1, 1, 1, 1])
    item_id = row["Item Number"]
    base_key = f"{selected_category}_{item_id}"

    cols[0].markdown(f"**{row['Item']}**<br><sub>{item_id}</sub>", unsafe_allow_html=True)
    cols[1].markdown(f"${row['box_price']:.2f}")

    for field, col_idx in zip(["Order Qty", "Promo Qty", "Free Qty"], [2, 3, 4]):
        key = f"{field[:3].lower()}_{base_key}"
        cols[col_idx].number_input(
            "",
            min_value=0,
            step=1,
            key=key,
            value=int(row[field]),
            label_visibility="collapsed",
            on_change=update_qty,
            args=(selected_category, idx, field, key)
        )

    matched_discount = 0
    for k, v in discount_rules.items():
        if k.lower() in f"{row['Product Category']} {row['Item']}".lower():
            matched_discount = v
            break

    toggle_key_str = f"disc_{base_key}"
    if matched_discount > 0:
        cols[5].toggle(
            f"{matched_discount}%",
            key=toggle_key_str,
            value=(row["Discount %"] > 0),
            on_change=update_discount,
            args=(selected_category, idx, matched_discount, toggle_key_str)
        )
    else:
        cols[5].markdown("-")

# ---------- Summary ----------
all_orders = pd.concat(st.session_state["category_dfs"].values(), ignore_index=True)
ordered_df = all_orders[(all_orders["Order Qty"] > 0) | (all_orders["Promo Qty"] > 0) | (all_orders["Free Qty"] > 0)]

if not ordered_df.empty:
    ordered_df["Order Total"] = ordered_df["Order Qty"] * ordered_df["box_price"] * (1 - ordered_df["Discount %"] / 100)
    ordered_df["Promo Total"] = ordered_df["Promo Qty"] * ordered_df["box_price"]
    ordered_df["Free Total"] = ordered_df["Free Qty"] * ordered_df["box_price"]

    total_order = ordered_df["Order Total"].sum()
    total_promo = ordered_df["Promo Total"].sum()
    total_free = ordered_df["Free Total"].sum()
    promo_ratio = (total_promo / total_order * 100) if total_order > 0 else 0
    free_ratio = (total_free / total_order * 100) if total_order > 0 else 0
else:
    total_order = total_promo = total_free = promo_ratio = free_ratio = 0

summary_placeholder.markdown(f"""
<div class="section-title">📊 Summary</div>
<div class="summary-container">
    <div class="summary-item"><div class="summary-title">Order</div><div class="summary-value">${total_order:,.2f}</div></div>
    <div class="summary-item"><div class="summary-title">Promo</div><div class="summary-value">${total_promo:,.2f}</div></div>
    <div class="summary-item"><div class="summary-title">Free</div><div class="summary-value">${total_free:,.2f}</div></div>
    <div class="summary-item"><div class="summary-title">Promo %</div><div class="summary-value">{promo_ratio:.2f}%</div></div>
    <div class="summary-item"><div class="summary-title">Free %</div><div class="summary-value">{free_ratio:.2f}%</div></div>
</div>
""", unsafe_allow_html=True)

# ---------- Ordered Items ----------
st.markdown("<div class='section-title'>📦 Ordered Items (All Categories)</div>", unsafe_allow_html=True)
if not ordered_df.empty:
    st.dataframe(
        ordered_df[[
            "Product Category", "Item", "Item Number", "box_price",
            "Order Qty", "Promo Qty", "Free Qty", "Discount %",
            "Order Total", "Promo Total", "Free Total"
        ]],
        use_container_width=True, height=260
    )
else:
    st.info("No items ordered yet.")

# ---------- Excel Export ----------
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="All Orders")
    return output.getvalue()

if not ordered_df.empty:
    st.markdown("<div class='section-title'>📤 Export</div>", unsafe_allow_html=True)
    store_name = st.text_input("🏪 Enter Store Name (optional):", placeholder="e.g. SalonPro, KimBeauty...")
    now = datetime.now().strftime("%Y-%m-%d")
    file_name = f"Order_{store_name.strip() or 'Store'}_{now}.xlsx"
    excel_data = to_excel(ordered_df)
    
    cols = st.columns([1, 1])
    cols[0].download_button(
        label="💾 Export to Excel",
        data=excel_data,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    if cols[1].button("🔄 Reset All"):
        st.session_state["category_dfs"] = {}
        st.experimental_rerun()
