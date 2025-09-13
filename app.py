from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length, Email
from connection.config import Config
from sqlalchemy import text

# --- Configuración ---
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# --- PROBAR CONEXIÓN ---
with app.app_context():
    try:
        db.session.execute(text("SELECT 1"))
        print("✅ Conexión exitosa a MySQL!")
    except Exception as e:
        print("❌ Error en la conexión:", e)

# --- MODELOS ---
class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.String(200))
    productos = db.relationship("Producto", backref="categoria", lazy=True)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    precio = db.Column(db.Float, nullable=False, default=0.0)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), nullable=True)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    ordenes = db.relationship("Orden", backref="cliente", lazy=True)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    contraseña = db.Column(db.String(120), nullable=False)
    rol = db.Column(db.String(50), default="empleado")

class Orden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=False)
    fecha = db.Column(db.String(20))
    total = db.Column(db.Float, default=0.0)

# --- FORMULARIOS ---
class CategoriaForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=100)])
    descripcion = StringField("Descripción")
    submit = SubmitField("Guardar")

class ProductoForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=120)])
    cantidad = IntegerField("Cantidad", validators=[DataRequired(), NumberRange(min=0)])
    precio = DecimalField("Precio", validators=[DataRequired(), NumberRange(min=0)])
    categoria_id = SelectField("Categoría", coerce=int)
    submit = SubmitField("Guardar")

class ClienteForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=120)])
    correo = StringField("Correo", validators=[DataRequired(), Email()])
    telefono = StringField("Teléfono")
    direccion = StringField("Dirección")
    submit = SubmitField("Guardar")

class UsuarioForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired()])
    correo = StringField("Correo", validators=[DataRequired(), Email()])
    contraseña = PasswordField("Contraseña", validators=[DataRequired()])
    rol = SelectField("Rol", choices=[("admin", "Administrador"), ("empleado", "Empleado")])
    submit = SubmitField("Guardar")

class OrdenForm(FlaskForm):
    cliente_id = SelectField("Cliente", coerce=int, validators=[DataRequired()])
    fecha = StringField("Fecha", validators=[DataRequired()])
    submit = SubmitField("Guardar")

# --- CREAR TABLAS ---
with app.app_context():
    db.create_all()
    print("✅ Tablas creadas o ya existentes")

# --- RUTAS DE PRUEBA ---
@app.route('/')
def index():
    return "DulceHogar - Conexión MySQL exitosa!"

# --- CRUD CATEGORIAS ---
@app.route('/categorias')
def listar_categorias():
    categorias = Categoria.query.all()
    return render_template("categories/list.html", categorias=categorias)

@app.route('/categorias/nuevo', methods=["GET", "POST"])
def nuevo_categoria():
    form = CategoriaForm()
    if form.validate_on_submit():
        db.session.add(Categoria(nombre=form.nombre.data, descripcion=form.descripcion.data))
        db.session.commit()
        flash("Categoría creada con éxito", "success")
        return redirect(url_for("listar_categorias"))
    return render_template("categories/form.html", form=form, modo="nuevo")

# --- CRUD PRODUCTOS ---
@app.route('/productos')
def listar_productos():
    productos = Producto.query.all()
    return render_template("products/list.html", productos=productos)

@app.route('/productos/nuevo', methods=["GET", "POST"])
def nuevo_producto():
    form = ProductoForm()
    form.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.all()]
    if form.validate_on_submit():
        db.session.add(Producto(
            nombre=form.nombre.data,
            cantidad=form.cantidad.data,
            precio=float(form.precio.data),
            categoria_id=form.categoria_id.data
        ))
        db.session.commit()
        flash("Producto creado con éxito", "success")
        return redirect(url_for("listar_productos"))
    return render_template("products/form.html", form=form, modo="nuevo")

# --- CRUD CLIENTES ---
@app.route('/clientes')
def listar_clientes():
    clientes = Cliente.query.all()
    return render_template("customers/list.html", clientes=clientes)

@app.route('/clientes/nuevo', methods=["GET", "POST"])
def nuevo_cliente():
    form = ClienteForm()
    if form.validate_on_submit():
        db.session.add(Cliente(
            nombre=form.nombre.data,
            correo=form.correo.data,
            telefono=form.telefono.data,
            direccion=form.direccion.data
        ))
        db.session.commit()
        flash("Cliente agregado con éxito", "success")
        return redirect(url_for("listar_clientes"))
    return render_template("customers/form.html", form=form, modo="nuevo")

# --- CRUD USUARIOS ---
@app.route("/usuarios")
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template("users/list.html", usuarios=usuarios)

@app.route("/usuarios/nuevo", methods=["GET", "POST"])
def nuevo_usuario():
    form = UsuarioForm()
    if form.validate_on_submit():
        db.session.add(Usuario(
            nombre=form.nombre.data,
            correo=form.correo.data,
            contraseña=form.contraseña.data,
            rol=form.rol.data
        ))
        db.session.commit()
        flash("Usuario agregado con éxito", "success")
        return redirect(url_for("listar_usuarios"))
    return render_template("users/form.html", form=form, modo="nuevo")

# --- CRUD ORDENES ---
@app.route('/ordenes')
def listar_ordenes():
    ordenes = Orden.query.all()
    return render_template("orders/list.html", ordenes=ordenes)

@app.route('/ordenes/nuevo', methods=["GET", "POST"])
def nueva_orden():
    form = OrdenForm()
    clientes = Cliente.query.all()
    if not clientes:
        flash("Debe agregar al menos un cliente antes de crear una orden.", "warning")
        return redirect(url_for("listar_clientes"))
    form.cliente_id.choices = [(c.id, c.nombre) for c in clientes]

    if form.validate_on_submit():
        nueva = Orden(
            cliente_id=form.cliente_id.data,
            fecha=form.fecha.data,
            total=0.0
        )
        db.session.add(nueva)
        db.session.commit()
        flash("Orden creada con éxito.", "success")
        return redirect(url_for("listar_ordenes"))
    return render_template("orders/form.html", form=form, modo="nuevo")

# --- EJECUTAR APP ---
if __name__ == '__main__':
    app.run(debug=True)
