@echo off
setlocal
cd /d D:\AIProjects\A1\SteelCoilInspection

powershell -NoProfile -ExecutionPolicy Bypass -Command "$c=@('# Python','__pycache__/','*.py[cod]','.pytest_cache/','.mypy_cache/','.ruff_cache/','','# Virtual environments','.venv/','venv/','.env','','# Build','*.egg-info/','dist/','build/','','# Large or generated data','data/raw/','data/labeling/','data/yolo_dataset/images/','data/yolo_dataset/labels/','runs/','models/','outputs/','reports/','*.pt','*.onnx','*.engine','','# IDE / OS','.vscode/','.idea/','.DS_Store','Thumbs.db'); [IO.File]::WriteAllText('.gitignore', ($c -join [Environment]::NewLine), [Text.UTF8Encoding]::new($false))"

if not exist .git git init

git add .gitignore README.md CHANGELOG.md docs configs scripts src archive *.ps1 *.bat pyproject.toml uv.lock requirements.txt

git commit -m "v0.1.0 Steel Coil Labeler MVP"

git tag -a v0.1.0 -m "Steel Coil Labeler MVP"

git status
pause
