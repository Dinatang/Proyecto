from flask import Flask, render_template

app = Flask(__name__)

# Ruta principal
#Esta ruta no lleva s indes
@app.route("/")
def index():
    return render_template("index.html", title="Inicio")

#Esta ruta nos lleva a About

@app.route("/about")
def about():
    return render_template("about.html", title="Sobre Nosotros")

# Ruta con un parámetro dinámico
@app.route('/usuario/<nombre>')
def usuario(nombre):
    return f'Bienvenido, {nombre}!'

# Ruta con dos parámetros dinámicos
@app.route('/saludo/<nombre>/<int:edad>')
def saludo(nombre, edad):
    return f'Hola {nombre}, tienes {edad} años!'

if __name__ == '__main__':
    app.run(debug=True)
