# Introduction
Orca is a workflow management solution similar in nature to [Airflow]() and [Luigi](),
but specifically for microservices and is built with data streaming in mind. It attempts to provide
a sensible way to define a workflow through a combination of yaml and python.  

Read the full docs [here]()
# orca.yml 
Below is the simplest example of a orca workflow definition
```yaml
apiversion: orca/'1.0'
version: '0.1'
job:
  # bash inline task
  - task: echo
    bash: echo "Hello world!"

```
This workflow introduces two concepts a `Job` and `Tasks`.
A `task` is an action that is taken as a step of the workflow, in this case its printing hello world.
A `job` defines an array structure that describes the dag (*Directed Acyclic Graph*) of the workflow.
Elements in the job array can be either a `task` or a `control structure` the above is a task. 

An example of a control structure is below.

```yaml
apiversion: orca/'1.0'
version: '0.1'
var:
  value: 5
job:
  - task: echo
    bash: echo "Hello world!"
  - if var.value > 5:
    - task: print value
      python: print(value)
  - task: run last
    bash: echo "done"
```

# Usage
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
# Contributing
To contribute 

## Prerequisites 
1. pipenv: ` pip install pipenv`

## Quickstart

1. clone the repo 'git clone https://github.com/KoduIsGreat/orca.git'
2. install python dependencies `pipenv install`
