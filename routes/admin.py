from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from models import db, Pairing, AffiliateLink, User
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_pairings = Pairing.query.count()
    pending = Pairing.query.filter_by(status='pending').count()
    approved = Pairing.query.filter_by(status='approved').count()
    total_users = User.query.count()
    top_pairings = Pairing.query.filter_by(status='approved')\
        .order_by(Pairing.view_count.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           total_pairings=total_pairings, pending=pending,
                           approved=approved, total_users=total_users,
                           top_pairings=top_pairings)

@admin_bp.route('/queue')
@login_required
@admin_required
def queue():
    pairings = Pairing.query.filter_by(status='pending')\
        .order_by(Pairing.created_at.asc()).all()
    return render_template('admin/queue.html', pairings=pairings)

@admin_bp.route('/approve/<int:pairing_id>', methods=['POST'])
@login_required
@admin_required
def approve(pairing_id):
    pairing = Pairing.query.get_or_404(pairing_id)
    pairing.status = 'approved'
    db.session.commit()
    flash(f'"{pairing.title}" approved.', 'success')
    return redirect(url_for('admin.queue'))

@admin_bp.route('/reject/<int:pairing_id>', methods=['POST'])
@login_required
@admin_required
def reject(pairing_id):
    pairing = Pairing.query.get_or_404(pairing_id)
    pairing.status = 'rejected'
    db.session.commit()
    flash(f'"{pairing.title}" rejected.', 'success')
    return redirect(url_for('admin.queue'))

@admin_bp.route('/affiliate')
@login_required
@admin_required
def affiliate():
    # Approved pairings with no affiliate links, sorted by view count
    pairings_no_links = db.session.query(Pairing)\
        .filter(Pairing.status == 'approved')\
        .filter(~Pairing.affiliate_links.any(AffiliateLink.approved_by_admin == True))\
        .order_by(Pairing.view_count.desc()).all()

    # Pairings with pending AI suggestions
    pending_suggestions = AffiliateLink.query\
        .filter_by(suggested_by_ai=True, approved_by_admin=False).all()

    return render_template('admin/affiliate.html',
                           pairings_no_links=pairings_no_links,
                           pending_suggestions=pending_suggestions)

@admin_bp.route('/affiliate/add', methods=['POST'])
@login_required
@admin_required
def add_affiliate():
    pairing_id = request.form.get('pairing_id', type=int)
    label = request.form.get('label', '').strip()
    url = request.form.get('url', '').strip()
    retailer = request.form.get('retailer', 'amazon')
    item_name = request.form.get('item_name', '').strip()

    if not pairing_id or not label or not url:
        flash('Missing required fields.', 'error')
        return redirect(url_for('admin.affiliate'))

    link = AffiliateLink(
        pairing_id=pairing_id,
        label=label, url=url,
        retailer=retailer, item_name=item_name,
        suggested_by_ai=False, approved_by_admin=True
    )
    db.session.add(link)
    db.session.commit()
    flash('Affiliate link added.', 'success')
    return redirect(url_for('admin.affiliate'))

@admin_bp.route('/affiliate/approve/<int:link_id>', methods=['POST'])
@login_required
@admin_required
def approve_affiliate(link_id):
    link = AffiliateLink.query.get_or_404(link_id)
    link.approved_by_admin = True
    db.session.commit()
    flash('Link approved.', 'success')
    return redirect(url_for('admin.affiliate'))
