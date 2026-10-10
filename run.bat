@echo off
cd /d "%~dp0"
python manga_notifier.py >> notifier.log 2>&1
