# Introduction
[![Build Status](https://dev.azure.com/org-ehs/orca/_apis/build/status/KoduIsGreat.orca?branchName=master)](https://dev.azure.com/org-ehs/orca/_build/latest?definitionId=18&branchName=master)

Orca is a workflow management solution similar in nature to [Airflow]() and [Luigi](),
but specifically for microservices and is built with data streaming in mind. It attempts to provide
a sensible way to define a workflow in yaml. 

Read the full docs [here](https://koduisgreat.github.io/orca/)
# Contributing
Review the following for contributing to this repository.

## Prerequisites 
1. pipenv: ` pip install pipenv`
2. flake8: `pip install flake8`
3. black: `pip install black`

## Quickstart

1. clone the repo 'git clone https://github.com/KoduIsGreat/orca.git'
2. install python dependencies `pipenv install`


## Development Setup
```bash
pipenv run flake8 --install-hook git
```
or if you have flake8 installed
```bash
flake8 --install-hook git
```

Set the linter to strict in git config
```bash
git config --bool flake8.strict true
```

lint and format 
```bash
flake8 . && black .
```

Run tests
```bash
pipenv run pytest tests
```

build package
```bash
python setup.py install
python setup.py sdist
```

install package locally
```bash
pip install dist/amanzi.orca-<version>.tar.gz
```




## Incrementing package versions
major.minor.patch-release{build}

To increment the package version by a build number use
`bumpversion build`

To increment the package version by a minor version / 
`bumpversion minor` or `bumpversion patch`

To generate a release version run 
`bumpversion release`
