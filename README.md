# Introduction
Orca is a workflow management solution similar in nature to [Airflow]() and [Luigi](),
but specifically for microservices and is built with data streaming in mind. It attempts to provide
a sensible way to define a workflow in yaml. 

Read the full docs [here]()
# Contributing
Review the following for contributing to this repository.

## Prerequisites 
1. pipenv: ` pip install pipenv`

## Quickstart

1. clone the repo 'git clone https://github.com/KoduIsGreat/orca.git'
2. install python dependencies `pipenv install`


## setup linting commit hooks
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

Run tests
```bash
pipenv run pytest tests
```

or if you already have pytests installed
```bash
pytest tests
```

build package
```bash
python setup.py install
python setup.py sdist
```

install package locally
```bash
pip install dist/orca-<version>.tar.gz
```

