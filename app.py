import platform
from flask import Flask, render_template, url_for

app = Flask(__name__)


@app.route("/")
def connexion():
    return render_template("connexion.html")


@app.route("/acceuil/")
def acceuil():
    return render_template("acceuil.html")



if __name__ == "__main__":
    # app.run(debug=True)
    # If the system is a windows /!\ Change  /!\ the   /!\ Port
    if platform.system() == "Windows":
        app.run(host='0.0.0.0', port=50000, debug=True)
