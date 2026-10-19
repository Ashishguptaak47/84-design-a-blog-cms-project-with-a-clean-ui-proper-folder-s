from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
import markdown
from database import get_db
from models import Post, Tag, Comment
from auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    q: str = "",
    tag: str = "",
    db: Session = Depends(get_db)
):
    query = db.query(Post).filter(Post.is_published.is_(True))
    
    if q.strip():
        term = f"%{q.strip()}%
"
        query = query.filter(or_(Post.title.ilike(term), Post.content_markdown.ilike(term)))
    
    if tag.strip():
        query = query.join(Post.tags).filter(Tag.slug == tag.strip().lower())
        
    posts = query.order_by(Post.created_at.desc()).all()
    tags = db.query(Tag).all()
    user = get_current_user(request, db)
    
    return templates.TemplateResponse("public/index.html", {
        "request": request,
        "posts": posts,
        "tags": tags,
        "current_tag": tag,
        "search_query": q,
        "user": user
    })

@router.get("/post/{slug}", response_class=HTMLResponse)
def post_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Article not found")
        
    post.views_count += 1
    db.commit()
    
    html_content = markdown.markdown(
        post.content_markdown,
        extensions=["extra", "codehilite", "toc"]
    )
    user = get_current_user(request, db)
    
    return templates.TemplateResponse("public/post.html", {
        "request": request,
        "post": post,
        "html_content": html_content,
        "comments": post.comments,
        "user": user
    })

@router.post("/post/{slug}/comment")
def add_comment(
    slug: str,
    author_name: str = Form(...),
    author_email: str = Form(""),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Article not found")
        
    comment = Comment(
        post_id=post.id,
        author_name=author_name.strip(),
        author_email=author_email.strip(),
        content=content.strip()
    )
    db.add(comment)
    db.commit()
    return RedirectResponse(url=f"/post/{slug}#comments", status_code=303)
