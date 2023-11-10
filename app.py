import platform
from datetime import datetime
from functools import wraps

from flask_bcrypt import Bcrypt
from flask import Flask, flash, redirect, render_template, request, url_for, session
import pymysql

app = Flask(__name__)

bcrypt = Bcrypt(app)

# ? Les informations pour la connexion à ma db
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'zorodb'


app.config['SECRET_KEY'] = 'secret key'


# ! Mécanisme de protection pour obligier le user à se connecter
# ? Utiliser le décorateur @login_required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'danger')
            return redirect(url_for('connexion'))
        return f(*args, **kwargs)
    return decorated_function


# ? Ou Vérifier si l'utilisateur est connecté au début de chaque route
    # if 'user_id' not in session:
    #     flash('Veuillez vous connecter pour accéder à cette page.', 'danger')
    #     return redirect(url_for('connexion'))


# ! Routes / et acceuil
@app.route("/")
def connexion():
    return render_template("connexion.html")


@app.route("/acceuil/")
@login_required
def acceuil():
    return render_template("base.html")


# ! Gestion Back-End des Users
# ? Register user
@app.route('/register', methods=['GET', 'POST'])
def register():
    # ? Connection à ma db
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
    cursor = mysql.cursor()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Vérifions si l'utilisateur existe déjà
        select_query = "SELECT id FROM Users WHERE username = %s"
        cursor.execute(select_query, (username,))
        user_exist = cursor.fetchone()

        if user_exist:
            flash(
                "Cet utilisateur existe déjà. Veuillez choisir un autre nom d'utilisateur.", 'danger')
        else:
            # Hash du mot de passe
            hashed_password = bcrypt.generate_password_hash(
                password)

            # Insertion de l'utilisateur dans la base de données
            insert_query = "INSERT INTO Users (username, password_hash) VALUES (%s, %s)"
            cursor.execute(insert_query, (username, hashed_password))
            mysql.commit()

            # Récupérerons l'ID de l'utilisateur nouvellement inscrit
            cursor.execute(
                "SELECT id FROM Users WHERE username = %s", (username,))
            user_id = cursor.fetchone()[0]

            # Connectons l'utilisateur en stockant son ID dans la session
            session['user_id'] = user_id

            flash('Inscription réussie! Vous êtes maintenant connecté.', 'success')
            return redirect(url_for('acceuil'))

    return render_template('register.html')


# ? Login user
@app.route('/', methods=['GET', 'POST'])
def login():
    # ? Connection à ma db
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
    cursor = mysql.cursor()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Récupérons l'utilisateur depuis la base de données
        select_query = "SELECT id, username, password_hash FROM Users WHERE username = %s"
        cursor.execute(select_query, (username,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user[2], password):
            # Si mot de passe est correct, alors enregistrons l'utilisateur dans la session
            session['user_id'] = user[0]
            flash('Connexion réussie!', 'success')
            return redirect(url_for('acceuil'))
        else:
            flash(f"Nom d'utilisateur: {
                  username} ou mot de passe incorrect: {password}.", 'danger')

    return render_template('connexion.html')


# ? Route pour la déconnexion
@app.route('/logout')
@login_required
def logout():

    # Déconnectons l'utilisateur en supprimant son ID de session
    session.pop('user_id', None)

    flash('Déconnexion réussie!', 'success')
    return redirect(url_for('connexion'))

# ! Gestion Back-End des Produits
# ? Affichons les produits


@app.route("/produit/")
@login_required
def produit():
    # ? Connection à ma db
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
    cursor = mysql.cursor()

    cursor.execute("SELECT * FROM Produit")
    produits = cursor.fetchall()
    print(produits)
    cursor.close()
    return render_template("produits/produit.html", produits=produits, title="produit")


# ? Ajouter un nouveau produit
@app.route("/ajouter_produit/", methods=["POST", "GET"])
@login_required
def ajouter_produit():
    try:
        if request.method == 'GET':
            return render_template('produits/ajouter_produit.html', title="ajouter_produit")

        if request.method == 'POST':
            # ? Connection à ma db
            mysql = pymysql.connect(
                host=app.config['MYSQL_HOST'],
                user=app.config['MYSQL_USER'],
                password=app.config['MYSQL_PASSWORD'],
                db=app.config['MYSQL_DB']
            )

            # ? Utilisons un curseur pour exécuter nos requêtes SQL
            cursor = mysql.cursor()
            name = request.form.get('name')
            categorie = request.form.get('categorie')
            prix = request.form.get('prix')
            # Exécutez la requête SQL pour ajouter un nouveau produit
            insert_query = """
                INSERT INTO Produit (NomProduit, CatProduit	, PrixUnitaire	)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (name, categorie, prix))
            mysql.commit()
            cursor.close()

            flash(f"Le produit {name} a été ajouté avec succès", 'success')
            return redirect("/produit/")

    except Exception as e:
        # Gérez les erreurs, par exemple, affichez un message d'erreur
        flash(f"Erreur lors de l'ajout du produit: {str(e)}", 'error')
        return redirect('/produit/')


# ? Récupération de l'ID du produit à supprimer
@app.route("/supp_prod_traitement/<int:_id>")
@login_required
def supp_prod_traitement(_id):
    # ? Connection à ma db
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
    cursor = mysql.cursor()
    # Récupérer les informations du magasin à supprimer
    select_query = "SELECT * FROM Produit WHERE IdProduit=%s"
    cursor.execute(select_query, (_id,))
    produit = cursor.fetchone()
    cursor.close()

    return render_template("produits/supp_prod_traitement.html", produit=produit, title="traitement_suppression")


# ? Suppression définitive du produit
@app.route("/supp_def_produit/<int:_id>")
@login_required
def supp_def_produit(_id):
    try:
        # ? Connection à ma db
        mysql = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB']
        )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
        cursor = mysql.cursor()
        # Requête SQL de suppression
        delete_query = "DELETE FROM Produit WHERE IdProduit=%s"
        cursor.execute(delete_query, (_id,))

        # Validation des changements dans la base de données
        mysql.commit()
        cursor.close()

        flash(f"Le magasin N°{_id} a été supprimé avec succès.")
        return redirect("/produit/")
    except Exception as e:
        # En cas d'erreur, annuler les changements et afficher un message d'erreur
        mysql.rollback()
        flash(f"Erreur lors de la suppression du magasin: {str(e)}", 'error')

        return redirect('/produit/')


# ? Modification du produit
@app.route("/modifier_produit/<int:_id>", methods=["POST", "GET"])
@login_required
def modifier_produit(_id):
    # ? Connection à ma db
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
    cursor = mysql.cursor()
    if request.method == 'POST':

        name = request.form.get('name')
        categorie = request.form.get('categorie')
        prix = request.form.get('prix')

        # Requête SQL de mise à jour
        # NomProduit, CatProduit	, PrixUnitaire
        update_query = "UPDATE Produit SET NomProduit=%s, CatProduit=%s, PrixUnitaire=%s WHERE IdProduit=%s"
        cursor.execute(update_query, (name, categorie, prix, _id))
        mysql.commit()
        cursor.close

        flash(f"Le produit n°{_id} a été modifié avec succès.")
        return redirect("/produit/")

    # Récupérerons les informations du magasin
    select_query = "SELECT * FROM Produit WHERE IdProduit=%s"
    cursor.execute(select_query, (_id,))
    produit = cursor.fetchone()
    return render_template("produits/modifier_produit.html", produit=produit, title="modifier_produit")


# ! Gestion Back-End des Magasins
# ? Affichons les magasins
@app.route("/magasin/")
@login_required
def magasin():
    # ? Connection à ma db
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
    cursor = mysql.cursor()

    cursor.execute("SELECT * FROM Magasin")
    magasins = cursor.fetchall()
    print(magasins)
    cursor.close()
    return render_template("magasins/magasin.html", magasins=magasins, title="magasin")


# ? Ajouter un nouveau magasin
@app.route("/ajouter_magasin/", methods=["POST", "GET"])
@login_required
def ajouter_magasin():
    try:
        if request.method == 'GET':
            return render_template('magasins/ajouter_magasin.html', title="ajouter_produit")

        if request.method == 'POST':
            # ? Connection à ma db
            mysql = pymysql.connect(
                host=app.config['MYSQL_HOST'],
                user=app.config['MYSQL_USER'],
                password=app.config['MYSQL_PASSWORD'],
                db=app.config['MYSQL_DB']
            )

            # ? Utilisons un curseur pour exécuter nos requêtes SQL
            cursor = mysql.cursor()
            name = request.form.get('name')
            adresse = request.form.get('adresse')
            telephone = request.form.get('telephone')
            email = request.form.get('email')
            # Exécutez la requête SQL pour ajouter un nouveau produit
            insert_query = """
                INSERT INTO Magasin (NomMagasin, AdresseMagasin	, Telephone, mail	)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (name, adresse, telephone, email))
            mysql.commit()
            cursor.close()

            flash(f"Le magasin {name} a été ajouté avec succès", 'success')
            return redirect("/magasin/")

    except Exception as e:
        # Gérez les erreurs, par exemple, affichez un message d'erreur
        flash(f"Erreur lors de l'ajout du magasin: {str(e)}", 'error')
        return redirect('/magasin/')


# ? Récupération de l'ID du produit à supprimer
@app.route("/supp_mag_traitement/<int:_id>")
@login_required
def supp_mag_traitement(_id):
    # ? Connection à ma db
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
    cursor = mysql.cursor()
    # Récupérer les informations du magasin à supprimer
    select_query = "SELECT * FROM Magasin WHERE IdMagasin=%s"
    cursor.execute(select_query, (_id,))
    magasin = cursor.fetchone()
    cursor.close()

    return render_template("magasins/supp_mag_traitement.html", magasin=magasin, title="traitement_suppression")


# ? Suppression définitive du produit
@app.route("/supp_def_magasin/<int:_id>")
@login_required
def supp_def_magasin(_id):
    try:
        # ? Connection à ma db
        mysql = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB']
        )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
        cursor = mysql.cursor()
        # Requête SQL de suppression
        delete_query = "DELETE FROM Magasin WHERE IdMagasin=%s"
        cursor.execute(delete_query, (_id,))

        # Validation des changements dans la base de données
        mysql.commit()
        cursor.close()

        flash(f"Le magasin N°{_id} a été supprimé avec succès.")
        return redirect("/magasin/")
    except Exception as e:
        # En cas d'erreur, annuler les changements et afficher un message d'erreur
        mysql.rollback()
        flash(f"Erreur lors de la suppression du magasin: {str(e)}", 'error')

        return redirect('/magasin/')

 # ? Modification du produit


@app.route("/modifier_magasin/<int:_id>", methods=["POST", "GET"])
@login_required
def modifier_magasin(_id):
    # ? Connection à ma db
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
    cursor = mysql.cursor()
    if request.method == 'POST':

        name = request.form.get('name')
        adresse = request.form.get('adresse')
        telephone = request.form.get('telephone')
        email = request.form.get('email')

        # Requête SQL de mise à jour
        # NomMagasin, AdresseMagasin	, Telephone, mail
        update_query = "UPDATE Magasin SET NomMagasin=%s, AdresseMagasin=%s, Telephone=%s, mail=%s WHERE IdMagasin=%s"
        cursor.execute(update_query, (name, adresse, telephone, email, _id))
        mysql.commit()
        cursor.close

        flash(f"Le produit n°{_id} a été modifié avec succès.")
        return redirect("/magasin/")

    # Récupérerons les informations du magasin
    select_query = "SELECT * FROM Magasin WHERE IdMagasin=%s"
    cursor.execute(select_query, (_id,))
    magasin = cursor.fetchone()
    return render_template("magasins/modifier_magasin.html", magasin=magasin, title="modifier_magasin")


# ! Gestion Back-End des Ventes
# ? Afficher la page d'enregistrement des ventes
@app.route('/vente/', methods=['GET', 'POST'])
@login_required
def vente():
    # ? Connection à ma db
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
    cursor = mysql.cursor()

    if request.method == 'POST':
        id_magasin = request.form.get('magasin')
        id_produit = request.form.get('produit')
        quantite = int(request.form.get('quantite'))

        # Récupération du stock actuel du produit dans le magasin
        select_stock_query = "SELECT Quantitestock FROM Stock WHERE IdMagasin=%s AND IdProduit=%s"
        cursor.execute(select_stock_query, (id_magasin, id_produit))
        stock_actuel = cursor.fetchone()

        if stock_actuel and stock_actuel[0] >= quantite:
            # Récupération du prix unitaire depuis la table Produit
            select_produit_query = "SELECT PrixUnitaire FROM Produit WHERE idProduit=%s"
            cursor.execute(select_produit_query, (id_produit,))
            prix_unitaire = cursor.fetchone()[0]
            print(prix_unitaire)

            prix_total = quantite * prix_unitaire
            print(prix_total)

            # Récupération de la date du jour
            date_vente = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            try:
                # Insertion de la vente dans la table Vente avec les ID du produit et du    magasin
                insert_vente_query = "INSERT INTO Vente (IdMagasin, IdProduit,  quantiteVendu, Prixtotal, Datevente) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(insert_vente_query, (id_magasin,
                                                    id_produit, quantite, prix_total, date_vente))

                # Mettre à jour la quantité de stock dans la table Stock
                new_stock = stock_actuel[0] - quantite
                update_stock_query = "UPDATE Stock SET Quantitestock=%s WHERE IdMagasin=%s AND IdProduit=%s"
                cursor.execute(update_stock_query,
                               (new_stock, id_magasin, id_produit))

                mysql.commit()

                flash(f"La vente a été enregistrée avec succès. Prix total: {
                    prix_total}", 'success')
                return redirect('/liste_vente')
            except Exception as e:
                # En cas d'erreur, annuler les changements et afficher un message d'erreur
                mysql.rollback()
                flash(f"Erreur lors de l'enregistrement de la vente: {
                    str(e)}", 'error')

        else:
            flash("Quantité insuffisante en stock.", 'error')
            return redirect("/vente/")

    # Remplir les options des Select avec les noms des magasins et des produits
    select_magasin_query = "SELECT IdMagasin, NomMagasin FROM Magasin GROUP BY NomMagasin "
    cursor.execute(select_magasin_query)
    magasins = cursor.fetchall()

    select_produit_query = "SELECT IdProduit, NomProduit FROM Produit GROUP BY NomProduit"
    cursor.execute(select_produit_query)
    produits = cursor.fetchall()

    return render_template('ventes/vente.html', magasins=magasins, produits=produits)


# ? Afficher toutes les ventes
@app.route('/liste_vente/', methods=['GET'])
@login_required
def liste_vente():
    try:
        # ? Connection à ma db
        mysql = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB']
        )

        # ? Utilisons un curseur pour exécuter nos requêtes SQL
        cursor = mysql.cursor()

        # Exécutez la requête SQL pour récupérer les données
        select_query = """
            SELECT p.NomProduit, v.IdProduit, v.Prixtotal AS montant_total,
                   v.Quantitevendu, v.IdVente
            FROM Vente v
            JOIN Produit p ON v.IdProduit = p.IdProduit
            ORDER BY v.IdVente
        """
        cursor.execute(select_query)
        results = cursor.fetchall()

        return render_template('ventes/liste_vente.html', results=results)
    except Exception as e:
        # Gérez les erreurs, par exemple, affichez un message d'erreur
        flash(f"Erreur lors de la récupération des données: {str(e)}", 'error')
        return redirect('/')


# ? Modifier les ventes
@app.route('/modifier_vente/<int:_id>', methods=['GET', 'POST'])
@login_required
def modifier_vente(_id):
    try:
        # ? Connection à ma db
        mysql = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB']
        )

        # ? Utilisons un curseur pour exécuter nos requêtes SQL
        cursor = mysql.cursor()

        if request.method == 'GET':
            # Récupérons  les détails de la vente
            select_query = """
                SELECT v.IdVente, v.Quantitevendu, v.Prixtotal, p.IdProduit, p.PrixUnitaire, m.IdMagasin, p.NomProduit
                FROM Vente v
                JOIN Produit p ON v.IdProduit = p.IdProduit
                JOIN Magasin m ON v.IdMagasin = m.IdMagasin
                WHERE v.IdVente = %s
            """
            cursor.execute(select_query, (_id,))
            vente_details = cursor.fetchone()

            print(vente_details)
            print(vente_details[2])

            if not vente_details:
                flash("La vente spécifiée n'existe pas.", 'danger')
                # Rediriger vers la liste des ventes
                return redirect(url_for('liste_vente'))

            # Récupérons la liste des produits et des magasins puis stockons les dans des sélect
            cursor.execute("SELECT IdProduit, NomProduit FROM Produit")
            produits = cursor.fetchall()

            cursor.execute("SELECT IdMagasin, NomMagasin FROM Magasin")
            magasins = cursor.fetchall()

            return render_template('ventes/modifier_vente.html', vente_details=vente_details, produits=produits, magasins=magasins)

        if request.method == 'POST':
            nouvelle_quantite = int(request.form.get('nouvelle_quantite'))
            nouveau_produit = int(request.form.get('produit'))
            nouveau_magasin = int(request.form.get('magasin'))

            # Récupérons le prix du produit sélectionné
            cursor.execute(
                "SELECT PrixUnitaire FROM Produit WHERE IdProduit = %s", (nouveau_produit,))
            prix_produit = cursor.fetchone()[0]

            # Calcul du nouveau prix total en fonction de la nouvelle quantité et du prix du nouveau produit
            nouveau_prix_total = nouvelle_quantite * prix_produit

            # Mise à jour de la vente avec la nouvelle quantité, le nouveau produit et le nouveau magasin
            update_query = """
                UPDATE Vente
                SET Quantitevendu = %s, Prixtotal = %s, IdProduit = %s, IdMagasin = %s
                WHERE IdVente = %s
            """
            cursor.execute(
                update_query, (nouvelle_quantite, nouveau_prix_total, nouveau_produit, nouveau_magasin, _id))
            mysql.commit()

            flash(f'La vente N°{_id} a été mise à jour.', 'success')
            # Rediriger vers la liste des ventes
            return redirect(url_for('liste_vente'))

    except Exception as e:
        # Gérez les erreurs, par exemple, affichez un message d'erreur
        flash(f"Erreur lors de la modification de la vente: {str(e)}", 'error')
        return redirect(url_for('liste_vente'))


# ? Supprimer les ventes
@app.route("/supprimer_vente/<int:_id>")
@login_required
def supprimer_vente(_id):
    try:
        # ? Connection à ma db
        mysql = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB']
        )

        # ? Utilisons un curseur pour exécuter nos requêtes SQL
        cursor = mysql.cursor()

        # Exécutez la requête SQL pour supprimer la vente
        delete_query = "DELETE FROM Vente WHERE IdVente = %s"
        cursor.execute(delete_query, (_id,))
        mysql.commit()
        cursor.close()

        flash(f"La Vente N°{_id} a été supprimée avec succès.")
        return redirect("/liste_vente")
    except Exception as e:
        # Gérez les erreurs, par exemple, affichez un message d'erreur
        flash(f"Erreur lors de la suppression de la vente: {str(e)}", 'error')
        return redirect("/liste_vente")


# ! Gestion Back-End des Stocks
# ? Afficher la page d'enregistrement des stocks
@app.route('/stock/', methods=['GET', 'POST'])
@login_required
def stock():
    # ? Connection à ma db
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )

    # ? Utilisons un curseur pour exécuter nos requêtes SQL
    cursor = mysql.cursor()

    if request.method == 'POST':
        id_magasin = request.form.get('magasin')
        id_produit = request.form.get('produit')
        quantite = int(request.form.get('quantite'))

        try:
            # Vérifions si le stock existe déjà pour ce magasin et ce produit
            verification_stock_query = "SELECT IdStock, Quantitestock FROM Stock WHERE IdMagasin = %s AND IdProduit = %s"
            cursor.execute(verification_stock_query, (id_magasin, id_produit))
            stock_exist = cursor.fetchone()

            if stock_exist:
                # Mettre à jour la quantité du stock existant
                new_quantite = stock_exist[1] + quantite
                update_stock_query = "UPDATE Stock SET Quantitestock = %s WHERE IdStock = %s"
                cursor.execute(update_stock_query,
                               (new_quantite, stock_exist[0]))

            else:
                # Insérer un nouvel enregistrement dans la table Stock
                insert_stock_query = "INSERT INTO Stock (IdMagasin, IdProduit, Quantitestock) VALUES (%s, %s, %s)"
                cursor.execute(insert_stock_query,
                               (id_magasin, id_produit, quantite))

            mysql.commit()

            flash(f"Le stock a été enregistrée avec succès. Quantité: {
                  quantite}", 'success')
            return redirect('/liste_stock')
        except Exception as e:
            # En cas d'erreur, annuler les changements et afficher un message d'erreur
            mysql.rollback()
            flash(f"Erreur lors de l'enregistrement du stock: {
                  str(e)}", 'error')

    # Remplir les options des Select avec les noms des magasins et des produits
    select_magasin_query = "SELECT IdMagasin, NomMagasin FROM Magasin GROUP BY NomMagasin "
    cursor.execute(select_magasin_query)
    magasins = cursor.fetchall()

    select_produit_query = "SELECT IdProduit, NomProduit FROM Produit GROUP BY NomProduit"
    cursor.execute(select_produit_query)
    produits = cursor.fetchall()

    return render_template('stocks/stock.html', magasins=magasins, produits=produits)


# ? Afficher tous les stocks
@app.route('/liste_stock/', methods=['GET'])
@login_required
def liste_stock():
    try:
        # ? Connection à ma db
        mysql = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB']
        )

        # ? Utilisons un curseur pour exécuter nos requêtes SQL
        cursor = mysql.cursor()

        # Exécutez la requête SQL pour récupérer les données
        select_query = """
            SELECT p.NomProduit, s.IdProduit, m.NomMagasin, s.IdMagasin,
                   s.Quantitestock, s.Idstock
            FROM Stock s
            JOIN Produit p ON s.IdProduit = p.IdProduit
            JOIN Magasin m ON s.IdMagasin = m.IdMagasin ORDER BY s.Idstock
            """
        cursor.execute(select_query)
        results = cursor.fetchall()
        print(results)

        return render_template('stocks/liste_stock.html', results=results)
    except Exception as e:
        # Gérez les erreurs, par exemple, affichez un message d'erreur
        flash(f"Erreur lors de la récupération des données: {str(e)}", 'error')
        return redirect('/')


# ? Supprimer les Stocks
@app.route("/supprimer_stock/<int:_id>")
@login_required
def supprimer_stock(_id):
    try:
        # ? Connection à ma db
        mysql = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB']
        )

        # ? Utilisons un curseur pour exécuter nos requêtes SQL
        cursor = mysql.cursor()

        # Exécutez la requête SQL pour supprimer la vente
        delete_query = "DELETE FROM Stock WHERE Idstock = %s"
        cursor.execute(delete_query, (_id,))
        mysql.commit()
        cursor.close()

        flash(f"La Vente N°{_id} a été supprimée avec succès.")
        return redirect("/liste_stock")
    except Exception as e:
        # Gérez les erreurs, par exemple, affichez un message d'erreur
        flash(f"Erreur lors de la suppression de la vente: {str(e)}", 'error')
        return redirect("/liste_stock")


# ? Modifier les stocks
@app.route('/modifier_stock/<int:_id>', methods=['GET', 'POST'])
@login_required
def modifier_stock(_id):
    try:
        # ? Connection à ma db
        mysql = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB']
        )

        # ? Utilisons un curseur pour exécuter nos requêtes SQL
        cursor = mysql.cursor()

        if request.method == 'GET':
            # Récupérons  les détails du stock
            select_query = """
                SELECT s.Idstock, s.Quantitestock, p.IdProduit, p.NomProduit,  m.IdMagasin, m.NomMagasin 
                FROM Stock s
                JOIN Produit p ON s.IdProduit = p.IdProduit
                JOIN Magasin m ON s.IdMagasin = m.IdMagasin
                WHERE s.Idstock = %s
            """
            cursor.execute(select_query, (_id,))
            stock_details = cursor.fetchone()

            print(stock_details)
            print(stock_details[2])

            if not stock_details:
                flash("Le stock spécifié n'existe pas.", 'danger')
                # Rediriger vers la liste des ventes
                return redirect(url_for('liste_stock'))

            # Récupérons la liste des produits et des magasins puis stockons les dans des sélects
            cursor.execute(
                "SELECT IdProduit, NomProduit FROM Produit GROUP BY NomProduit")
            produits = cursor.fetchall()

            cursor.execute(
                "SELECT IdMagasin, NomMagasin FROM Magasin GROUP BY NomMagasin")
            magasins = cursor.fetchall()

            return render_template('stocks/modifier_stock.html', stock_details=stock_details, produits=produits, magasins=magasins)

        if request.method == 'POST':
            nouvelle_quantite = int(request.form.get('nouvelle_quantite'))
            nouveau_produit = int(request.form.get('produit'))
            nouveau_magasin = int(request.form.get('magasin'))

            # Mise à jour du stock avec les nouvelles valeurs
            update_query = """
                UPDATE Stock
                SET Quantitestock = %s, IdProduit = %s, IdMagasin = %s
                WHERE Idstock = %s
            """
            cursor.execute(
                update_query, (nouvelle_quantite, nouveau_produit, nouveau_magasin, _id))
            mysql.commit()

            flash(f'Le stock N°{_id} a été mise à jour.', 'success')
            # Rediriger vers la liste des ventes
            return redirect(url_for('liste_stock'))

    except Exception as e:
        # Gérez les erreurs, par exemple, affichez un message d'erreur
        flash(f"Erreur lors de la modification du stock: {str(e)}", 'error')
        return redirect(url_for('liste_stock'))


if __name__ == "__main__":
    # app.run(debug=True)
    # If the system is a windows /!\ Change  /!\ the   /!\ Port
    if platform.system() == "Windows":
        app.run(host='0.0.0.0', port=50000, debug=True)
