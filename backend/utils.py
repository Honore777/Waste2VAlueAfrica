# utils.py
from models import Notification, NotificationTypeEnum
from extensions import db, socketio

def create_notification(user_id, message, link=None, notif_type="info", icon=None):
    """Create a notification and send a real-time update via Socket.IO."""

    # Convert string into enum safely
    if isinstance(notif_type, str):
        try:
            notif_type = NotificationTypeEnum(notif_type)
        except ValueError:
            notif_type = NotificationTypeEnum.info  # fallback

    notification = Notification(
        user_id=user_id,
        message=message,
        link=link,
        type=notif_type,
        icon=icon
    )

    db.session.add(notification)
    db.session.commit()

    # Emit socket event to that specific user room
    socketio.emit(
        "new_notification",
        {
            "id": notification.id,
            "message": notification.message,
            "link": notification.link,
            "type": notification.type.value,
            "icon": notification.icon,
            "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M")
        },
        room=f"user_{user_id}"
    )

    return notification
