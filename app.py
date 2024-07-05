from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import pandas as pd
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Tambahkan secret key untuk session

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

# Route untuk menampilkan form input
@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

# Route untuk menangani form submission dari web browser
@app.route('/process', methods=['POST'])
def process():
    try:
        teks = request.form['teks']
        teks_normalisasi = normalisasi_teks(teks, normalisasi_dict)
        
        # Simpan hasil input dan output normalisasi ke database
        conn = sqlite3.connect('normalisasi.db')
        c = conn.cursor()
        c.execute('INSERT INTO normalisasi (input_text, output_text) VALUES (?, ?)', (teks, teks_normalisasi))
        conn.commit()
        last_id = c.lastrowid
        conn.close()

        return render_template('result.html', input_text=teks, output_text=teks_normalisasi)
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
            return redirect(url_for('index'))
        else:
            return 'Invalid credentials!', 401
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
            result.append({'id': row[0], 'input_text': row[1], 'output_text': row[2]})
            
        return render_template('normalisasi_list.html', normalisasi_list=result)
    except Exception as e:
        print(e)
        return str(e), 500

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

# Menjalankan aplikasi pada port 5000
if __name__ == '__main__':
    app.run(port=5000, debug=True)
