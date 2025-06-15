from flask import Flask, request, render_template, redirect, url_for, jsonify, session
from twilio.rest import Client

import random
import mysql.connector
import base64


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Twilio Configuration
TWILIO_ACCOUNT_SID = 'AC6579f7347fe303d02ebc837ba9da7227'
TWILIO_AUTH_TOKEN = 'e302b47ad59ceaab9fa9ea3360118c87'
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

otp_storage = {}
otp_mitra_storage = {}

@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/login_user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        return redirect(url_for('index', username=username))
    return render_template('login_user.html')

@app.route('/login_mitra', methods=['GET', 'POST'])
def login_mitra():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        
        session['username'] = username
        
        return redirect(url_for('halaman_mitra', username=username))
    return render_template('login_mitra.html')


@app.route('/form_daftar_mitra')
def form_daftar_mitra():
    username = request.args.get('username')
    if not username:
        return "Username tidak diberikan", 400

    try:
        db = mysql.connector.connect(
            host="localhost", user="root", password="", database="medisgo"
        )
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM akun_mitra WHERE user_name = %s", (username,))
        mitra = cursor.fetchone()
        cursor.close()
        db.close()
    except Exception as e:
        return f"Error mengambil data: {str(e)}", 500

    return render_template('form_daftar_mitra.html', username=username, mitra=mitra)

@app.route('/simpan_data_mitra', methods=['POST'])
def simpan_data_mitra():
    username = request.form.get('username')
    jenis_mitra = request.form.get('jenis_mitra')
    alamat = request.form.get('alamat')
    no_telepon = request.form.get('no_telepon')
    no_izin_operasional = request.form.get('no_izin_operasional')
    nama_mitra = request.form.get('nama_klinik')
    email= request.form.get('email')

    session['nama_klinik'] = nama_mitra

    try:
        db = mysql.connector.connect(
            host="localhost", user="root", password="", database="medisgo"
        )
        cursor = db.cursor()
        cursor.execute("""
            UPDATE akun_mitra 
            SET jenis_mitra = %s, alamat = %s, no_telepon = %s, no_izin_operasional = %s, email = %s, nama_klinik = %s
            WHERE user_name = %s
        """, (jenis_mitra, alamat, no_telepon, no_izin_operasional, email, nama_mitra, username))

        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('form_daftar_mitra', username=username))
    except Exception as e:
        return f"Error menyimpan data: {str(e)}", 500


@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register_mitra')
def register_mitra():
    return render_template('register_mitra.html')

def format_phone(phone):
    if phone.startswith('0'):
        return 'whatsapp:+62' + phone[1:]
    elif phone.startswith('+62'):
        return 'whatsapp:' + phone
    return 'whatsapp:' + phone

@app.route('/send_otp', methods=['POST'])
def send_otp():
    username = request.form.get('username')
    password = request.form.get('password')
    phone = format_phone(request.form.get('phone'))

    if not username or not phone or not password:
        return "Semua field wajib diisi", 400

    otp = str(random.randint(100000, 999999))
    otp_storage[phone] = {"otp": otp, "username": username, "password": password}

    try:
        client.messages.create(
            body=f"Kode verifikasi Anda: {otp}",
            from_=TWILIO_WHATSAPP_NUMBER,
            to=phone
        )
    except Exception as e:
        return f"OTP gagal dikirim: {str(e)}", 500

    return redirect(url_for('verify_otp', phone=phone))

@app.route('/send_otp_mitra', methods=['POST'])
def send_otp_mitra():
    username = request.form.get('username')
    password = request.form.get('password')
    phone = format_phone(request.form.get('phone'))

    if not username or not phone or not password:
        return "Semua field wajib diisi", 400

    otp = str(random.randint(100000, 999999))
    otp_mitra_storage[phone] = {"otp": otp, "username": username, "password": password}

    try:
        client.messages.create(
            body=f"Kode verifikasi Mitra: {otp}",
            from_=TWILIO_WHATSAPP_NUMBER,
            to=phone
        )
    except Exception as e:
        return f"OTP gagal dikirim: {str(e)}", 500

    return redirect(url_for('verify_mitra', phone=phone))

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'GET':
        return render_template('verify_otp.html', phone=request.args.get('phone', ''))

    phone = request.form.get('phone')
    user_otp = request.form.get('otp')
    record = otp_storage.get(phone)

    if record and record['otp'] == user_otp:
        try:
            db = mysql.connector.connect(
                host="localhost", user="root", password="", database="medisgo"
            )
            cursor = db.cursor()
            cursor.execute("INSERT INTO akun (username, pasword) VALUES (%s, %s)", (record['username'], record['password']))
            db.commit()
            cursor.close()
            db.close()
        except Exception as e:
            return f"DB error: {str(e)}", 500

        del otp_storage[phone]
        return redirect(url_for('index', username=record['username']))

    return "OTP salah atau sudah kedaluwarsa", 400

@app.route('/verify_mitra', methods=['GET', 'POST'])
def verify_mitra():
    if request.method == 'GET':
        return render_template('verify_mitra.html', phone=request.args.get('phone', ''))

    phone = request.form.get('phone')
    user_otp = request.form.get('otp')
    record = otp_mitra_storage.get(phone)

    if record and record['otp'] == user_otp:
        try:
            db = mysql.connector.connect(
                host="localhost", user="root", password="", database="medisgo"
            )
            cursor = db.cursor()
            cursor.execute("INSERT INTO akun_mitra (user_name, pasword) VALUES (%s, %s)", (record['username'], record['password']))
            db.commit()
            cursor.close()
            db.close()
        except Exception as e:
            return f"DB error: {str(e)}", 500

        del otp_mitra_storage[phone]
        return redirect(url_for('form_daftar_mitra', username=record['username']))

    return "OTP salah atau sudah kedaluwarsa", 400

@app.route('/index')
def index():
    username = request.args.get('username', 'User')
    return render_template('index.html', username=username)

@app.route('/halaman_mitra')
def halaman_mitra():
    username = request.args.get('username')
    if not username:
        return "Username tidak diberikan", 400

    try:
        db = mysql.connector.connect(
            host="localhost", user="root", password="", database="medisgo"
        )
        cursor = db.cursor(dictionary=True, buffered=True)  # <-- tambahkan buffered=True
        cursor.execute("""
            SELECT jenis_mitra, nama_klinik, email, alamat, no_telepon, no_izin_operasional
            FROM akun_mitra WHERE user_name = %s
        """, (username,))
        result = cursor.fetchone()
        cursor.close()
        db.close()

        if result:
            jenis_mitra = result['jenis_mitra']
            return render_template('halaman_mitra.html',
                                   username=username,
                                   jenis_mitra=jenis_mitra,
                                   mitra=result)
        else:
            return "User tidak ditemukan", 404

    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/api/mitra')
def api_mitra():
    try:
        db = mysql.connector.connect(
            host="localhost", user="root", password="", database="medisgo"
        )
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT nama_klinik as nama, jenis_mitra as jenis, alamat, no_izin_operasional as izin
            FROM akun_mitra
            WHERE nama_klinik IS NOT NULL
        """)
        mitra_list = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(mitra_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/tambah_obat', methods=['GET', 'POST'])
def tambah_obat():
    if 'username' not in session:
        return "User belum login", 401

    if request.method == 'POST':
        username = session['username']
        nama_obat = request.form['nama_obat']
        keterangan = request.form['keterangan']
        harga = request.form['harga']

        file = request.files['foto']
        if file and file.filename != '':
            foto_blob = file.read()  # Baca isi file sebagai binary
        else:
            foto_blob = None  # Jika tidak ada file dikirim

        # Simpan ke database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="medisgo"
        )
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO obat (user_name, nama_obat, keterangan, harga, foto)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, nama_obat, keterangan, harga, foto_blob))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('tambah_obat', success=1))

    return render_template('tambah_obat.html', username=session['username'])


@app.route('/tambah_dokter', methods=['GET', 'POST'])
def tambah_dokter():
    if 'username' not in session:
        return "User belum login", 401

    username = session['username']

    db = mysql.connector.connect(
        host="localhost", user="root", password="", database="medisgo"
    )
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT nama_klinik FROM akun_mitra WHERE user_name = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    db.close()

    if not result or not result['nama_klinik']:
        return "Nama klinik belum diatur", 400

    nama_mitra = result['nama_klinik']

    if request.method == 'POST':
        nama_dokter = request.form['nama_dokter']
        spesialisasi = request.form['spesialis']
        jadwal_praktik = request.form['jadwal_praktek']

        if not nama_dokter or not spesialisasi or not jadwal_praktik:
            return "Semua field wajib diisi", 400

        try:
            db = mysql.connector.connect(
                host="localhost", user="root", password="", database="medisgo"
            )
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO dokter (nama_dokter, spesialis, jadwal_praktek, user_name, nama_klinik)
                VALUES (%s, %s, %s, %s, %s)
            """, (nama_dokter, spesialisasi, jadwal_praktik, username, nama_mitra))
            db.commit()
            cursor.close()
            db.close()

            return redirect(url_for('halaman_mitra', username=username))
        except Exception as e:
            return f"Error menyimpan data dokter: {str(e)}", 500

    return render_template('tambah_dokter.html', username=username)

@app.route('/daftar_obat', methods=['GET'])
def daftar_obat():
    if 'username' not in session:
        return "User belum login", 401

    username = session['username']

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  
        database="medisgo"
    )
    cursor = conn.cursor(dictionary=True)

   
    sql = "SELECT * FROM obat WHERE user_name = %s"
    val = (username,)
    cursor.execute(sql, val)

    data_obat = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('daftar_obat.html', username=username, data_obat=data_obat)

@app.route('/daftar_dokter', methods=['GET'])
def daftar_dokter():
    if 'username' not in session:
        return "User belum login", 401

    username = session['username']

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  
        database="medisgo"
    )
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM dokter WHERE user_name = %s"
    val = (username,)
    cursor.execute(sql, val)

    data_dokter = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('daftar_dokter.html', username=username, data_dokter=data_dokter)

@app.route("/api/mitrav2")
def api_mitrav2():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="medisgo"
    )
    cursor = conn.cursor(dictionary=True)

    # Ambil semua mitra (klinik dan apotek)
    cursor.execute("""
        SELECT 
            user_name, 
            nama_klinik AS nama, 
            jenis_mitra AS jenis, 
            alamat, 
            no_izin_operasional AS izin
        FROM akun_mitra
    """)
    mitra = cursor.fetchall()

    # Ambil semua dokter sekaligus
    cursor.execute("""
        SELECT 
            nama_dokter, 
            spesialis, 
            jadwal_praktek, 
            nama_klinik
        FROM dokter
    """)
    semua_dokter = cursor.fetchall()

    # Kelompokkan dokter berdasarkan nama_klinik
    dokter_by_klinik = {}
    for d in semua_dokter:
        key = d["nama_klinik"]
        if key not in dokter_by_klinik:
            dokter_by_klinik[key] = []
        dokter_by_klinik[key].append({
            "nama_dokter": d["nama_dokter"],
            "spesialis": d["spesialis"],
            "jadwal_praktek": d["jadwal_praktek"]
        })
    cursor.execute("""
        SELECT 
            nama_obat, 
            keterangan, 
            harga, 
            user_name,
            foto
        FROM obat
    """)
    semua_obat = cursor.fetchall()

    # Kelompokkan dokter berdasarkan nama_klinik
    obat_by_apotek = {}
    for d in semua_obat:
        key = d["user_name"]
        if key not in obat_by_apotek:
            obat_by_apotek[key] = []
        obat_by_apotek[key].append({
            "nama_obat": d["nama_obat"],
            "keterangan": d["keterangan"],
            "harga": d["harga"],
            "foto":d["foto"]
        })

    for m in mitra:
        nama_klinik = m["nama"]
        m["dokter"] = dokter_by_klinik.get(nama_klinik, [])
        m["apotek"] = obat_by_apotek.get(nama_klinik,[])

    cursor.close()
    conn.close()
    return jsonify(mitra)



@app.route("/detail-klinik")
def detail_klinik():
    user_name = request.args.get("user_name")

    if not user_name:
        return "<h3 class='text-danger text-center'>Parameter 'user_name' tidak ditemukan.</h3>"

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="medisgo"
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT user_name, nama_klinik, alamat, no_telepon, email,
               no_izin_operasional AS izin, jenis_mitra AS jenis
        FROM akun_mitra
        WHERE LOWER(user_name) = LOWER(%s) AND jenis_mitra = 'klinik'
    """, (user_name,))
    data_klinik = cursor.fetchone()

    if not data_klinik:
        cursor.close()
        conn.close()
        return f"<h4 class='text-center text-danger'>Klinik dengan user_name '{user_name}' tidak ditemukan.</h4>"

    cursor.execute("""
        SELECT nama_dokter, spesialis, jadwal_praktek
        FROM dokter
        WHERE LOWER(nama_klinik) = LOWER(%s)
    """, (data_klinik['nama_klinik'],))


    daftar_dokter = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("detail_klinik.html", data=data_klinik, dokter_list=daftar_dokter)

@app.route("/detail-apotek")
def detail_apotek():
    user_name = request.args.get("user_name")

    if not user_name:
        return "<h3 class='text-danger text-center'>Parameter 'user_name' tidak ditemukan.</h3>"

    # Koneksi ke database
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="medisgo"
    )
    cursor = conn.cursor(dictionary=True)

    # Ambil data apotek
    cursor.execute("""
        SELECT user_name, nama_klinik, alamat, no_telepon, email,
               no_izin_operasional AS izin, jenis_mitra AS jenis
        FROM akun_mitra
        WHERE LOWER(user_name) = LOWER(%s) AND jenis_mitra = 'apotek'
    """, (user_name,))
    data_klinik = cursor.fetchone()

    if not data_klinik:
        cursor.close()
        conn.close()
        return f"<h4 class='text-center text-danger'>Apotek dengan user_name '{user_name}' tidak ditemukan.</h4>"

    # Ambil daftar obat dan konversi foto BLOB ke base64
    cursor.execute("""
        SELECT nama_obat, keterangan, harga, foto
        FROM obat
        WHERE LOWER(user_name) = LOWER(%s)
    """, (data_klinik['user_name'],))

    daftar_obat = cursor.fetchall()

    for obat in daftar_obat:
        if obat['foto']:
            # Konversi foto dari BLOB ke base64 string
            obat['foto_base64'] = base64.b64encode(obat['foto']).decode('utf-8')
        else:
            obat['foto_base64'] = None

    cursor.close()
    conn.close()

    # Kirim ke template HTML
    return render_template("detail_apotek.html", data=data_klinik, obat_list=daftar_obat)





if __name__ == '__main__':
    app.run(debug=True)
