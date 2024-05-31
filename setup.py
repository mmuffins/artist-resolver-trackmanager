from setuptools import setup, find_packages

# auto-generate package requirements from requirement file
with open("requirements/common.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="artist-resolver-trackmanager",
    version="1.2.13",
    author="mmuffins",
    description="Python library for the artist resolver api",
    url="https://github.com/mmuffins/artist-resolver-trackmanager",
    packages=find_packages(),
    license_files=("LICENSE",),
    install_requires=requirements,
    python_requires=">=3.12",
)
