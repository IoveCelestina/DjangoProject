@echo off
setlocal enabledelayedexpansion

REM —— 统一切到脚本目录（关键） ——
pushd %~dp0

REM —— 统一日志目录 ——
set LOGDIR=%~dp0logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

REM —— 生成安全时间戳（去掉冒号空格） ——
set D=%date%
set T=%time: =0%
set T=%T::=-%
set T=%T:.=-%
set TS=%D%_%T%

REM —— 在公共目录打一枚“我启动了”的痕迹，方便判断任务是否进来过 ——
echo [!DATE! !TIME!] task started > "C:\Users\Public\AutoGetData_started.txt"

REM —— 记录环境信息 —— 
(
  echo ==== START %DATE% %TIME% ====
  echo USERNAME=!USERNAME!
  echo WORKDIR=%CD%
  where python 2^>^&1
  py -3 -V 2^>^&1
) >> "%LOGDIR%\scheduler_trace.log"

REM —— 尝试用 py 启动（更通用），失败再退回 python —— 
py -3 "1.py" >> "%LOGDIR%\run_!TS!.log" 2>&1
if errorlevel 1 (
  echo [!DATE! !TIME!] py -3 failed, try python >> "%LOGDIR%\scheduler_trace.log"
  python "1.py" >> "%LOGDIR%\run_!TS!.log" 2>&1
)

echo ==== END %DATE% %TIME% ====>> "%LOGDIR%\scheduler_trace.log"

popd
endlocal
