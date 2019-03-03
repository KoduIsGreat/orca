import os
test_dir = os.path.dirname(os.path.dirname(__file__))
os.path.join(test_dir, 'fixtures', 'a.py')
inline_python_inputs_mock = {
    'task': 'inline_python',
    'python': 'greeting = \'Hello {0}\'.format(name)',
    'inputs': {
        'name': '"Adam"'
    },
    'outputs': [
        'greeting'
    ]
}

inline_python_mock = {
    'task': 'inline_python',
    'python': 'greeting = \'Hello World\'',
    'outputs': [
        'greeting'
    ]
}

file_python_inputs_mock = {
    'task': 'file_python',
    'python': os.path.join(test_dir, 'fixtures', 'test_inputs.py'),
    'inputs': {
        'input_1': 10,
        'input_2': 15
    },
    'outputs': [
        'result'
    ]
}

file_python_mock = {
    'task': 'file_python',
    'python': os.path.join(test_dir, 'fixtures', 'test_no_inputs.py'),
    'outputs': [
        'result'
    ]
}
