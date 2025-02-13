@ECHO OFF
ruff format .
basedpyright .
ruff check .
