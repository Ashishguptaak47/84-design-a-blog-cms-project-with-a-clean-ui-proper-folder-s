import re
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import Post, Tag, Comment, User
from auth import verify_password, generate_session_token, get_current_user

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if get_current_user(request, db):
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})

@router.post("/login")
def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username.strip()).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Invalid credentials. Try again."},
            status_code=400
        )
    token = generate_session_token()
    user.session_token = token
    db.commit()
    
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(key="admin_session", value=token, httponly=True, samesite="lax")
    return response

@router.get("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        user.session_token = None
        db.commit()
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_session")
    return response

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    total_posts = db.query(Post).count()
    published_posts = db.query(Post).filter(Post.is_published.is_(True)).count()
    total_comments = db.query(Comment).count()
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "user": user,
        "total_posts": total_posts,
        "published_posts": published_posts,
        "total_comments": total_comments,
        "posts": posts
    })

@router.get("/posts/new", response_class=HTMLResponse)
def new_post_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    return templates.TemplateResponse("admin/editor.html", {"request": request, "user": user, "post": None})

@router.post("/posts/save")
def save_post(
    request: Request,
    post_id: int = Form(0),
    title: str = Form(...),
    excerpt: str = Form(""),
    content_markdown: str = Form(...),
    tags_input: str = Form(""),
    is_published: bool = Form(False),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    slug_base = slugify(title)
    if not slug_base:
        slug_base = "untitled-post"
        
    if post_id:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        post.title = title.strip()
        post.excerpt = excerpt.strip() or title.strip()
        post.content_markdown = content_markdown
        post.is_published = is_published
    else:
        slug = slug_base
        count = 1
        while db.query(Post).filter(Post.slug == slug).first():
            slug = f"{slug_base}-{count}"
            count += 1
            
        post = Post(
            title=title.strip(),
            slug=slug,
            excerpt=excerpt.strip() or title.strip(),
            content_markdown=content_markdown,
            is_published=is_published
        )
        db.add(post)

    parsed_tags = []
    for t in tags_input.split(","):
        tag_name = t.strip()
        if tag_name:
            tag_slug = slugify(tag_name)
            tag_obj = db.query(Tag).filter(Tag.slug == tag_slug).first()
            if not tag_obj:
                tag_obj = Tag(name=tag_name, slug=tag_slug)
                db.add(tag_obj)
            parsed_tags.append(tag_obj)
    post.tags = parsed_tags
    db.commit()
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@router.get("/posts/{post_id}/edit", response_class=HTMLResponse)
def edit_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse("admin/editor.html", {"request": request, "user": user, "post": post})

@router.post("/posts/{post_id}/delete")
def delete_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    post = db.query(Post).filter(Post.id == post_id).first()
    if post:
        db.delete(post)
        db.commit()
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@router.get("/comments", response_class=HTMLResponse)
def manage_comments(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    comments = db.query(Comment).order_by(Comment.created_at.desc()).all()
    return templates.TemplateResponse("admin/comments.html", {"request": request, "user": user, "comments": comments})

@router.post("/comments/{comment_id}/delete")
def delete_comment(comment_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment:
        db.delete(comment)
        db.commit()
    return RedirectResponse(url="/admin/comments", status_code=303)
