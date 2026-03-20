import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort
from flask_login import login_required, current_user
from models import db, Pairing, Rating, Comment, Tag

pairings_bp = Blueprint('pairings', __name__)

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

@pairings_bp.route('/pairing/<slug>')
def view(slug):
    pairing = Pairing.query.filter_by(slug=slug, status='approved').first_or_404()
    pairing.view_count += 1
    db.session.commit()

    user_rating = None
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(pairing_id=pairing.id, user_id=current_user.id).first()

    comments = pairing.comments.filter_by(status='visible').order_by(Comment.created_at.asc()).all()
    affiliate_links = pairing.get_approved_links()

    return render_template('pairing.html', pairing=pairing, user_rating=user_rating,
                           comments=comments, affiliate_links=affiliate_links)

@pairings_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        item_1 = request.form.get('item_1', '').strip()
        item_2 = request.form.get('item_2', '').strip()
        item_3 = request.form.get('item_3', '').strip()
        item_4 = request.form.get('item_4', '').strip()
        item_5 = request.form.get('item_5', '').strip()
        item_6 = request.form.get('item_6', '').strip()
        item_7 = request.form.get('item_7', '').strip()
        prep_note = request.form.get('prep_note', '').strip()
        description = request.form.get('description', '').strip()
        tag_ids = request.form.getlist('tags')

        # Require item_1 always; then either item_2+ or prep_note
        if not item_1:
            flash('At least one item is required.', 'error')
            return redirect(url_for('pairings.submit'))
        if not item_2 and not prep_note:
            flash('Add a second item or a prep note — we need at least one more detail.', 'error')
            return redirect(url_for('pairings.submit'))
        if not description:
            flash('Tell us why it works.', 'error')
            return redirect(url_for('pairings.submit'))

        all_items = [i for i in [item_1, item_2, item_3, item_4, item_5, item_6, item_7] if i]
        title = ' + '.join(all_items)
        slug_base = slugify(title)
        slug = slug_base
        counter = 1
        while Pairing.query.filter_by(slug=slug).first():
            slug = f"{slug_base}-{counter}"
            counter += 1

        status = 'approved' if current_user.can_auto_approve else 'pending'

        pairing = Pairing(
            title=title, slug=slug,
            description=description,
            item_1=item_1, item_2=item_2,
            item_3=item_3, item_4=item_4,
            item_5=item_5, item_6=item_6, item_7=item_7,
            prep_note=prep_note,
            author_id=current_user.id,
            status=status
        )
        db.session.add(pairing)
        db.session.flush()

        for tag_id in tag_ids:
            tag = Tag.query.get(int(tag_id))
            if tag:
                pairing.tags.append(tag)

        # Try AI moderation in background (non-blocking)
        try:
            from utils.ai_suggest import analyze_pairing
            result = analyze_pairing(item_1, item_2, description)
            if result and result.get('tags'):
                for tag_name in result['tags']:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if tag and tag not in pairing.tags:
                        pairing.tags.append(tag)
        except Exception:
            pass

        db.session.commit()

        if status == 'approved':
            flash('Pairing published!', 'success')
            return redirect(url_for('pairings.view', slug=pairing.slug))
        else:
            flash('Pairing submitted — it\'ll appear once approved.', 'success')
            return redirect(url_for('main.index'))

    tags = Tag.query.order_by(Tag.name).all()
    return render_template('submit.html', tags=tags)

@pairings_bp.route('/pairing/<int:pairing_id>/rate', methods=['POST'])
@login_required
def rate(pairing_id):
    pairing = Pairing.query.get_or_404(pairing_id)
    score = request.form.get('score', type=int)

    if not score or score < 1 or score > 5:
        flash('Pick a score between 1 and 5.', 'error')
        return redirect(url_for('pairings.view', slug=pairing.slug))

    existing = Rating.query.filter_by(pairing_id=pairing_id, user_id=current_user.id).first()
    if existing:
        existing.score = score
        existing.flavor_note = request.form.get('flavor_note', '').strip()
        existing.texture_note = request.form.get('texture_note', '').strip()
    else:
        rating = Rating(
            pairing_id=pairing_id, user_id=current_user.id,
            score=score,
            flavor_note=request.form.get('flavor_note', '').strip(),
            texture_note=request.form.get('texture_note', '').strip()
        )
        db.session.add(rating)

    pairing.update_avg_rating()
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'avg_rating': round(pairing.avg_rating, 1), 'stars': pairing.stars_display()})

    return redirect(url_for('pairings.view', slug=pairing.slug))

@pairings_bp.route('/pairing/<int:pairing_id>/comment', methods=['POST'])
@login_required
def comment(pairing_id):
    pairing = Pairing.query.get_or_404(pairing_id)
    body = request.form.get('body', '').strip()

    if not body:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('pairings.view', slug=pairing.slug))

    c = Comment(pairing_id=pairing_id, user_id=current_user.id, body=body)
    db.session.add(c)
    db.session.commit()

    return redirect(url_for('pairings.view', slug=pairing.slug) + '#comments')

@pairings_bp.route('/profile/<username>')
def profile(username):
    from models import User
    user = User.query.filter_by(username=username).first_or_404()
    pairings = user.pairings.filter_by(status='approved').order_by(Pairing.created_at.desc()).all()
    return render_template('profile.html', profile_user=user, pairings=pairings)
