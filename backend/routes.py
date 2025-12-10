from flask import Blueprint, render_template

from flask_login import login_required , current_user

from sqlalchemy import desc
from extensions import db
from models import (
    Listing,
    Post,
    Message,
    Conversation,
    PostUpvote,
    conversation_participants,
)

dashboard_bp= Blueprint('dashboard',__name__)



@dashboard_bp.route('/dashboard', endpoint='main_dashboard')
@login_required
def dashboard():
    user_id = current_user.id

    # Counts
    listings_count = Listing.query.filter_by(owner_id=user_id, is_active=True).count()
    posts_count = Post.query.filter_by(user_id=user_id, is_deleted=False).count()

    # Upvotes on user's posts:
    # join PostUpvote -> Post and count where Post.user_id == user_id
    upvotes_count = (
        db.session.query(PostUpvote)
        .join(Post, PostUpvote.post_id == Post.id)
        .filter(Post.user_id == user_id)
        .count()
    )

    # Unread messages for user:
    # Messages belonging to conversations the user participates in and is_read==False
    unread_messages_count = (
        db.session.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .join(conversation_participants, conversation_participants.c.conversation_id == Conversation.id)
        .filter(conversation_participants.c.user_id == user_id, Message.is_read == False)
        .count()
    )

    # Recent items (show latest 3)
    recent_listings = (
        Listing.query.filter_by(owner_id=user_id)
        .order_by(desc(Listing.created_at))
        .limit(3)
        .all()
    )

    recent_posts = (
        Post.query.filter_by(user_id=user_id, is_deleted=False)
        .order_by(desc(Post.created_at))
        .limit(3)
        .all()
    )

    # Recent messages (latest 5 messages across user's conversations)
    recent_messages = (
        db.session.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .join(conversation_participants, conversation_participants.c.conversation_id == Conversation.id)
        .filter(conversation_participants.c.user_id == user_id)
        .order_by(desc(Message.created_at))
        .limit(5)
        .all()
    )

    # Render template with context
    return render_template(
        "dashboard.html",
        user=current_user,
        listings_count=listings_count,
        posts_count=posts_count,
        upvotes_count=upvotes_count,
        unread_messages_count=unread_messages_count,
        recent_listings=recent_listings,
        recent_posts=recent_posts,
        recent_messages=recent_messages,
    )