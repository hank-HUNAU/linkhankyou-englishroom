@echo off
REM =====================================================================
REM  TH!NK 篇章音频 Web 重编码（提速用，可选）
REM  目标：把 assets/p*.mp3 由 ~128kbps 立体声 压成 ~64kbps 单声道 32kHz，
REM        语音内容几乎无损，体积约减半（1.8MB -> ~0.7MB），显著加快加载。
REM  前提：本机已安装 ffmpeg 且在 PATH（或改下面 FFMPEG 变量为完整路径）。
REM  安装：  choco install ffmpeg  或  从 https://www.gyan.dev/ffmpeg/ 下载静态版
REM  注意：只改「网站副本」assets/pXXX.mp3；归档正典（003 第三版课程材料/...）
REM        不受影响。重编码后需重新 commit + push。
REM =====================================================================
setlocal
set "FFMPEG=D:\软件备份\B站视频下载\[WPF]JJDown\OrderEXE\ffmpeg.exe"
REM 若换机器/路径，改成你本机的 ffmpeg.exe 完整路径（需引号包裹空格与括号）

cd /d "%~dp0"
if not exist assets\. ( echo 请在仓库根目录运行本脚本 & exit /b 1 )

set CNT=0
for %%f in (assets\p*.mp3) do (
  echo 处理 %%~nxf ...
  "%FFMPEG%" -y -i "%%f" -ac 1 -ar 32000 -b:a 64000 "%%~dpnf.tmp.mp3" >nul 2>&1
  if exist "%%~dpnf.tmp.mp3" (
    move /Y "%%~dpnf.tmp.mp3" "%%f" >nul
    set /a CNT+=1
  ) else (
    echo   [跳过] %%~nxf 处理失败（检查 ffmpeg 是否可用）
  )
)
echo 完成：重编码 %CNT% 个文件。随后请 git add assets & git commit & git push。
endlocal
