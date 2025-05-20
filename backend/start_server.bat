@echo off
call venv\Scripts\activate
waitress-serve --port=5000 --threads=4 app:app