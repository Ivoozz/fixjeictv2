import os
import secrets
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

from fixjeict_app.models import db, User, Ticket, Category, Message, TicketNote, TimeLog, BlogPost, KnowledgeBase, Lead, Testimonial, AuthToken

load_dotenv()

admin_app = Flask(__name__)
admin_app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
admin_app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fixjeict.db')
admin_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable ProxyFix for correct client IPs behind Cloudflare/nginx
admin_app.wsgi_app = ProxyFix(admin_app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

db.init_app(admin_app)

with admin_app.app_context():
    db.create_all()


# Admin authentication
def check_auth(username, password):
    return (username == os.environ.get('ADMIN_USERNAME', 'admin') and
            password == os.environ.get('ADMIN_PASSWORD', 'admin'))


def authenticate():
    return abort(401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


# Routes
@admin_app.route('/')
@requires_auth
def admin_index():
    stats = {
        'tickets': Ticket.query.count(),
        'open_tickets': Ticket.query.filter_by(status='Open').count(),
        'users': User.query.count(),
        'leads': Lead.query.filter_by(status='new').count(),
    }
    recent_tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(5).all()
    recent_leads = Lead.query.filter_by(status='new').order_by(Lead.created_at.desc()).limit(5).all()
    return render_template('admin_index.html', stats=stats, recent_tickets=recent_tickets, recent_leads=recent_leads)


# Tickets
@admin_app.route('/tickets')
@requires_auth
def admin_tickets():
    status_filter = request.args.get('status')
    query = Ticket.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    tickets = query.order_by(Ticket.updated_at.desc()).all()
    return render_template('admin_tickets.html', tickets=tickets, status_filter=status_filter)


@admin_app.route('/tickets/<int:id>')
@requires_auth
def admin_ticket_detail(id):
    ticket = Ticket.query.get_or_404(id)
    messages = Message.query.filter_by(ticket_id=id).order_by(Message.created_at).all()
    notes = TicketNote.query.filter_by(ticket_id=id).order_by(TicketNote.created_at).all()
    time_logs = TimeLog.query.filter_by(ticket_id=id).order_by(TimeLog.created_at.desc()).all()
    return render_template('admin_ticket_detail.html', ticket=ticket, messages=messages, notes=notes, time_logs=time_logs)


@admin_app.route('/tickets/<int:id>/edit', methods=['GET', 'POST'])
@requires_auth
def admin_ticket_edit(id):
    ticket = Ticket.query.get_or_404(id)
    categories = Category.query.filter_by(is_active=True).order_by(Category.order).all()

    if request.method == 'POST':
        ticket.title = request.form.get('title')
        ticket.description = request.form.get('description')
        ticket.status = request.form.get('status')
        ticket.priority = request.form.get('priority')
        ticket.category_id = request.form.get('category_id') or None
        ticket.estimated_hours = float(request.form.get('estimated_hours')) if request.form.get('estimated_hours') else None

        fixer_id = request.form.get('fixer_id')
        ticket.fixer_id = int(fixer_id) if fixer_id else None

        if ticket.status == 'Gereed' and not ticket.closed_at:
            ticket.closed_at = datetime.utcnow()
        elif ticket.status != 'Gereed' and ticket.closed_at:
            ticket.closed_at = None

        db.session.commit()
        flash('Ticket bijgewerkt!', 'success')
        return redirect(url_for('admin_ticket_detail', id=id))

    fixers = User.query.filter(User.role.in_(['fixer', 'admin'])).all()
    return render_template('admin_ticket_edit.html', ticket=ticket, categories=categories, fixers=fixers)


@admin_app.route('/tickets/<int:id>/delete', methods=['POST'])
@requires_auth
def admin_ticket_delete(id):
    ticket = Ticket.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    flash('Ticket verwijderd!', 'success')
    return redirect(url_for('admin_tickets'))


@admin_app.route('/tickets/<int:id>/message', methods=['POST'])
@requires_auth
def admin_ticket_message(id):
    ticket = Ticket.query.get_or_404(id)
    content = request.form.get('content')
    is_internal = request.form.get('is_internal') == 'on'

    # Get admin user
    admin_user = User.query.filter_by(role='admin').first()
    if not admin_user:
        admin_user = User(email='admin@fixjeict.nl', name='Admin', role='admin')
        db.session.add(admin_user)
        db.session.commit()

    message = Message(ticket_id=id, user_id=admin_user.id, content=content, is_internal=is_internal)
    db.session.add(message)
    db.session.commit()

    flash('Bericht toegevoegd!', 'success')
    return redirect(url_for('admin_ticket_detail', id=id))


@admin_app.route('/tickets/<int:id>/time', methods=['POST'])
@requires_auth
def admin_ticket_time(id):
    ticket = Ticket.query.get_or_404(id)
    hours = float(request.form.get('hours'))
    description = request.form.get('description')

    # Get admin user
    admin_user = User.query.filter_by(role='admin').first()
    if not admin_user:
        admin_user = User(email='admin@fixjeict.nl', name='Admin', role='admin')
        db.session.add(admin_user)
        db.session.commit()

    time_log = TimeLog(ticket_id=id, user_id=admin_user.id, hours=hours, description=description)
    db.session.add(time_log)

    ticket.actual_hours = db.session.query(db.func.sum(TimeLog.hours)).filter_by(ticket_id=id).scalar() or 0
    db.session.commit()

    flash('Tijd geregistreerd!', 'success')
    return redirect(url_for('admin_ticket_detail', id=id))


# Users
@admin_app.route('/users')
@requires_auth
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)


@admin_app.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@requires_auth
def admin_user_edit(id):
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        user.name = request.form.get('name')
        user.company = request.form.get('company')
        user.role = request.form.get('role')
        user.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('Gebruiker bijgewerkt!', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin_user_edit.html', user=user)


@admin_app.route('/users/<int:id>/delete', methods=['POST'])
@requires_auth
def admin_user_delete(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('Gebruiker verwijderd!', 'success')
    return redirect(url_for('admin_users'))


# Categories
@admin_app.route('/categories')
@requires_auth
def admin_categories():
    categories = Category.query.order_by(Category.order).all()
    return render_template('admin_categories.html', categories=categories)


@admin_app.route('/categories/new', methods=['GET', 'POST'])
@requires_auth
def admin_category_new():
    if request.method == 'POST':
        category = Category(
            name=request.form.get('name'),
            description=request.form.get('description'),
            icon=request.form.get('icon'),
            order=int(request.form.get('order', 0))
        )
        db.session.add(category)
        db.session.commit()
        flash('Categorie aangemaakt!', 'success')
        return redirect(url_for('admin_categories'))

    return render_template('admin_category_edit.html', category=None)


@admin_app.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@requires_auth
def admin_category_edit(id):
    category = Category.query.get_or_404(id)

    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.icon = request.form.get('icon')
        category.order = int(request.form.get('order', 0))
        category.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('Categorie bijgewerkt!', 'success')
        return redirect(url_for('admin_categories'))

    return render_template('admin_category_edit.html', category=category)


@admin_app.route('/categories/<int:id>/delete', methods=['POST'])
@requires_auth
def admin_category_delete(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Categorie verwijderd!', 'success')
    return redirect(url_for('admin_categories'))


# Blog Posts
@admin_app.route('/blog')
@requires_auth
def admin_blog():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin_blog.html', posts=posts)


@admin_app.route('/blog/new', methods=['GET', 'POST'])
@requires_auth
def admin_blog_new():
    if request.method == 'POST':
        import re
        from datetime import datetime

        title = request.form.get('title')
        slug = re.sub(r'[^\w\-]', '-', title.lower()).strip('-')

        post = BlogPost(
            title=title,
            slug=slug,
            content=request.form.get('content'),
            excerpt=request.form.get('excerpt'),
            image_url=request.form.get('image_url'),
            is_published=request.form.get('is_published') == 'on',
            published_at=datetime.utcnow() if request.form.get('is_published') == 'on' else None
        )
        db.session.add(post)
        db.session.commit()
        flash('Blog post aangemaakt!', 'success')
        return redirect(url_for('admin_blog'))

    return render_template('admin_blog_edit.html', post=None)


@admin_app.route('/blog/<int:id>/edit', methods=['GET', 'POST'])
@requires_auth
def admin_blog_edit(id):
    post = BlogPost.query.get_or_404(id)

    if request.method == 'POST':
        import re
        from datetime import datetime

        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.excerpt = request.form.get('excerpt')
        post.image_url = request.form.get('image_url')
        post.is_published = request.form.get('is_published') == 'on'

        was_published = post.published_at is not None
        is_now_published = post.is_published

        if is_now_published and not was_published:
            post.published_at = datetime.utcnow()

        db.session.commit()
        flash('Blog post bijgewerkt!', 'success')
        return redirect(url_for('admin_blog'))

    return render_template('admin_blog_edit.html', post=post)


@admin_app.route('/blog/<int:id>/delete', methods=['POST'])
@requires_auth
def admin_blog_delete(id):
    post = BlogPost.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('Blog post verwijderd!', 'success')
    return redirect(url_for('admin_blog'))


# Knowledge Base
@admin_app.route('/kb')
@requires_auth
def admin_kb():
    posts = KnowledgeBase.query.order_by(KnowledgeBase.created_at.desc()).all()
    return render_template('admin_kb.html', posts=posts)


@admin_app.route('/kb/new', methods=['GET', 'POST'])
@requires_auth
def admin_kb_new():
    if request.method == 'POST':
        import re

        title = request.form.get('title')
        slug = re.sub(r'[^\w\-]', '-', title.lower()).strip('-')

        post = KnowledgeBase(
            title=title,
            slug=slug,
            content=request.form.get('content'),
            category=request.form.get('category'),
            is_published=request.form.get('is_published') == 'on'
        )
        db.session.add(post)
        db.session.commit()
        flash('Knowledge base artikel aangemaakt!', 'success')
        return redirect(url_for('admin_kb'))

    return render_template('admin_kb_edit.html', post=None)


@admin_app.route('/kb/<int:id>/edit', methods=['GET', 'POST'])
@requires_auth
def admin_kb_edit(id):
    post = KnowledgeBase.query.get_or_404(id)

    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.category = request.form.get('category')
        post.is_published = request.form.get('is_published') == 'on'
        db.session.commit()
        flash('Knowledge base artikel bijgewerkt!', 'success')
        return redirect(url_for('admin_kb'))

    return render_template('admin_kb_edit.html', post=post)


@admin_app.route('/kb/<int:id>/delete', methods=['POST'])
@requires_auth
def admin_kb_delete(id):
    post = KnowledgeBase.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('Knowledge base artikel verwijderd!', 'success')
    return redirect(url_for('admin_kb'))


# Leads
@admin_app.route('/leads')
@requires_auth
def admin_leads():
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template('admin_leads.html', leads=leads)


@admin_app.route('/leads/<int:id>/edit', methods=['GET', 'POST'])
@requires_auth
def admin_lead_edit(id):
    lead = Lead.query.get_or_404(id)

    if request.method == 'POST':
        lead.status = request.form.get('status')
        db.session.commit()
        flash('Lead bijgewerkt!', 'success')
        return redirect(url_for('admin_leads'))

    return render_template('admin_lead_edit.html', lead=lead)


@admin_app.route('/leads/<int:id>/delete', methods=['POST'])
@requires_auth
def admin_lead_delete(id):
    lead = Lead.query.get_or_404(id)
    db.session.delete(lead)
    db.session.commit()
    flash('Lead verwijderd!', 'success')
    return redirect(url_for('admin_leads'))


# Testimonials
@admin_app.route('/testimonials')
@requires_auth
def admin_testimonials():
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin_testimonials.html', testimonials=testimonials)


@admin_app.route('/testimonials/new', methods=['GET', 'POST'])
@requires_auth
def admin_testimonial_new():
    if request.method == 'POST':
        testimonial = Testimonial(
            name=request.form.get('name'),
            company=request.form.get('company'),
            content=request.form.get('content'),
            rating=int(request.form.get('rating', 5)),
            is_published=request.form.get('is_published') == 'on'
        )
        db.session.add(testimonial)
        db.session.commit()
        flash('Testimonial toegevoegd!', 'success')
        return redirect(url_for('admin_testimonials'))

    return render_template('admin_testimonial_edit.html', testimonial=None)


@admin_app.route('/testimonials/<int:id>/edit', methods=['GET', 'POST'])
@requires_auth
def admin_testimonial_edit(id):
    testimonial = Testimonial.query.get_or_404(id)

    if request.method == 'POST':
        testimonial.name = request.form.get('name')
        testimonial.company = request.form.get('company')
        testimonial.content = request.form.get('content')
        testimonial.rating = int(request.form.get('rating', 5))
        testimonial.is_published = request.form.get('is_published') == 'on'
        db.session.commit()
        flash('Testimonial bijgewerkt!', 'success')
        return redirect(url_for('admin_testimonials'))

    return render_template('admin_testimonial_edit.html', testimonial=testimonial)


@admin_app.route('/testimonials/<int:id>/delete', methods=['POST'])
@requires_auth
def admin_testimonial_delete(id):
    testimonial = Testimonial.query.get_or_404(id)
    db.session.delete(testimonial)
    db.session.commit()
    flash('Testimonial verwijderd!', 'success')
    return redirect(url_for('admin_testimonials'))


if __name__ == '__main__':
    admin_app.run(host='0.0.0.0', port=5001, debug=True)
