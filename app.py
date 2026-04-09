# ============================================================
# app.py - Lab Inventory Management System v3.0
# Sekolah : SMKN 1 Cikarang Selatan, Bekasi - Lab TJKT
# Fitur   : CRUD, QR Code, Export Excel/PDF, Cetak Label QR,
#           Filter & Sorting, Peminjaman & Pengembalian Barang
# ============================================================

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, send_file)
from flask_mysqldb import MySQL
import bcrypt, qrcode, os, json, io
from datetime import datetime, date, timedelta
from functools import wraps

# ─────────────────────────────────────────────
# INISIALISASI APP
# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'labkomputer_secret_kp_2024'
app.config['MYSQL_HOST']        = 'localhost'
app.config['MYSQL_USER']        = 'root'
app.config['MYSQL_PASSWORD']    = ''
app.config['MYSQL_DB']          = 'inventaris_lab'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# ─────────────────────────────────────────────
# CONTEXT PROCESSOR
# ─────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return {'now_year': datetime.now().strftime('%Y')}

# ============================================================
# REFERENSI: Prefix kode, tipe produk per kategori
# Format kode: [PREFIX_KAT]-[PREFIX_TIPE]-[TAHUN]-[NOURUT]
# ============================================================
KATEGORI_PREFIX = {
    'Komputer' :'KOM','Monitor':'MON','Jaringan':'NET',
    'Peripheral':'PRP','Printer':'PRN','Listrik':'PWR',
    'Scanner'  :'SCN','Furnitur':'FRN','Lainnya':'LNY',
}

# Tipe produk per kategori (untuk dropdown)
TIPE_PER_KATEGORI = {
    'Komputer'  :['Core i3','Core i5','Core i7','Ryzen 3','Ryzen 5','Ryzen 7','Celeron','Pentium','Xeon'],
    'Monitor'   :['Full HD 22"','Full HD 24"','HD 19"','HD 20"','4K 27"','Touchscreen'],
    'Jaringan'  :['Switch 8 Port','Switch 16 Port','Switch 24 Port','Router','Access Point','Modem','Patch Panel','Media Converter'],
    'Peripheral':['Keyboard Mechanical','Keyboard Membrane','Mouse Wired','Mouse Wireless','Headset','Webcam','USB Hub','Flashdisk'],
    'Printer'   :['Laser B/W','Laser Color','Inkjet','Dot Matrix','Thermal'],
    'Listrik'   :['UPS 650VA','UPS 1200VA','UPS 2200VA','Stop Kontak','Stabilizer','Kabel Power'],
    'Scanner'   :['Flatbed','Sheet-fed','Barcode','Fingerprint'],
    'Furnitur'  :['Meja Komputer','Kursi Operator','Lemari','Rak Server','Papan Tulis'],
    'Lainnya'   :['Lainnya'],
}

JENIS_ASET = ['Aset Tetap', 'Aset Bergerak']

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu.','warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def generate_kode_barang(kategori, tipe_prefix='XXX'):
    prefix = KATEGORI_PREFIX.get(kategori,'LNY')
    tahun  = datetime.now().strftime('%Y')
    cur    = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS n FROM barang WHERE kode_barang LIKE %s",
                (f'{prefix}-{tipe_prefix}-{tahun}-%',))
    n = cur.fetchone()['n']; cur.close()
    return f"{prefix}-{tipe_prefix}-{tahun}-{n+1:04d}"

def generate_kode_pinjam():
    today = datetime.now().strftime('%Y%m%d')
    cur   = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS n FROM peminjaman WHERE kode_pinjam LIKE %s",
                (f'PJM-{today}-%',))
    n = cur.fetchone()['n']; cur.close()
    return f"PJM-{today}-{n+1:04d}"

def buat_qr_code(kode_barang):
    qr_dir = os.path.join(app.static_folder,'qr')
    os.makedirs(qr_dir, exist_ok=True)
    data = f"http://[IP_KOMPUTER]:5000/barang/detail/{kode_barang}"
    qr   = qrcode.QRCode(version=1,
                          error_correction=qrcode.constants.ERROR_CORRECT_H,
                          box_size=10, border=4)
    qr.add_data(data); qr.make(fit=True)
    img  = qr.make_image(fill_color="#1a1a2e", back_color="white")
    fn   = f"qr_{kode_barang}.png"
    img.save(os.path.join(qr_dir, fn))
    return f"qr/{fn}"

def build_filter(search, kategori, jenis, kondisi, sort, order):
    clauses, params = [], []
    if search:
        clauses.append("(nama_barang LIKE %s OR kode_barang LIKE %s OR tipe LIKE %s)")
        like = f"%{search}%"; params += [like,like,like]
    if kategori: clauses.append("kategori=%s"); params.append(kategori)
    if jenis:    clauses.append("jenis_aset=%s"); params.append(jenis)
    if kondisi:  clauses.append("kondisi=%s"); params.append(kondisi)
    where = ("WHERE "+" AND ".join(clauses)) if clauses else ""
    safe_sort  = sort  if sort  in {'nama_barang','kode_barang','kategori','kondisi','jenis_aset','created_at'} else 'created_at'
    safe_order = 'ASC' if order=='asc' else 'DESC'
    return where, params, f"ORDER BY {safe_sort} {safe_order}"

# ============================================================
# AUTH
# ============================================================
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        u = request.form.get('username','').strip()
        p = request.form.get('password','').strip()
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s",(u,))
        user = cur.fetchone(); cur.close()
        if user and bcrypt.checkpw(p.encode(), user['password'].encode()):
            session.update({'user_id':user['id'],'username':user['username'],
                            'nama_lengkap':user['nama_lengkap'],'role':user['role']})
            flash(f'Selamat datang, {user["nama_lengkap"]}!','success')
            return redirect(url_for('dashboard'))
        flash('Username atau password salah.','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.','info')
    return redirect(url_for('login'))

# ============================================================
# DASHBOARD
# ============================================================
@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS n FROM barang"); total = cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM barang WHERE kondisi='Baik'"); baik=cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM barang WHERE kondisi='Rusak Ringan'"); r_ringan=cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM barang WHERE kondisi='Rusak Berat'"); r_berat=cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM peminjaman WHERE status='Dipinjam'"); dipinjam=cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM peminjaman WHERE status='Terlambat'"); terlambat=cur.fetchone()['n']
    cur.execute("SELECT * FROM barang ORDER BY created_at DESC LIMIT 5"); barang_terbaru=cur.fetchall()
    cur.execute("""SELECT p.*,b.nama_barang FROM peminjaman p
                   LEFT JOIN barang b ON p.barang_id=b.id
                   WHERE p.status='Dipinjam' ORDER BY p.tgl_kembali_rencana ASC LIMIT 5""")
    pinjam_aktif = cur.fetchall()
    cur.execute("SELECT kategori,COUNT(*) AS n FROM barang GROUP BY kategori ORDER BY n DESC")
    chart_kat = cur.fetchall()
    cur.execute("SELECT kondisi,COUNT(*) AS n FROM barang GROUP BY kondisi")
    chart_kondisi = cur.fetchall()
    cur.execute("SELECT jenis_aset,COUNT(*) AS n FROM barang GROUP BY jenis_aset")
    chart_aset = cur.fetchall()
    cur.close()

    # Auto-update status terlambat
    _update_terlambat()

    return render_template('dashboard.html',
        stats=dict(total=total,baik=baik,rusak_ringan=r_ringan,rusak_berat=r_berat,
                   dipinjam=dipinjam,terlambat=terlambat),
        barang_terbaru=barang_terbaru,
        pinjam_aktif=pinjam_aktif,
        chart_kat=json.dumps([dict(r) for r in chart_kat]),
        chart_kondisi=json.dumps([dict(r) for r in chart_kondisi]),
        chart_aset=json.dumps([dict(r) for r in chart_aset]),
    )

def _update_terlambat():
    """Auto-update status jadi Terlambat jika sudah lewat waktu rencana kembali."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("""UPDATE peminjaman SET status='Terlambat'
                       WHERE status='Dipinjam'
                       AND tgl_kembali_rencana < NOW()""")
        mysql.connection.commit(); cur.close()
    except: pass

# ============================================================
# BARANG — LIST
# ============================================================
@app.route('/barang')
@login_required
def barang_list():
    search   = request.args.get('search','').strip()
    f_kat    = request.args.get('kategori','').strip()
    f_jenis  = request.args.get('jenis_aset','').strip()
    f_kondisi= request.args.get('kondisi','').strip()
    sort     = request.args.get('sort','created_at')
    order    = request.args.get('order','desc')
    page     = int(request.args.get('page',1))
    per_page = 10; offset=(page-1)*per_page

    where,params,order_sql = build_filter(search,f_kat,f_jenis,f_kondisi,sort,order)
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM barang {where} {order_sql} LIMIT %s OFFSET %s",
                params+[per_page,offset])
    rows = cur.fetchall()
    cur.execute(f"SELECT COUNT(*) AS n FROM barang {where}", params)
    total = cur.fetchone()['n']
    cur.close()

    return render_template('barang.html',
        barang_list=rows, search=search, f_kat=f_kat,
        f_jenis=f_jenis, f_kondisi=f_kondisi,
        sort=sort, order=order, next_order='asc' if order=='desc' else 'desc',
        page=page, total_pages=max(1,(total+per_page-1)//per_page),
        total_rows=total,
        kategori_list=list(KATEGORI_PREFIX.keys()),
        jenis_aset_list=JENIS_ASET,
    )

# ============================================================
# BARANG — TAMBAH
# ============================================================
@app.route('/barang/tambah', methods=['GET','POST'])
@login_required
def barang_tambah():
    if request.method=='POST':
        kategori   = request.form.get('kategori','Lainnya')
        tipe_input = request.form.get('tipe','').strip()
        # Ambil 3 huruf pertama dari tipe sebagai prefix kode
        tipe_pfx   = ''.join(c for c in tipe_input.upper()[:6] if c.isalpha())[:3] or 'XXX'
        kode       = generate_kode_barang(kategori, tipe_pfx)
        data = (kode,
                request.form['nama_barang'].strip(),
                kategori, tipe_input,
                request.form.get('jenis_aset','Aset Tetap'),
                request.form.get('spesifikasi','').strip(),
                request.form.get('kondisi','Baik'),
                int(request.form.get('jumlah',1)),
                request.form.get('tanggal_pengadaan') or None,
                buat_qr_code(kode),
                request.form.get('keterangan','').strip())
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO barang
            (kode_barang,nama_barang,kategori,tipe,jenis_aset,
             spesifikasi,kondisi,jumlah,tanggal_pengadaan,qr_path,keterangan)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", data)
        mysql.connection.commit(); cur.close()
        flash(f'Barang berhasil ditambahkan dengan kode {kode}.','success')
        return redirect(url_for('barang_list'))
    return render_template('barang_form.html', mode='tambah', barang=None,
                           kategori_list=list(KATEGORI_PREFIX.keys()),
                           jenis_aset_list=JENIS_ASET,
                           tipe_per_kategori=json.dumps(TIPE_PER_KATEGORI))

# ============================================================
# BARANG — EDIT
# ============================================================
@app.route('/barang/edit/<int:id>', methods=['GET','POST'])
@login_required
def barang_edit(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM barang WHERE id=%s",(id,))
    barang = cur.fetchone()
    if not barang:
        flash('Barang tidak ditemukan.','danger')
        return redirect(url_for('barang_list'))
    if request.method=='POST':
        cur.execute("""UPDATE barang SET
            nama_barang=%s,kategori=%s,tipe=%s,jenis_aset=%s,
            spesifikasi=%s,kondisi=%s,jumlah=%s,
            tanggal_pengadaan=%s,keterangan=%s WHERE id=%s""",
            (request.form['nama_barang'].strip(),
             request.form.get('kategori'),
             request.form.get('tipe','').strip(),
             request.form.get('jenis_aset','Aset Tetap'),
             request.form.get('spesifikasi','').strip(),
             request.form.get('kondisi','Baik'),
             int(request.form.get('jumlah',1)),
             request.form.get('tanggal_pengadaan') or None,
             request.form.get('keterangan','').strip(),
             id))
        mysql.connection.commit(); cur.close()
        flash('Barang berhasil diperbarui.','success')
        return redirect(url_for('barang_list'))
    cur.close()
    return render_template('barang_form.html', mode='edit', barang=barang,
                           kategori_list=list(KATEGORI_PREFIX.keys()),
                           jenis_aset_list=JENIS_ASET,
                           tipe_per_kategori=json.dumps(TIPE_PER_KATEGORI))

# ============================================================
# BARANG — HAPUS
# ============================================================
@app.route('/barang/hapus/<int:id>', methods=['POST'])
@login_required
def barang_hapus(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT nama_barang,qr_path FROM barang WHERE id=%s",(id,))
    b = cur.fetchone()
    if b:
        if b['qr_path']:
            f = os.path.join(app.static_folder, b['qr_path'])
            if os.path.exists(f): os.remove(f)
        cur.execute("DELETE FROM barang WHERE id=%s",(id,))
        mysql.connection.commit()
        flash(f'Barang "{b["nama_barang"]}" berhasil dihapus.','success')
    cur.close()
    return redirect(url_for('barang_list'))

# ============================================================
# BARANG — DETAIL (target QR scan)
# ============================================================
@app.route('/barang/detail/<kode>')
def barang_detail(kode):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM barang WHERE kode_barang=%s",(kode,))
    barang = cur.fetchone()
    if not barang: return render_template('404.html'),404
    cur.execute("""INSERT INTO riwayat_scan
        (barang_id,kode_barang,nama_barang,ip_scanner,user_agent)
        VALUES(%s,%s,%s,%s,%s)""",
        (barang['id'],kode,barang['nama_barang'],
         request.remote_addr,request.user_agent.string))
    mysql.connection.commit()
    cur.execute("SELECT * FROM riwayat_scan WHERE barang_id=%s ORDER BY scanned_at DESC LIMIT 10",
                (barang['id'],))
    riwayat = cur.fetchall(); cur.close()
    return render_template('detail.html', barang=barang, riwayat=riwayat)

# ============================================================
# CETAK LABEL QR
# ============================================================
@app.route('/barang/cetak-label')
@login_required
def cetak_label():
    ids_raw = request.args.get('ids','')
    cur     = mysql.connection.cursor()
    if ids_raw:
        ids = [int(i) for i in ids_raw.split(',') if i.strip().isdigit()]
        fmt = ','.join(['%s']*len(ids))
        cur.execute(f"SELECT * FROM barang WHERE id IN ({fmt}) AND qr_path IS NOT NULL", ids)
    else:
        cur.execute("SELECT * FROM barang WHERE qr_path IS NOT NULL ORDER BY kategori,nama_barang")
    rows = cur.fetchall(); cur.close()
    return render_template('cetak_label.html', barang_list=rows)

# ============================================================
# SCANNER QR
# ============================================================
@app.route('/scanner')
@login_required
def scanner():
    return render_template('scanner.html')

@app.route('/api/barang/<kode>')
def api_barang(kode):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM barang WHERE kode_barang=%s",(kode,))
    b = cur.fetchone(); cur.close()
    if b:
        for k in ('tanggal_pengadaan','created_at','updated_at'):
            if b.get(k): b[k]=str(b[k])
        return jsonify({'status':'found','data':b})
    return jsonify({'status':'not_found'}),404

# ============================================================
# PEMINJAMAN — LIST
# ============================================================
@app.route('/peminjaman')
@login_required
def peminjaman_list():
    _update_terlambat()
    f_status = request.args.get('status','').strip()
    search   = request.args.get('search','').strip()
    page     = int(request.args.get('page',1))
    per_page = 10; offset=(page-1)*per_page

    clauses,params=[],[]
    if search:
        clauses.append("(p.nama_peminjam LIKE %s OR p.kode_pinjam LIKE %s OR b.nama_barang LIKE %s)")
        like=f"%{search}%"; params+=[like,like,like]
    if f_status:
        clauses.append("p.status=%s"); params.append(f_status)
    where=("WHERE "+" AND ".join(clauses)) if clauses else ""

    cur = mysql.connection.cursor()
    cur.execute(f"""SELECT p.*,b.nama_barang,b.kategori,b.tipe,b.kode_barang AS kode_brg
                    FROM peminjaman p LEFT JOIN barang b ON p.barang_id=b.id
                    {where} ORDER BY p.created_at DESC LIMIT %s OFFSET %s""",
                params+[per_page,offset])
    rows = cur.fetchall()
    cur.execute(f"""SELECT COUNT(*) AS n FROM peminjaman p
                    LEFT JOIN barang b ON p.barang_id=b.id {where}""", params)
    total = cur.fetchone()['n']

    # Stats
    cur.execute("SELECT COUNT(*) AS n FROM peminjaman WHERE status='Dipinjam'");   s_dipinjam=cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM peminjaman WHERE status='Dikembalikan'");s_kembali=cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM peminjaman WHERE status='Terlambat'");  s_terlambat=cur.fetchone()['n']
    cur.close()

    return render_template('peminjaman.html',
        pinjam_list=rows, search=search, f_status=f_status,
        page=page, total_pages=max(1,(total+per_page-1)//per_page),
        total_rows=total,
        stats=dict(dipinjam=s_dipinjam,kembali=s_kembali,terlambat=s_terlambat),
    )

# ============================================================
# PEMINJAMAN — TAMBAH
# ============================================================
@app.route('/peminjaman/tambah', methods=['GET','POST'])
@login_required
def peminjaman_tambah():
    cur = mysql.connection.cursor()
    # Hanya barang kondisi Baik yang bisa dipinjam
    cur.execute("SELECT id,kode_barang,nama_barang,kategori,tipe,jumlah FROM barang WHERE kondisi='Baik' ORDER BY nama_barang")
    barang_tersedia = cur.fetchall()

    if request.method=='POST':
        barang_id  = int(request.form['barang_id'])
        jml_pinjam = int(request.form.get('jumlah_pinjam',1))

        # Cek stok
        cur.execute("SELECT kode_barang,nama_barang,jumlah FROM barang WHERE id=%s",(barang_id,))
        b = cur.fetchone()

        # Cek sudah berapa yang sedang dipinjam
        cur.execute("SELECT COALESCE(SUM(jumlah_pinjam),0) AS n FROM peminjaman WHERE barang_id=%s AND status IN ('Dipinjam','Terlambat')",(barang_id,))
        sdh_pinjam = cur.fetchone()['n']
        sisa = b['jumlah'] - sdh_pinjam

        if jml_pinjam > sisa:
            flash(f'Stok tidak cukup. Tersedia: {sisa} unit.','danger')
            cur.close()
            return render_template('peminjaman_form.html',
                                   barang_tersedia=barang_tersedia, mode='tambah', data=None)

        kode_pinjam = generate_kode_pinjam()

        # Gabungkan tanggal + jam menjadi DATETIME string
        tgl_pinjam_dt          = f"{request.form['tgl_pinjam']} {request.form['jam_pinjam']}:00"
        tgl_kembali_rencana_dt = f"{request.form['tgl_kembali_rencana']} {request.form['jam_kembali_rencana']}:00"

        cur.execute("""INSERT INTO peminjaman
            (kode_pinjam,barang_id,kode_barang,nama_peminjam,kelas_jabatan,
             no_hp,keperluan,jumlah_pinjam,tgl_pinjam,tgl_kembali_rencana,status)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Dipinjam')""",
            (kode_pinjam, barang_id, b['kode_barang'],
             request.form['nama_peminjam'].strip(),
             request.form.get('kelas_jabatan','').strip(),
             request.form.get('no_hp','').strip(),
             request.form.get('keperluan','').strip(),
             jml_pinjam,
             tgl_pinjam_dt,
             tgl_kembali_rencana_dt))
        mysql.connection.commit(); cur.close()
        flash(f'Peminjaman {kode_pinjam} berhasil dicatat.','success')
        return redirect(url_for('peminjaman_list'))

    cur.close()
    return render_template('peminjaman_form.html',
                           barang_tersedia=barang_tersedia, mode='tambah', data=None,
                           today=datetime.now().strftime('%Y-%m-%d'))

# ============================================================
# PEMINJAMAN — KEMBALIKAN
# ============================================================
@app.route('/peminjaman/kembalikan/<int:id>', methods=['GET','POST'])
@login_required
def peminjaman_kembalikan(id):
    cur = mysql.connection.cursor()
    cur.execute("""SELECT p.*,b.nama_barang,b.tipe FROM peminjaman p
                   LEFT JOIN barang b ON p.barang_id=b.id WHERE p.id=%s""",(id,))
    pinjam = cur.fetchone()
    if not pinjam or pinjam['status']=='Dikembalikan':
        flash('Data tidak valid atau sudah dikembalikan.','warning')
        cur.close()
        return redirect(url_for('peminjaman_list'))

    if request.method=='POST':
        # Gabungkan tanggal + jam kembali aktual
        tgl_aktual_dt   = f"{request.form['tgl_kembali_aktual']} {request.form['jam_kembali_aktual']}:00"
        kondisi_kembali = request.form.get('kondisi_kembali','Baik')
        catatan         = request.form.get('catatan_admin','').strip()

        cur.execute("""UPDATE peminjaman SET
            status='Dikembalikan', tgl_kembali_aktual=%s,
            kondisi_kembali=%s, catatan_admin=%s
            WHERE id=%s""",
            (tgl_aktual_dt, kondisi_kembali, catatan, id))

        # Update kondisi barang jika kondisi kembali lebih buruk
        cur.execute("SELECT kondisi FROM barang WHERE id=%s",(pinjam['barang_id'],))
        kondisi_skrg = cur.fetchone()['kondisi']
        urutan = {'Baik':0,'Rusak Ringan':1,'Rusak Berat':2}
        if urutan.get(kondisi_kembali,0) > urutan.get(kondisi_skrg,0):
            cur.execute("UPDATE barang SET kondisi=%s WHERE id=%s",
                        (kondisi_kembali, pinjam['barang_id']))

        mysql.connection.commit(); cur.close()
        flash(f'Barang "{pinjam["nama_barang"]}" berhasil dicatat kembali.','success')
        return redirect(url_for('peminjaman_list'))

    cur.close()
    today_now = datetime.now()
    return render_template('peminjaman_kembalikan.html', pinjam=pinjam,
                           today_date=today_now.strftime('%Y-%m-%d'),
                           today_time=today_now.strftime('%H:%M'))

# ============================================================
# PEMINJAMAN — DETAIL
# ============================================================
@app.route('/peminjaman/detail/<int:id>')
@login_required
def peminjaman_detail(id):
    cur = mysql.connection.cursor()
    cur.execute("""SELECT p.*,b.nama_barang,b.kategori,b.tipe,b.kode_barang AS kode_brg,b.qr_path
                   FROM peminjaman p LEFT JOIN barang b ON p.barang_id=b.id
                   WHERE p.id=%s""",(id,))
    pinjam = cur.fetchone(); cur.close()
    if not pinjam:
        flash('Data peminjaman tidak ditemukan.','danger')
        return redirect(url_for('peminjaman_list'))
    today = date.today()
    return render_template('peminjaman_detail.html', pinjam=pinjam, today=today)

# ============================================================
# PEMINJAMAN — HAPUS
# ============================================================
@app.route('/peminjaman/hapus/<int:id>', methods=['POST'])
@login_required
def peminjaman_hapus(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM peminjaman WHERE id=%s",(id,))
    mysql.connection.commit(); cur.close()
    flash('Data peminjaman berhasil dihapus.','success')
    return redirect(url_for('peminjaman_list'))

# ============================================================
# API: tipe produk per kategori (untuk form dinamis)
# ============================================================
@app.route('/api/tipe/<kategori>')
def api_tipe(kategori):
    return jsonify(TIPE_PER_KATEGORI.get(kategori,['Lainnya']))

# ============================================================
# EXPORT EXCEL
# ============================================================
@app.route('/export/excel')
@login_required
def export_excel():
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    search=request.args.get('search',''); f_kat=request.args.get('kategori','')
    f_jenis=request.args.get('jenis_aset',''); f_kondisi=request.args.get('kondisi','')
    where,params,order_sql = build_filter(search,f_kat,f_jenis,f_kondisi,'kategori','asc')
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM barang {where} {order_sql}", params)
    rows = cur.fetchall(); cur.close()

    wb = openpyxl.Workbook(); ws = wb.active
    ws.title = "Inventaris Lab TJKT"
    hfill = PatternFill("solid",fgColor="1e3a8a")
    hfont = Font(name='Calibri',bold=True,color="FFFFFF",size=11)
    center = Alignment(horizontal='center',vertical='center',wrap_text=True)
    left   = Alignment(horizontal='left',  vertical='center',wrap_text=True)
    thin   = Side(style='thin',color='CBD5E1')
    bdr    = Border(left=thin,right=thin,top=thin,bottom=thin)

    ws.merge_cells('A1:K1'); ws['A1']='LAPORAN INVENTARIS LAB TJKT — SMKN 1 Cikarang Selatan'
    ws['A1'].font=Font(name='Calibri',bold=True,size=14,color="1e3a8a"); ws['A1'].alignment=center
    ws.merge_cells('A2:K2'); ws['A2']=f'Dicetak: {datetime.now().strftime("%d %B %Y %H:%M")}'
    ws['A2'].font=Font(name='Calibri',size=10,italic=True,color="94a3b8"); ws['A2'].alignment=center
    ws.row_dimensions[1].height=28; ws.row_dimensions[2].height=18

    headers=['No','Kode Barang','Nama Barang','Kategori','Tipe Produk','Jenis Aset','Spesifikasi','Kondisi','Jml','Tgl Pengadaan','Keterangan']
    widths  =[5, 20, 30, 14, 18, 14, 35, 14, 6, 16, 28]
    ws.append([]); ws.append(headers)
    for ci,(h,w) in enumerate(zip(headers,widths),1):
        cell=ws.cell(row=4,column=ci)
        cell.fill=hfill; cell.font=hfont; cell.alignment=center; cell.border=bdr
        ws.column_dimensions[cell.column_letter].width=w
    ws.row_dimensions[4].height=22

    kfill={'Baik':'D1FAE5','Rusak Ringan':'FEF3C7','Rusak Berat':'FEE2E2'}
    for i,b in enumerate(rows,1):
        tgl=b['tanggal_pengadaan'].strftime('%d/%m/%Y') if b.get('tanggal_pengadaan') else '-'
        ws.append([i,b['kode_barang'],b['nama_barang'],b['kategori'],
                   b['tipe'] or '-', b['jenis_aset'] or '-',
                   b['spesifikasi'] or '-', b['kondisi'],
                   b['jumlah'], tgl, b['keterangan'] or '-'])
        rn=4+i; ws.row_dimensions[rn].height=18
        for ci in range(1,12):
            cell=ws.cell(row=rn,column=ci); cell.border=bdr
            cell.alignment=center if ci in (1,4,5,6,8,9,10) else left
            if ci==8:
                cell.fill=PatternFill("solid",fgColor=kfill.get(b['kondisi'],'FFFFFF'))
                cell.font=Font(name='Calibri',bold=True,size=10)
    ws.freeze_panes='A5'
    buf=io.BytesIO(); wb.save(buf); buf.seek(0)
    fname=f"Inventaris_TJKT_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(buf,as_attachment=True,download_name=fname,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ============================================================
# EXPORT PDF
# ============================================================
@app.route('/export/pdf')
@login_required
def export_pdf():
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    search=request.args.get('search',''); f_kat=request.args.get('kategori','')
    f_jenis=request.args.get('jenis_aset',''); f_kondisi=request.args.get('kondisi','')
    where,params,order_sql = build_filter(search,f_kat,f_jenis,f_kondisi,'kategori','asc')
    cur=mysql.connection.cursor()
    cur.execute(f"SELECT * FROM barang {where} {order_sql}",params)
    rows=cur.fetchall(); cur.close()

    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=landscape(A4),
                          leftMargin=1.5*cm,rightMargin=1.5*cm,
                          topMargin=2*cm,bottomMargin=1.5*cm)
    styles=getSampleStyleSheet(); elems=[]
    ts=ParagraphStyle('t',parent=styles['Title'],fontSize=14,
                      textColor=colors.HexColor('#1e3a8a'),spaceAfter=4)
    ss=ParagraphStyle('s',parent=styles['Normal'],fontSize=10,
                      textColor=colors.HexColor('#475569'),spaceAfter=2,alignment=1)
    ds=ParagraphStyle('d',parent=styles['Normal'],fontSize=8,
                      textColor=colors.HexColor('#94a3b8'),spaceAfter=12,alignment=1)
    elems+=[Paragraph('LAPORAN INVENTARIS LAB TJKT',ts),
            Paragraph('SMKN 1 Cikarang Selatan, Bekasi',ss),
            Paragraph(f'Dicetak: {datetime.now().strftime("%d %B %Y %H:%M")}',ds),
            Spacer(1,0.3*cm)]

    header=['No','Kode Barang','Nama Barang','Kategori','Tipe','Jenis Aset','Kondisi','Jml','Tgl Pengadaan']
    data=[header]
    for i,b in enumerate(rows,1):
        tgl=b['tanggal_pengadaan'].strftime('%d/%m/%Y') if b.get('tanggal_pengadaan') else '-'
        data.append([str(i),b['kode_barang'],b['nama_barang'],b['kategori'],
                     b['tipe'] or '-', b['jenis_aset'] or '-',
                     b['kondisi'],str(b['jumlah']),tgl])

    cw=[1*cm,3.5*cm,5.5*cm,3*cm,3.5*cm,3*cm,2.8*cm,1.2*cm,2.8*cm]
    tbl=Table(data,colWidths=cw,repeatRows=1)
    cfill={'Baik':colors.HexColor('#D1FAE5'),'Rusak Ringan':colors.HexColor('#FEF3C7'),
           'Rusak Berat':colors.HexColor('#FEE2E2')}
    ts_style=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1e3a8a')),
              ('TEXTCOLOR',(0,0),(-1,0),colors.white),
              ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
              ('FONTSIZE',(0,0),(-1,0),9),
              ('ALIGN',(0,0),(-1,-1),'CENTER'),
              ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
              ('FONTSIZE',(0,1),(-1,-1),8),
              ('FONTNAME',(0,1),(-1,-1),'Helvetica'),
              ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F8FAFF')]),
              ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#CBD5E1')),
              ('TOPPADDING',(0,0),(-1,-1),5),
              ('BOTTOMPADDING',(0,0),(-1,-1),5),
              ('ALIGN',(2,1),(2,-1),'LEFT')]
    for ri,b in enumerate(rows,1):
        fc=cfill.get(b['kondisi'])
        if fc: ts_style.append(('BACKGROUND',(6,ri),(6,ri),fc))
    tbl.setStyle(TableStyle(ts_style)); elems.append(tbl)
    doc.build(elems); buf.seek(0)
    fname=f"Inventaris_TJKT_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return send_file(buf,as_attachment=True,download_name=fname,mimetype='application/pdf')

# ============================================================
# RIWAYAT SCAN
# ============================================================
@app.route('/riwayat')
@login_required
def riwayat_scan():
    cur=mysql.connection.cursor()
    cur.execute("""SELECT r.*,b.nama_barang,b.kategori FROM riwayat_scan r
                   LEFT JOIN barang b ON r.barang_id=b.id
                   ORDER BY r.scanned_at DESC LIMIT 100""")
    riwayat=cur.fetchall(); cur.close()
    return render_template('riwayat.html',riwayat=riwayat)

# ============================================================
# ERROR HANDLER & MAIN
# ============================================================
@app.errorhandler(404)
def not_found(e): return render_template('404.html'),404

if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
