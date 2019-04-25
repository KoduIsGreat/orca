import orca.store as orca


def test_store():
    s = orca.store('test')
    w = s.workflow('simple_test', True)
    assert w.workflow is not None


def test_workflow():
    s = orca.store('test')
    w = s.workflow('simple_test', True)
    w.write('t', data={'test': 5}, meta={'meta': 'description'})

    task = w.task('t')
    assert task.data['test'] == 5
