@echo off
echo Running Tests...
echo.

cd ..
python -m pytest tests/ -v

echo.
echo Tests Complete
pause
