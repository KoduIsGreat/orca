# Orca 0.5.0

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
Create a file called orca.yml
```yaml
apiversion: orca/'1.0'
version: 0.1
name: 'quickstart example'
job:
    - task: hello_world
      print: print('Hello World!')


```
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
Execute the hello world example
```bash
$ orca run orca.yml
Hello World!
```

# Concepts
This section describes some core concepts to understand how to use orca

## What is a Orca Workflow ?
An orca workflow, is a yaml document describing the actions that make up the workflow.
Here is a simple "hello world" example
```yaml
apiversion: orca/'1.0'
name: 'hello-workflow'
version: 0.1
job:
  - task: hello
    python: print('Hello World!')

```
The document above describes a `Job` object that is an array describing the `tasks` to perform as steps in the workflow.
A task is some action that can be taken during the execution of the workflow, in this instance we are using
whats called a `python task`. There are a number of available tasks available for use in your workflows, They are:
* python
* bash
* http
* csip

You can read more about tasks at their [dedicated page](tasks.md).
Orca also has the ability to define `variables` for reuse throughout the workflow. These variables can be reused amongst
tasks and passed in as inputs. variables, are namespaced under the var yaml object, and any reference to a variable must
being with `var.`
**A side note about strings: as you may notice in the example below, for most of our yaml document we have not been
quoting our strings the one exception to  this rule is in the var section of the document. i.e if the variable is a string
you must quote it!**
```yaml
apiversion: orca/'1.0'
version: 0.1
var:
  name: 'Susie'
job:
  - task: hello
    python: |
      msg = 'Hello {0}'.format(person_to_greet)
      print(msg)
    inputs:
      person_to_greet: var.name
```
Another component of an orca workflow are `control structures`. Control structures allow for
control flow type operations to be performed on a subset of tasks by writing yaml describing the nature of the control
flow.
There are four kinds of control structures in orca.

* if control
* for control
* switch control
* fork control
----------------
## If Structures
```yaml
#Example of a if condition object
if: 5 > 0
do:
  - task: cond_task_1
    python: print('hello condition!')
```
`if` structures contain two required top level properties `if` which describes the condition and `do` 
the list of `tasks` to execute.
---------
## For structures
```yaml
for: i, range(0,10)
do:
  - task: print_i
    python: print(counter)
    inputs:
      counter: i

```
`for` control structures also contain two required properties they are : `for` and `do`.
The value of the `for` property must be defined as `var,expression`
-----
## Switch structures
```yaml
switch: 1
1:
  - task: start5_1
    python: var.afile
  - task: start5_2
    python: var.afile
2:
  - task: start1_1
    python: var.afile
  - task: start1_2
    python: var.afile
default:
  - task: default
    python: var.afile
```
`switch` statements require a `switch` and `default` properties. The `default` properties is the set of tasks to run given that
the switch condition does not resolve to a case. The `switch` property value can be be a variable thats evaluated at the time the switch block
is reached.

## Fork structures
```yaml
fork:     
   # first group of tasks
   -  - task: start1
        python: var.afile
      - task: start4
        python: var.afile
     # second group      
   -  - task: start2
        python: var.afile
     # third group     
   -  - task: start3
        python: var.afile

```

A Fork structure is an array, of `task` lists. each list in the topmost array is executed in parallel.
# Commands
Orca currently provides a concise set of commands for running workflows.

## run
The run command executes the workflow defined in the yaml configuration file.
Options include ledgers, to publish the results of each task in the workflow too, options include a json, mongo or kafka ledger
```bash
Usage: orca run [OPTIONS] FILE [ARGS]...

  Run an orca workflow.

Options:
  --ledger-json PATH   file ledger.
  --ledger-mongo TEXT  mongodb ledger, TEXT format "<host[:port]>/<db>/<col>".
  --ledger-kafka TEXT  kafka ledger, TEXT format "<host[:port]>/topic".
  --help               Show this message and exit.
```
## todot
Converts the yaml definition into a graphviz dotfile
## version
Prints the current orca version
```bash
$ orca version
0.4.0
```