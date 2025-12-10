from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user

from backend.forms import PostForm
from backend.models import Post, PostUpvote, Notification, NotificationTypeEnum, Comment
from backend.extensions import db

from datetime import datetime
import secrets
import os


from werkzeug.utils import secure_filename

community_bp = Blueprint("community", __name__, template_folder="../templates")

# List all posts
@community_bp.route("/community")
def community():
    
    posts = Post.query.filter_by(is_deleted=False).order_by(Post.created_at.desc()).all()
    return render_template("community.html", posts=posts)


# Ask a question / share idea
@community_bp.route("/community/ask", methods=["GET", "POST"])
@login_required
def ask_post():
    form = PostForm()
    if form.validate_on_submit():


        filename= None
        if form.image.data:
            random_hex= secrets.token_hex(8)
            _, ext= os.path.splitext(secure_filename(form.image.data.filename))
            filename= random_hex+ ext
            filepath = os.path.join("static/uploads/posts", filename)
            form.image.data.save(filepath)



        post = Post(
            title=form.title.data,
            content=form.content.data,
            image= filename,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
            is_deleted=False
        )
        db.session.add(post)
        db.session.commit()
        flash("Your post has been published!", "success")
        return redirect(url_for("community.view_post", slug=post.slug))
    return render_template("ask_post.html", form=form)


@community_bp.route("/community/<slug>")
def view_post(slug):
    post = Post.query.filter_by(slug=slug, is_deleted=False).first_or_404()

    comments= post.comments.filter_by(parent_id=None, is_deleted=False).order_by(Comment.created_at.asc()).all()
    return render_template("view_post.html", post=post, comments= comments)




@community_bp.route("/community/upvote/<int:post_id>", methods=["POST"])
@login_required
def upvote_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Check if user already upvoted
    existing_upvote = PostUpvote.query.filter_by(post_id=post.id, user_id=current_user.id).first()

    if existing_upvote:
        # User already upvoted → remove upvote (toggle)
        db.session.delete(existing_upvote)
        action = "removed"
    else:
        # Add a new upvote
        new_upvote = PostUpvote(post_id=post.id, user_id=current_user.id)
        db.session.add(new_upvote)
        action = "added"

        # Optional: Create a notification for the post author
        if post.author and post.author.id != current_user.id:
            # Assuming Notification and NotificationTypeEnum are already imported at the top
            notification = Notification(
                user_id=post.author.id,
                message=f"{current_user.username} upvoted your post '{post.title}'",
                type=NotificationTypeEnum.info,
                link=url_for('community.view_post', slug=post.slug)
            )
            db.session.add(notification)

    # Commit all changes (upvote/downvote and notification) at once
    db.session.commit()

    # Get the final count after the transaction
    total_upvotes= PostUpvote.query.filter_by(post_id=post.id).count()

    return jsonify({
        "status": "success",
        "action": action,
        "total_upvotes": total_upvotes
    }), 200

@community_bp.route('/community/comment/<slug>', methods=['POST'])

@login_required
def post_comment(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    content = request.form.get("content")
    parent_id = request.form.get("parent_id")  # optional for replies

    if not content or content.strip() == "":
        return jsonify({"status": "error", "message": "Comment cannot be empty"}), 400

    comment = Comment(
        post_id=post.id,
        user_id=current_user.id,
        content=content.strip(),
        parent_id=parent_id if parent_id else None
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "status": "success",
        "comment": {
            "id": comment.id,
            "author": current_user.username,
            "content": comment.content,
            "parent_id": comment.parent_id
        },
        "total_comments": post.comments.count()
    })