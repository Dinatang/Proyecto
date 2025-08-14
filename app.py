from flask import Flask

app = Flask(__name__)

# Ruta principal
@app.route('/')
def index():
    return "Hola, mundo!"

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
