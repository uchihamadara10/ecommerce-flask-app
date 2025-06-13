from flask import Flask, render_template,url_for, request, redirect, url_for, flash, session, current_app # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from sqlalchemy import or_ # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore
from datetime import datetime
import os
import uuid

# --- Configuração do Flask e Banco de Dados ---
app = Flask(__name__)

# Configuração da chave secreta (MUITO IMPORTANTE para segurança de sessões e cookies)
# !! MUDAR ESTA CHAVE EM PRODUÇÃO !!
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_segura_e_longa_aqui_para_a_sua_aplicacao_de_producao'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- NOVAS CONFIGURAÇÕES PARA RESOLVER O ERRO DE URL_FOR ---
app.config['SERVER_NAME'] = '127.0.0.1:5000' # O endereço do seu servidor local
app.config['PREFERRED_URL_SCHEME'] = 'http' # O esquema de URL preferido (http ou https)
# --- FIM DAS NOVAS CONFIGURAÇÕES ---

db = SQLAlchemy(app)

# Context Processor para injetar 'now', 'categories' e dados do usuário logado em TODOS os templates
@app.context_processor
def inject_global_data():
    categories = Category.query.all()
    logged_in_user = None
    if 'user_id' in session:
        logged_in_user = User.query.get(session['user_id'])
    return {'now': datetime.now(), 'categories': categories, 'logged_in_user': logged_in_user}


# --- Configuração de Pastas para Uploads ---
UPLOAD_FOLDER_BANNERS = 'static/uploads/banners'
UPLOAD_FOLDER_PRODUCTS = 'static/uploads/products'
app.config['UPLOAD_FOLDER_BANNERS'] = UPLOAD_FOLDER_BANNERS
app.config['UPLOAD_FOLDER_PRODUCTS'] = UPLOAD_FOLDER_PRODUCTS
# Cria as pastas se não existirem
os.makedirs(UPLOAD_FOLDER_BANNERS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_PRODUCTS, exist_ok=True)

# --- Modelos do Banco de Dados ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user') # 'admin', 'ceo', 'revendedor', 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image_filename = db.Column(db.String(255), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('products', lazy=True))
    # Adicionando os novos campos para preço antigo e parcelamento
    old_price = db.Column(db.Float, nullable=True)
    installments = db.Column(db.Integer, nullable=True)
    # Adicionando o campo para o código do produto (para o sistema de bipar/controle)
    product_code = db.Column(db.String(100), unique=True, nullable=True)


    def __repr__(self):
        return f'<Product {self.name}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'

class Banner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(255), nullable=False)
    alt_text = db.Column(db.String(255), nullable=True)
    link_url = db.Column(db.String(255), nullable=True)
    order_index = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Banner {self.image_filename}>'

class Revendedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    referral_token = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    comissao_percentual = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Revendedor {self.nome}>'

class Maleta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo_maleta = db.Column(db.String(50), unique=True, nullable=False)
    revendedor_id = db.Column(db.Integer, db.ForeignKey('revendedor.id'), nullable=True)
    revendedor = db.relationship('Revendedor', backref=db.backref('maletas', lazy=True))
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    data_devolucao = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='Em Posse da Revendedora') # 'Disponível', 'Em Posse da Revendedora', 'Em Devolução', 'Finalizada'
    valor_total_enviado = db.Column(db.Float, default=0.0)
    valor_total_vendido = db.Column(db.Float, default=0.0)
    # Relação com os itens da maleta
    itens = db.relationship('MaletaItem', backref='maleta', lazy=True)


    def __repr__(self):
        return f'<Maleta {self.codigo_maleta} - Rev: {self.revendedor.nome if self.revendedor else "N/A"}>'

class MaletaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    maleta_id = db.Column(db.Integer, db.ForeignKey('maleta.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product') # Relação com o produto
    quantidade_enviada = db.Column(db.Integer, nullable=False)
    quantidade_devolvida = db.Column(db.Integer, default=0) # Quantidade devolvida pela revendedora
    preco_unitario_envio = db.Column(db.Float, nullable=False) # Preço do produto quando foi colocado na maleta

    def __repr__(self):
        return f'<MaletaItem Maleta:{self.maleta_id} Prod:{self.product.name} Enviado:{self.quantidade_enviada}>'


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_value = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pendente')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    revendedor_id = db.Column(db.Integer, db.ForeignKey('revendedor.id'), nullable=True)
    revendedor = db.relationship('Revendedor', backref='pedidos')

    def __repr__(self):
        return f'<Order {self.id} - {self.status}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    order = db.relationship('Order', backref=db.backref('items', lazy=True))
    product = db.relationship('Product')

    def __repr__(self):
        return f'<OrderItem {self.quantity}x {self.product.name}>'


# --- DADOS MOCADOS PARA VISUALIZAÇÃO DOS PRODUTOS ---
# Esta lista será usada APENAS para simular produtos na página inicial
# até que o sistema de cadastro de produtos real seja implementado e a rota
# index possa consultar o banco de dados.
products_mock_data = [
    {
        'id': 1,
        'name': 'Brincos de corações',
        'image': 'brincos_corações.jpeg', # CERTIFIQUE-SE DE QUE ESTA IMAGEM EXISTE NO SEU CAMINHO
        'price': 180.00,
        'old_price': 220.00,
        'installments': 4,
        'description': 'Pulseira de corrente com elos grossos em prata 925.'
    },


    {
        'id': 2,
        'name': 'Brinco perola',
        'image': 'brinco_perola.jpeg', # Exemplo de imagem nova, ajuste
        'price': 350.00,
        'old_price': None,
        'installments': 7,
        'description': 'Anel robusto em ouro rosé, design moderno.'
    },

    {
        'id': 3,
        'name': 'brinco destaque',
        'image': 'brinco_destaque.jpeg', # Exemplo de imagem nova, ajuste
        'price': 499.00,
        'old_price': 550.00,
        'installments': 8,
        'description': 'Conjunto elegante de brinco e colar em prata com pedras.'
    },

    {
        'id': 4,
        'name': 'aneis',
        'image': 'aneis.jpeg', # CERTIFIQUE-SE DE QUE ESTA IMAGEM EXISTE NO SEU CAMINHO
        'price': 180.00,
        'old_price': 220.00,
        'installments': 4,
        'description': 'Pulseira de corrente com elos grossos em prata 925.'
    },

    {
        'id': 5,
        'name': 'Brincos dourados',
        'image': 'brinco_perola.jpeg', # Exemplo de imagem nova, ajuste
        'price': 350.00,
        'old_price': None,
        'installments': 7,
        'description': 'Anel robusto em ouro rosé, design moderno.'
    },

    ]



# --- Rotas Principais ---
@app.route('/')
def index():
    referral_token = request.args.get('ref')
    if referral_token:
        revendedor = Revendedor.query.filter_by(referral_token=referral_token, is_active=True).first()
        if revendedor:
            session['revendedor_id'] = revendedor.id
            flash(f'Você está acessando a loja através do link do revendedor {revendedor.nome}!', 'info')
        else:
            flash('Link de revendedor inválido ou inativo.', 'warning')
    
    # Banners do banco de dados (se houver, caso contrário, o template lida com isso)
    banners = Banner.query.filter_by(is_active=True).order_by(Banner.order_index).all()
    
    # ATENÇÃO: PARA VER OS PRODUTOS DE EXEMPLO, COMENTE A LINHA ABAIXO
    # products = Product.query.order_by(Product.name).limit(8).all()
    # E DESCOMENTE A LINHA ABAIXO
    products = products_mock_data # Usando os dados de exemplo para o front-end
    
    return render_template('index.html', banners=banners, products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: # Se já logado, redireciona
        if session['user_role'] in ['admin', 'ceo']:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        print(f"Tentativa de login para: {username}") # DEBUG
        print(f"Usuário encontrado: {user}") # DEBUG

        if user:
            print(f"Senha fornecida: {password}") # DEBUG
            if user.check_password(password):
                session['user_id'] = user.id
                session['user_role'] = user.role
                session['username'] = user.username
                flash('Login realizado com sucesso!', 'success')
                if user.role in ['admin', 'ceo']:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('index'))
            else:
                flash('Usuário ou senha inválidos.', 'danger')
                print("ERRO: Senha incorreta.") # DEBUG
        else:
            flash('Usuário ou senha inválidos.', 'danger')
            print("ERRO: Usuário não encontrado.") # DEBUG
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST']) # <-- NOVA ROTA DE REGISTRO
def register():
    if 'user_id' in session:
        flash('Você já está logado.', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Nome de usuário já existe. Por favor, escolha outro.', 'danger')
            return render_template('register.html')

        new_user = User(username=username, role='user') # Novo usuário padrão é 'user'
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        flash('Sua conta foi criada com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    session.pop('username', None)
    session.pop('revendedor_id', None)
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('index'))

# Rota para cadastrar o primeiro CEO/Admin (REMOVER EM PRODUÇÃO!)
# COMENTE OU REMOVA ESTA ROTA DEPOIS DE CADASTRAR O CEO PELA PRIMEIRA VEZ!
#@app.route('/register_admin_init')#
#def register_admin_init():
    #if User.query.filter_by(role='ceo').first():
      #  flash('Já existe um usuário CEO. Não é possível cadastrar outro por esta rota.', 'warning')
     #   return redirect(url_for('index'))

    #new_ceo = User(username='admin', role='ceo')
    # === MUDE A SENHA ABAIXO PARA UMA SENHA FORTE E QUE VOCÊ VAI LEMBRAR! ===
    #new_ceo.set_password("suasenhaforte") # <-- MUDE AQUI PARA UMA SENHA REAL!
   # db.session.add(new_ceo)
  #  db.session.commit()
 
 #   flash('Usuário CEO "ceo" criado com a senha definida no app.py! Remova a rota /register_admin_init em produção.', 'success')
#    return redirect(url_for('login'))

# --- Rotas do Painel Administrativo ---
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or (session['user_role'] not in ['admin', 'ceo']):
        flash('Acesso não autorizado.', 'danger')
    return render_template('admin/dashboard.html')

@app.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if 'user_id' not in session or (session['user_role'] not in ['admin', 'ceo']):
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))

    categories = Category.query.all()
    products = Product.query.all()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        # Adicione os novos campos aqui também ao processar o formulário
        old_price = request.form.get('old_price') # Usar .get para não dar erro se o campo não existir no form
        installments = request.form.get('installments')
        product_code = request.form.get('product_code')

        try:
            price = float(request.form['price'])
            stock = int(request.form['stock'])
            category_id = int(request.form['category_id'])
            # Converte old_price e installments para float/int se existirem, caso contrário None
            old_price = float(old_price) if old_price else None
            installments = int(installments) if installments else None
        except ValueError:
            flash('Preço, Estoque, Preço Antigo e Parcelas devem ser números válidos.', 'danger')
            return redirect(url_for('admin_products'))

        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    unique_filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_PRODUCTS'], unique_filename))
                    image_filename = unique_filename
                else:
                    flash('Formato de imagem não permitido. Apenas PNG, JPG, JPEG, GIF são aceitos.', 'danger')
                    return redirect(url_for('admin_products'))
        
        # Passa os novos campos para o modelo Product
        new_product = Product(name=name, description=description, price=price, stock=stock, 
                              category_id=category_id, image_filename=image_filename,
                              old_price=old_price, installments=installments, product_code=product_code)
        db.session.add(new_product)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/products.html', categories=categories, products=products)

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if 'user_id' not in session or (session['user_role'] not in ['admin', 'ceo']):
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))

    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        # Pega os novos campos no POST
        old_price = request.form.get('old_price')
        installments = request.form.get('installments')
        product_code = request.form.get('product_code')

        try:
            product.price = float(request.form['price'])
            product.stock = int(request.form['stock'])
            product.category_id = int(request.form['category_id'])
            # Converte e atribui ao objeto product
            product.old_price = float(old_price) if old_price else None
            product.installments = int(installments) if installments else None
            product.product_code = product_code # Atribui o código do produto
        except ValueError:
            flash('Preço, Estoque, Preço Antigo e Parcelas devem ser números válidos.', 'danger')
            return redirect(url_for('admin_edit_product', product_id=product.id))

        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    if product.image_filename:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER_PRODUCTS'], product.image_filename)
                        if os.path.exists(old_path):
                            os.remove(old_path)

                    unique_filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_PRODUCTS'], unique_filename))
                    product.image_filename = unique_filename
                else:
                    flash('Formato de imagem não permitido. Apenas PNG, JPG, JPEG, GIF são aceitos.', 'danger')
                    return redirect(url_for('admin_edit_product', product_id=product.id))
        
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/edit_product.html', product=product, categories=categories)

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    if 'user_id' not in session or (session['user_role'] not in ['admin', 'ceo']):
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(product_id)
    
    if product.image_filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER_PRODUCTS'], product.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(product)
    db.session.commit()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('admin_products'))


# --- Rotas da Loja ---
@app.route('/produtos')
def products_list():
    category_id = request.args.get('category')
    if category_id:
        products = Product.query.filter_by(category_id=category_id).all()
        category_obj = Category.query.get(category_id)
        current_category_name = category_obj.name if category_obj else 'Produtos'
    else:
        products = Product.query.all()
        current_category_name = 'Todos os Produtos'
    return render_template('products.html', products=products, current_category_name=current_category_name)

@app.route('/produto/<int:product_id>')
def product_detail(product_id):
    # ATENÇÃO: Se você estiver usando products_mock_data na index,
    # esta rota precisa continuar buscando do DB se você a usar para produtos reais.
    # Para testes com mock_data, você precisaria adaptar a busca aqui também:
    product = next((p for p in products_mock_data if p['id'] == product_id), None)
    if product:
        return render_template('product_detail.html', product=product) # Você pode criar este template depois
    return "Produto não encontrado", 404


@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    # Esta rota é um placeholder, você implementará a lógica do carrinho depois
    return f"Produto {product_id} adicionado ao carrinho!" # Mensagem de exemplo

@app.route('/about')
def about():
    return render_template('about.html', title="Sobre Nós")

@app.route('/contact')
def contact():
    return render_template('contact.html', title="Contato")

@app.route('/returns')
def returns():
    return render_template('returns.html', title="Trocas e Devoluções")

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html', title="Política de Privacidade")

# Não se esqueça de adicionar as rotas que você ainda não tem mas que o base.html referencia:
@app.route('/cart')
def cart():
    flash("A página do carrinho ainda está sendo construída!", "info")
    return render_template('cart.html', title="Carrinho") # Você precisará criar cart.html

@app.route('/track_order')
def track_order():
    flash("A página de rastreamento de pedidos ainda está sendo construída!", "info")
    return render_template('track_order.html', title="Rastrear Pedido") # Você precisará criar track_order.html

@app.route('/favorites')
def favorites():
    flash("A página de favoritos ainda está sendo construída!", "info")
    return render_template('favorites.html', title="Meus Favoritos") # Você precisará criar favorites.html

@app.route('/search') # <-- NOVA ROTA DE BUSCA
def search_products():
    query = request.args.get('q') # Pega o termo de busca do parâmetro 'q'
    products = []
    if query:
        # Busca por nome ou descrição, case-insensitive
        products = Product.query.filter(
            or_(
                Product.name.ilike(f'%{query}%'),
                Product.description.ilike(f'%{query}%')
            )
        ).all()
        flash(f"Resultados para '{query}'", 'info')
    else:
        flash("Por favor, digite um termo para busca.", 'warning')

    return render_template('search_results.html', products=products, query=query)


# --- Bloco para Rodar a Aplicação ---
if __name__ == '__main__':
    with app.app_context():
        # Antes de db.create_all(), precisamos garantir que os modelos estão atualizados
        # com os novos campos (old_price, installments, product_code)
        db.create_all() # Isso criará as novas tabelas/colunas se elas não existirem

        # Adiciona categorias iniciais se não existirem
        if not Category.query.first():
            db.session.add(Category(name='Anéis'))
            db.session.add(Category(name='Brincos'))
            db.session.add(Category(name='Colares'))
            db.session.add(Category(name='Pulseiras'))
            db.session.add(Category(name='Novidades'))
            db.session.add(Category(name='Promoções'))
            db.session.commit()
            print("Categorias iniciais criadas.")
        
        # Adiciona o usuário CEO se não existir (apenas para o primeiro acesso)
        if not User.query.filter_by(role='ceo').first():
            print("Nenhum usuário CEO encontrado. Criando um usuário CEO padrão.")
            new_ceo = User(username='admin', role='ceo') # Nome de usuário pode ser 'admin' ou 'ceo'
            new_ceo.set_password("admin123") # <--- ALTERE ESTA SENHA PARA UMA SENHA SEGURA!
            db.session.add(new_ceo)
            db.session.commit()
            print("Usuário CEO 'admin' criado. Lembre-se de mudar a senha e remover a rota /register_admin_init em produção!")
        else:
            print("Usuário CEO já existe.")

        # Remove todos os banners existentes antes de adicionar o(s) novo(s) para garantir que apenas o de mães fique.
        # ISSO APAGARÁ QUALQUER BANNER QUE VOCÊ TENHA CADASTRADO ANTERIORMENTE.
        # Remova esta parte do código após a primeira execução se quiser gerenciar banners pelo admin.
        print("Verificando e limpando banners antigos...")
        existing_banners = Banner.query.all()
        for banner in existing_banners:
            # Opcional: Remover o arquivo físico também
            file_path = os.path.join(app.config['UPLOAD_FOLDER_BANNERS'], banner.image_filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(banner)
            print(f"Banner '{banner.image_filename}' removido.")
        db.session.commit()
        print("Banners antigos limpos.")


        # Adiciona APENAS o banner de mães
        # Certifique-se de que a imagem 'banner_maes.png' (ou .jpg) está em static/uploads/banners/
        # Use o nome do arquivo que você tem no seu diretório 'static/uploads/banners/'
        if not Banner.query.filter_by(image_filename='banner_mães.jpg').first(): # Adapte o nome do arquivo aqui se for diferente
            promo_banner = Banner(
                image_filename='banner_mães.jpg', # << COLOQUE O NOME COMPLETO DO SEU ARQUIVO DE IMAGEM AQUI (ex: banner_maes.jpg)
                alt_text='Promoção para mães Imperdível de Joias!',
                link_url=url_for('products_list', category='6'), # Exemplo de link para categoria promoções (ID 6)
                order_index=1, # Será o primeiro e único banner inicial
                is_active=True
            )
            db.session.add(promo_banner)
            db.session.commit()
            print("Banner de promoção para mães adicionado.")
        else:
            print("Banner de promoção para mães já existe.")

    app.run(debug=True, host='0.0.0.0')
