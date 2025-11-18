import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# PDF 보고서 생성 모듈 import
try:
    from report_generator import generate_pdf_report
    PDF_AVAILABLE = True
except ImportError as e:
    PDF_AVAILABLE = False
    print(f"PDF 생성 모듈 로드 실패: {e}")

# 페이지 설정
st.set_page_config(
    page_title="서울 지하철 혼잡도 대시보드",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 캐시를 사용하여 데이터 로딩 최적화
@st.cache_data
def load_data():
    """지하철 혼잡도 데이터 로딩"""
    try:
        # EUC-KR 또는 CP949 인코딩으로 읽기
        df = pd.read_csv('SM_CrowdInfo.csv', encoding='cp949')
        
        # 컬럼명 정리
        df.columns = df.columns.str.strip()
        
        return df
    except Exception as e:
        st.error(f"데이터 로딩 중 오류 발생: {e}")
        return None

@st.cache_data
def preprocess_data(df):
    """데이터 전처리 및 변환"""
    if df is None:
        return None
    
    # 시간대 컬럼 추출 (5시30분부터 00시30분까지)
    time_columns = [col for col in df.columns if '시' in col and '분' in col]
    
    # 기본 정보 컬럼
    info_columns = [col for col in df.columns if col not in time_columns]
    
    # 숫자 데이터 정리 (공백 제거 후 숫자로 변환)
    for col in time_columns:
        df[col] = pd.to_numeric(df[col].astype(str).str.strip(), errors='coerce')
    
    return df, time_columns, info_columns

def get_line_color(line_name):
    """호선별 색상 매핑"""
    color_map = {
        '1호선': '#003DA5',
        '2호선': '#00A84D',
        '3호선': '#EF7C1C',
        '4호선': '#00A5DE',
        '5호선': '#996CAC',
        '6호선': '#CD7C2F',
        '7호선': '#747F00',
        '8호선': '#E6186C',
        '9호선': '#BDB092',
    }
    return color_map.get(line_name, '#666666')

def parse_time_to_minutes(time_str):
    """시간 문자열을 분으로 변환 (예: '07시00분' -> 420)"""
    try:
        # '07시00분' 형식 파싱
        time_str = time_str.replace('시', ':').replace('분', '')
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        
        # 자정 이후 시간 처리 (00시, 01시 등)
        if hours < 5:  # 5시 이전은 다음날로 간주
            hours += 24
        
        return hours * 60 + minutes
    except:
        return 0

def get_current_time_slot(time_columns):
    """현재 시간에 가장 가까운 시간대 찾기"""
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute
    
    # 자정 이후 시간 처리
    if current_minutes < 5 * 60:  # 5시 이전
        current_minutes += 24 * 60
    
    min_diff = float('inf')
    closest_time = time_columns[0]
    
    for time_col in time_columns:
        time_minutes = parse_time_to_minutes(time_col)
        diff = abs(time_minutes - current_minutes)
        if diff < min_diff:
            min_diff = diff
            closest_time = time_col
    
    return closest_time

def find_better_times(station_data, time_columns, current_time, threshold=20):
    """현재 시간보다 덜 혼잡한 시간대 찾기"""
    current_congestion = station_data[current_time]
    better_times = []
    
    current_idx = time_columns.index(current_time)
    
    # 전후 2시간 범위 내에서 검색 (4개 슬롯)
    for i in range(max(0, current_idx - 4), min(len(time_columns), current_idx + 5)):
        if i == current_idx:
            continue
        
        time_col = time_columns[i]
        congestion = station_data[time_col]
        
        if congestion < current_congestion - threshold:
            time_diff = (i - current_idx) * 30  # 30분 단위
            better_times.append({
                '시간': time_col,
                '혼잡도': congestion,
                '차이': current_congestion - congestion,
                '시간차': time_diff
            })
    
    return sorted(better_times, key=lambda x: x['차이'], reverse=True)

def main():
    st.title("🚇 서울 지하철 혼잡도 대시보드")
    st.markdown("---")
    
    # 데이터 로딩
    with st.spinner("데이터를 불러오는 중..."):
        df = load_data()
        
        if df is None:
            st.error("데이터를 불러올 수 없습니다.")
            return
        
        df, time_columns, info_columns = preprocess_data(df)
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 전체 대시보드",
        "🎯 나의 출퇴근 분석",
        "⚖️ 역 비교",
        "🕐 지금 타기 좋은 시간",
        "🔄 상행선/하행선 분석"
    ])
    
    # 탭 1: 전체 대시보드 (기존 코드)
    with tab1:
        render_main_dashboard(df, time_columns, info_columns)
    
    # 탭 2: 나의 출퇴근 시간 맞춤 분석
    with tab2:
        render_commute_analysis(df, time_columns, info_columns)
    
    # 탭 3: 역 비교 기능
    with tab3:
        render_station_comparison(df, time_columns, info_columns)
    
    # 탭 4: 지금 타기 좋은 시간
    with tab4:
        render_best_time_now(df, time_columns, info_columns)
    
    # 탭 5: 상행선/하행선 방향별 분석
    with tab5:
        render_direction_analysis(df, time_columns, info_columns)
    
    # 사이드바에 PDF 보고서 생성 버튼 추가
    st.sidebar.markdown("---")
    st.sidebar.header("📄 보고서 생성")
    
    if PDF_AVAILABLE:
        if st.sidebar.button("🎯 PDF 보고서 생성", use_container_width=True):
            with st.spinner("📊 보고서를 생성하는 중..."):
                try:
                    # PDF 생성
                    pdf_buffer = generate_pdf_report(df, time_columns, info_columns)
                    
                    # 다운로드 버튼
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"지하철혼잡도보고서_{timestamp}.pdf"
                    
                    st.sidebar.download_button(
                        label="📥 보고서 다운로드",
                        data=pdf_buffer,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                    st.sidebar.success("✅ 보고서 생성 완료!")
                    st.sidebar.info(f"파일명: {filename}")
                    
                except Exception as e:
                    st.sidebar.error(f"❌ 보고서 생성 중 오류 발생: {e}")
                    st.sidebar.info("누락된 패키지를 설치해주세요:\npip install reportlab kaleido Pillow")
    else:
        st.sidebar.warning("⚠️ PDF 생성 기능을 사용하려면 추가 패키지 설치가 필요합니다.")
        st.sidebar.code("pip install reportlab kaleido Pillow", language="bash")
    
    # 보고서 정보
    with st.sidebar.expander("ℹ️ 보고서 정보"):
        st.markdown("""
        **포함 내용:**
        - 주요 발견사항 요약
        - 시간대별 혼잡도 분석
        - TOP 5 혼잡 역
        - 평일/주말 비교
        - 권장사항
        
        **형식:** 전문적인 A4 PDF
        **생성 시간:** 약 5-10초
        """)

def render_main_dashboard(df, time_columns, info_columns):
    """전체 대시보드 렌더링 (기존 메인 화면)"""
    # 사이드바 - 필터링 옵션
    st.sidebar.header("🔍 필터 옵션")
    
    # 운영기관 선택
    operators = sorted(df[info_columns[0]].unique())
    selected_operator = st.sidebar.selectbox("운영기관", ["전체"] + operators)
    
    # 호선 선택
    if selected_operator != "전체":
        lines = sorted(df[df[info_columns[0]] == selected_operator][info_columns[1]].unique())
    else:
        lines = sorted(df[info_columns[1]].unique())
    selected_line = st.sidebar.selectbox("호선", ["전체"] + list(lines))
    
    # 요일 선택
    day_types = sorted(df[info_columns[4]].unique())
    selected_day = st.sidebar.selectbox("요일 구분", ["전체"] + list(day_types))
    
    # 역명 검색
    station_search = st.sidebar.text_input("역명 검색", "")
    
    # 데이터 필터링
    filtered_df = df.copy()
    
    if selected_operator != "전체":
        filtered_df = filtered_df[filtered_df[info_columns[0]] == selected_operator]
    
    if selected_line != "전체":
        filtered_df = filtered_df[filtered_df[info_columns[1]] == selected_line]
    
    if selected_day != "전체":
        filtered_df = filtered_df[filtered_df[info_columns[4]] == selected_day]
    
    if station_search:
        filtered_df = filtered_df[filtered_df[info_columns[3]].str.contains(station_search, na=False)]
    
    # 메인 대시보드
    if len(filtered_df) == 0:
        st.warning("선택한 조건에 맞는 데이터가 없습니다.")
        return
    
    # 주요 통계
    st.header("📊 주요 통계")
    col1, col2, col3, col4 = st.columns(4)
    
    # 전체 평균 혼잡도
    avg_congestion = filtered_df[time_columns].mean().mean()
    col1.metric("평균 혼잡도", f"{avg_congestion:.1f}%")
    
    # 최대 혼잡도
    max_congestion = filtered_df[time_columns].max().max()
    col2.metric("최대 혼잡도", f"{max_congestion:.1f}%")
    
    # 역 개수
    station_count = filtered_df[info_columns[3]].nunique()
    col3.metric("역 개수", f"{station_count}개")
    
    # 가장 혼잡한 시간대
    avg_by_time = filtered_df[time_columns].mean()
    peak_time = avg_by_time.idxmax()
    col4.metric("피크 시간대", peak_time)
    
    st.markdown("---")
    
    # 시간대별 평균 혼잡도
    st.header("⏰ 시간대별 평균 혼잡도")
    
    avg_by_time_df = pd.DataFrame({
        '시간': time_columns,
        '평균 혼잡도': [filtered_df[col].mean() for col in time_columns]
    })
    
    fig_line = px.line(
        avg_by_time_df,
        x='시간',
        y='평균 혼잡도',
        title='시간대별 평균 혼잡도 추이',
        markers=True
    )
    fig_line.update_layout(
        xaxis_tickangle=-45,
        height=400,
        hovermode='x unified'
    )
    fig_line.update_traces(line_color='#FF6B6B', line_width=3)
    st.plotly_chart(fig_line, use_container_width=True)
    
    # 평일/주말 비교
    if '전체' in [selected_day] or selected_day == "전체":
        st.header("📅 평일/주말 혼잡도 비교")
        
        comparison_data = []
        for day_type in day_types:
            day_df = filtered_df[filtered_df[info_columns[4]] == day_type]
            for col in time_columns:
                comparison_data.append({
                    '시간': col,
                    '요일구분': day_type,
                    '평균 혼잡도': day_df[col].mean()
                })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        fig_comparison = px.line(
            comparison_df,
            x='시간',
            y='평균 혼잡도',
            color='요일구분',
            title='평일/주말 혼잡도 비교',
            markers=True
        )
        fig_comparison.update_layout(
            xaxis_tickangle=-45,
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    # 역별 혼잡도 히트맵
    st.header("🗺️ 역별 혼잡도 히트맵")
    
    # 상위 20개 역만 표시 (너무 많으면 시각화가 어려움)
    top_stations = filtered_df.nlargest(20, time_columns, keep='first')
    
    heatmap_data = top_stations[time_columns].values
    station_labels = [f"{row[info_columns[3]]} ({row[info_columns[4]]})" 
                     for _, row in top_stations.iterrows()]
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=time_columns,
        y=station_labels,
        colorscale='RdYlGn_r',
        text=heatmap_data,
        texttemplate='%{text:.1f}',
        textfont={"size": 8},
        colorbar=dict(title="혼잡도(%)")
    ))
    
    fig_heatmap.update_layout(
        title='상위 20개 혼잡 역의 시간대별 혼잡도',
        xaxis_tickangle=-45,
        height=600,
        xaxis_title="시간대",
        yaxis_title="역명 (요일구분)"
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # 상위 혼잡 역 목록
    st.header("🏆 가장 혼잡한 역 TOP 10")
    
    station_max_congestion = []
    for _, row in filtered_df.iterrows():
        max_val = row[time_columns].max()
        max_time = row[time_columns].idxmax()
        station_max_congestion.append({
            '운영기관': row[info_columns[0]],
            '호선': row[info_columns[1]],
            '역명': row[info_columns[3]],
            '요일구분': row[info_columns[4]],
            '최대 혼잡도': max_val,
            '최대 혼잡 시간': max_time
        })
    
    top_congestion_df = pd.DataFrame(station_max_congestion)
    top_congestion_df = top_congestion_df.nlargest(10, '최대 혼잡도')
    
    st.dataframe(
        top_congestion_df.style.format({'최대 혼잡도': '{:.1f}%'}),
        use_container_width=True,
        hide_index=True
    )
    
    # 원본 데이터 보기
    with st.expander("📋 원본 데이터 보기"):
        st.dataframe(filtered_df, use_container_width=True)

def render_commute_analysis(df, time_columns, info_columns):
    """나의 출퇴근 시간 맞춤 분석"""
    st.header("🎯 나의 출퇴근 시간 맞춤 분석")
    st.markdown("출발역과 도착역, 출근 시간을 입력하면 최적의 이동 시간을 추천해드립니다!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 출근 경로 설정")
        
        # 역 목록
        stations = sorted(df[info_columns[3]].unique())
        
        departure = st.selectbox("출발역", stations, key="departure")
        arrival = st.selectbox("도착역", stations, key="arrival")
        
        # 요일 선택
        day_type = st.radio("요일", df[info_columns[4]].unique(), horizontal=True)
        
        # 시간 선택
        commute_time = st.selectbox("출근 시간", time_columns, index=8)  # 기본값: 8시30분
    
    with col2:
        st.subheader("📊 혼잡도 분석 결과")
        
        # 출발역 데이터
        dep_data = df[(df[info_columns[3]] == departure) & (df[info_columns[4]] == day_type)]
        arr_data = df[(df[info_columns[3]] == arrival) & (df[info_columns[4]] == day_type)]
        
        if len(dep_data) > 0 and len(arr_data) > 0:
            dep_congestion = dep_data.iloc[0][commute_time]
            arr_congestion = arr_data.iloc[0][commute_time]
            
            # 혼잡도 표시
            st.metric("출발역 혼잡도", f"{dep_congestion:.1f}%", 
                     delta=f"{dep_congestion - df[commute_time].mean():.1f}%p")
            st.metric("도착역 혼잡도", f"{arr_congestion:.1f}%",
                     delta=f"{arr_congestion - df[commute_time].mean():.1f}%p")
            
            # 혼잡도 평가
            avg_congestion = (dep_congestion + arr_congestion) / 2
            if avg_congestion < 50:
                st.success("✅ 쾌적한 시간대입니다!")
            elif avg_congestion < 80:
                st.warning("⚠️ 보통 혼잡도입니다.")
            else:
                st.error("🚨 매우 혼잡한 시간대입니다!")
        else:
            st.warning("선택한 역의 데이터가 없습니다.")
            return
    
    st.markdown("---")
    
    # 시간대별 혼잡도 추이
    st.subheader("⏰ 시간대별 혼잡도 추이")
    
    dep_series = dep_data.iloc[0][time_columns]
    arr_series = arr_data.iloc[0][time_columns]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_columns, y=dep_series,
        mode='lines+markers',
        name=f'{departure} (출발)',
        line=dict(color='#FF6B6B', width=3)
    ))
    fig.add_trace(go.Scatter(
        x=time_columns, y=arr_series,
        mode='lines+markers',
        name=f'{arrival} (도착)',
        line=dict(color='#4ECDC4', width=3)
    ))
    
    # 현재 선택한 시간 강조 - x축의 실제 위치 찾기
    try:
        commute_x_position = list(time_columns).index(commute_time)
        fig.add_shape(
            type="line",
            x0=commute_x_position, x1=commute_x_position,
            y0=0, y1=1,
            yref="paper",
            line=dict(color="gray", dash="dash", width=2)
        )
        fig.add_annotation(
            x=commute_x_position, y=1, yref="paper",
            text="선택한 시간",
            showarrow=False,
            yanchor="bottom"
        )
    except ValueError:
        pass  # 시간을 찾지 못한 경우 표시하지 않음
    
    fig.update_layout(
        title='출발역과 도착역의 시간대별 혼잡도',
        xaxis_title='시간',
        yaxis_title='혼잡도 (%)',
        hovermode='x unified',
        height=400,
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 더 나은 시간대 추천
    st.subheader("💡 더 쾌적한 출근 시간 추천")
    
    better_times_dep = find_better_times(dep_data.iloc[0], time_columns, commute_time, threshold=10)
    
    if better_times_dep:
        st.success(f"💡 더 쾌적한 시간대가 {len(better_times_dep)}개 있습니다!")
        
        cols = st.columns(min(3, len(better_times_dep)))
        for i, time_info in enumerate(better_times_dep[:3]):
            with cols[i]:
                time_diff_min = abs(time_info['시간차'])
                direction = "일찍" if time_info['시간차'] < 0 else "늦게"
                
                st.info(f"""
                **{time_info['시간']}**  
                {time_diff_min}분 {direction}  
                혼잡도: {time_info['혼잡도']:.1f}%  
                🔽 {time_info['차이']:.1f}%p 감소
                """)
    else:
        st.info("선택하신 시간이 이미 최적의 시간대입니다! 👍")

def render_station_comparison(df, time_columns, info_columns):
    """역 비교 기능"""
    st.header("⚖️ 역 비교 분석")
    st.markdown("여러 역의 혼잡도를 동시에 비교해보세요!")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🔍 비교할 역 선택")
        
        stations = sorted(df[info_columns[3]].unique())
        
        # 다중 선택
        selected_stations = st.multiselect(
            "역 선택 (최대 5개)",
            stations,
            default=[stations[0], stations[10]] if len(stations) > 10 else stations[:2],
            max_selections=5
        )
        
        # 요일 선택
        day_type = st.radio("요일 구분", df[info_columns[4]].unique(), key="compare_day", horizontal=True)
        
        # 특정 시간대 선택
        selected_time = st.selectbox("특정 시간대", ["전체"] + time_columns, key="compare_time")
    
    with col2:
        if len(selected_stations) < 2:
            st.warning("⚠️ 최소 2개 이상의 역을 선택해주세요.")
            return
        
        st.subheader("📊 혼잡도 비교 결과")
        
        # 선택한 시간대의 혼잡도 비교
        if selected_time != "전체":
            comparison_data = []
            for station in selected_stations:
                station_data = df[(df[info_columns[3]] == station) & (df[info_columns[4]] == day_type)]
                if len(station_data) > 0:
                    congestion = station_data.iloc[0][selected_time]
                    comparison_data.append({
                        '역명': station,
                        '혼잡도': congestion
                    })
            
            if comparison_data:
                comp_df = pd.DataFrame(comparison_data).sort_values('혼잡도')
                
                fig = px.bar(comp_df, x='역명', y='혼잡도',
                            title=f'{selected_time} 혼잡도 비교',
                            color='혼잡도',
                            color_continuous_scale='RdYlGn_r')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    # 시간대별 비교 차트
    st.subheader("⏰ 시간대별 혼잡도 비교")
    
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    for i, station in enumerate(selected_stations):
        station_data = df[(df[info_columns[3]] == station) & (df[info_columns[4]] == day_type)]
        if len(station_data) > 0:
            congestion_values = station_data.iloc[0][time_columns]
            fig.add_trace(go.Scatter(
                x=time_columns,
                y=congestion_values,
                mode='lines+markers',
                name=station,
                line=dict(color=colors[i % len(colors)], width=2)
            ))
    
    fig.update_layout(
        title='선택한 역들의 시간대별 혼잡도 추이',
        xaxis_title='시간',
        yaxis_title='혼잡도 (%)',
        hovermode='x unified',
        height=500,
        xaxis_tickangle=-45,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 통계 테이블
    st.subheader("📋 상세 통계")
    
    stats_data = []
    for station in selected_stations:
        station_data = df[(df[info_columns[3]] == station) & (df[info_columns[4]] == day_type)]
        if len(station_data) > 0:
            congestion_series = station_data.iloc[0][time_columns]
            stats_data.append({
                '역명': station,
                '평균 혼잡도': f"{congestion_series.mean():.1f}%",
                '최대 혼잡도': f"{congestion_series.max():.1f}%",
                '최소 혼잡도': f"{congestion_series.min():.1f}%",
                '가장 혼잡한 시간': congestion_series.idxmax(),
                '가장 한가한 시간': congestion_series.idxmin()
            })
    
    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

def render_best_time_now(df, time_columns, info_columns):
    """지금 타기 좋은 시간 가이드"""
    st.header("🕐 지금 타기 좋은 시간")
    
    # 현재 시간 표시
    now = datetime.now()
    st.info(f"⏰ 현재 시간: **{now.strftime('%Y-%m-%d %H:%M')}**")
    
    # 현재 시간대 찾기
    current_time_slot = get_current_time_slot(time_columns)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🔍 역 선택")
        
        stations = sorted(df[info_columns[3]].unique())
        selected_station = st.selectbox("역명", stations, key="now_station")
        
        # 요일 자동 감지
        weekday = now.weekday()
        auto_day = "평일" if weekday < 5 else "주말"
        
        day_type = st.radio("요일", df[info_columns[4]].unique(), 
                           index=list(df[info_columns[4]].unique()).index(auto_day) 
                           if auto_day in df[info_columns[4]].unique() else 0,
                           key="now_day", horizontal=True)
    
    with col2:
        st.subheader("📊 현재 혼잡도")
        
        station_data = df[(df[info_columns[3]] == selected_station) & (df[info_columns[4]] == day_type)]
        
        if len(station_data) > 0:
            current_congestion = station_data.iloc[0][current_time_slot]
            avg_congestion = station_data.iloc[0][time_columns].mean()
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("현재 시간대 혼잡도", f"{current_congestion:.1f}%",
                         delta=f"{current_congestion - avg_congestion:.1f}%p")
            with col_b:
                st.metric("평균 대비", 
                         "혼잡" if current_congestion > avg_congestion else "쾌적",
                         delta=f"{abs(current_congestion - avg_congestion):.1f}%p")
            
            # 혼잡도 게이지
            if current_congestion < 50:
                st.success("✅ 지금 타기 좋은 시간입니다!")
            elif current_congestion < 80:
                st.warning("⚠️ 보통 혼잡도입니다.")
            else:
                st.error("🚨 매우 혼잡합니다. 다른 시간을 고려해보세요.")
        else:
            st.warning("해당 역의 데이터가 없습니다.")
            return
    
    st.markdown("---")
    
    # 향후 혼잡도 예측
    st.subheader("🔮 향후 혼잡도 변화")
    
    current_idx = time_columns.index(current_time_slot)
    
    # 전체 시간대와 혼잡도
    all_congestions = [station_data.iloc[0][t] for t in time_columns]
    
    fig = go.Figure()
    
    past_times = []  # 초기화
    
    # 과거 데이터 (회색)
    if current_idx > 0:
        past_indices = list(range(max(0, current_idx - 4), current_idx + 1))
        past_times = [time_columns[i] for i in past_indices]
        past_congestions = [all_congestions[i] for i in past_indices]
        fig.add_trace(go.Scatter(
            x=past_times, y=past_congestions,
            mode='lines+markers',
            name='과거',
            line=dict(color='lightgray', width=2),
            marker=dict(size=8)
        ))
    
    # 미래 예측 (파란색)
    future_indices = list(range(current_idx, min(current_idx + 6, len(time_columns))))
    future_times = [time_columns[i] for i in future_indices]
    future_congestions = [all_congestions[i] for i in future_indices]
    
    fig.add_trace(go.Scatter(
        x=future_times, y=future_congestions,
        mode='lines+markers',
        name='예상',
        line=dict(color='#4ECDC4', width=3),
        marker=dict(size=10)
    ))
    
    # 현재 시간 표시
    # x축에서 현재 시간의 위치 찾기
    all_x_values = past_times + future_times
    if current_time_slot in all_x_values:
        current_x_position = all_x_values.index(current_time_slot)
        fig.add_shape(
            type="line",
            x0=current_x_position, x1=current_x_position,
            y0=0, y1=1,
            yref="paper",
            line=dict(color="red", dash="dash", width=2)
        )
        fig.add_annotation(
            x=current_x_position, y=1, yref="paper",
            text="현재",
            showarrow=False,
            yanchor="bottom",
            font=dict(color="red", size=12, weight="bold")
        )
    
    fig.update_layout(
        title=f'{selected_station}역 혼잡도 변화 추이',
        xaxis_title='시간',
        yaxis_title='혼잡도 (%)',
        hovermode='x unified',
        height=400,
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 추천 시간대
    st.subheader("💡 추천 시간대")
    
    better_times = find_better_times(station_data.iloc[0], time_columns, current_time_slot, threshold=15)
    
    if better_times:
        cols = st.columns(3)
        for i, time_info in enumerate(better_times[:3]):
            with cols[i]:
                time_diff_min = abs(time_info['시간차'])
                if time_info['시간차'] < 0:
                    direction = "⏪ 조금 전"
                    st.info(f"""
                    **{time_info['시간']}**  
                    {time_diff_min}분 전  
                    혼잡도: {time_info['혼잡도']:.1f}%  
                    🔽 {time_info['차이']:.1f}%p 감소
                    """)
                else:
                    direction = "⏩ 조금 후"
                    st.success(f"""
                    **{time_info['시간']}**  
                    {time_diff_min}분 후  
                    혼잡도: {time_info['혼잡도']:.1f}%  
                    🔽 {time_info['차이']:.1f}%p 감소
                    """)
    else:
        st.info("현재 시간이 최적의 시간대입니다! ✨")

def render_direction_analysis(df, time_columns, info_columns):
    """상행선/하행선 방향별 분석"""
    st.header("🔄 상행선/하행선 방향별 분석")
    st.markdown("상행선(도심 방향)과 하행선(외곽 방향)의 혼잡도 패턴을 비교합니다.")
    
    # 역명에서 상행/하행 정보 추출
    # 데이터에 상행/하행 정보가 있는지 확인
    direction_col = None
    for col in info_columns:
        if '방향' in col or '상하행' in col:
            direction_col = col
            break
    
    # 역명 컬럼에서 상행/하행 구분이 있는지 확인
    sample_stations = df[info_columns[3]].head(100).tolist()
    has_direction = any('상행' in str(s) or '하행' in str(s) or '내선' in str(s) or '외선' in str(s) 
                        for s in sample_stations)
    
    if not has_direction:
        st.warning("""
        ⚠️ 현재 데이터에는 상행선/하행선 구분 정보가 명시적으로 포함되어 있지 않습니다.
        
        대신 **요일별 출퇴근 시간대 분석**을 제공합니다:
        - **평일 오전(07:00~09:00)**: 주로 도심 방향(상행선) 혼잡
        - **평일 오후(18:00~20:00)**: 주로 외곽 방향(하행선) 혼잡
        """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🔍 분석 설정")
        
        # 호선 선택
        lines = sorted(df[info_columns[1]].unique())
        selected_line = st.selectbox("호선", lines, key="direction_line")
        
        # 요일 선택
        day_type = st.selectbox("요일", df[info_columns[4]].unique(), key="direction_day")
        
        # 역 선택 (선택사항)
        line_df = df[df[info_columns[1]] == selected_line]
        stations_in_line = sorted(line_df[info_columns[3]].unique())
        
        selected_station = st.selectbox(
            "특정 역 (선택사항)",
            ["전체"] + stations_in_line,
            key="direction_station"
        )
    
    with col2:
        st.subheader("📊 출퇴근 시간대 혼잡도")
        
        # 출퇴근 시간대 정의 (시간 형식이 '7시'이지 '07시'가 아님)
        # startswith를 사용하거나 정확한 매칭 필요
        morning_rush = [col for col in time_columns if 
                       col.startswith('7시') or col.startswith('8시') or col.startswith('9시')]
        evening_rush = [col for col in time_columns if 
                       col.startswith('18시') or col.startswith('19시') or col.startswith('20시')]
        
        filtered_df = line_df[line_df[info_columns[4]] == day_type]
        
        if selected_station != "전체":
            filtered_df = filtered_df[filtered_df[info_columns[3]] == selected_station]
        
        if len(filtered_df) > 0:
            if morning_rush and evening_rush:
                morning_avg = filtered_df[morning_rush].mean().mean()
                evening_avg = filtered_df[evening_rush].mean().mean()
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("오전 출근시간", f"{morning_avg:.1f}%",
                             help="07:00 ~ 09:00 평균")
                with col_b:
                    st.metric("오후 퇴근시간", f"{evening_avg:.1f}%",
                             help="18:00 ~ 20:00 평균")
                
                # 비교
                diff = evening_avg - morning_avg
                if abs(diff) < 10:
                    st.info("📊 출퇴근 시간대 혼잡도가 비슷합니다.")
                elif diff > 0:
                    st.warning(f"📈 퇴근시간이 출근시간보다 {diff:.1f}%p 더 혼잡합니다.")
                else:
                    st.warning(f"📈 출근시간이 퇴근시간보다 {abs(diff):.1f}%p 더 혼잡합니다.")
            else:
                st.warning("⚠️ 출퇴근 시간대 데이터를 찾을 수 없습니다.")
    
    st.markdown("---")
    
    # 시간대별 상세 분석
    st.subheader("⏰ 하루 전체 혼잡도 패턴")
    
    # 호선별 평균 혼잡도
    avg_by_time = []
    for time_col in time_columns:
        avg_by_time.append({
            '시간': time_col,
            '평균 혼잡도': filtered_df[time_col].mean()
        })
    
    pattern_df = pd.DataFrame(avg_by_time)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=pattern_df['시간'],
        y=pattern_df['평균 혼잡도'],
        mode='lines+markers',
        name='평균 혼잡도',
        line=dict(color='#FF6B6B', width=3),
        fill='tozeroy',
        fillcolor='rgba(255, 107, 107, 0.2)'
    ))
    
    # 출퇴근 시간대 영역 표시
    if morning_rush and evening_rush:  # 리스트가 비어있지 않은지 확인
        try:
            morning_start_idx = time_columns.index(morning_rush[0])
            morning_end_idx = time_columns.index(morning_rush[-1])
            evening_start_idx = time_columns.index(evening_rush[0])
            evening_end_idx = time_columns.index(evening_rush[-1])
            
            fig.add_shape(
                type="rect",
                x0=morning_start_idx, x1=morning_end_idx,
                y0=0, y1=1,
                yref="paper",
                fillcolor="yellow", opacity=0.2,
                line=dict(width=0)
            )
            fig.add_annotation(
                x=(morning_start_idx + morning_end_idx) / 2,
                y=0.95, yref="paper",
                text="출근시간",
                showarrow=False,
                font=dict(size=10)
            )
            
            fig.add_shape(
                type="rect",
                x0=evening_start_idx, x1=evening_end_idx,
                y0=0, y1=1,
                yref="paper",
                fillcolor="orange", opacity=0.2,
                line=dict(width=0)
            )
            fig.add_annotation(
                x=(evening_start_idx + evening_end_idx) / 2,
                y=0.95, yref="paper",
                text="퇴근시간",
                showarrow=False,
                font=dict(size=10)
            )
        except (ValueError, IndexError):
            pass  # 시간대를 찾지 못한 경우 영역 표시 생략
    
    fig.update_layout(
        title=f'{selected_line} 시간대별 혼잡도 패턴',
        xaxis_title='시간',
        yaxis_title='혼잡도 (%)',
        hovermode='x unified',
        height=450,
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 역별 출퇴근 시간 혼잡도 비교
    st.subheader("🚉 역별 출퇴근 시간 혼잡도 비교")
    
    station_comparison = []
    if morning_rush and evening_rush:
        for station in stations_in_line[:10]:  # 상위 10개 역
            station_df = line_df[(line_df[info_columns[3]] == station) & 
                                (line_df[info_columns[4]] == day_type)]
            if len(station_df) > 0:
                try:
                    morning_cong = station_df[morning_rush].mean().mean()
                    evening_cong = station_df[evening_rush].mean().mean()
                    station_comparison.append({
                        '역명': station,
                        '출근시간': morning_cong,
                        '퇴근시간': evening_cong,
                        '차이': evening_cong - morning_cong
                    })
                except Exception:
                    pass  # 데이터가 없는 경우 건너뛰기
    
    if station_comparison:
        comp_df = pd.DataFrame(station_comparison)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=comp_df['역명'],
            y=comp_df['출근시간'],
            name='출근시간 (07-09시)',
            marker_color='#FFD93D'
        ))
        fig.add_trace(go.Bar(
            x=comp_df['역명'],
            y=comp_df['퇴근시간'],
            name='퇴근시간 (18-20시)',
            marker_color='#FF6B6B'
        ))
        
        fig.update_layout(
            title='역별 출퇴근 시간대 혼잡도 비교',
            xaxis_title='역명',
            yaxis_title='혼잡도 (%)',
            barmode='group',
            height=400,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 가장 큰 차이를 보이는 역
        max_diff_station = comp_df.loc[comp_df['차이'].abs().idxmax()]
        
        if max_diff_station['차이'] > 0:
            st.info(f"💡 **{max_diff_station['역명']}**은 퇴근시간이 출근시간보다 **{max_diff_station['차이']:.1f}%p** 더 혼잡합니다.")
        else:
            st.info(f"💡 **{max_diff_station['역명']}**은 출근시간이 퇴근시간보다 **{abs(max_diff_station['차이']):.1f}%p** 더 혼잡합니다.")
    else:
        st.warning("⚠️ 출퇴근 시간대 비교 데이터를 찾을 수 없습니다.")

if __name__ == "__main__":
    main()

