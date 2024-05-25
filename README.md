# Artist Relation Resolver Frontend
A gui application for the artist relation resolver api

## Installing dependencies
Create a virtual environment
```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r ./requirements/dev.txt
```

Check for outdated libraries:
```powershell
pip list --outdated
python.exe -m pip install --upgrade [packagename]
pip freeze > requirements.txt
```
When freezing requirements, make sture manually check the created file to only include top-level packages, and set all packages to match by '~=' instead of '==' to always install the lastest patch version of a package.

## Cleanup
To clean up environment when done
```powershell
deactivate
Remove-Item -Path ./.venv/ -Recurse -Force
```