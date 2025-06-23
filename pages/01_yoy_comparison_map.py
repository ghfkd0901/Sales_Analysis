import streamlit as st
import pandas as pd
import plotly.express as px

# ✅ 와이드 페이지 설정
st.set_page_config(layout="wide")

# 📂 데이터 경로
file_path = "data/out/sales_yoy_comparison_final.csv"

@st.cache_data
def load_data():
    return pd.read_csv(file_path, parse_dates=["매출년월"])

data = load_data()

# 📝 사용 설명 (토글로 열고 닫기 가능하게 구성)
with st.expander("ℹ️ 지도 사용 설명 보기"):
    st.markdown("""
    ## 📌 지도 사용 가이드

    ### 1. 필터 선택
    - 좌측 사이드바에서 원하는 **상품명**과 **매출년월**을 선택해 주세요.
    - 지역, 업종, 상태 등 다양한 조건으로 필터링이 가능합니다.

    ### 2. 지도 탭 안내
    - 아래 지도는 두 개의 탭으로 구성되어 있습니다:
      - **전년동월 비교 지도**: 당해 연도와 전년의 해당 월 데이터를 비교합니다.
      - **전년동월 누계 비교 지도**: 누계 데이터를 기준으로 비교합니다.

    ### 3. 판매량 단위
    - 지도에 표시되는 판매량 단위는 **㎥(세제곱미터)**입니다.

    ### 4. 색상 기준
    - **기본 색상 기준은 "상태"입니다**:
      - 🟩 유지: 전년도와 당해년도 모두 판매량이 존재하는 고객
      - 🔵 신규: 당해년도에만 판매량이 존재하는 고객
      - 🔴 해지: 전년도에만 판매량이 존재하는 고객

    - **상태가 '유지'로 필터링되었을 경우**, 색상 기준이 **증감범주**로 전환됩니다:
      - 🟩 정상 (변동 없음)
      - 🔵 20% 이상 증가
      - 🔴 20% 이상 감소

    ### 5. 상태 분류 기준
    - **유지**: 전년도와 당해 연도 모두 해당 월에 판매량이 존재하는 경우입니다.
    - **신규**: 전년도에는 판매량이 `null`이고, 당해 연도에는 판매량이 존재하는 경우입니다.
    - **해지**: 전년도에는 판매량이 존재하고, 당해 연도에는 `null`인 경우입니다.
    - 이때 "판매량이 존재한다"는 것은 값이 `null`이 아니라는 뜻이며, **판매량이 0이어도 값이 존재한다고 판단**합니다.
    - 예를 들어, 계약은 유지된 채로 실제 소비가 없어 판매량이 0인 경우도 상태는 "유지"로 분류됩니다.

    ### 6. 데이터 출처
    - 이 데이터는 **고객지원시스템 → 상품별판매량조회** 화면에서 추출한 결과입니다.

    ### 7. 데이터 오차 안내
    - 지도에서 보여지는 판매량의 합계가 실제 화면에서 보이는 수치와 일치하지 않는 경우가 있을 수 있습니다.
    - 이는 다음과 같은 이유로 발생할 수 있습니다:
      - 원본 데이터가 이 앱의 생성 시점 이후 수정되었을 경우
      - 데이터 전처리 과정에서 예상치 못한 오류가 발생한 경우
    - 데이터에 오류가 있거나 문의사항이 있을 경우 **마케팅기획팀 배경호 사원(053-606-1317)**에게 연락해 주세요.

    ---
    **작성자: 마케팅기획팀 배경호 사원**
    """)

# 📌 전처리 요약 (토글로 구성)
with st.expander("🧪 데이터 전처리 과정 보기"):
    st.markdown("""
    ### 데이터 전처리 과정 요약

    이 Streamlit 앱에서 사용된 데이터는 다음과 같은 전처리 과정을 거쳐 생성되었습니다:

    1. **CSV 파일 수집 및 통합**: 여러 개의 월별 판매량 CSV 파일을 한 폴더에 모아 `glob`으로 전체 읽기.
    2. **불필요한 열 제거 및 필터링**: 분석에 사용되지 않는 열들을 제거하고, 사용량 결측치가 있는 행은 제거.
    3. **문자열 및 날짜 형식 정제**: 계약번호, 시설물번호는 문자열로 변환하고, 날짜 형식은 `datetime`으로 변환.
    4. **판매량 단위 통일 및 숫자 변환**: 천 단위 콤마 제거 후 `float`으로 변환하여 열 이름도 `판매량`, `판매열량`으로 정리.
    5. **고객+계약+시설물+월 단위로 그룹화**: 그룹별 판매량은 합계, 그 외 항목은 최초값으로 통합.
    6. **도로명주소 정제 및 위경도 병합**: `정제된 도로명주소`를 생성하고 좌표 데이터와 병합하여 지도 시각화 가능하게 구성.
    7. **전년도 데이터와 매출년월 기준 outer join**: 당해연도-전년도 비교를 위해 1년 이동 후 join.
    8. **신규/유지/해지 상태 분류**: 전년도, 당해년도 판매량 존재 여부에 따라 상태 판별.
    9. **월별 및 누계 증감/증감률 계산**: 월 단위 비교뿐 아니라 누적 판매량 비교까지 수행.
    10. **시도 및 시군구 정보 추출**: 지도 필터링을 위해 도로명주소에서 시도/시군구 구분 추출.
    11. **증감범주 구간화**: 증감률이 20% 이상 증감인지 아닌지를 기준으로 세 가지 색상 범주로 나눔.

    위의 과정을 통해 최종 데이터가 생성되며, 이 앱의 지도 시각화에 사용됩니다.
    """)

# 🎛️ 사이드바 필터
st.sidebar.header("필터")

selected_product = st.sidebar.selectbox("상품명 선택", sorted(data["상품명"].dropna().unique()))
selected_month_str = st.sidebar.selectbox(
    "매출년월 선택", 
    sorted(data["매출년월"].dropna().dt.strftime("%Y-%m-%d").unique())
)
selected_month = pd.to_datetime(selected_month_str)

selected_sido = st.sidebar.multiselect("시도 선택", sorted(data["시도"].dropna().unique()))
if selected_sido:
    sigungu_options = sorted(data[data["시도"].isin(selected_sido)]["시군구"].dropna().unique())
else:
    sigungu_options = sorted(data["시군구"].dropna().unique())
selected_sigungu = st.sidebar.multiselect("시군구 선택", sigungu_options)

category1_options = sorted(data["업종분류"].dropna().unique())
selected_industry_category = st.sidebar.multiselect("업종분류 선택", category1_options)
if selected_industry_category:
    category2_options = sorted(data[data["업종분류"].isin(selected_industry_category)]["업종"].dropna().unique())
else:
    category2_options = sorted(data["업종"].dropna().unique())
selected_industry = st.sidebar.multiselect("업종 선택", category2_options)

selected_status = st.sidebar.multiselect("상태 선택", sorted(data["상태"].dropna().unique()))
selected_change = st.sidebar.multiselect("증감범주 선택", sorted(data["증감범주"].dropna().unique()))

# 📊 필터 적용
filtered = data[
    (data["상품명"] == selected_product) &
    (data["매출년월"] == selected_month)
]
if selected_sido:
    filtered = filtered[filtered["시도"].isin(selected_sido)]
if selected_sigungu:
    filtered = filtered[filtered["시군구"].isin(selected_sigungu)]
if selected_industry_category:
    filtered = filtered[filtered["업종분류"].isin(selected_industry_category)]
if selected_industry:
    filtered = filtered[filtered["업종"].isin(selected_industry)]
if selected_status:
    filtered = filtered[filtered["상태"].isin(selected_status)]
if selected_change:
    filtered = filtered[filtered["증감범주"].isin(selected_change)]

# 🟡 마커 크기 계산
filtered["마커크기"] = filtered.apply(
    lambda row: row["전년동월판매량"] if row["상태"] == "해지" else row["당년당월판매량"],
    axis=1
)
filtered["마커크기"] = filtered["마커크기"].fillna(0).clip(lower=10)

# 컬러 구분: 상태가 '유지'만 선택되면 증감범주 기준 색상
color_column = "증감범주" if selected_status == ["유지"] else "상태"
if color_column == "증감범주":
    filtered = filtered[filtered["증감범주"] != "데이터 없음"]

# 📌 요약 계산
유지 = filtered[filtered["상태"] == "유지"]["고객명"].nunique()
신규 = filtered[filtered["상태"] == "신규"]["고객명"].nunique()
해지 = filtered[filtered["상태"] == "해지"]["고객명"].nunique()

당월 = int(filtered["당년당월판매량"].sum())
전년 = int(filtered["전년동월판매량"].sum())
증감 = 당월 - 전년
증감률 = f"{증감 / 전년:.1%}" if 전년 != 0 else "0%"

당월누계 = int(filtered["당년당월누계판매량"].sum())
전년누계 = int(filtered["전년동월누계판매량"].sum())
증감누계 = 당월누계 - 전년누계
증감률누계 = f"{증감누계 / 전년누계:.1%}" if 전년누계 != 0 else "0%"

# 📋 요약 지표 출력
st.markdown("### 📊 요약 지표")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🟩 유지 고객 수", f"{유지}명")
with col2:
    st.metric("🟧 신규 고객 수", f"{신규}명")
with col3:
    st.metric("🟥 해지 고객 수", f"{해지}명")

col4, col5 = st.columns(2)
with col4:
    st.metric("📦 당월 판매량", f"{당월:,} m³", f"{증감:,} m³ / {증감률}")
with col5:
    st.metric("📦 누계 판매량", f"{당월누계:,} m³", f"{증감누계:,} m³ / {증감률누계}")

# 🧼 툴팁용 포맷 열
filtered["당년당월판매량_fmt"] = filtered["당년당월판매량"].fillna(0).astype(int).map("{:,}".format)
filtered["전년동월판매량_fmt"] = filtered["전년동월판매량"].fillna(0).astype(int).map("{:,}".format)
filtered["증감_fmt"] = (filtered["당년당월판매량"].fillna(0) - filtered["전년동월판매량"].fillna(0)).astype(int).map("{:,}".format)
filtered["증감률_fmt"] = (filtered["증감률"] * 100).round().astype("Int64").astype(str) + "%"

st.markdown("---")

# 🗺️ 지도 시각화
tab1, tab2 = st.tabs(["📌 전년동월 비교 지도", "📌 전년동월 누계 비교 지도"])

with tab1:
    st.subheader("전년동월 비교 지도")
    if not filtered.empty:
        fig_yoy = px.scatter_mapbox(
            filtered,
            lat="위도",
            lon="경도",
            color=color_column,
            size=filtered["마커크기"],
            hover_name="고객명",
            hover_data={
                "정제된 도로명주소": True,
                "당년당월판매량_fmt": True,
                "전년동월판매량_fmt": True,
                "증감_fmt": True,
                "증감률_fmt": True,
                "위도": False,
                "경도": False,
                "마커크기": False
            },
            mapbox_style="carto-positron",
            zoom=10,
            height=600,
            color_discrete_map={
                "정상": "green",
                "20% 이상 증가": "blue",
                "20% 이상 감소": "red",
                "유지": "green",
                "신규": "blue",
                "해지": "red"
            }
        )
        st.plotly_chart(fig_yoy, use_container_width=True)
    else:
        st.warning("해당 조건에 맞는 데이터가 없습니다.")

with tab2:
    st.subheader("전년동월 누계 비교 지도")
    if not filtered.empty:
        fig_cum = px.scatter_mapbox(
            filtered,
            lat="위도",
            lon="경도",
            color=color_column,
            size=filtered["마커크기"],
            hover_name="고객명",
            hover_data={
                "정제된 도로명주소": True,
                "당년당월누계판매량": ":,",
                "전년동월누계판매량": ":,",
                "누계증감": ":,",
                "누계증감률": True,
                "위도": False,
                "경도": False,
                "마커크기": False
            },
            mapbox_style="carto-positron",
            zoom=10,
            height=600,
            color_discrete_map={
                "정상": "green",
                "20% 이상 증가": "blue",
                "20% 이상 감소": "red",
                "유지": "green",
                "신규": "blue",
                "해지": "red"
            }
        )
        st.plotly_chart(fig_cum, use_container_width=True)
    else:
        st.warning("해당 조건에 맞는 누계 데이터가 없습니다.")
st.markdown("---")

# 📄 데이터 표시
with st.expander("📄 필터링된 데이터 확인 (클릭하여 열기/닫기)"):
    df_display = filtered.drop(
        columns=["당년당월판매량_fmt", "전년동월판매량_fmt", "증감_fmt", "증감률_fmt"],
        errors="ignore"
    ).copy()

    int_cols = [
        "당년당월판매량", "전년동월판매량",
        "당년당월누계판매량", "전년동월누계판매량",
        "증감", "누계증감"
    ]
    for col in int_cols:
        if col in df_display.columns:
            df_display[col] = df_display[col].fillna(0).astype(int)

    percent_cols = ["증감률", "누계증감률"]
    for col in percent_cols:
        if col in df_display.columns:
            df_display[col] = (df_display[col] * 100).round(0).astype("Int64").astype(str) + "%"

    st.dataframe(df_display)

    csv = df_display.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 CSV 다운로드", csv, file_name="filtered_sales_data.csv", mime="text/csv")
