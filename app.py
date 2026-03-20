import os
from flask import Flask
from models import db, User, Pairing, Tag, Rating, Comment, AffiliateLink
from flask_login import LoginManager
from config import config
import re

login_manager = LoginManager()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('APP_ENV', os.environ.get('FLASK_ENV', 'development'))

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Sign in to do that.'

    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.pairings import pairings_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(pairings_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        seed_tags()

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


def seed_tags():
    tag_names = ['sweet', 'salty', 'sour', 'bitter', 'umami', 'crunchy', 'creamy',
                 'chewy', 'rich', 'light', 'spicy', 'acidic', 'dessert', 'snack', 'meal', 'drink']
    for name in tag_names:
        if not Tag.query.filter_by(name=name).first():
            tag = Tag(name=name, slug=slugify(name))
            db.session.add(tag)
    db.session.commit()


def seed_db():
    """Run this once to populate sample pairings."""
    from werkzeug.security import generate_password_hash

    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@thoughtsnpairs.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.flush()

    sample_pairings = [
        {
            'item_1': 'Oreo Cookie', 'item_2': 'Crunchy Peanut Butter',
            'title': 'Oreo Cookie + Crunchy Peanut Butter',
            'description': 'Salt cuts the sweetness. Crunch-on-crunch layering is deeply satisfying. Scrape the filling, dip in PB, repeat forever.',
            'tags': ['sweet', 'salty', 'crunchy', 'dessert', 'snack']
        },
        {
            'item_1': 'Apple Slices', 'item_2': 'Sharp Cheddar',
            'title': 'Apple Slices + Sharp Cheddar',
            'description': 'Tart apple acid against aged cheddar funk. The crunch contrast is excellent. Works with Honeycrisp or Granny Smith — avoid mealy apples.',
            'tags': ['sweet', 'salty', 'crunchy', 'snack']
        },
        {
            'item_1': 'Pickle', 'item_2': 'Fried Chicken',
            'title': 'Pickle + Fried Chicken',
            'description': 'Acid cuts the fat instantly. The brine resets your palate so each bite tastes like the first. Every fast food chain knows this.',
            'tags': ['salty', 'acidic', 'crunchy', 'meal']
        },
        {
            'item_1': 'Dark Chocolate', 'item_2': 'Espresso',
            'title': 'Dark Chocolate + Espresso',
            'description': 'Bitter amplifies bitter, then sweetness emerges from both. The fat in chocolate smooths espresso\'s edge. 70%+ cacao only.',
            'tags': ['bitter', 'rich', 'drink', 'dessert']
        },
        {
            'item_1': 'Miso Paste', 'item_2': 'Butter on Toast',
            'title': 'Miso Butter Toast',
            'description': 'Fermented umami bomb meets dairy fat. Spread butter, add a thin stripe of white miso. Toast until edges go dark. This will ruin regular toast for you.',
            'tags': ['umami', 'rich', 'salty', 'snack', 'meal']
        },
        {
            'item_1': 'Crackers', 'item_2': 'Brie',
            'title': 'Crackers + Brie',
            'description': 'Neutral crunch lets the brie speak. Room temperature brie only — cold brie is a crime against texture. Add a dot of fig jam if you have it.',
            'tags': ['creamy', 'crunchy', 'rich', 'snack']
        },
        {
            'item_1': 'Lemon Juice', 'item_2': 'Avocado Toast',
            'title': 'Lemon + Avocado Toast',
            'description': 'Acid lifts the fat. Without it avocado toast is just green butter. A full half-lemon squeezed over, not just a few drops.',
            'tags': ['acidic', 'creamy', 'light', 'meal', 'snack']
        },
        {
            'item_1': 'Soy Sauce', 'item_2': 'Popcorn',
            'title': 'Soy Sauce Popcorn',
            'description': 'Drizzle a teaspoon while still hot, toss immediately. The umami depth makes regular salted popcorn feel hollow. Add a tiny bit of sesame oil if feeling dangerous.',
            'tags': ['umami', 'salty', 'crunchy', 'snack']
        },
        {
            'item_1': 'Chips', 'item_2': 'Hummus',
            'title': 'Chips + Hummus',
            'description': 'Salt and crunch against creamy earthiness. The tahini in hummus adds a bitterness that balances the corn oil in chips. Better than salsa.',
            'tags': ['salty', 'creamy', 'crunchy', 'snack']
        },
        {
            'item_1': 'Arugula', 'item_2': 'Parmesan',
            'title': 'Arugula + Parmesan',
            'description': 'Peppery bitterness against aged salt crystals. The nutty umami of parmesan tames the arugula\'s aggression. Just olive oil and lemon, nothing else needed.',
            'tags': ['bitter', 'umami', 'salty', 'light', 'meal']
        },
    ]

    for p_data in sample_pairings:
        slug_base = slugify(p_data['title'])
        slug = slug_base
        counter = 1
        while Pairing.query.filter_by(slug=slug).first():
            slug = f"{slug_base}-{counter}"
            counter += 1

        pairing = Pairing(
            title=p_data['title'],
            slug=slug,
            description=p_data['description'],
            item_1=p_data['item_1'],
            item_2=p_data['item_2'],
            author_id=admin.id,
            status='approved',
            avg_rating=4.0
        )
        db.session.add(pairing)
        db.session.flush()

        for tag_name in p_data['tags']:
            tag = Tag.query.filter_by(name=tag_name).first()
            if tag and tag not in pairing.tags:
                pairing.tags.append(tag)

    db.session.commit()
    print('Seeded 10 sample pairings.')


if __name__ == '__main__':
    app = create_app()
    # with app.app_context():
    #     seed_db()
    app.run(debug=True)
