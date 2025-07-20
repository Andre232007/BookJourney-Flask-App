@echo off
REM Este script automatiza o processo de commit e push para o GitHub.
REM Ele espera uma mensagem de commit como argumento.

REM Verifica se um argumento (mensagem de commit) foi fornecido
if "%~1"=="" (
    echo.
    echo ERRO: Por favor, forneca uma mensagem de commit.
    echo.
    echo Uso: commit "Sua mensagem de commit aqui"
    echo.
    goto :eof
)

echo.
echo Adicionando todas as alteracoes...
git add .
if %errorlevel% neq 0 (
    echo ERRO: Falha ao adicionar arquivos.
    goto :eof
)

echo.
echo Realizando commit com a mensagem: "%~1"
git commit -m "%~1"
if %errorlevel% neq 0 (
    echo ERRO: Falha ao realizar commit. Verifique se ha algo para commitar.
    goto :eof
)

echo.
echo Enviando alteracoes para o GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo ERRO: Falha ao enviar para o GitHub. Verifique sua conexao ou credenciais.
    goto :eof
)

echo.
echo Sucesso! Alteracoes enviadas para o GitHub.
echo.

:eof
pause
