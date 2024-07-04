from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Kamus normalisasi di-load sekali ketika aplikasi Flask dimulai
df_normalisasi = pd.read_csv('../new_kamusalay.csv', header=None, names=['tidak_baku', 'baku'], encoding='latin1')
normalisasi_dict = pd.Series(df_normalisasi['baku'].values, index=df_normalisasi['tidak_baku']).to_dict()

# Tempat untuk menyimpan hasil normalisasi
normalisasi_storage = []

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

# Membuat endpoint API untuk proses normalisasi teks
@app.route('/normalisasi', methods=['POST'])
def normalisasi():
    try:
        data = request.get_json()
        teks = data.get('teks', '')
        teks_normalisasi = normalisasi_teks(teks, normalisasi_dict)
        
        # Simpan hasil input dan output normalisasi ke storage
        normalisasi_storage.append({'input': teks, 'output': teks_normalisasi})

        return jsonify({'teks_normalisasi': teks_normalisasi})
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

# Membuat endpoint API untuk mendapatkan semua hasil normalisasi
@app.route('/get_normalisasi', methods=['GET'])
def get_normalisasi():
    try:
        return jsonify(normalisasi_storage)
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

# Menjalankan aplikasi pada port 5000
if __name__ == '__main__':
    app.run(port=5000, debug=True)
