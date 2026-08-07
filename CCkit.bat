@echo off
REM CCkit Windows 启动脚本：将命令行参数转交给同目录下的 CCkit Python 入口。
python "%~dp0CCkit" %*
