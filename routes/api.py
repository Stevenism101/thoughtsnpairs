from flask import Blueprint, jsonify, request, redirect, abort
from flask_login import login_required, current_user
from models import db, AffiliateLink, Pairing, Rating

api_bp = Blueprint('api', __name__)

@api_bp.route('/out/<int:link_id>')
def affiliate_redirect(link_id):
    link = AffiliateLink.query.get_or_404(link_id)
    if not link.approved_by_admin:
        abort(404)
    link.click_count += 1
    db.session.commit()
    return redirect(link.url, code=302)

@api_bp.route('/api/rate/<int:pairing_id>', methods=['POST'])
@login_required
def api_rate(pairing_id):
    pairing = Pairing.query.get_or_404(pairing_id)
    data = request.get_json()
    score = data.get('score')

    if not score or not (1 <= score <= 5):
        return jsonify({'error': 'Invalid score'}), 400

    existing = Rating.query.filter_by(pairing_id=pairing_id, user_id=current_user.id).first()
    if existing:
        existing.score = score
    else:
        rating = Rating(pairing_id=pairing_id, user_id=current_user.id, score=score)
        db.session.add(rating)

    pairing.update_avg_rating()
    db.session.commit()

    return jsonify({'avg_rating': round(pairing.avg_rating, 1), 'stars': pairing.stars_display(), 'user_score': score})
