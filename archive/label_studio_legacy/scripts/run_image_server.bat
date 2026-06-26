@echo off
cd /d D:\AIProjects\A1\SteelCoilInspection\data\raw
echo Image server root: %cd%
echo Image server: http://127.0.0.1:8090
echo This window must stay open.
uv run python -m http.server 8090
pause
