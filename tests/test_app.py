import pytest
import os
from app import create_app
from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions

@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture(scope="module")
def client(app):
    return app.test_client()

@pytest.fixture(scope="module")
def couchbase_setup(app):
    # Setup Couchbase connection
    auth = PasswordAuthenticator(
        app.config['COUCHBASE_USERNAME'],
        app.config['COUCHBASE_PASSWORD']
    )
    cluster = Cluster(app.config['COUCHBASE_CONNECTION_STRING'], ClusterOptions(auth))
    bucket = cluster.bucket(app.config['COUCHBASE_DEFAULT_BUCKET'])
    collection = bucket.scope(app.config['COUCHBASE_DEFAULT_SCOPE']).collection(app.config['COUCHBASE_DEFAULT_COLLECTION'])
    
    yield collection
    
    # Cleanup after tests
    collection.remove('test_doc')

def is_env_vars_not_configured():
    return os.getenv('COUCHBASE_CONNECTION_STRING') is None or os.getenv('COUCHBASE_USERNAME') is None or os.getenv('COUCHBASE_PASSWORD') is None or os.getenv('COUCHBASE_DEFAULT_BUCKET') is None

@pytest.mark.skipif(is_env_vars_not_configured(), reason = "Skipping as environment variables are not configured")
def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to Couchbase Flask Starter Kit" in response.data

@pytest.mark.skipif(is_env_vars_not_configured(), reason = "Skipping as environment variables are not configured")
def test_create_and_get_document(client, couchbase_setup):
    # Create a document
    create_response = client.post("/documents", json={"id": "test_doc", "content": "Test content"})
    assert create_response.status_code == 201
    assert create_response.json["id"] == "test_doc"
    assert create_response.json["content"] == "Test content"

    # Get the created document
    get_response = client.get("/documents/test_doc")
    assert get_response.status_code == 200
    assert get_response.json["id"] == "test_doc"
    assert get_response.json["content"] == "Test content"