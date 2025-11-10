import pandas as pd
import streamlit as st
from io import BytesIO

# ---------- 페이지 설정 ----------
st.set_page_config(page_title="💰 Order · Promo · Free", layout="wide")

# ---------- 스타일 ----------
st.markdown("""
<style>
    /* 전체 여백 */
    .block-container {
        padding-top: 8rem !important; /* Summary 고정 공간 확보 */
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    html, body, [class*="css"] {
        font-size: 1rem !important;
    }

    /* 🔹 Summary 고정 */
    .summary-fixed {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        z-index: 1000;
        background-color: #f8f9fb;
        padding: 12px 8%;
        border-bottom: 1px solid #ccc;
        box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.08);
    }

    .summary-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 8px 16px;
        background-color: #fff;
    }

    .summary-item {
        flex: 1;
        text-align: center;
        border-right: 1px solid #ddd;
        padding: 8px 10px;
    }
    .summary-item:last-child {border-right: none;}

    .summary-title {
        font-weight: 600;
        font-size: 0.9rem;
        color: #444;
    }
    .summary-value {
        font-weight: 700;
        font-size: 1rem;
        color: #000;
    }

    /* 🔹 섹션 제목 */
    .section-title {
        font-weight: 800;
        font-size: 1.1rem;
        margin: 1rem 0 0.5rem 0;
        color: #000;
    }

    /* ✅ Category 제목 위로 여백 추가 */
    .section-title:has(> span:contains("Category")),
    .section-title:contains("Category") {
        margin-top: 2.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:30px'></div>", unsafe_allow_html=True)

# ---------- 데이터 로드 ----------
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
header = st.columns([1.2, 0.4, 1, 1, 1, 0.4])
for c, title in zip(header, ["Product", "Price", "Order", "Promo", "Free", "Disc %"]):
    c.markdown(f"**{title}**")

for idx, row in cat_df.iterrows():
    cols = st.columns([1.2, 0.4, 1, 1, 1, 0.4])
    item_id = row["Item Number"]
    base_key = f"{selected_category}_{item_id}"

    cols[0].markdown(f"**{row['Item']}**<br><sub>{item_id}</sub>", unsafe_allow_html=True)
    cols[1].markdown(f"${row['box_price']:.2f}")

    # 수량 입력
    for field, col_idx in zip(["Order Qty", "Promo Qty", "Free Qty"], [2, 3, 4]):
        key = f"{field[:3].lower()}_{base_key}"
        if key not in st.session_state:
            st.session_state[key] = int(row[field])
        with cols[col_idx]:
            qty_val = st.number_input("", min_value=0, step=1, key=key, label_visibility="collapsed")
        st.session_state["category_dfs"][selected_category].loc[idx, field] = qty_val

    # 🔢 할인 직접 입력란 (버튼 없는 텍스트 입력창 형태)
    with cols[5]:
        disc_key = f"disc_input_{selected_category}_{item_id}_{idx}"

        # 기본 할인값 설정 (discount_rules 참고)
        matched_discount = 0
        for k, v in discount_rules.items():
            if k.lower() in f"{row['Product Category']} {row['Item']}".lower():
                matched_discount = v
                break

        # 세션 상태 초기화 (문자열 형태)
        if disc_key not in st.session_state:
            st.session_state[disc_key] = str(int(row["Discount %"] or matched_discount or 0))

        # 🔹 value 인수 제거 (이제 key만 사용)
        discount_str = st.text_input(
            "",
            key=disc_key,
            label_visibility="collapsed"
        )

        # 입력값 숫자 변환
        try:
            discount_val = float(discount_str)
        except ValueError:
            discount_val = 0.0

        # 반영
        st.session_state["category_dfs"][selected_category].loc[idx, "Discount %"] = discount_val

# ---------- Summary 계산 ----------
all_orders = pd.concat(st.session_state["category_dfs"].values(), ignore_index=True)
ordered_df = all_orders[
    (all_orders["Order Qty"] > 0) | (all_orders["Promo Qty"] > 0) | (all_orders["Free Qty"] > 0)
]

if not ordered_df.empty:
    ordered_df["Order Total"] = (
        ordered_df["Order Qty"] * ordered_df["box_price"] * (1 - ordered_df["Discount %"] / 100)
    )
    ordered_df["Promo Total"] = ordered_df["Promo Qty"] * ordered_df["box_price"]
    ordered_df["Free Total"] = ordered_df["Free Qty"] * ordered_df["box_price"]

    ordered_df[["Order Total", "Promo Total", "Free Total"]] = ordered_df[
        ["Order Total", "Promo Total", "Free Total"]
    ].round(2)

    total_order = ordered_df["Order Total"].sum()
    total_promo = ordered_df["Promo Total"].sum()
    total_free = ordered_df["Free Total"].sum()

    promo_ratio = (total_promo / total_order * 100) if total_order > 0 else 0
    free_ratio = (total_free / total_order * 100) if total_order > 0 else 0
else:
    total_order = total_promo = total_free = promo_ratio = free_ratio = 0

# ---------- Summary 출력 ----------
st.markdown(f"""
<div class="summary-fixed">
    <div class="section-title">📊 Summary</div>
    <div class="summary-container">
        <div class="summary-item"><div class="summary-title">Order</div><div class="summary-value">${total_order:,.2f}</div></div>
        <div class="summary-item"><div class="summary-title">Promo</div><div class="summary-value">${total_promo:,.2f}</div></div>
        <div class="summary-item"><div class="summary-title">Free</div><div class="summary-value">${total_free:,.2f}</div></div>
        <div class="summary-item"><div class="summary-title">Promo %</div><div class="summary-value">{promo_ratio:.2f}%</div></div>
        <div class="summary-item"><div class="summary-title">Free %</div><div class="summary-value">{free_ratio:.2f}%</div></div>
    </div>
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

st.markdown("<div class='section-title'>💾 Export to Excel</div>", unsafe_allow_html=True)
if "export_input_key" not in st.session_state:
    st.session_state["export_input_key"] = "export_filename_input_1"

custom_name = st.text_input(
    "Enter file name (required):",
    value="",
    placeholder="e.g., GA1234",
    label_visibility="visible",
    key=st.session_state["export_input_key"]
)

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
                st.session_state["export_input_key"] = f"export_filename_input_{int(pd.Timestamp.now().timestamp())}"
                st.rerun()
    else:
        st.warning("⚠️ Please enter a file name before exporting.")
else:
    st.info("⚠️ No ordered data to export.")
