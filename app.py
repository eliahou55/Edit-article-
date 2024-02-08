from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from werkzeug.utils import secure_filename
import os
from datetime import date
from flask_mail import Mail , Message





app = Flask(__name__)
app.secret_key = 'votre_cle_secrete'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/images')  # Utilisation du chemin absolu pour le dossier d'images
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # Extensions autorisées pour les images


app.config['MAIL_SERVER'] = 'localhost'  # Utilisation de MailDev, donc le serveur SMTP est local
app.config['MAIL_PORT'] = 1025  # Port par défaut de MailDev
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None

mail = Mail(app)



def connect_db():
    return psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="12345678abcD&", port=5432)


def insert_article(title, description, admin_id, image_filename):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute('''
        INSERT INTO article (title, description, article_date, admin_id, image_path)
        VALUES (%s, %s, %s, %s, %s)
    ''', (title, description, date.today(), admin_id, image_filename))

    conn.commit()
    cur.close()
    conn.close()


def authenticate_user(email, password):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM admin WHERE email = %s AND password = %s", (email, password))
    user = cur.fetchone()

    cur.close()
    conn.close()

    return user


def get_all_articles():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute('SELECT * FROM article')
    articles = cur.fetchall()

    cur.close()
    conn.close()

    return articles


def get_user_details(user_id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT name, email FROM admin WHERE id = %s", (user_id,))
    user_details = cur.fetchone()

    cur.close()
    conn.close()

    return user_details


def insert_admin(name, email, password):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute('''
        INSERT INTO admin (name, email, password)
        VALUES (%s, %s, %s)
    ''', (name, email, password))

    conn.commit()
    cur.close()
    conn.close()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# requette pour l'affichage de l'auteur par article

@app.context_processor
def utility_processor():
    return dict(get_author_name=get_author_name)

def get_author_name(admin_id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT name FROM admin WHERE id = %s", (admin_id,))
    author_name = cur.fetchone()[0] if cur.rowcount > 0 else "Auteur inconnu"

    cur.close()
    conn.close()

    return author_name


# Route pour la réinitialisation du mot de passe
@app.route('/reset_password_confirm', methods=['GET'])
def reset_password_confirm():
    # Récupérez le jeton de réinitialisation à partir de la requête
    token = request.args.get('token')
    print(f"Token reçu : {token}")


    try:
        # Connexion à la base de données PostgreSQL
        conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="12345678abcD&", port=5432)
        cur = conn.cursor()

        # Vérification du jeton et récupération de l'ID de l'admin associé
        cur.execute("SELECT id FROM admin WHERE tokens = %s", (token,))
        admin_id = cur.fetchone()

        # Fermeture de la connexion
        cur.close()
        conn.close()

        if admin_id:
            # Si le jeton est valide, affichez le formulaire de réinitialisation du mot de passe
            return render_template('reset_password_confirm.html', token=token)
        else:
            flash("Jeton de réinitialisation invalide. Veuillez réessayer.", 'danger')
            return redirect(url_for('login'))
    except Exception as e:
        print(f"Erreur lors de la vérification du jeton de réinitialisation : {e}")
        flash("Une erreur s'est produite. Veuillez réessayer.", 'danger')
        return redirect(url_for('login'))

# Route pour la réinitialisation du mot de passe
@app.route('/reset_password', methods=['POST'])
def reset_password():
    # Récupérez les données du formulaire de réinitialisation du mot de passe
    token = request.form.get('token')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Vérification de la correspondance des mots de passe
    if new_password != confirm_password:
        flash("Les mots de passe ne correspondent pas. Veuillez réessayer.", 'danger')
        return redirect(url_for('reset_password_confirm', token=token))

    try:
        # Connexion à la base de données PostgreSQL
        conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="12345678abcD&", port=5432)
        cur = conn.cursor()

        # Vérification du jeton et récupération de l'ID de l'admin associé
        cur.execute("SELECT id FROM admin WHERE tokens = %s", (token,))
        admin_id = cur.fetchone()

        if admin_id:
            # Mise à jour du mot de passe
            cur.execute("UPDATE admin SET password = %s, tokens = NULL WHERE id = %s", (new_password, admin_id[0]))

            # Fermeture de la connexion et validation des changements
            conn.commit()
            cur.close()
            conn.close()

            flash('Le mot de passe a été réinitialisé avec succès. Connectez-vous avec votre nouveau mot de passe.', 'success')
            return redirect(url_for('login'))
        else:
            flash("Jeton de réinitialisation invalide. Veuillez réessayer.", 'danger')
            return redirect(url_for('reset_password_confirm', token=token))
    except Exception as e:
        print(f"Erreur lors de la mise à jour du mot de passe : {e}")
        flash("Une erreur s'est produite lors de la réinitialisation du mot de passe. Veuillez réessayer.", 'danger')
        return redirect(url_for('reset_password_confirm', token=token))

# Route pour la demande de réinitialisation de mot de passe
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        # Génération du jeton de réinitialisation (pour simplifier, ici on utilise l'email)
        reset_token = email

        try:
            # Connexion à la base de données PostgreSQL
            conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="12345678abcD&", port=5432)
            cur = conn.cursor()

            # Enregistrement du jeton de réinitialisation dans la base de données
            cur.execute("UPDATE admin SET tokens = %s WHERE email = %s", (reset_token, email))
            
            # Fermeture de la connexion et validation des changements
            conn.commit()
            cur.close()
            conn.close()

            reset_link = f"http://127.0.0.1:5000/reset_password_confirm?token={reset_token}"

            # Envoi de l'e-mail avec le lien de réinitialisation
            msg = Message('Réinitialisation du mot de passe', sender='steven232stv@gmail.com', recipients=[email])
            msg.body = f"Pour réinitialiser votre mot de passe, veuillez suivre le lien : {reset_link}"

            mail.send(msg)
            flash('Un e-mail de réinitialisation du mot de passe a été envoyé à votre adresse.', 'info')
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'e-mail : {e}")
            flash("Une erreur s'est produite lors de l'envoi de l'e-mail de réinitialisation.", 'danger')

    return render_template('forgot_password.html')
# Route pour la création du jeton de réinitialisation
@app.route('/create_reset_token', methods=['POST'])
def create_reset_token():
    if request.method == 'POST':
        email = request.form.get('email')

        # Génération du jeton de réinitialisation (pour simplifier, ici on utilise l'email)
        reset_token = email

        try:
            # Connexion à la base de données PostgreSQL
            conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="12345678abcD&", port=5432)
            cur = conn.cursor()

            # Enregistrement du jeton de réinitialisation dans la base de données
            cur.execute("UPDATE admin SET tokens = %s WHERE email = %s", (reset_token, email))
            
            # Fermeture de la connexion et validation des changements
            conn.commit()
            cur.close()
            conn.close()

            reset_link = f"http://127.0.0.1:5000/reset_password_confirm?token={reset_token}"

            # Envoi de l'e-mail avec le lien de réinitialisation
            msg = Message('Réinitialisation du mot de passe', sender='steven232stv@gmail.com', recipients=[email])
            msg.body = f"Pour réinitialiser votre mot de passe, veuillez suivre le lien : {reset_link}"

            mail.send(msg)
            flash('Un e-mail de réinitialisation du mot de passe a été envoyé à votre adresse.', 'info')
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'e-mail : {e}")
            flash("Une erreur s'est produite lors de l'envoi de l'e-mail de réinitialisation.", 'danger')

        return redirect(url_for('login'))

# Route pour la vérification du jeton et la redirection vers la page de réinitialisation
@app.route('/verify_reset_token/<token>', methods=['GET'])
def verify_reset_token(token):
    try:
        # Connexion à la base de données PostgreSQL
        conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="12345678abcD&", port=5432)
        cur = conn.cursor()

        # Vérification du jeton et récupération de l'ID de l'admin associé
        cur.execute("SELECT id FROM admin WHERE tokens = %s", (token,))
        admin_id = cur.fetchone()

        # Fermeture de la connexion
        cur.close()
        conn.close()

        if admin_id:
            # Si le jeton est valide, redirigez vers la page de réinitialisation du mot de passe
            return redirect(url_for('reset_password_confirm', token=token))
        else:
            flash("Jeton de réinitialisation invalide. Veuillez réessayer.", 'danger')
            return redirect(url_for('login'))
    except Exception as e:
        print(f"Erreur lors de la vérification du jeton de réinitialisation : {e}")
        flash("Une erreur s'est produite. Veuillez réessayer.", 'danger')
        return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def root():
    # Rediriger directement vers la page de connexion
    return redirect(url_for('bienvenue'))


@app.route('/bienvenue')
def bienvenue():
    return render_template('bienvenue.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('register'))
        try:
            # Insérer dans la base de données
            insert_admin(name, email, password)

            # Rediriger vers la page de connexion ou effectuer une autre action après l'inscription réussie
            flash('Inscription réussie. Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            # Gestion des erreurs
            print(f"Erreur lors de l'inscription : {e}")
            flash("Une erreur s'est produite lors de l'inscription. Veuillez réessayer.", 'danger')

    return render_template('register.html', request_method=request.method, form_data=None)

@app.route('/read', methods=['GET', 'POST'])
def read():
    # Vérifiez d'abord si l'utilisateur est connecté
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Récupérer les détails de l'utilisateur
    user_details = get_user_details(session['user_id'])

    # Ensuite, vérifiez si la déconnexion a été demandée
    if request.args.get('logout') == 'true':
        # Déconnectez l'utilisateur et redirigez-le vers la page de connexion
        session.pop('user_id', None)
        return redirect(url_for('login'))
    request_method = request.method
    form_data = None
    title = None
    description = None
    image_path = None

    articles = get_all_articles()
    print(articles)


    return render_template('read.html', request_method=request_method, form_data=form_data, title=title,
                           description=description, image_path=image_path, articles=articles, user_details=user_details)

@app.route('/poster', methods=['GET', 'POST'])
def hello_word():
    # Vérifiez d'abord si l'utilisateur est connecté
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Récupérer les détails de l'utilisateur
    user_details = get_user_details(session['user_id'])

    # Ensuite, vérifiez si la déconnexion a été demandée
    if request.args.get('logout') == 'true':
        # Déconnectez l'utilisateur et redirigez-le vers la page de connexion
        session.pop('user_id', None)
        return redirect(url_for('login'))

    # Continuez avec le reste du code seulement si l'utilisateur est connecté
    request_method = request.method
    form_data = None
    title = None
    description = None
    image_path = None

    articles = get_all_articles()
    print(articles)

    if request.method == 'POST':
        form_data = request.form

        # Extraire le titre, la description et le chemin de l'image
        title = form_data.get('title')
        description = form_data.get('description')
        image = request.files['image']

        if image and allowed_file(image.filename):
            # Utilisez secure_filename pour garantir la sécurité du nom du fichier
            image_filename = secure_filename(image.filename)

            try:
                # Insérer dans la base de données avec l'admin_id récupéré de la session
                insert_article(title, description, session['user_id'], image_filename)

                # Enregistrez également l'image dans le dossier 'images' à la racine du projet
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

                # Rediriger en cas de succès
                return redirect(url_for('name'))

            except Exception as e:
                # Gestion des erreurs
                print(f"Erreur lors de l'insertion dans la base de données : {e}")

        else:
            flash('Extension de fichier non autorisée. Utilisez uniquement les extensions : png, jpg, jpeg, gif.', 'danger')

    return render_template('edit_article.html', request_method=request_method, form_data=form_data, title=title,
                           description=description, image_path=image_path, articles=articles, user_details=user_details)


@app.route('/name')
def name():
    # Vérifiez d'abord si l'utilisateur est connecté
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Récupérer les détails de l'utilisateur
    user_details = get_user_details(session['user_id'])

    return render_template('comfirmation.html', user_details=user_details)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Ajoutez une fonction de déconnexion
    if request.args.get('logout') == 'true':
        session.pop('user_id', None)
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = authenticate_user(email, password)

        if user:
            # L'authentification a réussi, stockez l'identifiant de l'utilisateur dans la session
            session['user_id'] = user[0]  # Supposons que l'identifiant de l'utilisateur est en position 0 dans la ligne de résultat
            return redirect(url_for('read'))
        else:
            # L'authentification a échoué, ajoutez un message flash pour avertir l'utilisateur
            flash('Identifiants incorrects. Veuillez réessayer.', 'danger')

    return render_template('conexion.html')


@app.route('/delete/<int:article_id>', methods=['GET'])
def delete_article(article_id):
    conn = connect_db()
    cur = conn.cursor()

    # Récupérer l'auteur de l'article
    cur.execute("SELECT admin_id, image_path FROM article WHERE article_id = %s", (article_id,))
    article_info = cur.fetchone()

    # Vérifier si l'utilisateur connecté est l'auteur de l'article
    if 'user_id' not in session or session['user_id'] != article_info[0]:
        flash("danger Vous ne pouvez supprimer que vos propres articles.")
        return redirect(url_for('hello_word'))

    # Supprimer l'article avec l'ID donné
    cur.execute("DELETE FROM article WHERE article_id = %s", (article_id,))

    # Supprimer également le fichier image associé
    image_path = article_info[1]
    if image_path:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    conn.commit()
    cur.close()
    conn.close()

    flash("success L'article a été supprimé avec succès.")
    return redirect(url_for('read'))


@app.route('/edit/<int:article_id>', methods=['GET', 'POST'])
def edit_article(article_id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT article_id, title, description, article_date, admin_id, image_path FROM article WHERE article_id = %s", (article_id,))
    article_data = cur.fetchone()

    if 'user_id' not in session or session['user_id'] != article_data[4]:
        flash("danger Vous ne pouvez modifier que vos propres articles.")
        return redirect(url_for('hello_word'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        print(f"Article ID: {article_id}")
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"Existing Image Path: {article_data[3]}")  

        cur.execute("UPDATE article SET title = %s, description = %s WHERE article_id = %s", (title, description, article_id))
        conn.commit()

        # Gérer l'upload d'une nouvelle image
        if 'image' in request.files:
            image = request.files['image']

            if image.filename != '':
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)

                # Mettez à jour le chemin de l'image dans la base de données
                cur.execute("UPDATE article SET image_path = %s WHERE article_id = %s", (filename, article_id))
                conn.commit()

        cur.close()
        conn.close()

        flash("success L'article a été modifié avec succès.")
        return redirect(url_for('read'))

    else:
        print(f"Article ID (GET): {article_id}")
        print(f"Existing Title: {article_data[1]}")
        print(f"Existing Description: {article_data[2]}")
        print(f"Existing Image Path: {article_data[3]}")
        cur.close()
        conn.close()
        return render_template('update_article.html', article=article_data)





if __name__ == '__main__':
    app.run(debug=True)