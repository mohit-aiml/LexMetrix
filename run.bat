@echo off
echo =====================================================================
echo  LexMetrix - Legal Metrology Automated Compliance System
echo  Department of Consumer Affairs (DoCA), Govt. of India
echo  Problem Statement ID: 26034
echo =====================================================================
echo.
echo Starting LexMetrix Server on http://127.0.0.1:8000 ...
echo Press Ctrl+C to stop.
echo.
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
