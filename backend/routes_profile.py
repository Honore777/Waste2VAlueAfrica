from backend.forms import EditProfileForm, AvatarUploadForm

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from backend.extensions import db
from datetime import datetime


import os 
from  werkzeug.utils import secure_filename
import imghdr
import uuid

from backend.models import User, Post




profile_bp=Blueprint('profile', __name__, template_folder='../templates')
@profile_bp.route('/profile/edit',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm(obj=current_user)
    avatar_form = AvatarUploadForm()

    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.bio = form.bio.data
        current_user.location = form.location.data
        current_user.twitter = form.twitter.data
        current_user.instagram = form.instagram.data
        current_user.github = form.github.data

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile.profile", username=current_user.username))

    return render_template(
        "edit_profile.html",
        user=current_user,
        form=form,
        avatar_form=avatar_form
    )

@profile_bp.route("/profile/upload-avatar", methods=["POST"])
@login_required
def upload_avatar():
    form = AvatarUploadForm()

    if not form.validate_on_submit():
        flash("Invalid image format.", "danger")
        return redirect(url_for("profile.edit_profile"))

    file = form.avatar.data

    # Extra validation: check real image type
    kind = imghdr.what(file)
    if kind not in ["jpeg", "png", "webp"]:
        flash("Invalid or corrupted image file!", "danger")
        return redirect(url_for("profile.edit_profile"))

    # Generate a secure filename
    ext = file.filename.split(".")[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"

    upload_folder = os.path.join( 'static', 'uploads', 'avatars')
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    # Store only the filename in DB
    current_user.avatar_url_filename = filename
    current_user.updated_at = datetime.utcnow()  # optional: for cache-busting
    db.session.commit()

    flash("Avatar updated successfully!", "success")
    return redirect(url_for("profile.edit_profile"))


@profile_bp.route("/profile/<username>")
def profile(username):
    """View a public profile."""
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("profile.html", user=user, Post=Post)
