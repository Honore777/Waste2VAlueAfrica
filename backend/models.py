# models.py
from datetime import datetime
import enum
from enum import Enum
import secrets
from flask_login import UserMixin
from slugify import slugify
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import Index, Table, UniqueConstraint
from backend.extensions import db  # your flask-sqlalchemy instance


# ----------------------------
# Enums
# ----------------------------
class RoleEnum(str, enum.Enum):
    producer = "producer"
    recycler = "recycler"
    consumer = "consumer"
    expert = "expert"
    admin = "admin"


class ListingTypeEnum(str, enum.Enum):
    waste = "waste"
    recycled = "recycled"


# ----------------------------
# Mixins
# ----------------------------
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SoftDeleteMixin:
    is_deleted = db.Column(db.Boolean, default=False, index=True)


# ----------------------------
# User
# ----------------------------
# ---------- CLEANED User model (replace existing User class) ----------
class User(db.Model, UserMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    _password = db.Column("password", db.String(255), nullable=False)

    # Role and verification
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.consumer, index=True)
    is_verified = db.Column(db.Boolean, default=False, index=True)

    # Profile fields (single source of truth)
    full_name = db.Column(db.String(120), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=True, index=True)
    avatar_url = db.Column(db.String(512), nullable=True, default="/static/images/default-avatar.png")

    # Social links
    twitter = db.Column(db.String(255), nullable=True)
    instagram = db.Column(db.String(255), nullable=True)
    github = db.Column(db.String(255), nullable=True)

    # Last seen / timestamps provided by TimestampMixin
    # (created_at and updated_at come from TimestampMixin already)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    avatar_url_filename = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)

    # Reverse relationships
    listings = db.relationship(
        "Listing",
        back_populates="owner",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    posts = db.relationship(
        "Post",
        back_populates="author",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    comments = db.relationship("Comment", back_populates="author", lazy="dynamic", cascade="all, delete-orphan")
    post_upvotes = db.relationship("PostUpvote", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    sent_messages = db.relationship("Message", back_populates="sender", lazy="dynamic", cascade="all, delete-orphan")

    conversations = db.relationship(
        "Conversation",
        secondary="conversation_participants",
        back_populates="participants",
        lazy="subquery"
    )

    # --- Convenience properties ---
    @property
    def total_messages(self):
        # cheaper alternative: count messages across conversations without loading all messages
        return sum(conv.messages.count() if hasattr(conv.messages, 'count') else len(conv.messages) for conv in self.conversations)

    @property
    def total_upvotes_received(self):
        # sum upvotes on posts (posts are lazy='dynamic')
        return sum(p.upvotes.count() for p in self.posts)

    @property
    def total_posts(self):
        return self.posts.count()

    @property
    def total_listings(self):
        return self.listings.count()

    @property
    def profile_completion(self):
        fields = [
            self.full_name,
            self.bio,
            self.location,
            self.avatar_url,
            self.twitter,
            self.instagram,
            self.github,
        ]
        filled = sum(
    1 for f in fields 
    if f and str(f).strip() != "" and f != "/static/images/default-avatar.png"
)
        total = len(fields)
        return int(filled / total * 100) if total else 0

    # --- Password helpers ---
    def set_password(self, plaintext: str):
        self._password = generate_password_hash(plaintext)

    def check_password(self, plaintext: str) -> bool:
        return check_password_hash(self._password, plaintext)

    # --- Role helpers ---
    def is_producer(self) -> bool:
        return self.role == RoleEnum.producer

    def is_recycler(self) -> bool:
        return self.role == RoleEnum.recycler

    def is_consumer(self) -> bool:
        return self.role == RoleEnum.consumer

    def is_expert(self) -> bool:
        return self.role == RoleEnum.expert

    def is_admin(self) -> bool:
        return self.role == RoleEnum.admin

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
# --------------------------------------------------------------------


# ---------- FIX wishlist table definition (replace existing wishlist) ----------
wishlist = db.Table(
    "wishlist",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("listing_id", db.Integer, db.ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True),
    db.Column("created_at", db.DateTime, default=datetime.utcnow),
)
# --------------------------------------------------------------------

# ----------------------------
# Category
# ----------------------------
class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with listings
    listings = db.relationship("Listing", back_populates="category", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category {self.name}>"


Index("ix_category_slug_active", Category.slug, Category.is_active)


# ----------------------------
# Listing
# ----------------------------
class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    slug = db.Column(db.String(300), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    listing_type = db.Column(db.Enum(ListingTypeEnum), nullable=False, index=True)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    category = db.relationship("Category", back_populates="listings", lazy=True)

    quantity = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20), default="kg")
    price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), default="RWF")
    location = db.Column(db.String(200), nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner = db.relationship("User", back_populates="listings", lazy=True)

    views = db.Column(db.Integer, default=0)
    contact_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = db.relationship("ListingImage", back_populates="listing", lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not getattr(self, "slug", None) and getattr(self, "title", None):
            base = slugify(self.title)[:200]
            self.slug = f"{base}-{secrets.token_hex(4)}"

    def __repr__(self):
        return f"<Listing {self.title} ({self.listing_type})>"


Index("ix_listing_type_active", Listing.listing_type, Listing.is_active)
Index("ix_listing_owner_category", Listing.owner_id, Listing.category_id)


# ----------------------------
# Post / Tag many-to-many table
# ----------------------------
post_tags = Table(
    "post_tags",
    db.metadata,
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    content=db.Column(db.Text, nullable=False)
    image= db.Column(db.String(255), nullable= True)
    slug = db.Column(db.String(300), nullable=False, unique=True, index=True) 
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    author = db.relationship("User", back_populates="posts", lazy=True, foreign_keys=[user_id])

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    pinned = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)

    tags = db.relationship("Tag", secondary=post_tags, back_populates="posts", lazy="subquery")

    comments = db.relationship("Comment", back_populates="post",lazy='dynamic', cascade="all, delete-orphan")
    upvotes = db.relationship("PostUpvote", back_populates="post",lazy='dynamic', cascade="all, delete-orphan")

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        if not getattr(self, 'slug', None) and getattr(self,'title', None):
            base= slugify(self.title)[:200]
            self.slug=f"{base}-{secrets.token_hex(3)}"


    def __repr__(self):
        author_name = self.author.username if self.author else "Unknown"
        return f"<Post {self.title} by {author_name}>"


Index("ix_posts_pinned_deleted", Post.pinned, Post.is_deleted)


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True, index=True)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)

    posts = db.relationship("Post", secondary=post_tags, back_populates="tags", lazy="subquery")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not getattr(self, "slug", None) and getattr(self, "name", None):
            self.slug = slugify(self.name)

    def __repr__(self):
        return f"<Tag {self.name}>"


# ----------------------------
# Comments
# ----------------------------
class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)

    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)

    post = db.relationship("Post", back_populates="comments")
    author = db.relationship("User", back_populates="comments", lazy=True, foreign_keys=[user_id])

    replies = db.relationship(
        "Comment",
        backref=db.backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        author_name = self.author.username if self.author else "Unknown"
        return f"<Comment by {author_name} on Post {self.post_id}>"


# ----------------------------
# PostUpvote
# ----------------------------
class PostUpvote(db.Model):
    __tablename__ = "post_upvotes"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    post = db.relationship("Post", back_populates="upvotes")
    user = db.relationship("User", back_populates="post_upvotes", lazy=True)

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_user_upvote"),
    )

    def __repr__(self):
        return f"<PostUpvote User {self.user_id} -> Post {self.post_id}>"


# ----------------------------
# ListingImage
# ----------------------------
class ListingImage(db.Model):
    __tablename__ = "listing_images"

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = db.Column(db.String(512), nullable=False)
    alt_text = db.Column(db.String(255), nullable=True)
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    listing = db.relationship("Listing", back_populates="images", lazy=True)

    def __repr__(self):
        return f"<ListingImage {self.image_url} for Listing {self.listing_id}>"


# ----------------------------
# Conversations / Messages
# ----------------------------
conversation_participants = db.Table(
    "conversation_participants",
    db.Column("conversation_id", db.Integer, db.ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    is_group = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    participants = db.relationship(
        "User",
        secondary=conversation_participants,
        back_populates="conversations",
        lazy="subquery"
    )

    messages = db.relationship("Message", back_populates="conversation", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<Conversation {self.id} Group:{self.is_group}>"


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    conversation = db.relationship("Conversation", back_populates="messages")
    sender = db.relationship("User", back_populates="sent_messages", lazy=True, foreign_keys=[sender_id])

    def __repr__(self):
        return f"<Message {self.id} from {self.sender_id}>"


# ----------------------------
# Notifications
# ----------------------------
class NotificationTypeEnum(str, Enum):
    info = "info"
    success = "success"
    warning = "warning"
    alert = "alert"
    message = "message"

# ----------------------------
# Notification Model
# ----------------------------
class Notification(db.Model):
    __tablename__ = "notifications"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign key to the user
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Notification content
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(512), nullable=True)  # Optional link when clicked

    # Status and type
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    type = db.Column(db.Enum(NotificationTypeEnum), default=NotificationTypeEnum.info, nullable=False)
    icon = db.Column(db.String(100), nullable=True)  # Optional icon class (FontAwesome / Bootstrap)

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationship with User (back_populates from User.notifications)
    user = db.relationship("User", back_populates="notifications", lazy="joined")

    # String representation for debugging/logging
    def __repr__(self):
        return f"<Notification {self.id} ({self.type}) for User {self.user_id}>"
# ----------------------------




# Wishlist association table
# ----------------------------
wishlist = db.Table(
    "wishlist",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("listing_id", db.Integer, db.ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True),
    db.Column("created_at", db.DateTime, default=datetime.utcnow),
    extend_existing= True
)
