from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory, flash
from flask_session import Session
import pandas as pd
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False  # Sesi akan dihapus ketika browser ditutup
Session(app)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Pastikan folder untuk mengunggah file ada
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Kamus normalisasi di-load sekali ketika aplikasi Flask dimulai
df_normalisasi = pd.read_csv('new_kamusalay.csv', header=None, names=['tidak_baku', 'baku'], encoding='latin1')
normalisasi_dict = pd.Series(df_normalisasi['baku'].values, index=df_normalisasi['tidak_baku']).to_dict()

# Inisialisasi database SQLite
def init_sqlite_db():
    conn = sqlite3.connect('normalisasi.db')
    c = conn.cursor()
    # Buat tabel dengan kolom input_text dan output_text
    c.execute('''
        CREATE TABLE IF NOT EXISTS normalisasi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT NOT NULL,
            output_text TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_sqlite_db()

# Fungsi normalisasi teks yang akan digunakan untuk endpoint API
def normalisasi_teks(teks, normalisasi_dict):
    words = teks.split()
    normalized_words = []
    for word in words:
        if word in normalisasi_dict:
            normalized_word = normalisasi_dict[word]
        else:
            normalized_word = word
        normalized_words.append(normalized_word)
    return ' '.join(normalized_words)

# Fungsi untuk memproses unggahan file
def normalisasi_dari_file(file_path, normalisasi_dict):
    try:
        ext = os.path.splitext(file_path)[1]
        if ext == '.txt':
            with open(file_path, 'r', encoding="utf-8") as file:
                teks = file.read()
        elif ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
            teks = ' '.join(df.astype(str).values.flatten())
        else:
            return None
        
        return normalisasi_teks(teks, normalisasi_dict)
    except Exception as e:
        print(e)
        return None

@app.before_request
def before_request():
    if 'username' not in session and request.endpoint not in ['login', 'static']:
        return redirect(url_for('login'))

# Route untuk halaman dashboard
@app.route('/process_normalisasi')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    return render_template('dashboard.html', username=username)
# Route untuk menampilkan form input
@app.route('/')
def index():
    if 'username' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))

# Route untuk menangani form submission dari web browser
@app.route('/process', methods=['POST'])
def process():
    try:
        teks = request.form.get('teks', '')
        file = request.files.get('file')

        if file and file.filename != '':
            # Simpan file ke server
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            teks_normalisasi = normalisasi_dari_file(file_path, normalisasi_dict)
            input_text = file.filename  # Simpan nama file sebagai input
        else:
            teks_normalisasi = normalisasi_teks(teks, normalisasi_dict)
            input_text = teks

        # Simpan hasil input dan output normalisasi ke database
        conn = sqlite3.connect('normalisasi.db')
        c = conn.cursor()
        c.execute('INSERT INTO normalisasi (input_text, output_text) VALUES (?, ?)', (input_text, teks_normalisasi))
        conn.commit()
        last_id = c.lastrowid
        conn.close()

        return render_template('result.html', input_text=input_text, output_text=teks_normalisasi)
    except Exception as e:
        print(e)
        return str(e), 500



# Route untuk halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Abaikan validasi sederhana (hanya contoh)
        if username == 'admin' and password == 'password':
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials, please try again', 'danger')
            return render_template('login')
    return render_template('login.html')

# Route untuk login keluar
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Route untuk menampilkan hasil normalisasi
@app.route('/normalisasi_list')
def normalisasi_list():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        conn = sqlite3.connect('normalisasi.db')
        c = conn.cursor()
        c.execute('SELECT * FROM normalisasi')
        rows = c.fetchall()
        conn.close()

        result = []
        for row in rows:
            is_file = row[1].endswith('.txt') or row[1].endswith('.xls') or row[1].endswith('.xlsx')
            result.append({'id': row[0], 'input_text': row[1], 'output_text': row[2], 'is_file': is_file})
            
        return render_template('normalisasi_list.html', normalisasi_list=result)
    except Exception as e:
        print(e)
        return str(e), 500

# Route untuk mengunduh file
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Endpoint API untuk mendapatkan semua hasil normalisasi
@app.route('/get_normalisasi', methods=['GET'])
def get_normalisasi():
    try:
        conn = sqlite3.connect('normalisasi.db')
        c = conn.cursor()
        c.execute('SELECT * FROM normalisasi')
        rows = c.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({'id': row[0], 'input': row[1], 'output': row[2]})
            
        return jsonify(result)
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

# Endpoint API untuk proses normalisasi
@app.route('/normalisasi', methods=['POST'])
def normalisasi():
    try:
        data = request.get_json()
        teks = data.get('teks', '')
        teks_normalisasi = normalisasi_teks(teks, normalisasi_dict)
        
        # Simpan hasil input dan output normalisasi ke database
        conn = sqlite3.connect('normalisasi.db')
        c = conn.cursor()
        c.execute('INSERT INTO normalisasi (input_text, output_text) VALUES (?, ?)', (teks, teks_normalisasi))
        conn.commit()
        last_id = c.lastrowid
        conn.close()

        return jsonify({'id': last_id, 'teks_normalisasi': teks_normalisasi})
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

# Swagger UI konfigurasi
from flask_swagger_ui import get_swaggerui_blueprint

### Swagger specific ###
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'  # Adjust the URL to where your swagger.json is located

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Normalisasi Teks API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Menjalankan aplikasi pada port 5000
if __name__ == '__main__':
    app.run(port=5000, debug=True)
