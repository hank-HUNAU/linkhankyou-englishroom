@echo off
chcp 65001 >nul
rem One-click push for pending commits. Pure ASCII; uses %~dp0 so no hardcoded path.
cd /d "%~dp0"
echo ============================================
echo   TH!NK site - push local commits to origin main
echo ============================================
echo.
echo [1/3] Pending commits (origin/main..main):
git --no-pager log --oneline origin/main..main
echo.
echo [2/3] Pushing...
git push origin main
if errorlevel 1 goto FAIL
echo.
echo [3/3] Done. GitHub Pages rebuilds in 1-2 min.
echo Then HARD REFRESH the site: Ctrl+Shift+R, or close the tab and reopen.
goto END
:FAIL
echo.
echo [FAIL] Push failed. Check network / git login, then retry.
:END
pause
