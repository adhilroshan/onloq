@echo off
echo Starting Onloq for a quick test...
echo You'll see activity tracking and code monitoring in action.
echo.

echo Starting the logger in the background...
start /B python main.py run --daemon

echo Waiting 10 seconds for initialization...
timeout /t 10 /nobreak

echo Making a code change to trigger monitoring...
echo. >> test_demo.py
echo # This is a test comment >> test_demo.py

echo Waiting another 5 seconds to capture the change...
timeout /t 5 /nobreak

echo Stopping the logger...
taskkill /F /IM python.exe

echo.
echo Test complete! Let's check the status...
python main.py status

echo.
echo You can now run: python main.py summarize --model qwen3
echo to see an AI-generated summary of this brief activity!
