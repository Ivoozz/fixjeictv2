import os
import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

from fixjeict_app.models import db, User, Ticket, Category, Message, TicketNote, TimeLog, BlogPost, KnowledgeBase, Lead, Testimonial, AuthToken
from fixjeict_app.email_service import email_service
from fixjeict_app.cloudflare_service import cloudflare_service

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fixjeict.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable ProxyFix for correct client IPs behind Cloudflare/nginx
# x_for=2 for Cloudflare tunnels (Cloudflare adds one X-Forwarded-For header)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=1, x_host=1, x_prefix=1)

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
    except Exception:
        # Tables might already exist, that's OK
        pass


# Helper functions
def generate_auth_token(user_id):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    auth_token = AuthToken(user_id=user_id, token=token, expires_at=expires_at)
    db.session.add(auth_token)
    db.session.commit()
    return token


def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None


def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Log in om toegang te krijgen tot deze pagina.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


def fixer_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Log in om toegang te krijgen tot deze pagina.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role not in ['fixer', 'admin']:
            flash('Geen toegang. Fixer account vereist.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# Routes
@app.route('/')
def index():
    featured_posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).limit(3).all()
    testimonials = Testimonial.query.filter_by(is_published=True).all()
    return render_template('index.html', featured_posts=featured_posts, testimonials=testimonials)


@app.route('/services')
def services():
    return render_template('services.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        company = request.form.get('company')
        phone = request.form.get('phone')
        message = request.form.get('message')

        lead = Lead(name=name, email=email, company=company, phone=phone, message=message)
        db.session.add(lead)
        db.session.commit()

        email_service.send_lead_notification(lead)

        flash('Bedankt voor uw bericht! We nemen zo snel mogelijk contact op.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/blog')
def blog():
    posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).all()
    return render_template('blog.html', posts=posts)


@app.route('/blog/<slug>')
def blog_post(slug):
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template('blog_post.html', post=post)


@app.route('/knowledge-base')
def knowledge_base():
    posts = KnowledgeBase.query.filter_by(is_published=True).order_by(KnowledgeBase.views.desc()).all()
    categories = db.session.query(KnowledgeBase.category).filter(KnowledgeBase.category.isnot(None)).distinct().all()
    return render_template('knowledge_base.html', posts=posts, categories=categories)


@app.route('/knowledge-base/<slug>')
def kb_post(slug):
    post = KnowledgeBase.query.filter_by(slug=slug, is_published=True).first_or_404()
    post.views += 1
    db.session.commit()
    return render_template('kb_post.html', post=post)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()

        user = User.query.filter_by(email=email).first()

        if not user:
            # Create new user
            name = email.split('@')[0].replace('.', ' ').title()
            user = User(email=email, name=name)
            db.session.add(user)
            db.session.commit()
            flash('Nieuw account aangemaakt!', 'info')

        # Generate and send magic link
        token = generate_auth_token(user.id)
        email_service.send_magic_link(user.email, token, user.name)

        flash('Login link verzonden naar uw email!', 'success')
        return redirect(url_for('login_sent', email=email))

    return render_template('login.html')


@app.route('/login/sent')
def login_sent():
    email = request.args.get('email', '')
    return render_template('login_sent.html', email=email)


@app.route('/auth/verify/<token>')
def auth_verify(token):
    auth_token = AuthToken.query.filter_by(token=token).first()

    if not auth_token or auth_token.used:
        flash('Ongeldige of verlopen login link.', 'danger')
        return redirect(url_for('login'))

    if auth_token.expires_at < datetime.utcnow():
        flash('Login link is verlopen. Vraag een nieuwe aan.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(auth_token.user_id)
    if not user:
        flash('Gebruiker niet gevonden.', 'danger')
        return redirect(url_for('login'))

    # Mark token as used
    auth_token.used = True
    user.last_login = datetime.utcnow()
    db.session.commit()

    session['user_id'] = user.id
    session['user_name'] = user.name
    session['user_role'] = user.role

    flash(f'Welkom terug, {user.name}!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    flash('U bent uitgelogd.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()

    if user.role == 'client':
        tickets = Ticket.query.filter_by(client_id=user.id).order_by(Ticket.updated_at.desc()).all()
        return render_template('dashboard.html', user=user, tickets=tickets)

    elif user.role == 'fixer':
        my_tickets = Ticket.query.filter_by(fixer_id=user.id).order_by(Ticket.updated_at.desc()).all()
        available_tickets = Ticket.query.filter(
            (Ticket.fixer_id == None) | (Ticket.fixer_id == user.id)
        ).order_by(Ticket.created_at.desc()).all()
        return render_template('dashboard_fixer.html', user=user, my_tickets=my_tickets, available_tickets=available_tickets)

    return render_template('dashboard.html', user=user)


@app.route('/tickets/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    if request.method == 'POST':
        user = get_current_user()
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        priority = request.form.get('priority', 'normaal')

        ticket = Ticket(
            title=title,
            description=description,
            client_id=user.id,
            category_id=category_id,
            priority=priority
        )
        db.session.add(ticket)
        db.session.commit()

        email_service.send_ticket_created(ticket, user.email)

        flash('Ticket succesvol aangemaakt!', 'success')
        return redirect(url_for('ticket_detail', id=ticket.id))

    categories = Category.query.filter_by(is_active=True).order_by(Category.order).all()
    return render_template('new_ticket.html', categories=categories)


@app.route('/tickets/<int:id>')
@login_required
def ticket_detail(id):
    user = get_current_user()
    ticket = Ticket.query.get_or_404(id)

    # Check access
    if user.role == 'client' and ticket.client_id != user.id:
        flash('Geen toegang tot dit ticket.', 'danger')
        return redirect(url_for('dashboard'))

    if user.role == 'fixer' and ticket.fixer_id and ticket.fixer_id != user.id:
        flash('Geen toegang tot dit ticket.', 'danger')
        return redirect(url_for('dashboard'))

    messages = Message.query.filter_by(ticket_id=id, is_internal=False).order_by(Message.created_at).all()
    notes = TicketNote.query.filter_by(ticket_id=id).order_by(TicketNote.created_at).all() if user.role in ['fixer', 'admin'] else []
    time_logs = TimeLog.query.filter_by(ticket_id=id).order_by(TimeLog.created_at.desc()).all()

    return render_template('ticket_detail.html', ticket=ticket, messages=messages, notes=notes, time_logs=time_logs)


@app.route('/tickets/<int:id>/message', methods=['POST'])
@login_required
def add_message(id):
    user = get_current_user()
    ticket = Ticket.query.get_or_404(id)

    # Check access
    if user.role == 'client' and ticket.client_id != user.id:
        flash('Geen toegang.', 'danger')
        return redirect(url_for('dashboard'))

    content = request.form.get('content')
    is_internal = request.form.get('is_internal') == 'on' and user.role in ['fixer', 'admin']

    message = Message(ticket_id=id, user_id=user.id, content=content, is_internal=is_internal)
    db.session.add(message)
    db.session.commit()

    # Send notification to client if fixer responds
    if user.role in ['fixer', 'admin'] and not is_internal:
        email_service.send_message_notification(ticket, message, ticket.client.email)

    flash('Bericht toegevoegd!', 'success')
    return redirect(url_for('ticket_detail', id=id))


@app.route('/tickets/<int:id>/note', methods=['POST'])
@fixer_required
def add_note(id):
    user = get_current_user()
    content = request.form.get('content')

    note = TicketNote(ticket_id=id, user_id=user.id, content=content)
    db.session.add(note)
    db.session.commit()

    flash('Notitie toegevoegd!', 'success')
    return redirect(url_for('ticket_detail', id=id))


@app.route('/tickets/<int:id>/time', methods=['POST'])
@fixer_required
def log_time(id):
    user = get_current_user()
    hours = int(request.form.get('hours', 0))
    minutes = int(request.form.get('minutes', 0))
    description = request.form.get('description')

    time_log = TimeLog(ticket_id=id, user_id=user.id, hours=hours, minutes=minutes, description=description)
    db.session.add(time_log)

    ticket = Ticket.query.get(id)
    time_logs = TimeLog.query.filter_by(ticket_id=id).all()
    ticket.actual_hours = sum(tl.total_hours for tl in time_logs)

    db.session.commit()

    flash('Tijd geregistreerd!', 'success')
    return redirect(url_for('ticket_detail', id=id))


@app.route('/tickets/<int:id>/claim', methods=['POST'])
@fixer_required
def claim_ticket(id):
    user = get_current_user()
    ticket = Ticket.query.get_or_404(id)

    if ticket.fixer_id:
        flash('Ticket is al geclaimd.', 'warning')
    else:
        ticket.fixer_id = user.id
        db.session.commit()
        flash('Ticket geclaimd!', 'success')

    return redirect(url_for('ticket_detail', id=id))


@app.route('/tickets/<int:id>/status', methods=['POST'])
@fixer_required
def update_status(id):
    ticket = Ticket.query.get_or_404(id)
    status = request.form.get('status')
    old_status = ticket.status

    ticket.status = status

    if status == 'Gereed':
        ticket.closed_at = datetime.utcnow()
    elif status == 'Open' and ticket.closed_at:
        ticket.closed_at = None

    db.session.commit()

    # Send email notification to client
    if old_status != status:
        email_service.send_ticket_updated(ticket, ticket.client.email, status)

    flash('Status bijgewerkt!', 'success')
    return redirect(url_for('ticket_detail', id=id))


@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    return render_template('profile.html', user=user)


@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user = get_current_user()
    user.name = request.form.get('name')
    user.company = request.form.get('company')
    db.session.commit()

    flash('Profiel bijgewerkt!', 'success')
    return redirect(url_for('profile'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
