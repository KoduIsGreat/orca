# Orca 0.4.0

Orca is a workflow management solution similar in nature to [Airflow]() and [Luigi](),
but specifically for microservices and is built with data streaming in mind. It attempts to provide
a sensible way to define a data driven model workflow through a combination of yaml and python.  

## Installation
The easiest way to install orca is from pip
```bash
pip install orca
```
To verify that the install succeeded run the version command
```bash
orca version
```

## Quickstart

To invoke the CLI after installing one just invokes orca:
```
$ orca
Usage: orca [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbosity LVL  Either CRITICAL, ERROR, WARNING, INFO or DEBUG
  --help               Show this message and exit.

Commands:
  run       Run an orca workflow.
  todot     Create a graphviz dot file from an orca workflow.
  validate  Validate an orca workflow.
  version   Print the orca version.

```