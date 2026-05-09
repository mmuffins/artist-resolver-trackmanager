# Artist Relation Resolver Frontend
A gui application for the artist relation resolver api

## Installing dependencies
Handled by uv, it is not needed to actively install dependencies

Check for outdated libraries:
```bash
$ uv tree --outdated --depth 1
$ uv add 'httpx~=0.28.0'
#or 
$ uv add --dev 'httpx~=0.28.0'
```
uv automatically upgrades versions matching the constraint, and will do so silently, they will not be listed in the outdated packages. `uv tree --outdated` only highlights packages that need to be upgraded manually.