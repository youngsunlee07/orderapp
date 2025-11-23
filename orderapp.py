import pandas as pd
import streamlit as st
from io import BytesIO
from streamlit_js_eval import streamlit_js_eval


# ---------- 페이지 설정 ----------
st.set_page_config(page_title="💰 Order · Promo · Free", layout="wide")

st.markdown("""
<style>
/* 전체 컨테이너 여백 */
.block-container {
    padding-top: 8rem !important; /* Summary 높이만큼 아래로 밀기 */
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* 기본 글자 크기 */
html, body, [class*="css"] {
    font-size: 1rem !important;
}

/* Summary 고정바 */
.summary-fixed {
    position: fixed;
    top: 60px;
    left: 0;
    width: 100%;
    height: 95px;
    z-index: 1000;
    background-color: #f8f9fb;
    border-bottom: 1px solid #ccc;
    box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.08);

    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 0 8%;
}

.summary-spacer {
    height: 22px; /* 타이틀이 차지했던 자리만큼 여백 */
}

/* Summary 컨테이너 */
.summary-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 8px 16px;
    background-color: #fff;
    width: 100%;
}

/* Summary 아이템 */
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

/* 섹션 타이틀 (숨김) */
.section-title {
    visibility: hidden;
    height: 20px;
}

/* 숫자 입력 스핀 제거 */
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button {
    -webkit-appearance: none !important;
    margin: 0 !important;
}
input[type=number] {
    -moz-appearance: textfield !important;
}

/* 카테고리 버튼 */
div.stButton > button {
    width: 100%;
    padding: 9px 12px;
    border-radius: 8px;
    font-weight: 600;
    margin-bottom: 6px;
    text-align: left !important;
    justify-content: flex-start !important;
    display: flex !important;
    align-items: center !important;
}

/* 선택 안 된 버튼 */
div.stButton > button[kind="secondary"] {
    background-color: #f1f1f1;
    color: #333;
}

/* 선택된 버튼 */
div.stButton > button[kind="primary"] {
    background-color: #004c9c;
    border: 1px solid #002b5c;
    color: #ffffff;
    box-shadow: 0px 0px 6px rgba(0,0,0,0.3);
}
            
/* Brand 가로 스크롤 영역 */
.brand-scroll-wrapper {
    display: flex;
    overflow-x: auto;
    white-space: nowrap;
    gap: 8px;
    padding: 4px 0 10px 0;
}

.brand-scroll-wrapper::-webkit-scrollbar {
    height: 6px; /* 아이패드에서 너무 크지 않게 */
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
    "30 EYELASH GLUE 1dz": 16,
    "30 CHIC BOND & REMOVER": 50,
    "VIA TUBE OIL 24PC": 10,
    "SMOOTH MOISTURE": 30
}

# ---------- 콜백 ----------
def update_discount(category, index, matched_discount, toggle_key_str):
    toggle_value = st.session_state[toggle_key_str]
    new_discount = matched_discount if toggle_value else 0
    st.session_state["category_dfs"][category].loc[index, "Discount %"] = new_discount

# ---------- Summary Placeholder ----------
summary_placeholder = st.empty()

# ---------- Brand + Category 구조 적용 ----------

# Brand 아이콘 함수
def get_brand_icon(brand: str) -> str:
    b = str(brand).upper()
    if b.startswith("AE"):
        return "🟥"
    elif b.startswith("SP"):
        return "🟨"
    elif b.startswith("30"):
        return "🟪"
    elif b.startswith("VIA"):
        return "🟦"
    elif any(x in b for x in ["JML", "ROBERT"]):
        return "⬛"
    elif "COLOR" in b:
        return "⬜"   # 밝은 회색
    else:
        return "🟧"   # OTHER

# ---------- Brand 리스트 ----------
brands = df["Brand"].dropna().unique().tolist()

df["Brand"] = df["Brand"].astype(str).str.strip().str.upper()

brand_order = ["AE", "SP", "30", "VIA", "JML", "COLOR", "OTHER"]

# 1) 우선순위에 있는 브랜드만 순서대로
ordered_brands = [b for b in brand_order if b in brands]

# 2) brand_order에 없는 기타 브랜드가 있다면 뒤에 붙이기
others = [b for b in brands if b not in brand_order]

# 최종 브랜드 리스트 (여기서 brands를 다시 설정해야 함)
brands = ordered_brands + others

if "selected_brand" not in st.session_state:
    st.session_state["selected_brand"] = brands[0] if brands else ""

selected_brand = st.session_state["selected_brand"]

st.markdown("<div class='section-title'>Brand</div>", unsafe_allow_html=True)

# ---------- Brand 라디오 스크롤 스타일 ----------
st.markdown("""
<style>
/* 라디오 전체 wrapper */
.brand-radio-wrapper {
    overflow-x: auto;
    white-space: nowrap;
    padding: 6px 0;
}

/* 내부 라디오 Flex 정렬 */
.brand-radio-wrapper div[role="radiogroup"] {
    display: flex;
    flex-wrap: nowrap !important;
    gap: 10px;
}

/* 라디오 항목 스타일 */
.brand-radio-wrapper label {
    padding: 6px 14px;
    border-radius: 8px;
    background-color: #f1f1f1;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid #ddd;
    white-space: nowrap;
}

/* 선택된 라디오 스타일 */
.brand-radio-wrapper label[data-baseweb="radio"]:has(input:checked) {
    background-color: #004c9c !important;
    color: #ffffff !important;
    border: 1px solid #002b5c !important;
    box-shadow: 0px 0px 4px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

# ---------- Brand 라디오 표시 ----------
st.markdown("<div class='section-title'>Brand</div>", unsafe_allow_html=True)
st.markdown('<div class="brand-radio-wrapper">', unsafe_allow_html=True)

# 옵션용 라벨: "🟥 AE", "🟨 SP" 이런 식으로 만들기
brand_labels = [f"{get_brand_icon(b)} {b}" for b in brands]

# 세션에 기존 선택값이 있으면 그 위치를 index로 사용
if "selected_brand" in st.session_state and st.session_state["selected_brand"] in brands:
    default_index = brands.index(st.session_state["selected_brand"])
else:
    default_index = 0

selected_label = st.radio(
    "",
    brand_labels,
    horizontal=True,
    index=default_index,
    key="brand_radio",
    label_visibility="collapsed"
)

st.markdown("</div>", unsafe_allow_html=True)

# 라벨에서 다시 순수 브랜드명으로 역매핑
selected_brand = brands[brand_labels.index(selected_label)]

# 상태 저장 및 카테고리 리셋
if st.session_state.get("selected_brand") != selected_brand:
    st.session_state["selected_brand"] = selected_brand
    st.session_state["selected_category"] = ""
    st.rerun()

# ---------- Brand 기반 Category 리스트 ----------
filtered_df = df[df["Brand"] == selected_brand]
categories = filtered_df["Product Category"].dropna().unique().tolist()

# 🔥 카테고리를 Column-first 로 보이도록 강제 재정렬
if len(categories) > 1:
    half = (len(categories) + 1) // 2
    left_column = categories[:half]
    right_column = categories[half:]
else:
    left_column = categories
    right_column = []

if ("selected_category" not in st.session_state) or (st.session_state["selected_category"] not in categories):
    st.session_state["selected_category"] = left_column[0] if left_column else ""

selected_category = st.session_state["selected_category"]

st.markdown("<div class='section-title'>🗂️ Category</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2) if len(categories) > 1 else (st.columns(1)[0], None)


def get_cat_icon(cat):
    cat_up = cat.upper()
    if cat_up.startswith("AE"):
        return "🟥"
    elif cat_up.startswith("SP"):
        return "🟨"
    elif cat_up.startswith("30"):
        return "🟪"
    elif "COLOR" in cat_up:
        return "⬜"
    elif cat_up.startswith("VIA"):
        return "🟦"
    elif any(x in cat_up for x in ["JML", "ROBERT", "SMOOTH MOISTURE", "GROGANICS"]):
        return "⬛"
    else:
        return "🟧"


# 왼쪽
with col1:
    for cat in left_column:
        icon = get_cat_icon(cat)
        is_selected = (cat == selected_category)
        btn_type = "primary" if is_selected else "secondary"

        if st.button(f"{icon} {cat}", key=f"cat_left_{cat}", type=btn_type, use_container_width=True):
            st.session_state["selected_category"] = cat
            st.rerun()

# 오른쪽
if col2:
    with col2:
        for cat in right_column:
            icon = get_cat_icon(cat)
            is_selected = (cat == selected_category)
            btn_type = "primary" if is_selected else "secondary"

            if st.button(f"{icon} {cat}", key=f"cat_right_{cat}", type=btn_type, use_container_width=True):
                st.session_state["selected_category"] = cat
                st.rerun()



# ---------- 카테고리별 세션 데이터 ----------
if selected_category not in st.session_state["category_dfs"]:
    cat_df = df[df["Product Category"] == selected_category].copy()
    cat_df["Order Qty"] = 0
    cat_df["Promo Qty"] = 0
    cat_df["Free Qty"] = 0
    cat_df["Discount %"] = 0  # 기본은 0, 이후 rule로 덮어씀

    # 🔥 기본 할인 즉시 적용
    for key, val in discount_rules.items():
        mask = cat_df["Item"].str.contains(key, case=False, na=False)
        cat_df.loc[mask, "Discount %"] = val

    # 세션 저장
    st.session_state["category_dfs"][selected_category] = cat_df

else:
    cat_df = st.session_state["category_dfs"][selected_category]

# ---------- 제품 테이블 ----------
st.markdown("<div class='section-title'>📋 Products</div>", unsafe_allow_html=True)
header = st.columns([1.2, 0.4, 1, 1, 1, 0.4])
for c, title in zip(header, ["Product", "Price", "Order", "Promo", "Free", "Disc %"]):
    c.markdown(f"**{title}**")

# ---------- 안정화된 반복문 ----------
for idx, row in cat_df.iterrows():

    cols = st.columns([1.2, 0.4, 1, 1, 1, 0.4])
    item_id = row["Item Number"]
    base_key = f"{selected_category}_{item_id}_{idx}"

    # 상품명
    cols[0].markdown(f"**{row['Item']}**<br><sub>{item_id}</sub>", unsafe_allow_html=True)
    cols[1].markdown(f"${row['box_price']:.2f}")

    # ---------- 수량 입력 ----------
    for field, col_idx in zip(["Order Qty", "Promo Qty", "Free Qty"], [2, 3, 4]):

        qty_key = f"{field[:3].lower()}_{base_key}"

        # 최초 1회 세션 초기화
        if qty_key not in st.session_state:
            st.session_state[qty_key] = int(row[field]) if pd.notna(row[field]) else 0

        # number_input은 key만 설정 (value 사용 X)
        with cols[col_idx]:
            st.number_input(
                "",
                min_value=0,
                step=1,
                key=qty_key,
                label_visibility="collapsed"
            )

        # DF 업데이트는 항상 session_state 기준
        st.session_state["category_dfs"][selected_category].loc[idx, field] = st.session_state[qty_key]

    # ---------- 🔢 할인 입력 ----------
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
    <div class="summary-spacer"></div> <!-- 숨겨진 타이틀 공간 대체 -->
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