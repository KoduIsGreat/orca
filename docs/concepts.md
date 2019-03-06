# Concepts


## What is a Orca Workflow ?
An orca workflow, is a yaml document describing the actions that make up the workflow.
Heres a simple "hello world"
```yaml
apiversion: orca/'1.0'

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

You can read more about tasks at their [dedicated page]().
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
control flow type operations to be performed by writing yaml describing the nature of the control
flow. A simple example:

```yaml
apiversion: orca/'1.0'
version: 0.1
job:
  - task: hello
    python: print(

```