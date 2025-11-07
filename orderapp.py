import pandas as pd
import streamlit as st
from io import BytesIO

# ---------- 데스크탑 전용 설정 ----------
st.set_page_config(page_title="💰 Order · Promo · Free", layout="wide")

# ---------- 스타일 ----------
st.markdown("""
<style>
    .block-container {padding: 1.2rem 2rem;}
    html, body, [class*="css"] {font-size: 1rem !important;}
    .main-title {font-weight: 800; font-size: 1.4rem; margin-bottom: 0.4rem;}
    .section-title {font-weight: 700; font-size: 1.1rem; margin-top: 0.8rem; margin-bottom: 0.4rem;}
    .subtext {font-size: 0.9rem; color: #555; margin-bottom: 1rem;}

    .summary-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 8px 16px;
        margin-bottom: 12px;
        background-color: #f8f9fb;
    }
    .summary-item {
        flex: 1;
        text-align: center;
        border-right: 1px solid #ddd;
        padding: 8px 10px;
    }
    .summary-item:last-child {border-right: none;}
    .summary-title {font-weight: 600; font-size: 0.9rem; color: #444;}
    .summary-value {font-weight: 700; font-size: 1rem; color: #000;}

    /* number_input 폭 통일 */
    div[data-baseweb="input"] input {
        text-align: center;
        width: 70px !important;
    }
    @media (max-width: 768px) {
        div[data-baseweb="input"] input {
            width: 55px !important;
            font-size: 0.9rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------- 데이터 ----------
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

# ---------- 세션 초기화 ----------
if "category_dfs" not in st.session_state:
    st.session_state["category_dfs"] = {}

# ---------- 할인 규칙 ----------
discount_rules = {
    "30 WEAVE WONDER WRAP": 10,
    "30 EYELASH GLUE 1DZ DISPLAY": 16,
    "30 CHIC BOND & REMOVER": 50,
    "VIA TUBE OIL 24PC": 10,
    "SMOOTH MOISTURE SILKENING SYSTEM": 30
}

# ---------- 콜백 ----------
def update_discount(category, index, matched_discount, toggle_key_str):
    toggle_value = st.session_state[toggle_key_str]
    new_discount = matched_discount if toggle_value else 0
    st.session_state["category_dfs"][category].loc[index, "Discount %"] = new_discount

# ---------- 제목 ----------
st.markdown("<div class='main-title'>💰 Order · Promo · Free</div>", unsafe_allow_html=True)
st.markdown("<div class='subtext'>Input Order, Promo, and Free quantities. Discounts can be toggled for eligible products. Orders remain across categories.</div>", unsafe_allow_html=True)

# ---------- Summary Placeholder ----------
summary_placeholder = st.empty()

# ---------- Category 선택 ----------
st.markdown("<div class='section-title'>🗂️ Category</div>", unsafe_allow_html=True)
categories = df["Product Category"].unique()
selected_category = st.selectbox("", categories, label_visibility="collapsed")

# ---------- 카테고리별 세션 데이터 ----------
if selected_category not in st.session_state["category_dfs"]:
    cat_df = df[df["Product Category"] == selected_category].copy()
    cat_df["Order Qty"] = 0
    cat_df["Promo Qty"] = 0
    cat_df["Free Qty"] = 0
    cat_df["Discount %"] = 0
    st.session_state["category_dfs"][selected_category] = cat_df
else:
    cat_df = st.session_state["category_dfs"][selected_category]

# ---------- 기본 할인 적용 ----------
for key, val in discount_rules.items():
    mask = cat_df["Item"].str.contains(key, case=False, na=False)
    cat_df.loc[mask & (cat_df["Discount %"] == 0), "Discount %"] = val

# ---------- 제품 테이블 ----------
st.markdown("<div class='section-title'>📋 Products</div>", unsafe_allow_html=True)
header = st.columns([1.2, 0.4, 1, 1, 1, 0.6])
for c, title in zip(header, ["Product", "Price", "Order", "Promo", "Free", "Discount"]):
    c.markdown(f"**{title}**")

for idx, row in cat_df.iterrows():
    cols = st.columns([1.2, 0.4, 1, 1, 1, 0.6])
    item_id = row["Item Number"]
    base_key = f"{selected_category}_{item_id}"

    cols[0].markdown(f"**{row['Item']}**<br><sub>{item_id}</sub>", unsafe_allow_html=True)
    cols[1].markdown(f"${row['box_price']:.2f}")

    # ✅ 중복 초기화 방지 - value 제거
    for field, col_idx in zip(["Order Qty", "Promo Qty", "Free Qty"], [2, 3, 4]):
        key = f"{field[:3].lower()}_{base_key}"

        if key not in st.session_state:
            st.session_state[key] = int(row[field])

        with cols[col_idx]:
            qty_val = st.number_input(
                label="",
                min_value=0,
                step=1,
                key=key,
                label_visibility="collapsed"
            )

        st.session_state["category_dfs"][selected_category].loc[idx, field] = qty_val

    # 할인 토글
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
ordered_df = all_orders[
    (all_orders["Order Qty"] > 0) |
    (all_orders["Promo Qty"] > 0) |
    (all_orders["Free Qty"] > 0)
]

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
        use_container_width=True, height=300
    )
else:
    st.info("No items ordered yet.")

# ---------- Excel Export ----------
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="All Orders")
    return output.getvalue()

st.markdown("### 💾 Export Excel File")

# 세션 상태 초기화용 키
if "export_input_key" not in st.session_state:
    st.session_state["export_input_key"] = "export_filename_input_1"

# 파일명 입력창 (key를 세션에서 제어)
custom_name = st.text_input(
    "Enter file name (required):",
    value="",
    placeholder="e.g., GA1234",
    label_visibility="visible",
    key=st.session_state["export_input_key"]
)

# ---------- 스타일 ----------
st.markdown("""
<style>
div[data-testid="stTextInput"] {
    width: 100% !important;
    max-width: 600px !important;
}
div[data-testid="stTextInput"] input {
    width: 100% !important;
    font-size: 1rem !important;
    padding: 10px 12px !important;
    border-radius: 6px !important;
}
button.export-btn, button.reset-btn {
    width: 100% !important;
    font-size: 1rem !important;
    padding: 10px 14px !important;
    border-radius: 6px !important;
    color: white !important;
    border: none !important;
}
button.export-btn {
    background-color: #4CAF50 !important;
}
button.reset-btn {
    background-color: #888 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- Export + Reset 로직 ----------
if not ordered_df.empty:
    if custom_name.strip():
        file_name = custom_name.strip() + ".xlsx"
        excel_data = to_excel(ordered_df)

        exported = st.download_button(
            label=f"📤 Export to Excel ({file_name})",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="export_button",
            use_container_width=True
        )

        if exported:
            st.session_state["export_done"] = True

        if st.session_state.get("export_done", False):
            st.markdown("---")
            st.success("✅ Export completed! You can reset all orders if you wish.")
            st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
            reset_btn = st.button("🔄 Reset All", key="reset_button", use_container_width=True)
            if reset_btn:
                st.session_state.clear()
                # ✅ 입력창 캐시 무효화를 위해 키 변경
                st.session_state["export_input_key"] = f"export_filename_input_{int(pd.Timestamp.now().timestamp())}"
                st.rerun()

    else:
        st.warning("⚠️ Please enter a file name before exporting.")
else:
    st.info("⚠️ No ordered data to export.")
