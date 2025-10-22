# tests/test_app.py
import os
import tempfile
import pytest
import re

# Import the application module
import app as app_module
from app import app, init_db

@pytest.fixture(scope='module')
def temp_db():
    """Create a temporary sqlite db file and point app to it, then initialize."""
    fd, path = tempfile.mkstemp(suffix='.db')
    # Point module-level DB to our temp db
    original_db = getattr(app_module, 'DB', None)
    app_module.DB = path
    try:
        init_db()  # create tables and seed data
        yield path
    finally:
        # restore and cleanup
        if original_db is not None:
            app_module.DB = original_db
        os.close(fd)
        try:
            os.remove(path)
        except OSError:
            pass

@pytest.fixture
def client(temp_db):
    app.testing = True
    with app.test_client() as client:
        yield client

def test_app_exists():
    assert app is not None

def test_index_redirects_when_not_logged_in(client):
    resp = client.get('/')
    # should redirect to /login
    assert resp.status_code in (301, 302)
    assert '/login' in resp.headers['Location']

def test_login_page_get(client):
    resp = client.get('/login')
    assert resp.status_code == 200
    assert 'form' in resp.get_data(as_text=True).lower()


def test_show_api_shows_key(client):
    resp = client.get('/show_api')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert 'API_KEY=' in text
