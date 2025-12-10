from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Notification
from extensions import db

notifications_bp = Blueprint("notifications", __name__, template_folder="../templates")

# List all notifications
@notifications_bp.route("/notifications")
@login_required
def list_notifications():
    notes = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()

    return render_template("notifications.html", notifications=notes)


# Mark one notification as read
@notifications_bp.route("/notifications/read/<int:note_id>")
@login_required
def read_notification(note_id):
    note = Notification.query.get_or_404(note_id)

    if note.user_id != current_user.id:
        flash("Unauthorized action", "danger")
        return redirect(url_for("notifications.list_notifications"))

    note.is_read = True
    db.session.commit()

    if note.link:
        return redirect(note.link)

    return redirect(url_for("notifications.list_notifications"))


# Mark all as read
@notifications_bp.route("/notifications/read-all")
@login_required
def read_all_notifications():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({ "is_read": True })
    db.session.commit()

    flash("All notifications marked as read", "success")
    return redirect(url_for("notifications.list_notifications"))
