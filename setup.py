from setuptools import setup, find_packages


with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

setup(
    name="gadi",
    version="0.1.0",
    description="Zugänglichere Versionen der Daten von gesetze-im-internet.de",
    long_description=readme,
    author="Niko Felger",
    author_email="niko.felger@gmail.com",
    url="https://github.com/nfelger/gesetze-aus-dem-internet",
    license=license,
    packages=find_packages(exclude=("tests", "docs", "example_json")),
)
