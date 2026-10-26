@echo off
rem Starts IPL InsightX using the project's own Python environment.
rem OPENBLAS_NUM_THREADS=1 keeps NumPy's memory use small on computers with little free RAM.
cd /d "%~dp0"
set OPENBLAS_NUM_THREADS=1
".venv\Scripts\python.exe" -m streamlit run app.py
pause
