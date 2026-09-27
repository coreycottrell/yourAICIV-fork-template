"""
Blog Module
============
Blog CRUD (admin) + public blog listing and post display.
Toggleable via config: modules.blog
"""

import os
import json
import uuid
from datetime import datetime
from functools import wraps

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, g, jsonify, abort, session)

blog_bp = Blueprint('blog', __name__, template_folder='../templates')


def _is_admin():
    """Admin check shared with app.py (honours session revocation)."""
    from flask import current_app
    return current_app.config['_helpers']['is_admin']()

# ── Schema extension ────────────────────────────────────────────────────

BLOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS blog_posts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    image TEXT,
    author TEXT DEFAULT '',
    tags TEXT DEFAULT '[]',
    published INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_blog_slug ON blog_posts(slug);
CREATE INDEX IF NOT EXISTS idx_blog_published ON blog_posts(published);
"""


def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _get_app_helpers():
    from flask import current_app
    return current_app.config['_helpers']


def _admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _is_admin():
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ── Public routes ───────────────────────────────────────────────────────

@blog_bp.route('/blog')
def blog_list():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    posts = db.execute(
        "SELECT * FROM blog_posts WHERE published = 1 ORDER BY created_at DESC"
    ).fetchall()
    return render_template('public/blog.html', posts=posts)


@blog_bp.route('/blog/<slug>')
def blog_post(slug):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    post = db.execute(
        "SELECT * FROM blog_posts WHERE slug = ? AND published = 1", (slug,)
    ).fetchone()
    if not post:
        abort(404)
    related = db.execute(
        "SELECT title, slug, image, excerpt FROM blog_posts "
        "WHERE published = 1 AND slug != ? ORDER BY RANDOM() LIMIT 3",
        (slug,)
    ).fetchall()
    return render_template('public/blog_post.html', post=post, related=related)


# ── Admin routes ────────────────────────────────────────────────────────

@blog_bp.route('/admin/blog')
@_admin_required
def admin_blog_list():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    posts = db.execute(
        "SELECT * FROM blog_posts ORDER BY created_at DESC"
    ).fetchall()
    return render_template('admin/blog_list.html', posts=posts)


@blog_bp.route('/admin/blog/new', methods=['GET', 'POST'])
@_admin_required
def admin_blog_new():
    if request.method == 'POST':
        helpers = _get_app_helpers()
        db = helpers['get_db']()
        post_id = str(uuid.uuid4())
        title = request.form.get('title', '').strip()
        slug = request.form.get('slug', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        content = request.form.get('content', '')
        author = request.form.get('author', '').strip()
        published = 1 if request.form.get('published') else 0
        now = now_iso()

        if not title or not slug:
            flash('Title and slug are required.', 'error')
            return render_template('admin/blog_edit.html', post=None)

        existing = db.execute(
            "SELECT id FROM blog_posts WHERE slug = ?", (slug,)
        ).fetchone()
        if existing:
            flash('A post with that slug already exists.', 'error')
            return render_template('admin/blog_edit.html', post=None)

        db.execute(
            """INSERT INTO blog_posts
               (id, title, slug, content, excerpt, author, published,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (post_id, title, slug, content, excerpt, author,
             published, now, now))
        db.commit()
        flash('Blog post created!', 'success')
        return redirect(url_for('blog.admin_blog_list'))

    return render_template('admin/blog_edit.html', post=None)


@blog_bp.route('/admin/blog/<post_id>/edit', methods=['GET', 'POST'])
@_admin_required
def admin_blog_edit(post_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    post = db.execute(
        "SELECT * FROM blog_posts WHERE id = ?", (post_id,)
    ).fetchone()
    if not post:
        abort(404)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        slug = request.form.get('slug', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        content = request.form.get('content', '')
        author = request.form.get('author', '').strip()
        published = 1 if request.form.get('published') else 0
        now = now_iso()

        if not title or not slug:
            flash('Title and slug are required.', 'error')
            return render_template('admin/blog_edit.html', post=post)

        existing = db.execute(
            "SELECT id FROM blog_posts WHERE slug = ? AND id != ?",
            (slug, post_id)
        ).fetchone()
        if existing:
            flash('A post with that slug already exists.', 'error')
            return render_template('admin/blog_edit.html', post=post)

        db.execute(
            """UPDATE blog_posts SET title=?, slug=?, content=?, excerpt=?,
               author=?, published=?, updated_at=? WHERE id=?""",
            (title, slug, content, excerpt, author, published, now, post_id))
        db.commit()
        flash('Blog post updated!', 'success')
        return redirect(url_for('blog.admin_blog_list'))

    return render_template('admin/blog_edit.html', post=post)


@blog_bp.route('/admin/blog/<post_id>/delete', methods=['POST'])
@_admin_required
def admin_blog_delete(post_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    db.execute("DELETE FROM blog_posts WHERE id = ?", (post_id,))
    db.commit()
    flash('Blog post deleted.', 'success')
    return redirect(url_for('blog.admin_blog_list'))


@blog_bp.route('/admin/blog/<post_id>/toggle-publish', methods=['POST'])
@_admin_required
def admin_blog_toggle_publish(post_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    post = db.execute(
        "SELECT * FROM blog_posts WHERE id = ?", (post_id,)
    ).fetchone()
    if not post:
        abort(404)
    new_status = 0 if post['published'] else 1
    db.execute(
        "UPDATE blog_posts SET published=?, updated_at=? WHERE id=?",
        (new_status, now_iso(), post_id))
    db.commit()
    status_text = 'published' if new_status else 'unpublished'
    flash(f'Post {status_text}.', 'success')
    return redirect(url_for('blog.admin_blog_list'))


# ── Module registration ─────────────────────────────────────────────────

def get_nav_items():
    return [
        {'label': 'Blog Posts', 'endpoint': 'blog.admin_blog_list',
         'match': 'blog.admin_blog'},
    ]


def get_metrics(db):
    published = db.execute(
        "SELECT COUNT(*) as c FROM blog_posts WHERE published = 1"
    ).fetchone()['c']
    draft = db.execute(
        "SELECT COUNT(*) as c FROM blog_posts WHERE published = 0"
    ).fetchone()['c']
    metrics = [{'label': 'Blog Posts', 'value': published}]
    if draft:
        metrics.append({'label': 'Draft Posts', 'value': draft})
    return metrics


def get_schema():
    return BLOG_SCHEMA
