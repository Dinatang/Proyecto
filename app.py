from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

# --- Configuración Flask ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dulcehogar-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventario.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Modelo ---
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    precio = db.Column(db.Float, nullable=False, default=0.0)

# --- Inventario CRUD ---
class Inventario:
    def listar_todos(self):
        return Producto.query.all()

    def buscar_por_nombre(self, nombre):
        return Producto.query.filter(Producto.nombre.ilike(f"%{nombre}%")).all()

    def agregar(self, nombre, cantidad, precio):
        if Producto.query.filter_by(nombre=nombre).first():
            raise ValueError("Ya existe un producto con ese nombre.")
        db.session.add(Producto(nombre=nombre, cantidad=cantidad, precio=precio))
        db.session.commit()

    def actualizar(self, id, nombre, cantidad, precio):
        p = Producto.query.get(id)
        if not p:
            raise ValueError("Producto no encontrado.")
        p.nombre = nombre
        p.cantidad = cantidad
        p.precio = precio
        db.session.commit()

    def eliminar(self, id):
        p = Producto.query.get(id)
        if not p:
            return False
        db.session.delete(p)
        db.session.commit()
        return True

inventario = Inventario()

# --- Formulario ---
class ProductoForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=120)])
    cantidad = IntegerField("Cantidad", validators=[DataRequired(), NumberRange(min=0)])
    precio = DecimalField("Precio", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("Guardar")

# --- Rutas ---
@app.route('/')
def index():
    return render_template("index.html", title="Inicio")

@app.route('/about/')
def about():
    return render_template("about.html", title="Acerca de")

@app.route('/productos')
def listar_productos():
    q = request.args.get('q', '').strip()
    productos = inventario.buscar_por_nombre(q) if q else inventario.listar_todos()
    return render_template('products/list.html', title='Productos', productos=productos, q=q)

@app.route('/productos/nuevo', methods=['GET', 'POST'])
def crear_producto():
    form = ProductoForm()
    if form.validate_on_submit():
        try:
            inventario.agregar(form.nombre.data, form.cantidad.data, float(form.precio.data))
            flash("Producto agregado correctamente.", "success")
            return redirect(url_for('listar_productos'))
        except ValueError as e:
            form.nombre.errors.append(str(e))
    return render_template('products/form.html', title='Nuevo Producto', form=form, modo='crear')

@app.route('/productos/<int:pid>/editar', methods=['GET', 'POST'])
def editar_producto(pid):
    producto = Producto.query.get_or_404(pid)
    form = ProductoForm(obj=producto)
    if form.validate_on_submit():
        try:
            inventario.actualizar(pid, form.nombre.data, form.cantidad.data, float(form.precio.data))
            flash("Producto actualizado.", "success")
            return redirect(url_for('listar_productos'))
        except ValueError as e:
            form.nombre.errors.append(str(e))
    return render_template('products/form.html', title='Editar Producto', form=form, modo='editar')

@app.route('/productos/<int:pid>/eliminar', methods=['POST'])
def eliminar_producto(pid):
    ok = inventario.eliminar(pid)
    flash('Producto eliminado.' if ok else 'Producto no encontrado.', 'info' if ok else 'warning')
    return redirect(url_for('listar_productos'))

# --- Crear DB y ejecutar ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
