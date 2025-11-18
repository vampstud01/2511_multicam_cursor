@echo off
echo ====================================
echo   지하철 혼잡도 대시보드 실행 중...
echo ====================================
echo.
echo 브라우저에서 http://localhost:8501 로 접속하세요
echo 종료하려면 Ctrl+C를 누르세요
echo.
cd /d "%~dp0"
streamlit run app.py
pause

