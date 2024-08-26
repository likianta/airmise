@echo off
cd /d %~dp0
set "PYTHONPATH=.;lib/core_part1;lib/core_part2;lib/extra"
set "PYTHONUTF8=1"
.\python\python.exe -m aircontrol run-local-server
pause
