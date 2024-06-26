@echo off
echo делает бекапы всей БД
set POSTGRES_FOLDER="C:\Program Files\PostgreSQL\15"
set USERNAME=postgres
set HOSTNAME=localhost
set PORT=5432
set DATABASE=wildberries_parser_1

For /f "tokens=1-4 delims=/." %%a in ('date /t') do (set DATE=%%c_%%b_%%a)
set DATE=%DATE:~0,4%%DATE:~5,6%
For /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set TIME=%%a_%%b)
set DATETIME=%DATE%_%TIME%
echo datetime is %DATETIME%

set BACKUP_FILE="%cd%\%DATABASE%_%DATETIME%.backup"
echo backup file name is %BACKUP_FILE%

echo on
%POSTGRES_FOLDER%\bin\pg_dump -h %HOSTNAME% -p %PORT% -U %USERNAME% -N pgagent -F c -f %BACKUP_FILE% %DATABASE%
