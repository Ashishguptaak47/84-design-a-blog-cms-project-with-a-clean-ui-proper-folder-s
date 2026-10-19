from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import engine, Base, SessionLocal
from models import User, Post, Tag
from auth import hash_password
from routers import public, admin

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Ensure admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                password_hash=hash_password("admin123")
            )
            db.add(admin_user)
            db.commit()

        # Seed a welcome post if none exists
        if db.query(Post).count() == 0:
            tag_py = Tag(name="Python", slug="python")
            tag_fastapi = Tag(name="FastAPI", slug="fastapi")
            db.add_all([tag_py, tag_fastapi])
            db.flush()

            first_post = Post(
                title="Welcome to your new Blog CMS",
                slug="welcome-to-your-new-blog-cms",
                excerpt="A complete overview of features and architecture packed into this clean Python Blog CMS.",
                content_markdown="""# Welcome to your modern Blog CMS

This application is built with **FastAPI**, **SQLAlchemy**, and a clean server-rendered **Jinja2** interface.

### Key Highlights
- **Zero complex build steps**: No Webpack, Vite, or Node.js required.
- **Full Markdown support**: Write code blocks, headers, and bullet lists effortlessly.
- **Built-in Admin Dashboard**: Create, draft, and modify your posts at `/admin`.
- **Reader comments**: Visitors can discuss articles instantly.

```python
def greet_reader(name: str) -> str:
    return f"Enjoy reading, {name}!"
```

Login to the admin area using username `admin` and password `admin123` to start publishing!
""",
                is_published=True,
                views_count=12
            )
            first_post.tags.extend([tag_py, tag_fastapi])
            db.add(first_post)
            db.commit()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_database()
    yield

app = FastAPI(title="Modern Blog CMS", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(public.router)
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main.py:app", host="127.0.0.1", port=8000, reload=True)
