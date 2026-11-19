@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Verificando o Rig do M1 e a compatibilidade MyHub v9...
py -c "import sys,inspect; sys.path.insert(0,'estudio'); from estudio.cenas2d.rig import Rig; print('Arquivo:',inspect.getsourcefile(Rig)); print('Assinatura:',inspect.signature(Rig.__init__)); r=Rig({'id':'verificacao','partes':[],'camadas':[],'animacoes':{}}, origem='ia'); print('OK: Rig aceita origem=',r.origem)"
if errorlevel 1 (
  echo FALHA: o Python nao conseguiu carregar o Rig atualizado.
  pause
  exit /b 1
)
echo.
echo Executando testes de lote e compatibilidade...
py -m unittest tests.test_myhub_v9_compat tests.test_myhub_lotes_svg -v
if errorlevel 1 (
  echo Alguns testes falharam. Copie o resultado para diagnostico.
  pause
  exit /b 1
)
echo.
echo VERIFICACAO CONCLUIDA.
pause
