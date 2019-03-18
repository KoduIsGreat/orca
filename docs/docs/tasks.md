# Tasks
Tasks are an abstraction that represent some action to take at workflow execution time. Some examples are:

* call a service
* insert data into a database
* do some 


## Task Types
There are four types of tasks currently supported: 

* python
* bash
* csip
* http

## Task Structure
A task has a common list of properties and structure amongst all the different types:

<table>
    <tr>
        <th> Property</th>
        <th> Description</th>
        <th> Type </th>
        <th> Required </th>
    </tr>
    <tr> 
        <td>task</td>
        <td>The task name, must be unique and a valid identifier (i.e. no spaces) </td>
        <td> string</td>
        <td>Y </td>        
    </tr>
    <tr> 
        <td>python</td>
        <td> Either an inline python string, or a path to a python file</td>
        <td> string</td>
        <td> At least one kind is required </td>        
    </tr>
    <tr> 
        <td>bash</td>
        <td> Either an inline bash string, or a path to a shell</td>
        <td> string</td>
        <td> At least one kind is required </td>        
    </tr>
        <tr> 
        <td>http</td>
        <td> a http url to make a request against, can be to a rest api, or just a normal website</td>
        <td> string</td>
        <td> At least one kind is required </td>        
    </tr>
    <tr> 
        <td>csip</td>
        <td> A url to a csip service</td>
        <td> string</td>
        <td> At least one kind is required </td>        
    </tr>
    <tr> 
        <td>inputs</td>
        <td> a object describing inputs to call the task with, the values can reference from other tasks or workflow variables</td>
        <td> object</td>
        <td>N </td>        
    </tr>
    <tr> 
        <td>outputs</td>
        <td> a list of outputs to capture from the tasks execution </td>
        <td> string array</td>
        <td>N </td>        
    </tr>
</table>


# Referencing Task data later in the workflow
Each orca task once completed persists its state for reuse later.
```yaml
apiVersion: '1.0'
version: 0.1
name: referencing task outputs
job:
    - task: get_today
      python: |
        import datetime
        today = datetime.datetime.utcnow()
      outputs:
        - today
    - task: print_today
      python: print(today)
      inputs: 
        today: task.get_today.today

```
In this example we are referencing the output specified by the `get_today` task by the string `task.get_today.today`
Task state is namespaced under the `task.` directive and each tasks data is namespaced further under the task name.

# Python Task
A python task is flexible and can be used in a number of different ways to suit different needs, these are:
* inline python
* external script
* external module with function calls


### Inline python example
This is the example we are familiar with at this point:

```yaml
task: get_today
python: |
    import datetime
    today = datetime.datetime.utcnow()
outputs:
    - today

```
Here we are just writing our python inline to the task, this can be useful for very simple things but for more complex 
tasks, its recommended to either use a external script or a module to complete your python needs. Here we can retrieve
the `today` variable for use later in our workflow, just like we would be able to if we were writing all of this in 
a normal python script


### External python script example
External scripts are useful for when you want to perform some action that does not have any inputs (right now external 
scripts do not support injecting inputs, but we are actively working to change this)
given the python file 
`scrape.py`
```python
import bs4
import requests
import datetime
today = datetime.datetime.utcnow()
forecast = 0
file = 'nwm.t{0}z.short_range.channel_rt'
url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/prod/nwm.{0}/short_range/'
formatted_url = url.format(today.strftime("%Y%m%d"))
html = requests.get(formatted_url, headers={'Content-Type': 'text/plain'}).content
soup = bs4.BeautifulSoup(html, 'html.parser')
a_tags = soup.find_all('a')
fmt_file = file.format(str(forecast).zfill(2))
find_file = lambda f: f.get_text().startswith(fmt_file)
file_exists = len ( list ( filter ( find_file, a_tags ) ) ) > 0
print('file {0} is present ?  = {1}'.format(fmt_file, file_exists))
```

```yaml
apiVersion: '1.0'
version: '0.1'
name: 'scrape nomads for netcdf file'
job:
  - task: scrape
    python: ./scrape.py
    outputs:
      - file_exists
  - if: task.scrape.file_exists
    do:
      - ...

```


### External python modules
Another way to use the python task is to reference a python module and directly access functions in the module. 
To do this you must utilize a special configuration for the python task using the config object.

The python config object has the following properties available
<table>
    <tr>
        <th> property </th>
        <th> description </th>
        <th> type </th>
        <th> required </th>
    </tr>
    <tr>
        <td> callable </td>
        <td> The python function in the module to call</td>
        <td> string </td>
        <td> Y </td>
    </tr>
    <tr>
        <td> returns </td>
        <td> A name to assign the return value of the callable</td>
        <td> string </td>
        <td> Y </td>
    </tr>
</table>

Lets rewrite the example above to a module, and see how orca can utilize it
`scrape.py`
```python

import bs4
import requests

def get_html(url, today):
    formatted_url = url.format(today.strftime("%Y%m%d"))
    return requests.get(formatted_url, headers={'Content-Type': 'text/plain'}).content
    
def scrape_html(url, today, forecast, file):
    html = get_html(url, today)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    a_tags = soup.find_all('a')
    fmt_file = file.format(str(forecast).zfill(2))
    find_file = lambda f: f.get_text().startswith(fmt_file)
    file_exists = len ( list ( filter ( find_file, a_tags ) ) ) > 0
    print('file {0} is present ?  = {1}'.format(fmt_file, file_exists))
    return file_exists

``` 
```yaml
apiVersion: '1.0'
version: '0.1'
name: 'check if netcdf file exists for current hour'
var:
  forecast: 0
  nomadsUrl: 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/prod/nwm.{0}/short_range/'
  fileName: 'nwm.t{0}z.short_range.channel_rt'
job:
    - task: get_today
      python: |
        import datetime
        today = datetime.datetime.utcnow()
    - task: scrape
      python: ./scrape.py
      config:
        callable: scrape_html
        returns: current_file_exists 
      inputs:
        url: var.nomadsUrl
        today: task.get_today.today
        forecast: var.forecast
        file: var.fileName
      outputs:
        - current_file_exists
    - if: current_file_exists
      do:
        - .....

```
In this example we introduced a config object that specifies which function to call, and maps the inputs defined on the task
to the inputs defined in the callable function. Additionally we specified a name for the return value, this name can be 
any valid identifier. If the function returns nothing then returns is not required