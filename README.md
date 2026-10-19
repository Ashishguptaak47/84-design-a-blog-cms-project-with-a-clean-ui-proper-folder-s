# Minimalist Blog CMS

A modern, lightweight Blog Content Management System built with Python, FastAPI, SQLAlchemy, and clean semantic HTML/CSS.

## Features

- **Clean Public UI**: Distraction-free typography, responsive cards, tag badges, and reading time estimation.
- **Markdown Rendering**: Write posts in Markdown with automatic HTML generation.
- **Full Search & Filter**: Search by title or body, and filter by tags.
- **Interactive Reader Comments**: Instant comment submission per post.
- **Admin CMS Dashboard**: Authenticated control panel to create, edit, publish, draft, and delete posts.
- **Comment Moderation**: Admin dashboard to review and remove spam comments.
- **Zero External JS Frameworks**: Fast page loads powered by server-side Jinja2 templates and minimal CSS.

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```
   The app initializes a SQLite database with seed articles and an admin user.

3. **Access URLs**:
   - **Public Blog**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - **Admin Login**: [http://127.0.0.1:8000/admin/login](http://127.0.0.1:8000/admin/login)
     - **Username**: `admin`
     - **Password**: `admin123`

## Running Tests

```bash
pytest
```
