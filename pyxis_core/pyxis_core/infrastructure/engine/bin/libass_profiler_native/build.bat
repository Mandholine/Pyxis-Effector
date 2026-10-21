@echo off
rem Build script for libass_profiler on Windows (MSYS2 / MinGW-w64)

echo === Building libass_profiler on Windows ===

where gcc >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: GCC not found in PATH.
    echo Please install MSYS2 with mingw-w64-x86_64-gcc and mingw-w64-x86_64-libass.
    exit /b 1
)

gcc -O3 -Wall -Wextra -std=c99 libass_profiler.c -o libass_profiler.exe -lass -lfreetype -lm

if %ERRORLEVEL% EQU 0 (
    echo Build successful: libass_profiler.exe
    libass_profiler.exe
) else (
    echo Compilation failed.
    exit /b %ERRORLEVEL%
)
