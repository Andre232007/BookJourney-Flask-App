from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
from datetime import datetime
from flask_migrate import Migrate # Importe Flask-Migrate

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
# É uma boa prática usar 'instance' para o banco de dados SQLite para evitar problemas de permissão
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = 'uma_chave_muito_secreta_e_segura_aqui_substitua_isso_por_algo_complexo'

# Aumenta o limite máximo de tamanho do conteúdo para 500 MB (500 * 1024 * 1024 bytes)
# Isso deve prevenir o erro "Request Entity Too Large" para a maioria dos textos de livros.
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 # 500 Megabytes

db = SQLAlchemy(app)
migrate = Migrate(app, db) # Inicialize Flask-Migrate AQUI, depois de 'app' e 'db'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    user_books = db.relationship('UserBook', backref='user', lazy=True, cascade="all, delete-orphan")
    # Adicionando relacionamento para CommunityBook
    contributed_books = db.relationship('CommunityBook', backref='contributor', lazy=True, cascade="all, delete-orphan")
    # Novo relacionamento para o progresso de leitura dos livros da comunidade
    reading_progresses = db.relationship('UserCommunityBookProgress', backref='user', lazy=True, cascade="all, delete-orphan")


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    publication_year = db.Column(db.Integer, nullable=True)
    genre = db.Column(db.String(50), nullable=True)

    user_books = db.relationship('UserBook', backref='book', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'

class UserBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    
    status = db.Column(db.String(20), default='desejado', nullable=False) 
    
    progress_pages = db.Column(db.Integer, nullable=True)
    progress_percentage = db.Column(db.Integer, nullable=True)

    notes = db.Column(db.Text, nullable=True)
    
    rating = db.Column(db.Integer, nullable=True)
    
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    
    added_date = db.Column(db.DateTime, default=datetime.utcnow)

    is_public_recommendation = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f'<UserBook UserID: {self.user_id}, BookID: {self.book_id}, Status: {self.status}>'

# NOVO MODELO: CommunityBook para livros que os usuários podem ler no app
class CommunityBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    snippet = db.Column(db.Text, nullable=False) # Pequena descrição
    content = db.Column(db.Text, nullable=False) # Conteúdo completo do livro
    contributor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Quem adicionou o livro
    added_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Novo relacionamento para o progresso de leitura
    progresses = db.relationship('UserCommunityBookProgress', backref='community_book', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<CommunityBook {self.title} by {self.author}>'

# NOVO MODELO: UserCommunityBookProgress para rastrear o progresso de leitura
class UserCommunityBookProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    community_book_id = db.Column(db.Integer, db.ForeignKey('community_book.id'), nullable=False)
    current_page = db.Column(db.Integer, default=0, nullable=False)
    progress_percentage = db.Column(db.Float, default=0.0, nullable=False)
    last_read_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'community_book_id', name='_user_community_book_uc'),)

    def __repr__(self):
        return f'<UserProgress UserID: {self.user_id}, BookID: {self.community_book_id}, Page: {self.current_page}, Progress: {self.progress_percentage}%>'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('auth', message='Você precisa fazer login para acessar esta página.', type='error', next=request.url)) 
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'error')
            return redirect(url_for('auth', message='Você precisa fazer login para acessar esta página.', type='error', next=request.url)) 
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Acesso negado. Você não tem permissão de administrador.', 'error')
            return redirect(url_for('dashboard', message='Acesso negado. Você não tem permissão de administrador.', type='error'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas da Aplicação ---

@app.route('/')
def index():
    user_id = session.get('user_id')
    
    # Suas recomendações (livros adicionados pelo usuário logado)
    user_recommendations = []
    if user_id:
        user_books_entries = UserBook.query.filter_by(user_id=user_id, is_public_recommendation=True).order_by(UserBook.added_date.desc()).limit(5).all() # Mostra as 5 mais recentes
        for entry in user_books_entries:
            user_recommendations.append({
                'title': entry.book.title,
                'author': entry.book.author,
                'status': entry.status,
                'notes': entry.notes,
                'rating': entry.rating,
                'added_date': entry.added_date.strftime('%d/%m/%Y %H:%M')
            })

    # Últimas recomendações de outros usuários (excluindo as do usuário logado)
    other_users_recommendations = []
    
    # Busca todas as entradas públicas de UserBook
    query = UserBook.query.filter_by(is_public_recommendation=True)
    if user_id:
        # Se o usuário estiver logado, exclui as recomendações dele
        query = query.filter(UserBook.user_id != user_id) 
    
    # Ordena e limita as recomendações de outros usuários para 3
    recent_public_entries = query.order_by(UserBook.added_date.desc()).limit(3).all() # LIMITADO A 3 CARDS AQUI
    
    for entry in recent_public_entries:
        other_users_recommendations.append({
            'title': entry.book.title,
            'author': entry.book.author,
            'notes': entry.notes,
            'rating': entry.rating,
            'username': entry.user.username, # Pega o username do relacionamento com User
            'added_date': entry.added_date.strftime('%d/%m/%Y %H:%M')
        })

    return render_template('index.html',
                           user_recommendations=user_recommendations,
                           other_users_recommendations=other_users_recommendations)

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    if not username or not email or not password:
        flash('Por favor, preencha todos os campos.', 'error')
        return redirect(url_for('auth', message='Por favor, preencha todos os campos.', type='error'))

    existing_user = User.query.filter_by(username=username).first()
    existing_email = User.query.filter_by(email=email).first()

    if existing_user:
        flash('Nome de usuário já existe.', 'error')
        return redirect(url_for('auth', message='Nome de usuário já existe.', type='error'))
    if existing_email:
        flash('Email já registrado.', 'error')
        return redirect(url_for('auth', message='Email já registrado.', type='error'))

    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    flash('Conta criada com sucesso! Você já pode fazer login.', 'success')
    return redirect(url_for('auth', message='Conta criada com sucesso! Você já pode fazer login.', type='success'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        flash(f'Bem-vindo, {user.username}!', 'success')

        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect(url_for('dashboard'))
    else:
        flash('Email ou senha inválidos.', 'error')
        next_url = request.args.get('next')
        if next_url:
            return redirect(url_for('auth', message='Email ou senha inválidos.', type='error', next=next_url))
        else:
            return redirect(url_for('auth', message='Email ou senha inválidos.', type='error'))

@app.route('/dashboard')
@login_required
def dashboard():
    username = session.get('username', 'Usuário')
    is_admin = session.get('is_admin', False)
    
    user_id = session['user_id']
    
    user_books_entries = UserBook.query.filter_by(user_id=user_id).order_by(
        UserBook.status.desc(), UserBook.added_date.desc()
    ).all()
    
    books_data = {
        'lendo': [],
        'lido': [],
        'desejado': []
    }
    
    for entry in user_books_entries:
        book_info = {
            'entry_id': entry.id,
            'title': entry.book.title,
            'author': entry.book.author,
            'status': entry.status,
            'notes': entry.notes,
            'rating': entry.rating,
            'progress_pages': entry.progress_pages,
            'progress_percentage': entry.progress_percentage,
            'start_date': entry.start_date.strftime('%d/%m/%Y') if entry.start_date else 'N/A',
            'end_date': entry.end_date.strftime('%d/%m/%Y') if entry.end_date else 'N/A',
            'is_public_recommendation': entry.is_public_recommendation # Incluir no dashboard
        }
        books_data[entry.status].append(book_info)

    reading_goal = "Nenhuma meta definida ainda."

    return render_template('dashboard.html', 
                           username=username, 
                           is_admin=is_admin,
                           books_data=books_data,
                           reading_goal=reading_goal)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    flash('Você foi desconectado.', 'success')
    return redirect(url_for('index', message='Você foi desconectado.', type='success'))

@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        status = request.form['status']
        notes = request.form.get('notes')
        rating = request.form.get('rating', type=int)
        
        is_public_recommendation = request.form.get('is_public_recommendation') == 'on'

        book = Book.query.filter_by(title=title, author=author).first()
        if not book:
            book = Book(title=title, author=author)
            db.session.add(book)
            db.session.commit()

        user_id = session['user_id']
        new_user_book = UserBook(
            user_id=user_id,
            book_id=book.id,
            status=status,
            notes=notes,
            rating=rating,
            is_public_recommendation=is_public_recommendation
        )
        db.session.add(new_user_book)
        db.session.commit()
        
        flash(f'Livro "{title}" adicionado ao seu diário!', 'success')
        return redirect(url_for('index'))

    return render_template('add_book.html')

@app.route('/edit_book_entry/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_book_entry(entry_id):
    user_id = session['user_id']
    user_book_entry = UserBook.query.filter_by(id=entry_id, user_id=user_id).first_or_404()

    if request.method == 'POST':
        user_book_entry.status = request.form['status']
        user_book_entry.notes = request.form.get('notes')
        user_book_entry.rating = request.form.get('rating', type=int)
        
        user_book_entry.is_public_recommendation = request.form.get('is_public_recommendation') == 'on'

        progress_pages = request.form.get('progress_pages', type=int)
        progress_percentage = request.form.get('progress_percentage', type=int)
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        user_book_entry.progress_pages = progress_pages if progress_pages is not None else user_book_entry.progress_pages
        user_book_entry.progress_percentage = progress_percentage if progress_percentage is not None else user_book_entry.progress_percentage
        
        user_book_entry.start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else user_book_entry.start_date
        user_book_entry.end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else user_book_entry.end_date

        db.session.commit()
        flash('Entrada do livro atualizada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_book_entry.html', entry=user_book_entry)

@app.route('/delete_book_entry/<int:entry_id>', methods=['POST'])
@login_required
def delete_book_entry(entry_id):
    user_id = session['user_id']
    user_book_entry = UserBook.query.filter_by(id=entry_id, user_id=user_id).first_or_404()
    
    db.session.delete(user_book_entry)
    db.session.commit()
    flash('Livro removido do seu diário.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/all_recommendations')
def all_recommendations():
    all_public_entries = UserBook.query.filter_by(is_public_recommendation=True).order_by(UserBook.added_date.desc()).all()
    
    recommendations_data = []
    for entry in all_public_entries:
        recommendations_data.append({
            'title': entry.book.title,
            'author': entry.book.author,
            'notes': entry.notes,
            'rating': entry.rating,
            'username': entry.user.username,
            'added_date': entry.added_date.strftime('%d/%m/%Y %H:%M')
        })
    
    return render_template('all_recommendations.html', recommendations=recommendations_data)

# Rota para a página de leituras da comunidade
@app.route('/leitura')
def leitura():
    user_id = session.get('user_id')
    
    # Busca todos os livros da comunidade do banco de dados
    community_books = CommunityBook.query.order_by(CommunityBook.added_date.desc()).all()
    
    books_data = []
    for book in community_books:
        book_info = {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'snippet': book.snippet,
            'content': book.content,
            'contributor_username': book.contributor.username if book.contributor else 'Anônimo',
            'user_progress': None # Inicializa como None
        }
        
        # Se o usuário estiver logado, busca o progresso dele para este livro
        if user_id:
            progress = UserCommunityBookProgress.query.filter_by(
                user_id=user_id, 
                community_book_id=book.id
            ).first()
            if progress:
                book_info['user_progress'] = {
                    'current_page': progress.current_page,
                    'progress_percentage': progress.progress_percentage
                }
        books_data.append(book_info)
    return render_template('leitura.html', community_books=books_data)

# Rota para adicionar um livro à comunidade
@app.route('/add_community_book', methods=['POST'])
@login_required # Apenas usuários logados podem adicionar livros à comunidade
def add_community_book():
    title = request.form['title']
    author = request.form['author']
    snippet = request.form['snippet']
    content = request.form['content']
    user_id = session['user_id'] # Pega o ID do usuário logado

    if not title or not author or not snippet or not content:
        flash('Por favor, preencha todos os campos para adicionar um livro.', 'error')
        return redirect(url_for('leitura'))

    new_community_book = CommunityBook(
        title=title,
        author=author,
        snippet=snippet,
        content=content,
        contributor_id=user_id # Associa o livro ao usuário que o adicionou
    )
    db.session.add(new_community_book)
    db.session.commit()

    flash(f'Livro "{title}" adicionado à biblioteca da comunidade!', 'success')
    return redirect(url_for('leitura'))

# NOVA ROTA: Para atualizar o progresso de leitura do usuário
@app.route('/update_reading_progress', methods=['POST'])
@login_required
def update_reading_progress():
    data = request.get_json()
    book_id = data.get('book_id')
    current_page = data.get('current_page')
    progress_percentage = data.get('progress_percentage')
    user_id = session['user_id']

    if book_id is None or current_page is None or progress_percentage is None:
        return jsonify({'status': 'error', 'message': 'Dados incompletos.'}), 400

    progress_entry = UserCommunityBookProgress.query.filter_by(
        user_id=user_id, 
        community_book_id=book.id
    ).first()

    if progress_entry:
        progress_entry.current_page = current_page
        progress_entry.progress_percentage = progress_percentage
        progress_entry.last_read_date = datetime.utcnow() # Atualiza a data da última leitura
    else:
        new_progress = UserCommunityBookProgress(
            user_id=user_id,
            community_book_id=book_id,
            current_page=current_page,
            progress_percentage=progress_percentage
        )
        db.session.add(new_progress)
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Progresso atualizado.'}), 200


# --- Rotas Administrativas ---
@app.route('/users')
@admin_required
def list_users():
    users = User.query.all()
    users_list_data = []
    for user in users:
        users_list_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin
        })
    return render_template('users.html', users=users_list_data)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if 'user_id' in session and session['user_id'] == user_id:
        flash('Você não pode excluir sua própria conta de administrador por aqui.', 'error')
        return redirect(url_for('list_users'))

    user_to_delete = User.query.get(user_id)

    if user_to_delete:
        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash(f'Usuário "{user_to_delete.email}" excluído com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir usuário: {e}', 'error')
    else:
        flash('Usuário não encontrado.', 'error')
    
    return redirect(url_for('list_users'))

if __name__ == '__main__':
    # Remova db.create_all() daqui se estiver usando Flask-Migrate
    # db.create_all() 
    app.run(debug=True)
