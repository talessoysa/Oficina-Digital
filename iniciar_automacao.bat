@echo off
title Automacao de Reserva - Oficina Digital
color 0A
cd /d "%~dp0"
echo =================================================================
echo   Oficina Digital - Automacao de Reserva (Triagem por Grafo)
echo =================================================================
python automacao_reserva.py
pause

