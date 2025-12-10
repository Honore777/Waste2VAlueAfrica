# routes_messaging.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Conversation, Message, User, conversation_participants
from extensions import db
from datetime import datetime

messaging_bp = Blueprint("messaging", __name__, template_folder="../templates")

# List all conversations
@messaging_bp.route("/messages")
@login_required
def conversations():
    # Get conversations current_user participates in
    convs = current_user.conversations
    return render_template("conversations.html", conversations=convs)

# View a conversation and send a message
@messaging_bp.route("/messages/<int:conversation_id>", methods=["GET", "POST"])
@login_required
def view_conversation(conversation_id):
    conv = Conversation.query.get_or_404(conversation_id)
    # Check if user is participant
    if current_user not in conv.participants:
        flash("Access denied", "danger")
        return redirect(url_for("messaging.conversations"))

    if request.method == "POST":
        content = request.form.get("content")
        if content:
            msg = Message(
                conversation_id=conv.id,
                sender_id=current_user.id,
                content=content,
                is_read=False,
                created_at=datetime.utcnow(),
            )
            db.session.add(msg)
            db.session.commit()
            flash("Message sent", "success")
            return redirect(url_for("messaging.view_conversation", conversation_id=conv.id))

    # Mark unread messages as read for current user
    for msg in conv.messages:
        if msg.sender_id != current_user.id and not msg.is_read:
            msg.is_read = True
    db.session.commit()

    return render_template("view_conversation.html", conversation=conv)

# Start new conversation
@messaging_bp.route("/messages/new/<int:user_id>", methods=["GET", "POST"])
@login_required
def new_conversation(user_id):
    other_user = User.query.get_or_404(user_id)
    # Check if conversation exists
    conv = (
        Conversation.query
        .join(conversation_participants)
        .filter(conversation_participants.c.user_id.in_([current_user.id, other_user.id]))
        .first()
    )
    if not conv:
        conv = Conversation()
        conv.participants.append(current_user)
        conv.participants.append(other_user)
        db.session.add(conv)
        db.session.commit()
    return redirect(url_for("messaging.view_conversation", conversation_id=conv.id))
