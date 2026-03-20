import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Many-to-many: Pairing <-> Tag
pairing_tags = db.Table('pairing_tags',
    db.Column('pairing_id', db.Integer, db.ForeignKey('pairing.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, default='')
    avatar_url = db.Column(db.String(500), default='')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pairings = db.relationship('Pairing', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    ratings = db.relationship('Rating', backref='user', lazy='dynamic')

    def set_password(self, password):
        import bcrypt
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    @property
    def approved_pairing_count(self):
        return self.pairings.filter_by(status='approved').count()

    @property
    def can_auto_approve(self):
        return self.approved_pairing_count >= 3


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)


class Pairing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    item_1 = db.Column(db.String(100), nullable=False)
    item_2 = db.Column(db.String(100), nullable=False, default='')
    item_3 = db.Column(db.String(100), nullable=True, default='')
    item_4 = db.Column(db.String(100), nullable=True, default='')
    item_5 = db.Column(db.String(100), nullable=True, default='')
    item_6 = db.Column(db.String(100), nullable=True, default='')
    item_7 = db.Column(db.String(100), nullable=True, default='')
    prep_note = db.Column(db.Text, nullable=True, default='')
    item_1_photo_url = db.Column(db.String(500), default='')
    item_2_photo_url = db.Column(db.String(500), default='')
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending | approved | rejected
    avg_rating = db.Column(db.Float, default=0.0)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.relationship('Tag', secondary=pairing_tags, backref='pairings')
    ratings = db.relationship('Rating', backref='pairing', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='pairing', lazy='dynamic', cascade='all, delete-orphan')
    affiliate_links = db.relationship('AffiliateLink', backref='pairing', lazy='dynamic', cascade='all, delete-orphan')

    def update_avg_rating(self):
        ratings = self.ratings.all()
        if ratings:
            self.avg_rating = sum(r.score for r in ratings) / len(ratings)
        else:
            self.avg_rating = 0.0

    def stars_display(self):
        full = int(self.avg_rating)
        empty = 5 - full
        return '★' * full + '☆' * empty

    def get_all_items(self):
        """Returns list of all non-empty item strings."""
        return [i for i in [self.item_1, self.item_2, self.item_3,
                             self.item_4, self.item_5, self.item_6, self.item_7]
                if i and i.strip()]

    def get_approved_links(self):
        return self.affiliate_links.filter_by(approved_by_admin=True).all()


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pairing_id = db.Column(db.Integer, db.ForeignKey('pairing.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    flavor_note = db.Column(db.String(200), default='')
    texture_note = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('pairing_id', 'user_id'),)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pairing_id = db.Column(db.Integer, db.ForeignKey('pairing.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='visible')  # visible | flagged | hidden
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AffiliateLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pairing_id = db.Column(db.Integer, db.ForeignKey('pairing.id'), nullable=False)
    label = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    retailer = db.Column(db.String(50), default='amazon')  # amazon | walmart | brand
    item_name = db.Column(db.String(200), default='')
    suggested_by_ai = db.Column(db.Boolean, default=False)
    approved_by_admin = db.Column(db.Boolean, default=False)
    click_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
