from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from backend.forms import ListingForm
from backend.models import Listing, Category, ListingImage
from backend.extensions import db

from datetime import datetime

marketplace_bp = Blueprint("marketplace", __name__, template_folder="../templates")

# List all active listings
@marketplace_bp.route("/marketplace")
def marketplace():
    listings = Listing.query.filter_by(is_active=True).order_by(Listing.created_at.desc()).all()
    return render_template("marketplace.html", listings=listings)

# View single listing
@marketplace_bp.route("/marketplace/<slug>")
def view_listing(slug):
    listing = Listing.query.filter_by(slug=slug, is_active=True).first_or_404()
    return render_template("view_listing.html", listing=listing)

# Create new listing
@marketplace_bp.route("/marketplace/create", methods=["GET", "POST"])
@login_required
def create_listing():
    form = ListingForm()
    form.set_choices()
    if form.validate_on_submit():
        listing = Listing(
            title=form.title.data,
            description=form.description.data,
            quantity=form.quantity.data,
            unit=form.unit.data,
            owner_id=current_user.id,
            category_id=form.category_id.data,
            is_active=True,
            created_at=datetime.utcnow(),
        )
       
        db.session.add(listing)
        db.session.commit()
        flash("Listing created successfully!", "success")
        return redirect(url_for("marketplace.view_listing", slug=listing.slug))
    return render_template("create_listing.html", form=form)
