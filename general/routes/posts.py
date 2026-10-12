from flask import Blueprint, redirect, render_template, request, url_for
import psycopg

from post_rules import validate_post
from auth_helpers import current_user, valid_csrf
from repositories.posts import create_post, delete_post, find_post, list_posts, update_post

posts_bp = Blueprint("posts", __name__)


@posts_bp.before_request
def require_login():
    if current_user() is None:
        return redirect(url_for("auth.login"), code=303)
    if request.method == "POST" and not valid_csrf():
        return render_template("error.html", title="요청을 확인할 수 없습니다", message="화면을 새로고침한 뒤 다시 시도해 주세요."), 403


@posts_bp.get("/board")
def index():
    try:
        posts = list_posts()
    except (RuntimeError, psycopg.Error):
        return render_template("error.html"), 503
    return render_template("index.html", posts=posts)


@posts_bp.get("/board/<int:post_id>")
def detail(post_id):
    try:
        post = find_post(post_id)
    except (RuntimeError, psycopg.Error):
        return render_template("error.html"), 503
    if post is None:
        return render_template(
            "error.html", title="게시글을 찾을 수 없습니다",
            message="해당 번호의 게시글이 없습니다.",
        ), 404
    return render_template("detail.html", post=post)


@posts_bp.route("/board/new", methods=["GET", "POST"])
def new_post():
    if request.method == "GET":
        return render_template("new.html", title="", body="")

    title, body, error = validate_post(
        request.form.get("title", ""), request.form.get("body", "")
    )
    if error:
        return render_template("new.html", title=title, body=body, error=error), 400

    try:
        post_id = create_post(title, body)
    except (RuntimeError, psycopg.Error):
        return render_template(
            "new.html", title=title, body=body,
            error="DB에 저장하지 못했습니다. 연결 상태를 확인해 주세요.",
        ), 503
    return redirect(url_for("posts.detail", post_id=post_id), code=303)


@posts_bp.route("/board/<int:post_id>/edit", methods=["GET", "POST"])
def edit_post(post_id):
    try:
        post = find_post(post_id)
    except (RuntimeError, psycopg.Error):
        return render_template("error.html"), 503

    if post is None:
        return render_template(
            "error.html", title="게시글을 찾을 수 없습니다",
            message="해당 번호의 게시글이 없습니다.",
        ), 404

    if request.method == "GET":
        return render_template(
            "edit.html", post_id=post_id, title=post["title"], body=post["body"]
        )

    title, body, error = validate_post(
        request.form.get("title", ""), request.form.get("body", "")
    )
    if error:
        return render_template(
            "edit.html", post_id=post_id, title=title, body=body, error=error
        ), 400

    try:
        updated = update_post(post_id, title, body)
    except (RuntimeError, psycopg.Error):
        return render_template(
            "edit.html", post_id=post_id, title=title, body=body,
            error="DB에 저장하지 못했습니다. 연결 상태를 확인해 주세요.",
        ), 503

    if updated is None:
        return render_template(
            "error.html", title="게시글을 찾을 수 없습니다",
            message="해당 번호의 게시글이 없습니다.",
        ), 404
    return redirect(url_for("posts.detail", post_id=post_id), code=303)


@posts_bp.route("/board/<int:post_id>/delete", methods=["GET", "POST"])
def confirm_delete(post_id):
    try:
        if request.method == "GET":
            post = find_post(post_id)
        else:
            post = delete_post(post_id)
    except (RuntimeError, psycopg.Error):
        return render_template("error.html"), 503

    if post is None:
        return render_template(
            "error.html", title="게시글을 찾을 수 없습니다",
            message="해당 번호의 게시글이 없습니다.",
        ), 404

    if request.method == "GET":
        return render_template("delete.html", post=post)
    return redirect(url_for("posts.index"), code=303)
