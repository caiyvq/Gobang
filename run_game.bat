@echo off

set CONDA_ENV_NAME=gameenv
set CONDA_PATH=C:\Users\CYQ\miniconda3\Scripts\activate

echo Activating conda environment: %CONDA_ENV_NAME%...

call %CONDA_PATH%
call conda activate %CONDA_ENV_NAME%

echo Starting the game...
python -m gobang.main