# Gera o "Demon's Crest Open Randomizer.exe" (pasta de cima; nome escolhido pelo Neitan, 27/09): só o lançador dcor_launcher.py com o Python embutido. O código do rando fica
# nesta pasta data e é lido ao abrir o exe: só precisa rodar isto de novo se o lançador mudar ou se o código da data
# passar a usar um módulo da biblioteca padrão que o lançador ainda não importa.
# PyInstaller num venv (padrão: .venv_dcor na pasta acima do DCOR; outro: $env:DCOR_VENV). Ícone: make_dcor_icon.py.
$data = $PSScriptRoot
$dcor = Split-Path $data
$venv = if ($env:DCOR_VENV) { $env:DCOR_VENV } else { Join-Path (Split-Path $dcor) '.venv_dcor' }
$py = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $py)) { py -3.11 -m venv $venv; & $py -m pip install pyinstaller }
$ico = Join-Path $data 'dcor.ico'
if (-not (Test-Path $ico)) { python (Join-Path $data 'make_dcor_icon.py') }
$work = Join-Path $venv 'build'
& $py -m PyInstaller --noconfirm --onefile --windowed --name "Demon's Crest Open Randomizer" --icon $ico `
    --distpath $dcor --workpath $work --specpath $work (Join-Path $data 'dcor_launcher.py')
