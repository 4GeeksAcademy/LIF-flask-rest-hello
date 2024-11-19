"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Characters, Planet_Favorites, Favorite_Characters
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app) #Comentario de Prueba para subir a GitHub

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.al()
    print(users)# users es una lista que contiene todos los usuarios
    users_serialized = []
    for user in users:
        users_serialized.append(user.serialize())
        #serializar es convertir un dato tipo modelo a dict
        #solo asi se puede convertir en JSON
    return jsonify({'msg':'ok', 'data': users_serialized}), 200

#Traer presonajes favoritos de un usuario
@app.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    favorite_characters = [fav.character_relationship.serialize()for fav in user.character_favorites]
    favorite_planets = [fav.planet_relationship.serialize() for fav in user.planet_favorites]

    return jsonify(
        {
            'msg': 'Favoritos obtenidos con éxito',
            'favorites':{
                'characters': favorite_characters,
                'planets': favorite_planets

            }
        }
    ), 200


@app.route('/planet', methods=['POST'])   
def post_planet():
    #para crear un planeta necesitamos un body que contenga
    #el nombre y el clima del planeta
    body = request.get_json( silent=True)
    if body is None:
        return jsonify({'msg': 'Debes enviar información en el body'}), 400
    if 'name' not in body:
        return jsonify({'msg': 'El campo name es obligatorio'}), 400
    if 'climate' not in body:
        return jsonify({'msg': 'El campo climate es obligatorio'}), 400
    new_planet = Planet()
    new_planet.name = body['name']
    new_planet.climate = body ['climate']
    db.session.add(new_planet)
    db.session.commit()

    return jsonify(
        {
            'msg': 'Planeta agregado con éxito',
            'data': new_planet.serialize() 
        }
    ), 201

@app.route('/characters/<int:id>', methods = ['GET'])
def get_characters(id):
    character = Characters.query.get(id)
    print(character) #objeto
    print(character.name)
    print(character.planet_id)
    print(character.planet_id_relationship) #objeto
    print(character.planet_id_relationship.name)
    character_serialized = character.serialize()

    return jsonify(
        {
            'msg': 'ok',
            'data': character_serialized
        }
    )

@app.route('/favorite_planets/<int:user_id>', methods = ['GET'])
def get_favorites_buy_user(user_id):
    user = User.query.get(user_id)
    #print (user)
    #print (user.planet_favorites)
    favorite_planets_serialized =[]
    for fav_planet in user.planet_favorites:
        favorite_planets_serialized.append(fav_planet.planet_relationship.serilized())
    data ={
        'user_info': user.serialize(),
        'planets_favorites': favorite_planets_serialized
    }

    return jsonify(
        {
            'msg': 'ok',
            'data': data
        }
    )

@app.route('/favorite/people/<int:people_id>/<int:user_id>', methods=['POST'])
def add_favorite_character(people_id, user_id):
    user = User.query.get(user_id)
    character = Characters.query.get(people_id)

    if not user or not character:
        return jsonify({'msg': 'Usuario o persona no econtrado'}), 404
    
    new_favorite = Favorite_Characters(user_id = user_id, character_id = people_id)
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify (
        {
            'msg': 'Personaje favorito agregado con éxito',
            'data': new_favorite.serialize()
        }
    ), 201

# Borrar un personaje favorito
@app.route('/favorite/people/<int:people_id>/ <ing:user_id>', methods =['DELETE'])
def delete_favorite_character(people_id, user_id):
    favorite = Favorite_Characters.query.filter_by(user_id =user_id, character_id= people_id).first()

    if not favorite:
        return jsonify({'msg': 'Personaje favorito no encontrado'}), 404
    
    db.session.delete(favorite)
    db.session.commit()

    return jsonify({'msg': 'Personaje favorito eliminado con éxito'}), 200

   


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
