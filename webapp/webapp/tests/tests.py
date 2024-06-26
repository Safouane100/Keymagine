import pytest
from webapp.app import create_app

@pytest.yield_fixture(scope='session')
def app():
    """
    Setup flask test app
    """
    params = {
        'DEBUG': False,
        'TESTING': True
    }

    _app = create_app(settings_override=params)

    ctx = _app.app_context()
    ctx.push()

    yield _app
    ctx.pop()