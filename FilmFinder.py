from flask import Flask, jsonify, request, render_template
import webbrowser
from threading import Timer

import sqlite3
import requests

# Configuración de la API
API_KEY = "731e41f"
BASE_URL = "http://www.omdbapi.com/"

# Inicializar la aplicación Flask
app = Flask(__name__)

# Ruta para inicializar la base de datos
@app.route('/init_db', methods=['GET'])
def init_db():
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            year INTEGER NOT NULL,
            poster TEXT,
            rating INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    return "Base de datos inicializada."

# Ruta para obtener y guardar películas de Harry Potter
@app.route('/fetch_movies', methods=['GET'])
def fetch_movies():
    response = requests.get(f"{BASE_URL}?s=Harry%20Potter&apikey={API_KEY}")
    if response.status_code != 200:
        return jsonify({"error": "Error al obtener datos de la API"}), 500

    data = response.json()
    movies = data.get("Search", [])

    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    for movie in movies:
        # Datos a guardar
        imdb_id = movie.get("imdbID")
        title = movie.get("Title")
        year = int(movie.get("Year", "0").split()[0])  # Solo el año
        poster = movie.get("Poster")
        rating = 4  # Valor inventado, puede ser dinámico

        # Guardar en la base de datos
        cursor.execute('''
            INSERT OR REPLACE INTO movies (id, title, year, poster, rating)
            VALUES (?, ?, ?, ?, ?)
        ''', (imdb_id, title, year, poster, rating))

    conn.commit()
    conn.close()
    return jsonify({"message": "Películas guardadas en la base de datos."})

# Ruta para mostrar películas con filtros opcionales
@app.route('/movies', methods=['GET'])
def get_movies():
    title_filter = request.args.get('title', '').lower()
    year_filter = request.args.get('year', '')
    rating_filter = request.args.get('rating', '')

    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    query = "SELECT * FROM movies WHERE 1=1"
    params = []

    if title_filter:
        query += " AND LOWER(title) LIKE ?"
        params.append(f"%{title_filter}%")
    if year_filter:
        query += " AND year = ?"
        params.append(year_filter)
    if rating_filter:
        query += " AND rating = ?"
        params.append(rating_filter)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    movies = [
        {"id": row[0], "title": row[1], "year": row[2], "poster": row[3], "rating": row[4]}
        for row in rows
    ]
    return jsonify(movies)

# Ruta para renderizar la tabla en HTML (opcional)
@app.route('/')
def index():
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM movies')
    rows = cursor.fetchall()
    conn.close()

    return render_template('index.html', movies=rows)


def open_browser():
    """Abre el navegador predeterminado en la URL de la aplicación."""
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Inicializar la base de datos
    with app.app_context():
        init_db()
        fetch_movies()

    # Abrir el navegador después de un breve retraso
    Timer(1, open_browser).start()

    # Iniciar la aplicación Flask
    app.run(debug=False)