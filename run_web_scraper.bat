@echo off
echo Setting up the environment for web scraping...
cd /d "%~dp0"

:: Create a virtual environment
python -m venv venv
call venv\Scripts\activate.bat

:: Install required packages
echo Installing required packages...
pip install --upgrade pip
pip install -r data_collection\requirements.txt

:: Run the web scraper
echo Starting the web scraper...
cd data_collection
python web_scraper.py

pause
