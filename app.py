from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from wtforms import StringField, IntegerField, DecimalField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length, Email, Optional
from functools import wraps
from connection.config import Config
from sqlalchemy import text

# --- Configuración ---
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# --- Decoradores para autenticación ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_rol' not in session or session['usuario_rol'] != 'admin':
            flash('No tienes permisos para acceder a esta página.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

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
    contraseña = db.Column(db.String(200), nullable=False)  # Aumentado a 200 para el hash
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
    contraseña = PasswordField("Contraseña", validators=[Optional()])
    rol = SelectField("Rol", choices=[("admin", "Administrador"), ("empleado", "Empleado")])
    submit = SubmitField("Guardar")

class OrdenForm(FlaskForm):
    cliente_id = SelectField("Cliente", coerce=int, validators=[DataRequired()])
    fecha = StringField("Fecha", validators=[DataRequired()])
    submit = SubmitField("Guardar")

class LoginForm(FlaskForm):
    correo = StringField("Correo", validators=[DataRequired(), Email()])
    contraseña = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Iniciar Sesión")

# --- CREAR TABLAS Y USUARIO POR DEFECTO ---
with app.app_context():
    db.create_all()
    print("✅ Tablas creadas o ya existentes")
    
    # Crear usuario administrador por defecto si no existe
    if not Usuario.query.filter_by(correo="admin@dulcehogar.com").first():
        contraseña_encriptada = bcrypt.generate_password_hash("admin123").decode('utf-8')
        admin = Usuario(
            nombre="Administrador",
            correo="admin@dulcehogar.com",
            contraseña=contraseña_encriptada,
            rol="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuario administrador creado: admin@dulcehogar.com / admin123")

# --- RUTAS DE AUTENTICACIÓN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(correo=form.correo.data).first()
        
        if usuario and bcrypt.check_password_hash(usuario.contraseña, form.contraseña.data):
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre
            session['usuario_rol'] = usuario.rol
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('index'))

# --- RUTAS DE PRUEBA ---
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

# --- CRUD CATEGORIAS ---
@app.route('/categorias')
@login_required
@admin_required
def listar_categorias():
    categorias = Categoria.query.all()
    return render_template("categories/list.html", categorias=categorias)

@app.route('/categorias/nuevo', methods=["GET", "POST"])
@login_required
@admin_required
def nuevo_categoria():
    form = CategoriaForm()
    if form.validate_on_submit():
        db.session.add(Categoria(nombre=form.nombre.data, descripcion=form.descripcion.data))
        db.session.commit()
        flash("Categoría creada con éxito", "success")
        return redirect(url_for("listar_categorias"))
    return render_template("categories/form.html", form=form, modo="nuevo")

@app.route('/categorias/editar/<int:id>', methods=["GET", "POST"])
@login_required
@admin_required
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    form = CategoriaForm(obj=categoria)
    
    if form.validate_on_submit():
        form.populate_obj(categoria)
        db.session.commit()
        flash("Categoría actualizada con éxito", "success")
        return redirect(url_for("listar_categorias"))
    
    return render_template("categories/form.html", form=form, modo="editar")

@app.route('/categorias/eliminar/<int:id>', methods=["POST"])
@login_required
@admin_required
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    db.session.delete(categoria)
    db.session.commit()
    flash("Categoría eliminada con éxito", "success")
    return redirect(url_for("listar_categorias"))

# --- CRUD PRODUCTOS ---
@app.route('/productos')
@login_required
def listar_productos():
    productos = Producto.query.all()
    return render_template("products/list.html", productos=productos)

@app.route('/productos/nuevo', methods=["GET", "POST"])
@login_required
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

@app.route('/productos/editar/<int:id>', methods=["GET", "POST"])
@login_required
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    form = ProductoForm(obj=producto)
    form.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.all()]
    
    if form.validate_on_submit():
        form.populate_obj(producto)
        db.session.commit()
        flash("Producto actualizado con éxito", "success")
        return redirect(url_for("listar_productos"))
    
    return render_template("products/form.html", form=form, modo="editar")

@app.route('/productos/eliminar/<int:id>', methods=["POST"])
@login_required
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash("Producto eliminado con éxito", "success")
    return redirect(url_for("listar_productos"))

# --- CRUD CLIENTES ---
@app.route('/clientes')
@login_required
def listar_clientes():
    clientes = Cliente.query.all()
    return render_template("customers/list.html", clientes=clientes)

@app.route('/clientes/nuevo', methods=["GET", "POST"])
@login_required
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

@app.route('/clientes/editar/<int:id>', methods=["GET", "POST"])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    form = ClienteForm(obj=cliente)
    
    if form.validate_on_submit():
        form.populate_obj(cliente)
        db.session.commit()
        flash("Cliente actualizado con éxito", "success")
        return redirect(url_for("listar_clientes"))
    
    return render_template("customers/form.html", form=form, modo="editar")

@app.route('/clientes/eliminar/<int:id>', methods=["POST"])
@login_required
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente eliminado con éxito", "success")
    return redirect(url_for("listar_clientes"))

# --- CRUD USUARIOS ---
@app.route("/usuarios")
@login_required
@admin_required
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template("users/list.html", usuarios=usuarios)

@app.route("/usuarios/nuevo", methods=["GET", "POST"])
@login_required
@admin_required
def nuevo_usuario():
    form = UsuarioForm()
    if form.validate_on_submit():
        if not form.contraseña.data:
            flash("La contraseña es obligatoria para nuevos usuarios", "danger")
            return render_template("users/form.html", form=form, modo="nuevo")
        
        contraseña_encriptada = bcrypt.generate_password_hash(form.contraseña.data).decode('utf-8')
        
        db.session.add(Usuario(
            nombre=form.nombre.data,
            correo=form.correo.data,
            contraseña=contraseña_encriptada,
            rol=form.rol.data
        ))
        db.session.commit()
        flash("Usuario agregado con éxito", "success")
        return redirect(url_for("listar_usuarios"))
    return render_template("users/form.html", form=form, modo="nuevo")

@app.route('/usuarios/editar/<int:id>', methods=["GET", "POST"])
@login_required
@admin_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    form = UsuarioForm(obj=usuario)
    
    form.contraseña.data = ""
    
    if form.validate_on_submit():
        usuario.nombre = form.nombre.data
        usuario.correo = form.correo.data
        usuario.rol = form.rol.data
        
        if form.contraseña.data:
            contraseña_encriptada = bcrypt.generate_password_hash(form.contraseña.data).decode('utf-8')
            usuario.contraseña = contraseña_encriptada
        
        db.session.commit()
        flash("Usuario actualizado con éxito", "success")
        return redirect(url_for("listar_usuarios"))
    
    return render_template("users/form.html", form=form, modo="editar")

@app.route('/usuarios/eliminar/<int:id>', methods=["POST"])
@login_required
@admin_required
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash("Usuario eliminado con éxito", "success")
    return redirect(url_for("listar_usuarios"))

# --- CRUD ORDENES ---
@app.route('/ordenes')
@login_required
def listar_ordenes():
    ordenes = Orden.query.all()
    return render_template("orders/list.html", ordenes=ordenes)

@app.route('/ordenes/nuevo', methods=["GET", "POST"])
@login_required
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

@app.route('/ordenes/editar/<int:id>', methods=["GET", "POST"])
@login_required
def editar_orden(id):
    orden = Orden.query.get_or_404(id)
    form = OrdenForm(obj=orden)
    form.cliente_id.choices = [(c.id, c.nombre) for c in Cliente.query.all()]
    
    if form.validate_on_submit():
        form.populate_obj(orden)
        db.session.commit()
        flash("Orden actualizada con éxito", "success")
        return redirect(url_for("listar_ordenes"))
    
    return render_template("orders/form.html", form=form, modo="editar")

@app.route('/ordenes/eliminar/<int:id>', methods=["POST"])
@login_required
def eliminar_orden(id):
    orden = Orden.query.get_or_404(id)
    db.session.delete(orden)
    db.session.commit()
    flash("Orden eliminada con éxito", "success")
    return redirect(url_for("listar_ordenes"))

@app.route('/ordenes/ver/<int:id>')
@login_required
def ver_orden(id):
    orden = Orden.query.get_or_404(id)
    return render_template('orders/detalle.html', orden=orden)

# --- EJECUTAR APP ---
if __name__ == '__main__':
    app.run(debug=True)