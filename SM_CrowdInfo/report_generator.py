"""
서울 지하철 혼잡도 분석 PDF 보고서 생성 모듈
ReportLab을 사용한 전문적인 보고서 생성
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np
from io import BytesIO
from PIL import Image as PILImage

# 한글 폰트 등록 시도
def register_korean_font():
    """한글 폰트 등록"""
    import os
    import platform
    
    # 여러 경로에서 폰트 찾기
    font_paths = [
        # Windows
        'C:/Windows/Fonts/malgun.ttf',
        'C:/Windows/Fonts/gulim.ttc',
        # Linux (Ubuntu/Debian) - packages.txt로 설치된 경로
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf',
        '/usr/share/fonts/truetype/nanum-gothic/NanumGothic.ttf',
        # macOS
        '/Library/Fonts/NanumGothic.ttf',
        '/System/Library/Fonts/AppleGothic.ttf',
        # 상대 경로
        'NanumGothic.ttf',
        'malgun.ttf',
    ]
    
    # 사용 가능한 폰트 찾기
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_name = 'KoreanFont'
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                print(f"✓ 한글 폰트 등록 성공: {font_path}")
                return font_name
            except Exception as e:
                print(f"✗ 폰트 등록 실패 ({font_path}): {e}")
                continue
    
    # 모든 폰트 실패 시 DejaVu Sans 사용 (유니코드 지원)
    print("⚠ 한글 폰트를 찾을 수 없습니다. DejaVuSans를 사용합니다.")
    try:
        # DejaVu Sans는 대부분의 Linux에 기본 설치됨
        pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        return 'DejaVu'
    except:
        print("⚠ 기본 폰트를 사용합니다. 한글이 제대로 표시되지 않을 수 있습니다.")
        return 'Helvetica'

KOREAN_FONT = register_korean_font()

def create_custom_styles():
    """커스텀 스타일 생성"""
    styles = getSampleStyleSheet()
    
    # 제목 스타일
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontName=KOREAN_FONT,
        fontSize=24,
        textColor=colors.HexColor('#003DA5'),
        spaceAfter=30,
        alignment=TA_CENTER,
        leading=30
    ))
    
    # 섹션 제목
    styles.add(ParagraphStyle(
        name='CustomHeading',
        parent=styles['Heading2'],
        fontName=KOREAN_FONT,
        fontSize=16,
        textColor=colors.HexColor('#003DA5'),
        spaceAfter=12,
        spaceBefore=12,
        leading=20
    ))
    
    # 본문
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['BodyText'],
        fontName=KOREAN_FONT,
        fontSize=10,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    ))
    
    # 강조
    styles.add(ParagraphStyle(
        name='CustomHighlight',
        parent=styles['BodyText'],
        fontName=KOREAN_FONT,
        fontSize=11,
        textColor=colors.HexColor('#FF6B6B'),
        leading=16,
        spaceAfter=10
    ))
    
    return styles

def save_plotly_chart(fig, width=700, height=400):
    """Plotly 차트를 이미지로 변환 (Kaleido 대신 matplotlib 사용)"""
    try:
        # Kaleido 대신 matplotlib으로 차트 생성
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # GUI 없는 백엔드
        
        # Plotly 데이터 추출
        if hasattr(fig, 'data') and len(fig.data) > 0:
            trace = fig.data[0]
            x = trace.x
            y = trace.y
            
            # matplotlib으로 그리기
            plt.figure(figsize=(width/100, height/100), dpi=100)
            plt.plot(x, y, color='#FF6B6B', linewidth=2, marker='o', markersize=4)
            plt.fill_between(range(len(y)), y, alpha=0.2, color='#FF6B6B')
            plt.xticks(rotation=45, ha='right', fontsize=6)
            plt.yticks(fontsize=8)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # BytesIO로 저장
            buffer = BytesIO()
            plt.savefig(buffer, format='PNG', dpi=150, bbox_inches='tight')
            plt.close()
            buffer.seek(0)
            return buffer
        else:
            raise Exception("No data in figure")
            
    except Exception as e:
        print(f"차트 저장 오류: {e}")
        # 텍스트로 대체 이미지 생성
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        
        fig, ax = plt.subplots(figsize=(width/100, height/100))
        ax.text(0.5, 0.5, 'Chart\n(Visualization)', 
                ha='center', va='center', fontsize=20, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        buffer = BytesIO()
        plt.savefig(buffer, format='PNG', dpi=100, bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        return buffer

def extract_insights(df, time_columns, info_columns):
    """핵심 인사이트 추출"""
    insights = {}
    
    # 전체 평균 혼잡도
    insights['avg_congestion'] = df[time_columns].mean().mean()
    
    # 최대 혼잡도
    insights['max_congestion'] = df[time_columns].max().max()
    
    # 가장 혼잡한 시간대
    avg_by_time = df[time_columns].mean()
    insights['peak_time'] = avg_by_time.idxmax()
    insights['peak_value'] = avg_by_time.max()
    
    # 가장 한가한 시간대
    insights['off_peak_time'] = avg_by_time.idxmin()
    insights['off_peak_value'] = avg_by_time.min()
    
    # 가장 혼잡한 역 TOP 5
    station_max = []
    for _, row in df.iterrows():
        max_val = row[time_columns].max()
        station_max.append({
            'station': row[info_columns[3]],
            'line': row[info_columns[1]],
            'day': row[info_columns[4]],
            'congestion': max_val,
            'time': row[time_columns].idxmax()
        })
    
    station_max_df = pd.DataFrame(station_max).nlargest(5, 'congestion')
    insights['top_stations'] = station_max_df.to_dict('records')
    
    # 평일/주말 비교
    day_types = df[info_columns[4]].unique()
    if len(day_types) > 1:
        day_comparison = {}
        for day in day_types:
            day_df = df[df[info_columns[4]] == day]
            day_comparison[day] = day_df[time_columns].mean().mean()
        insights['day_comparison'] = day_comparison
    
    return insights

def create_time_series_chart(df, time_columns, title="시간대별 평균 혼잡도"):
    """시간대별 추이 차트 생성"""
    avg_by_time = [df[col].mean() for col in time_columns]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_columns,
        y=avg_by_time,
        mode='lines+markers',
        line=dict(color='#FF6B6B', width=3),
        marker=dict(size=6),
        fill='tozeroy',
        fillcolor='rgba(255, 107, 107, 0.2)'
    ))
    
    # 폰트가 없을 경우 영문으로 표시
    if KOREAN_FONT in ['Helvetica', 'DejaVu']:
        title = "Average Congestion by Time"
        xaxis_title = "Time"
        yaxis_title = "Congestion (%)"
    else:
        xaxis_title = '시간대'
        yaxis_title = '평균 혼잡도 (%)'
    
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        xaxis_tickangle=-45,
        height=400,
        showlegend=False,
        font=dict(family="Arial", size=10),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridcolor='lightgray')
    
    return fig

def create_top_stations_chart(insights):
    """TOP 5 혼잡 역 차트"""
    top_stations = insights['top_stations']
    
    stations = [s['station'] for s in top_stations]
    congestions = [s['congestion'] for s in top_stations]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=stations,
        y=congestions,
        marker_color=['#FF6B6B', '#FF8787', '#FFA5A5', '#FFC3C3', '#FFE1E1'],
        text=[f"{c:.1f}%" for c in congestions],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='가장 혼잡한 역 TOP 5',
        xaxis_title='역명',
        yaxis_title='최대 혼잡도 (%)',
        height=400,
        showlegend=False,
        font=dict(family="Malgun Gothic, Arial", size=10),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='lightgray')
    
    return fig

def create_day_comparison_chart(insights):
    """평일/주말 비교 차트"""
    if 'day_comparison' not in insights:
        return None
    
    day_comparison = insights['day_comparison']
    days = list(day_comparison.keys())
    values = list(day_comparison.values())
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=days,
        y=values,
        marker_color=['#4ECDC4', '#FFD93D'],
        text=[f"{v:.1f}%" for v in values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='평일 vs 주말 평균 혼잡도',
        xaxis_title='요일 구분',
        yaxis_title='평균 혼잡도 (%)',
        height=350,
        showlegend=False,
        font=dict(family="Malgun Gothic, Arial", size=10),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

def generate_pdf_report(df, time_columns, info_columns, filename="subway_report.pdf"):
    """PDF 보고서 생성 메인 함수"""
    
    # PDF 문서 생성
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # 스토리 (콘텐츠) 리스트
    story = []
    styles = create_custom_styles()
    
    # === 표지 페이지 ===
    story.append(Spacer(1, 2*inch))
    
    title = Paragraph("서울 지하철 혼잡도 분석 보고서", styles['CustomTitle'])
    story.append(title)
    story.append(Spacer(1, 0.3*inch))
    
    subtitle = Paragraph(
        f"<font size=12>생성일: {datetime.now().strftime('%Y년 %m월 %d일')}</font>",
        styles['CustomBody']
    )
    story.append(subtitle)
    story.append(Spacer(1, 0.2*inch))
    
    # 분석 범위
    analysis_range = Paragraph(
        f"<font size=10>분석 대상: {len(df)}개 데이터 포인트<br/>"
        f"역 개수: {df[info_columns[3]].nunique()}개<br/>"
        f"호선 개수: {df[info_columns[1]].nunique()}개</font>",
        styles['CustomBody']
    )
    story.append(analysis_range)
    
    story.append(PageBreak())
    
    # === 인사이트 추출 ===
    insights = extract_insights(df, time_columns, info_columns)
    
    # === 요약 (Executive Summary) ===
    story.append(Paragraph("1. 주요 발견사항", styles['CustomHeading']))
    story.append(Spacer(1, 0.2*inch))
    
    summary_text = f"""
    • 전체 평균 혼잡도: <b>{insights['avg_congestion']:.1f}%</b><br/>
    • 최대 혼잡도: <b>{insights['max_congestion']:.1f}%</b><br/>
    • 피크 시간대: <b>{insights['peak_time']}</b> (평균 {insights['peak_value']:.1f}%)<br/>
    • 가장 한가한 시간대: <b>{insights['off_peak_time']}</b> (평균 {insights['off_peak_value']:.1f}%)<br/>
    """
    
    story.append(Paragraph(summary_text, styles['CustomBody']))
    story.append(Spacer(1, 0.3*inch))
    
    # === 시간대별 분석 ===
    story.append(Paragraph("2. 시간대별 혼잡도 분석", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    # 차트 생성 및 추가
    time_chart = create_time_series_chart(df, time_columns)
    chart_img = save_plotly_chart(time_chart, width=700, height=400)
    
    img = Image(chart_img, width=6*inch, height=3.5*inch)
    story.append(img)
    story.append(Spacer(1, 0.3*inch))
    
    analysis_text = f"""
    시간대별 분석 결과, <b>{insights['peak_time']}</b>에 가장 높은 혼잡도를 기록했습니다. 
    반면 <b>{insights['off_peak_time']}</b>가 가장 쾌적한 시간대로 나타났습니다. 
    피크 시간대와 오프피크 시간대의 혼잡도 차이는 약 <b>{insights['peak_value'] - insights['off_peak_value']:.1f}%p</b>입니다.
    """
    story.append(Paragraph(analysis_text, styles['CustomBody']))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(PageBreak())
    
    # === TOP 5 혼잡 역 ===
    story.append(Paragraph("3. 가장 혼잡한 역 TOP 5", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    # 차트
    top_chart = create_top_stations_chart(insights)
    chart_img2 = save_plotly_chart(top_chart, width=700, height=400)
    img2 = Image(chart_img2, width=6*inch, height=3.5*inch)
    story.append(img2)
    story.append(Spacer(1, 0.3*inch))
    
    # 테이블
    table_data = [['순위', '역명', '호선', '요일', '최대 혼잡도', '시간']]
    for i, station in enumerate(insights['top_stations'], 1):
        table_data.append([
            str(i),
            station['station'],
            station['line'],
            station['day'],
            f"{station['congestion']:.1f}%",
            station['time']
        ])
    
    table = Table(table_data, colWidths=[0.8*inch, 1.5*inch, 1*inch, 1*inch, 1.2*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003DA5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), KOREAN_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), KOREAN_FONT),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    story.append(PageBreak())
    
    # === 평일/주말 비교 ===
    if 'day_comparison' in insights:
        story.append(Paragraph("4. 평일 vs 주말 비교", styles['CustomHeading']))
        story.append(Spacer(1, 0.1*inch))
        
        day_chart = create_day_comparison_chart(insights)
        if day_chart:
            chart_img3 = save_plotly_chart(day_chart, width=600, height=350)
            img3 = Image(chart_img3, width=5*inch, height=3*inch)
            story.append(img3)
            story.append(Spacer(1, 0.3*inch))
        
        # 비교 분석
        day_comp = insights['day_comparison']
        days = list(day_comp.keys())
        if len(days) >= 2:
            diff = abs(day_comp[days[0]] - day_comp[days[1]])
            higher = days[0] if day_comp[days[0]] > day_comp[days[1]] else days[1]
            
            comp_text = f"""
            {higher}의 평균 혼잡도가 약 <b>{diff:.1f}%p</b> 더 높게 나타났습니다. 
            이는 {higher} 출퇴근 패턴과 관련이 있는 것으로 분석됩니다.
            """
            story.append(Paragraph(comp_text, styles['CustomBody']))
        
        story.append(PageBreak())
    
    # === 권장사항 ===
    story.append(Paragraph("5. 권장사항", styles['CustomHeading']))
    story.append(Spacer(1, 0.2*inch))
    
    recommendations = f"""
    <b>일반 시민을 위한 권장사항:</b><br/>
    • 가능하다면 <b>{insights['off_peak_time']}</b> 전후로 이동하시면 쾌적하게 이용할 수 있습니다.<br/>
    • 피크 시간대(<b>{insights['peak_time']}</b>)는 가급적 피하시기 바랍니다.<br/>
    • 혼잡한 역({insights['top_stations'][0]['station']}, {insights['top_stations'][1]['station']} 등)보다 
      인근 역을 이용하시면 더 편리할 수 있습니다.<br/>
    <br/>
    <b>운영 기관을 위한 제언:</b><br/>
    • 피크 시간대 배차 간격 단축 검토<br/>
    • 혼잡 역 승강장 안전 관리 강화<br/>
    • 실시간 혼잡도 정보 제공 확대<br/>
    """
    
    story.append(Paragraph(recommendations, styles['CustomBody']))
    story.append(Spacer(1, 0.5*inch))
    
    # === 푸터 ===
    footer = Paragraph(
        f"<font size=8 color='gray'>본 보고서는 서울교통공사 공공데이터를 기반으로 자동 생성되었습니다. | "
        f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</font>",
        styles['CustomBody']
    )
    story.append(footer)
    
    # PDF 빌드
    doc.build(story)
    
    # BytesIO에서 데이터 가져오기
    buffer.seek(0)
    return buffer

if __name__ == "__main__":
    print("PDF Report Generator Module")
    print(f"Korean Font: {KOREAN_FONT}")

