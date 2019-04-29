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

def test_create_snapshot():
    s = orca.store('test')
    w = s.workflow('snapshot_test', True)
    w.write('t', data={'test': 5}, meta={'meta': 'description'}, overwrite=True)
    w.create_snapshot()
    w.write('t', data={'test': 6}, meta={'meta': 'description'}, overwrite=True)
    snapshot = w.list_snapshots()[0]
    snap_data = w.task('t', snapshot=snapshot).data
    task_data = w.task('t').data
    assert snap_data['test'] != task_data['test']
