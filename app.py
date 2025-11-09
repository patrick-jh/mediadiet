from dotenv import load_dotenv
import os
from datetime import date, datetime
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from flask_migrate import Migrate
from forms import LoginForm, EntryForm
from models import db, User, Post  # <-- use the single shared db/models
from sqlalchemy import func
from utils.aggregations import compute_aggregations

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Ensure instance folder exists and keep DB there
os.makedirs(app.instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the shared db with this app
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

@login_manager.user_loader
def load_user(user_id):
    # modern pattern; avoids a deprecated query.get
    return db.session.get(User, int(user_id))

# ---------------- ROUTES ----------------
@app.route('/search')
def search():
    query = request.args.get('query', '').strip()
    results = []
    
    if query:
        # Use LIKE with wildcards for fuzzy matching
        search_pattern = f"%{query}%"
        results = Post.query.filter(Post.title.ilike(search_pattern))\
                          .order_by(Post.date.desc())\
                          .all()
    
    return render_template('search.html', results=results)

@app.route('/')
def home():
    recent_movies = Post.query.filter_by(media_type='Movie').order_by(Post.date.desc()).limit(5).all()
    recent_tv = Post.query.filter_by(media_type='TV').order_by(Post.date.desc()).limit(5).all()
    recent_music = Post.query.filter_by(media_type='Music').order_by(Post.date.desc()).limit(5).all()
    recent_book = Post.query.filter_by(media_type='Book').order_by(Post.date.desc()).limit(5).all()
    recent_posts = Post.query.order_by(Post.date.desc()).limit(15).all()
    recent_recs= Post.query.filter_by(recommended=True).order_by(Post.date.desc()).limit(10).all()
    recent_ratings = [post.rating for post in Post.query.order_by(Post.date.desc()).limit(15).all()][::-1]
    return render_template('home.html', recent_movies=recent_movies, recent_tv=recent_tv, recent_music=recent_music, recent_book=recent_book, recent_posts=recent_posts, recent_recs=recent_recs, recent_ratings=recent_ratings)

@app.route('/entry', methods=['GET', 'POST'])
@login_required
def entry():
    form = EntryForm()

    # Use VALID_GENRES from forms.py
    from forms import VALID_GENRES
    
    selected_media = form.media_type.data or 'Book'
    form.set_genre_choices(selected_media)

    if form.validate_on_submit():
        print("✅ Form validated")   # DEBUG
        # Create entry object here
    else:
        if request.method == "POST":
            print("❌ Form validation failed")  # DEBUG
            print(form.errors)  # DEBUG to see why
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            media_type=form.media_type.data,
            genre=form.genre.data,
            year_released=form.year_released.data,
            source=form.source.data,
            date=form.date.data or date.today(),
            notes=form.notes.data,
            rating=form.rating.data,
            dnf=form.dnf.data,
            recommended=form.recommended.data,
            foreign=form.foreign.data,
            country=form.country.data if form.foreign.data else None
        )
        db.session.add(post)
        try:
            db.session.commit()
            print("✅ Entry committed to database")  # DEBUG
        except Exception as e:
            db.session.rollback()
            print("❌ Commit failed:", e)  # DEBUG

        # store the title in the session temporarily
        session['last_entry_title'] = post.title

        return redirect(url_for('entry_success'))
   # else:
   #     if request.method == "POST":
   #         flash("Form validation failed. Please check your inputs.", "danger")
   #         print(form.errors)   # <-- helpful debugging
    return render_template('entry.html', form=form)

@app.route('/entry_success')
@login_required
def entry_success():
    title = session.pop('last_entry_title', None)
    return render_template('entry_success.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/calendar')
def calendar():
    # Get filter params with defaults (current year, Books)
    current_year = datetime.now().year
    year = request.args.get('year', str(current_year))
    media_type = request.args.get('media_type', 'Book')

    # Build query with filters
    q = Post.query
    if year:
        q = q.filter(db.extract('year', Post.date) == int(year))
    if media_type:
        q = q.filter(Post.media_type == media_type)

    # Get all ratings in chronological order for sparkline
    ratings = [post.rating for post in q.order_by(Post.date.asc()).all()]

    # Get distinct years and media types for filters
    years = sorted([y for (y,) in db.session.query(db.extract('year', Post.date)).distinct().all() if y], reverse=True)
    media_types = [t for (t,) in db.session.query(Post.media_type).distinct().order_by(Post.media_type).all()]

    return render_template('calendar.html',
                         ratings=ratings,
                         years=years,
                         media_types=media_types,
                         selected_year=year,
                         selected_media_type=media_type)

@app.route('/statistics')
def statistics():
    # Build filters in the DB (faster than filtering Python lists)
    media_type = request.args.get('media_type') or None
    genre = request.args.get('genre') or None
    rating = request.args.get('rating') or None
    source = request.args.get('source') or None
    recommended = request.args.get('recommended') or None
    year_released = request.args.get('year_released') or None
    year_consumed = request.args.get('year_consumed') or None

    q = Post.query
    if media_type:
        q = q.filter(Post.media_type == media_type)
    if genre:
        q = q.filter(Post.genre == genre)
    if rating:
        q = q.filter(Post.rating == int(rating))
    if source:
        q = q.filter(Post.source == source)
    if recommended == 'yes':
        q = q.filter(Post.recommended == True)
    if year_released:
        q = q.filter(Post.year_released == int(year_released))
    if year_consumed:
        q = q.filter(db.extract('year', Post.date) == int(year_consumed))

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50
    pagination = q.order_by(Post.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    year_consumed_list = [d.year for (d,) in db.session.query(Post.date).distinct().order_by(Post.date.desc()).all() if d]
    year_consumed_list = sorted(set(year_consumed_list), reverse=True)
    posts = pagination.items

    # For the genre filter options, show all distinct genres
    all_genres = [g for (g,) in db.session.query(Post.genre).distinct().order_by(Post.genre.asc()).all()]
    all_years = [y for (y,) in db.session.query(Post.year_released).distinct().order_by(Post.year_released.desc()).all() if y]
    all_sources = [s for (s,) in db.session.query(Post.source).distinct().order_by(Post.source.asc()).all() if s]
    genre_map = {
        'Book': ['Fiction', 'Non-Fiction', 'Biography', 'Other'],
        'Movie': ['Action', 'Comedy', 'Drama', 'Documentary', 'Other'],
        'Museum': ['Art', 'History', 'Science', 'Other'],
        'Music': ['Pop', 'Rock', 'Classical', 'Jazz', 'Other'],
        'Podcast': ['Entertainment', 'Commentary', 'News'],
        'Sports': ['Baseball', 'Basketball', 'Football', 'Auto Racing', 'Olympics', 'Other'],
        'TV': ['Drama', 'Comedy', 'Documentary', 'Other']
    }

    # Aggregations for charts — use helper
    group_attr = Post.genre if media_type else Post.media_type
    (top_labels, top_values), (bottom_labels, bottom_values) = compute_aggregations(q, group_attr, avg_attr=Post.rating)

    return render_template('statistics.html', posts=posts, genres=all_genres, years=all_years, year_consumed_list=year_consumed_list, pagination=pagination, genre_map=genre_map, top_labels=top_labels, top_values=top_values, bottom_labels=bottom_labels, bottom_values=bottom_values, sources=all_sources)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data.strip()
        password = form.password.data

        # Try to find user by username OR email
        user = db.session.query(User).filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))

        flash('Invalid username/email or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))


# Temporary debug endpoint to insert a post via JSON for troubleshooting
@app.route('/debug/create_post', methods=['POST'])
def debug_create_post():
    # Simple token guard to avoid accidental public use
    token = request.args.get('token')
    if token != 'letmein':
        abort(403)
    data = request.get_json() or {}
    try:
        post = Post(
            title=data.get('title', 'debug post'),
            media_type=data.get('media_type', 'Book'),
            genre=data.get('genre'),
            year_released=data.get('year_released'),
            source=data.get('source'),
            date=data.get('date') or date.today(),
            notes=data.get('notes'),
            rating=data.get('rating'),
            dnf=data.get('dnf', False),
            recommended=data.get('recommended', False),
            foreign=data.get('foreign', False),
            country=data.get('country')
        )
        db.session.add(post)
        db.session.commit()
        return jsonify({'status': 'ok', 'id': post.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    # Make sure tables exist before serving
    with app.app_context():
        db.create_all()
    app.run(debug=True)