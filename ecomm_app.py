from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_marshmallow import Marshmallow
from datetime import date
from typing import List
from marshmallow import ValidationError, fields
from sqlalchemy import select, delete



app = Flask(__name__)
                                                                
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Martinez!1996@localhost/ecomm_db'

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)


class Customer(Base):
    __tablename__ = 'Customer'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    email: Mapped[str] = mapped_column(db.String(300))
    phone: Mapped[str] = mapped_column(db.String(16))

    orders: Mapped[List["Orders"]] = db.relationship(back_populates='customer') 
    
order_products = db.Table(
    "Order_Products",
    Base.metadata, 
    db.Column('order_id', db.ForeignKey('Orders.id'), primary_key=True),
    db.Column('product_id', db.ForeignKey('Products.id'), primary_key=True)
)


class Orders(Base):
    __tablename__ = 'Orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date] = mapped_column(db.Date, nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('Customer.id'))
    
    customer: Mapped['Customer'] = db.relationship(back_populates='orders')
    
    products: Mapped[List['Products']] = db.relationship(secondary=order_products)

class Products(Base):
    __tablename__ = "Products"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(db.String(255), nullable=False )
    price: Mapped[float] = mapped_column(db.Float, nullable=False)


with app.app_context():

    db.create_all()



class CustomerSchema(ma.Schema):
    id = fields.Integer(required=False)
    customer_name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ('id', 'customer_name', 'email', 'phone')

class ProductSchema(ma.Schema):
    id = fields.Integer(required=False)
    product_name = fields.String(required=True)
    price = fields.Float(required=True)

    class Meta:
        fields = ('id', 'product_name', 'price')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many= True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)




@app.route('/')
def home():
    return "Welcome to E-Comm!"


#====================Customer Interactions==========================


@app.route("/customers", methods=['GET'])
def get_customers():
    query = select(Customer)
    result = db.session.execute(query).scalars() 
    customers = result.all() 
    return customers_schema.jsonify(customers)


@app.route("/customers/<int:id>", methods=['GET'])
def get_customer(id):
    
    query = select(Customer).filter(Customer.id == id)
    result = db.session.execute(query).scalars().first()

    if result is None:
        return jsonify({"Error": "Customer not found"}), 404
    
    return customer_schema.jsonify(result)


@app.route("/customers", methods=["POST"])
def add_customer():

    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_customer = Customer(customer_name=customer_data['customer_name'], email=customer_data['email'], phone=customer_data['phone'])
    db.session.add(new_customer)
    db.session.commit()

    return jsonify({"Message": "New Customer added successfully"}), 201


@app.route("/customers/<int:id>", methods=['PUT'])
def update_customer(id):

    query = select(Customer).where(Customer.id == id)
    result = db.session.execute(query).scalars().first()
    if result is None:
        return jsonify({"Error": "Customer not found"}), 404
    
    customer = result
    
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    for field, value in customer_data.items():
        setattr(customer, field, value)

    db.session.commit()
    return jsonify({"Message": "Customer details have been updated!"})


@app.route("/customers/<int:id>", methods=['DELETE'])
def delete_customer(id):
    query = delete(Customer).filter(Customer.id == id)

    result = db.session.execute(query)

    if result.rowcount == 0:
        return jsonify({'Error': 'Customer not found'}), 404
    
    db.session.commit()
    return jsonify({"Message": "Customer removed Successfully!"}), 200



#====================Products Interactions==========================

#Create Single Product
@app.route('/products', methods=['POST'])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Products(product_name=product_data['product_name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"Messages": "New Product added!"}), 201

#Read Single product 
@app.route("/products/<int:id>", methods=['GET'])
def get_product(id):
    
    query = select(Products).filter(Products.id == id)
    result = db.session.execute(query).scalars().first() 

    if result is None:
        return jsonify({"Error": "Product not found"}), 404
    
    return product_schema.jsonify(result)

#Update Product
@app.route("/products/<int:id>", methods=['PUT'])
def update_product(id):

    query = select(Products).where(Products.id == id)
    result = db.session.execute(query).scalars().first()
    if result is None:
        return jsonify({"Error": "Product not found"}), 404
    
    product = result
    
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    for field, value in product_data.items():
        setattr(product, field, value)

    db.session.commit()
    return jsonify({"Message": "Customer details have been updated!"})

#Delete Product
@app.route("/products/<int:id>", methods=['DELETE'])
def delete_product(id):
    query = delete(Products).filter(Products.id == id)

    result = db.session.execute(query)

    if result.rowcount == 0:
        return jsonify({'Error': 'Product not found'}), 404
    
    db.session.commit()
    return jsonify({"Message": "Product removed Successfully!"}), 200

#List All Products
@app.route("/products", methods=['GET'])
def get_products():
    query = select(Products)
    result = db.session.execute(query).scalars() 
    products = result.all() 
    return products_schema.jsonify(products)


#====================Order Operations================================



class OrderSchema(ma.Schema):
    id= fields.Integer(required=False)
    order_date = fields.Date(required=False)
    customer_id = fields.Integer(required=True)
    status = fields.String(required=False)

    
    class Meta:
        fields = ('id', 'order_date', 'customer_id', 'status', 'items') 


order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

@app.route('/orders', methods=['POST'])
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_order = Orders(order_date=date.today(), customer_id = order_data['customer_id'])

    for item_id in order_data['items']:
        query = select(Products).filter(Products.id == item_id)
        item = db.session.execute(query).scalar()
        new_order.products.append(item)
    
    db.session.add(new_order)
    db.session.commit()

    return jsonify({"Message": "New Order Placed!"}), 201


@app.route("/order_items/<int:id>", methods=['GET'])
def order_items(id):
    query = select(Orders).filter(Orders.id == id)
    order = db.session.execute(query).scalar()
    return products_schema.jsonify(order.products)



@app.route('/orders/track/<int:id>', methods=['GET'])
def track_order(id):
    query = select(Orders).filter(Orders.id == id)
    result = db.session.execute(query).scalar()
    if result is None:
        return jsonify({"Error": "Order not found"}), 404
    order_data = {
        "id": result.id,
        "order_date": result.order_date,
        "customer_id": result.customer_id,}
        
    return jsonify(order_data)



if __name__ == '__main__':
    app.run(debug=True)