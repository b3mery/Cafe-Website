from http import HTTPStatus
import random
import requests
import sqlalchemy.exc
from flask import Flask, jsonify, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

API_KEY = "TopSecretAPIKey"
##Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##Cafe TABLE Configuration
class Cafe(db.Model):
    """_summary_

    Args:
        db (_type_): _description_

    Returns:
        _type_: _description_
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}     

###################3#################################################### APIs  ##############################################################################################
@app.route("/random",  methods=["GET"])
def get_random_cafe():
    all_cafes = db.session.query(Cafe).all()
    rand_cafe = random.choice(all_cafes)
    # Simply convert the random_cafe data record to a dictionary of key-value pairs. 
    # return jsonify(cafe=rand_cafe.to_dict())
    return jsonify(
        cafe={
            "id": rand_cafe.id,
            "name": rand_cafe.name,
            "map_url": rand_cafe.map_url,
            "img_url": rand_cafe.img_url,
            "location": rand_cafe.location,
            "coffee_price": rand_cafe.coffee_price,

            "amenities": {
                "seats": rand_cafe.seats,
                "has_toilet": rand_cafe.has_toilet,
                "has_wifi": rand_cafe.has_wifi,
                "has_sockets": rand_cafe.has_sockets,
                "can_take_calls": rand_cafe.can_take_calls,
            }

        } 
    )

@app.route("/all",  methods=["GET"])
def get_all_cafes():
    all_cafes = db.session.query(Cafe).all()
    return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])

@app.route("/search",  methods=["GET"])
def get_search():
    args = request.args
    loc = args.get('loc')
    if loc is None:
        return jsonify(status=HTTPStatus.BAD_REQUEST, desc="Invalid parameters expected parameter 'loc' " ), 404
    all_cafe = db.session.query(Cafe).filter_by(location=loc)
    if all_cafe:
        return jsonify(cafes=[cafe.to_dict() for cafe in all_cafe])
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."}), 404

## HTTP POST - Create Record
@app.route("/add", methods=["POST"])
def post_new_cafe():
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=bool(request.form.get("sockets", False)),
        has_toilet=bool(request.form.get("toilet", False)),
        has_wifi=bool(request.form.get("wifi", False)),
        can_take_calls=bool(request.form.get("calls", False)),
        seats=request.form.get("seats", 'False'),
        coffee_price=request.form.get("coffee_price"),
    )
    try:
        db.session.add(new_cafe)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        return jsonify(response={"bad request": "Could not add the cafe."}),403    
    else:
        return jsonify(response={"success": "Successfully added the new cafe."}), 200

## HTTP PUT/PATCH - Update Record
@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def put_update_price(cafe_id):
    
    args = request.args
    new_price = args.get('new_price') 
    if new_price is None:
        return jsonify(status=HTTPStatus.BAD_REQUEST, desc="Invalid parameters expected parameter 'new_price' " ), 404
    cafe = db.session.query(Cafe).get(cafe_id)
    if cafe is None:
        return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404
    
    cafe.coffee_price = new_price
    db.session.commit() 
    return jsonify(response={"success": "Successfully updated the coffee price."}), 200 

## HTTP DELETE - Delete Record
@app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
def delete_remove_cafe(cafe_id):
    args = request.args
    api_key = args.get('api-key')
    if api_key != API_KEY:
        return jsonify(error={"error": "Sorry that is not allowed, make sure you have the correct api-key"}), 403
    
    cafe = db.session.query(Cafe).get(cafe_id)
    if cafe is None:
        return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404
    
    db.session.delete(cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully deleted the cafe from the database."}), 200

###################3#################################################### Web Page ##############################################################################################

@app.route("/") 
def home():
    response = requests.get(f"{request.base_url[:-1]}{url_for('get_all_cafes')}")
    data = response.json()['cafes']
    # print(f"{request.base_url[:-1]}{url_for('get_all_cafes')}")
    return render_template("index.html", cafes=data)

@app.route("/cafe/<int:cafe_id>")
def show_cafe(cafe_id):
    cafe = Cafe.query.get(cafe_id)
    return render_template("cafe.html", cafe = cafe)

@app.route("/cafe/new",  methods=["GET", "POST"])
def add_cafe():
    if request.method == 'POST':
        new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=bool(request.form.get("sockets", False)),
        has_toilet=bool(request.form.get("toilet", False)),
        has_wifi=bool(request.form.get("wifi", False)),
        can_take_calls=bool(request.form.get("calls", False)),
        seats=request.form.get("seats", 'False'),
        coffee_price=request.form.get("coffee_price"),
    )
        try:
            db.session.add(new_cafe)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            # return render_template('new_cafe.html')   
            # Could add error messages to new_cafe.html
            return redirect(url_for('home')) 
        else:
            return redirect(url_for('home'))
    return render_template('new_cafe.html')    


if __name__ == '__main__':
    app.run(debug=True)
