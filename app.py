from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Création de l'instance Flask
app = Flask(__name__)

# Configuration de la clé secrète et de la base de données
app.config['SECRET_KEY'] = '5f89fa56ea3bf3e8385e14b600c4e4a7f557c4418c707eecbd423a3d8921dcf0'  # Utilisée pour sécuriser les sessions
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'  # URI pour la base de données SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Désactiver les notifications de modifications****

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)

# Définition des modèles
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Clé primaire
    username = db.Column(db.String(150), unique=True, nullable=False)  # Nom d'utilisateur unique
    email = db.Column(db.String(150), unique=True, nullable=False)  # Adresse e-mail unique
    password = db.Column(db.String(150), nullable=False)  # Mot de passe haché

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Clé primaire
    title = db.Column(db.String(200), nullable=False)  # Titre de l'article
    content = db.Column(db.Text, nullable=False)  # Contenu de l'article
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)  # Date de publication****
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Clé étrangère pour l'auteur
    author = db.relationship('User', backref=db.backref('posts', lazy=True))  # Relation avec le modèle User

# Création des tables si elles n'existent pas
with app.app_context():
    db.create_all()

# Routes et vues

@app.route('/')
def index():
    posts = Post.query.order_by(Post.date_posted.desc()).all()  # Récupération des articles, triés du plus récent au plus ancien
    return render_template('index.html', posts=posts)  # Rendu du template avec les articles

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Si le formulaire est soumis
        email = request.form['email']  # Récupération de l'email du formulaire
        password = request.form['password']  # Récupération du mot de passe du formulaire
        user = User.query.filter_by(email=email).first()  # Recherche de l'utilisateur par e-mail
        if user and check_password_hash(user.password, password):  # Vérification du mot de passe
            session['user_id'] = user.id  # Stockage de l'ID utilisateur dans la session
            flash('Connexion réussie!')  # Message flash pour indiquer la réussite
            return redirect(url_for('index'))  # Redirection vers la page d'accueil
        flash('Échec de la connexion. Vérifiez votre e-mail et votre mot de passe.')  # Message flash en cas d'échec
    return render_template('login.html')  # Rendu du template de connexion

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Suppression de l'ID utilisateur de la session
    flash('Déconnexion réussie!')  # Message flash pour indiquer la déconnexion
    return redirect(url_for('index'))  # Redirection vers la page d'accueil

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # Si le formulaire est soumis
        username = request.form['username']  # Récupération du nom d'utilisateur du formulaire
        email = request.form['email']  # Récupération de l'email du formulaire
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')  # Hachage du mot de passe
        new_user = User(username=username, email=email, password=password)  # Création d'un nouvel utilisateur
        db.session.add(new_user)  # Ajout de l'utilisateur à la session
        db.session.commit()  # Commit des changements dans la base de données
        flash('Inscription réussie!')  # Message flash pour indiquer la réussite
        return redirect(url_for('login'))  # Redirection vers la page de connexion
    return render_template('register.html')  # Rendu du template d'inscription

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)  # Récupération de l'article par ID ou erreur 404 si non trouvé
    return render_template('post.html', post=post)  # Rendu du template avec l'article

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:  # Vérification si l'utilisateur est connecté
        flash('Vous devez être connecté pour créer un article.')  # Message flash si non connecté
        return redirect(url_for('login'))  # Redirection vers la page de connexion
    if request.method == 'POST':  # Si le formulaire est soumis
        title = request.form['title']  # Récupération du titre du formulaire
        content = request.form['content']  # Récupération du contenu du formulaire
        new_post = Post(title=title, content=content, author_id=session['user_id'])  # Création d'un nouvel article
        db.session.add(new_post)  # Ajout de l'article à la session
        db.session.commit()  # Commit des changements dans la base de données
        flash('Article créé avec succès!')  # Message flash pour indiquer la réussite
        return redirect(url_for('index'))  # Redirection vers la page d'accueil
    return render_template('create.html')  # Rendu du template de création d'article

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)  # Récupération de l'article par ID ou erreur 404 si non trouvé
    if post.author_id != session.get('user_id'):  # Vérification si l'utilisateur connecté est l'auteur de l'article
        flash('Vous n\'êtes pas autorisé à modifier cet article.')  # Message flash si l'utilisateur n'est pas l'auteur
        return redirect(url_for('index'))  # Redirection vers la page d'accueil
    
    if request.method == 'POST':  # Si le formulaire est soumis
        post.title = request.form['title']  # Mise à jour du titre de l'article
        post.content = request.form['content']  # Mise à jour du contenu de l'article
        post.date_posted = datetime.utcnow()  # Mise à jour de la date de publication à l'heure actuelle
        db.session.commit()  # Commit des changements dans la base de données
        flash('Article mis à jour avec succès!')  # Message flash pour indiquer la réussite
        return redirect(url_for('post', post_id=post.id))  # Redirection vers la page de l'article mis à jour
    
    return render_template('edit.html', post=post)  # Rendu du template pour éditer l'article

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)  # Récupération de l'article par ID ou erreur 404 si non trouvé
    if post.author_id != session.get('user_id'):  # Vérification si l'utilisateur connecté est l'auteur de l'article
        flash('Vous n\'êtes pas autorisé à supprimer cet article.')  # Message flash si l'utilisateur n'est pas l'auteur
        return redirect(url_for('index'))  # Redirection vers la page d'accueil
    
    db.session.delete(post)  # Suppression de l'article de la base de données
    db.session.commit()  # Commit des changements dans la base de données
    flash('Article supprimé avec succès!')  # Message flash pour indiquer la réussite
    return redirect(url_for('index'))  # Redirection vers la page d'accueil

# Exécution de l'application
if __name__ == "__main__":
    app.run(debug=True) # Lancement de l'application en mode débogage
