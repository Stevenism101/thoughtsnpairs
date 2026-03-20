from flask import Blueprint, render_template, request
from models import Pairing, Tag

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'new')
    query = Pairing.query.filter_by(status='approved')
    if sort == 'top':
        query = query.order_by(Pairing.avg_rating.desc(), Pairing.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Pairing.created_at.asc())
    else:  # new (default)
        query = query.order_by(Pairing.created_at.desc())
    pairings = query.paginate(page=page, per_page=20, error_out=False)
    return render_template('index.html', pairings=pairings, sort=sort)

@main_bp.route('/explore')
def explore():
    tag_slug = request.args.get('tag', '')
    sort = request.args.get('sort', 'top')
    page = request.args.get('page', 1, type=int)

    query = Pairing.query.filter_by(status='approved')

    active_tag = None
    if tag_slug:
        active_tag = Tag.query.filter_by(slug=tag_slug).first()
        if active_tag:
            query = query.filter(Pairing.tags.contains(active_tag))

    if sort == 'new':
        query = query.order_by(Pairing.created_at.desc())
    else:
        query = query.order_by(Pairing.avg_rating.desc(), Pairing.created_at.desc())

    pairings = query.paginate(page=page, per_page=20, error_out=False)
    tags = Tag.query.all()
    return render_template('explore.html', pairings=pairings, tags=tags, active_tag=active_tag, sort=sort)
