import importlib

def get_client():
    m = importlib.import_module('backend.app')
    return m.app.test_client()

def test_index_served():
    c = get_client()
    r = c.get('/')
    assert r.status_code in (200, 304)

def test_static_assets_served():
    c = get_client()
    r1 = c.get('/styles.css')
    r2 = c.get('/app.js')
    assert r1.status_code == 200
    assert r2.status_code == 200

def test_torch_compat_endpoint():
    c = get_client()
    r = c.get('/api/system/check')
    assert r.status_code == 200
    data = r.get_json()
    assert 'torch' in data
    assert 'installed' in data['torch']
    assert 'compatible' in data['torch']