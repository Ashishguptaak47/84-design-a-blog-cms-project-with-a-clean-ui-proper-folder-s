import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from models import User, Post, Tag
from auth import hash_password

TEST_DB_URL = "sqlite:///./test_blog.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True, scope="module")
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    admin = User(username="admin", password_hash=hash_password("admin123"))
    db.add(admin)
    
    post = Post(
        title="Test Article",
        slug="test-article",
        excerpt="This is a test post excerpt",
        content_markdown="# Test Header\nTest body content with markdown.",
        is_published=True
    )
    tag = Tag(name="Testing", slug="testing")
    post.tags.append(tag)
    db.add(post)
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=test_engine)

def test_public_homepage():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Test Article" in response.text
    assert "#Testing" in response.text

def test_search_and_tag_filter():
    client = TestClient(app)
    # Test query filter
    res = client.get("/?q=Article")
    assert res.status_code == 200
    assert "Test Article" in res.text
    
    # Test non-matching query
    res_empty = client.get("/?q=NonExistentSubject123")
    assert res_empty.status_code == 200
    assert "No posts found" in res_empty.text

def test_post_detail_and_comment():
    client = TestClient(app)
    response = client.get("/post/test-article")
    assert response.status_code == 200
    assert "Test Header" in response.text
    
    # Submit a comment
    post_comment = client.post(
        "/post/test-article/comment",
        data={
            "author_name": "Alice",
            "author_email": "alice@example.com",
            "content": "Great article!"
        },
        follow_redirects=True
    )
    assert post_comment.status_code == 200
    assert "Alice" in post_comment.text
    assert "Great article!" in post_comment.text

def test_admin_flow():
    client = TestClient(app)
    
    # Login with bad credentials
    bad_login = client.post("/admin/login", data={"username": "admin", "password": "wrongpass"})
    assert bad_login.status_code == 400
    assert "Invalid credentials" in bad_login.text
    
    # Successful login
    login = client.post("/admin/login", data={"username": "admin", "password": "admin123"})
    assert login.status_code == 303
    session_cookie = login.cookies.get("admin_session")
    assert session_cookie is not None
    
    # Access dashboard with session
    client.cookies.set("admin_session", session_cookie)
    dash = client.get("/admin/dashboard")
    assert dash.status_code == 200
    assert "Admin Dashboard" in dash.text
    
    # Create a new post
    create_res = client.post(
        "/admin/posts/save",
        data={
            "post_id": "0",
            "title": "Automated Post Creation",
            "excerpt": "Created from pytest",
            "content_markdown": "Detailed text goes here.",
            "tags_input": "python, automated",
            "is_published": "true"
        },
        follow_redirects=True
    )
    assert create_res.status_code == 200
    assert "Automated Post Creation" in create_res.text
