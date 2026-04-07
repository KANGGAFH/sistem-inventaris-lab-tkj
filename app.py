# ============================================================
# app.py - Lab Inventory Management System v2.0
# Backend: Python Flask + MySQL (XAMPP)
# Sekolah : SMKN 1 Cikarang Selatan, Bekasi - Lab TJKT
# Fitur   : CRUD, QR Code, Export Excel/PDF, Cetak Label QR,
#           Filter & Sorting, Tipe Barang, Kode Otomatis
# ============================================================

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, send_file, make_response)
from flask_mysqldb import MySQL
import bcrypt, qrcode, os, json, io
from datetime import datetime, date
from functools import wraps

# ─────────────────────────────────────────────
# INISIALISASI APLIKASI
# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'labkomputer_secret_kp_2024'


# ─────────────────────────────────────────────
# CONTEXT PROCESSOR: inject now_year ke semua template
# ─────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return {'now_year': datetime.now().strftime('%Y')}

# ── Coba import library export (opsional, tidak wajib ada) ──
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    EXCEL_OK = True
except ImportError:
    EXCEL_OK = False

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    PDF_OK = True
except ImportError:
    PDF_OK = False

# ─────────────────────────────────────────────
# INISIALISASI APLIKASI
# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'labkomputer_secret_kp_2024'

app.config['MYSQL_HOST']        = 'localhost'
app.config['MYSQL_USER']        = 'root'
app.config['MYSQL_PASSWORD']    = ''
app.config['MYSQL_DB']          = 'inventory_tkj'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ============================================================
# REFERENSI PREFIX KODE BARANG
# Format: [PREFIX_KATEGORI]-[PREFIX_TIPE]-[TAHUN]-[NOURUT]
# ============================================================
KATEGORI_PREFIX = {
    'Komputer'  : 'KOM',
    'Monitor'   : 'MON',
    'Jaringan'  : 'NET',
    'Peripheral': 'PER',
    'Printer'   : 'PRN',
    'Scanner'   : 'SCN',
    'Listrik'   : 'LST',
    'Lainnya'   : 'LAN',
}

TIPE_PREFIX = {
    'Desktop'       : 'DES',
    'Laptop'        : 'LAP',
    'LED'           : 'LED',
    'Switch'        : 'SWT',
    'Router'        : 'ROU',
    'Access Point'  : 'APT',
    'Keyboard'      : 'KEY',
    'Mouse'         : 'MOU',
    'Laser'         : 'LSR',
    'Inkjet'        : 'INK',
    'UPS'           : 'UPS',
    'Proyektor'     : 'PRY',
    'Server'        : 'SRV',
    'Kabel'         : 'KBL',
    'Lainnya'       : 'LAN',
}

# Mapping kategori → daftar tipe yang tersedia (untuk dropdown dinamis)
KATEGORI_TIPE_MAP = {
    'Komputer'  : ['Desktop','Laptop','Server'],
    'Monitor'   : ['LED','Proyektor'],
    'Jaringan'  : ['Switch','Router','Access Point','Kabel'],
    'Peripheral': ['Keyboard','Mouse','Lainnya'],
    'Printer'   : ['Laser','Inkjet'],
    'Scanner'   : ['Lainnya'],
    'Listrik'   : ['UPS','Lainnya'],
    'Lainnya'   : ['Lainnya'],
}

# ─────────────────────────────────────────────
# HELPER: Generate Kode Barang
# ─────────────────────────────────────────────
def generate_kode_barang(kategori, tipe_barang):
    kat_pfx  = KATEGORI_PREFIX.get(kategori, 'LAN')
    tipe_pfx = TIPE_PREFIX.get(tipe_barang, 'LAN')
    tahun    = datetime.now().strftime('%Y')
    prefix   = f"{kat_pfx}-{tipe_pfx}-{tahun}-"

    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT COUNT(*) AS total FROM barang WHERE kode_barang LIKE %s",
        (f'{prefix}%',)
    )
    row = cursor.fetchone()
    cursor.close()
    nomor = (row['total'] if row else 0) + 1
    return f"{prefix}{nomor:04d}"

# ─────────────────────────────────────────────
# HELPER: Buat QR Code
# ─────────────────────────────────────────────
def buat_qr_code(kode_barang):
    qr_dir = os.path.join(app.static_folder, 'qr')
    os.makedirs(qr_dir, exist_ok=True)
    qr_data = f"http://[IP_KOMPUTER]:5000/barang/detail/{kode_barang}"
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a2e", back_color="white")
    filename = f"qr_{kode_barang}.png"
    img.save(os.path.join(qr_dir, filename))
    return f"qr/{filename}"

# ─────────────────────────────────────────────
# DECORATOR: Login Required
# ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
# HELPER: Build filter query
# ─────────────────────────────────────────────
def build_filter_query(search, filter_kondisi, filter_kategori, filter_tipe, sort_col, sort_dir):
    conditions = []
    params     = []

    if search:
        like = f"%{search}%"
        conditions.append("""(nama_barang LIKE %s OR kode_barang LIKE %s
                               OR merk LIKE %s OR tipe_barang LIKE %s)""")
        params += [like, like, like, like]

    if filter_kondisi:
        conditions.append("kondisi = %s")
        params.append(filter_kondisi)

    if filter_kategori:
        conditions.append("kategori = %s")
        params.append(filter_kategori)

    if filter_tipe:
        conditions.append("tipe_barang = %s")
        params.append(filter_tipe)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    allowed_cols = ['kode_barang','nama_barang','kategori','tipe_barang',
                    'kondisi','jumlah','tanggal_pengadaan','created_at']
    col = sort_col if sort_col in allowed_cols else 'created_at'
    direction = 'ASC' if sort_dir == 'asc' else 'DESC'
    order = f"ORDER BY {col} {direction}"

    return where, order, params

# ============================================================
# ROUTE: AUTH
# ============================================================

@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        if user and bcrypt.checkpw(password.encode(), user['password'].encode()):
            session['user_id']      = user['id']
            session['username']     = user['username']
            session['nama_lengkap'] = user['nama_lengkap']
            session['role']         = user['role']
            flash(f'Selamat datang, {user["nama_lengkap"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Username atau password salah.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

# ============================================================
# ROUTE: DASHBOARD
# ============================================================

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM barang")
    total = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS t FROM barang WHERE kondisi='Baik'")
    baik = cursor.fetchone()['t']
    cursor.execute("SELECT COUNT(*) AS t FROM barang WHERE kondisi='Rusak Ringan'")
    rusak_ringan = cursor.fetchone()['t']
    cursor.execute("SELECT COUNT(*) AS t FROM barang WHERE kondisi='Rusak Berat'")
    rusak_berat = cursor.fetchone()['t']
    cursor.execute("SELECT * FROM barang ORDER BY created_at DESC LIMIT 5")
    barang_terbaru = cursor.fetchall()
    cursor.execute("""SELECT r.*, b.nama_barang FROM riwayat_scan r
                      LEFT JOIN barang b ON r.barang_id=b.id
                      ORDER BY r.scanned_at DESC LIMIT 5""")
    scan_terbaru = cursor.fetchall()
    cursor.execute("SELECT kategori, COUNT(*) AS jumlah FROM barang GROUP BY kategori ORDER BY jumlah DESC")
    chart_kategori = cursor.fetchall()
    cursor.execute("SELECT kondisi, COUNT(*) AS jumlah FROM barang GROUP BY kondisi")
    chart_kondisi = cursor.fetchall()
    cursor.close()
    return render_template('dashboard.html',
        stats={'total':total,'baik':baik,'rusak_ringan':rusak_ringan,'rusak_berat':rusak_berat},
        barang_terbaru=barang_terbaru, scan_terbaru=scan_terbaru,
        chart_kategori=json.dumps([dict(r) for r in chart_kategori]),
        chart_kondisi=json.dumps([dict(r) for r in chart_kondisi]),
    )

# ============================================================
# ROUTE: MANAJEMEN BARANG
# ============================================================

@app.route('/barang')
@login_required
def barang_list():
    search          = request.args.get('search','').strip()
    filter_kondisi  = request.args.get('kondisi','').strip()
    filter_kategori = request.args.get('kategori','').strip()
    filter_tipe     = request.args.get('tipe','').strip()
    sort_col        = request.args.get('sort','created_at').strip()
    sort_dir        = request.args.get('dir','desc').strip()
    page            = max(int(request.args.get('page', 1)), 1)
    per_page        = 10
    offset          = (page - 1) * per_page

    where, order, params = build_filter_query(
        search, filter_kondisi, filter_kategori, filter_tipe, sort_col, sort_dir)

    cursor = mysql.connection.cursor()
    cursor.execute(f"SELECT * FROM barang {where} {order} LIMIT %s OFFSET %s",
                   params + [per_page, offset])
    barang_data = cursor.fetchall()
    cursor.execute(f"SELECT COUNT(*) AS total FROM barang {where}", params)
    total_rows  = cursor.fetchone()['total']

    # Untuk dropdown filter
    cursor.execute("SELECT DISTINCT kategori FROM barang ORDER BY kategori")
    all_kategori = [r['kategori'] for r in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT tipe_barang FROM barang ORDER BY tipe_barang")
    all_tipe = [r['tipe_barang'] for r in cursor.fetchall()]
    cursor.close()

    total_pages = max((total_rows + per_page - 1) // per_page, 1)

    return render_template('barang.html',
        barang_list=barang_data, search=search,
        filter_kondisi=filter_kondisi, filter_kategori=filter_kategori,
        filter_tipe=filter_tipe, sort_col=sort_col, sort_dir=sort_dir,
        page=page, total_pages=total_pages, total_rows=total_rows,
        all_kategori=all_kategori, all_tipe=all_tipe,
    )


@app.route('/barang/tambah', methods=['GET','POST'])
@login_required
def barang_tambah():
    if request.method == 'POST':
        nama_barang       = request.form['nama_barang'].strip()
        kategori          = request.form.get('kategori','Komputer')
        tipe_barang       = request.form.get('tipe_barang','Desktop')
        merk              = request.form.get('merk','').strip()
        spesifikasi       = request.form.get('spesifikasi','').strip()
        kondisi           = request.form.get('kondisi','Baik')
        jumlah            = int(request.form.get('jumlah',1))
        tanggal_pengadaan = request.form.get('tanggal_pengadaan') or None
        keterangan        = request.form.get('keterangan','').strip()

        kode_barang = generate_kode_barang(kategori, tipe_barang)
        qr_path     = buat_qr_code(kode_barang)

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO barang (kode_barang,nama_barang,kategori,tipe_barang,merk,
                spesifikasi,kondisi,jumlah,tanggal_pengadaan,qr_path,keterangan)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (kode_barang,nama_barang,kategori,tipe_barang,merk,
              spesifikasi,kondisi,jumlah,tanggal_pengadaan,qr_path,keterangan))
        mysql.connection.commit()
        cursor.close()
        flash(f'Barang "{nama_barang}" ditambahkan dengan kode {kode_barang}.','success')
        return redirect(url_for('barang_list'))

    return render_template('barang_form.html', mode='tambah', barang=None,
                           kategori_tipe_map=json.dumps(KATEGORI_TIPE_MAP))


@app.route('/barang/edit/<int:id>', methods=['GET','POST'])
@login_required
def barang_edit(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM barang WHERE id=%s", (id,))
    barang = cursor.fetchone()
    if not barang:
        flash('Barang tidak ditemukan.','danger')
        return redirect(url_for('barang_list'))

    if request.method == 'POST':
        nama_barang       = request.form['nama_barang'].strip()
        kategori          = request.form.get('kategori','Komputer')
        tipe_barang       = request.form.get('tipe_barang','Desktop')
        merk              = request.form.get('merk','').strip()
        spesifikasi       = request.form.get('spesifikasi','').strip()
        kondisi           = request.form.get('kondisi','Baik')
        jumlah            = int(request.form.get('jumlah',1))
        tanggal_pengadaan = request.form.get('tanggal_pengadaan') or None
        keterangan        = request.form.get('keterangan','').strip()

        cursor.execute("""
            UPDATE barang SET nama_barang=%s,kategori=%s,tipe_barang=%s,merk=%s,
                spesifikasi=%s,kondisi=%s,jumlah=%s,tanggal_pengadaan=%s,keterangan=%s
            WHERE id=%s
        """, (nama_barang,kategori,tipe_barang,merk,spesifikasi,
              kondisi,jumlah,tanggal_pengadaan,keterangan,id))
        mysql.connection.commit()
        cursor.close()
        flash(f'Barang "{nama_barang}" berhasil diperbarui.','success')
        return redirect(url_for('barang_list'))

    cursor.close()
    return render_template('barang_form.html', mode='edit', barang=barang,
                           kategori_tipe_map=json.dumps(KATEGORI_TIPE_MAP))


@app.route('/barang/hapus/<int:id>', methods=['POST'])
@login_required
def barang_hapus(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT nama_barang,qr_path FROM barang WHERE id=%s",(id,))
    barang = cursor.fetchone()
    if barang:
        if barang['qr_path']:
            qr_file = os.path.join(app.static_folder, barang['qr_path'])
            if os.path.exists(qr_file): os.remove(qr_file)
        cursor.execute("DELETE FROM barang WHERE id=%s",(id,))
        mysql.connection.commit()
        flash(f'Barang "{barang["nama_barang"]}" berhasil dihapus.','success')
    else:
        flash('Barang tidak ditemukan.','danger')
    cursor.close()
    return redirect(url_for('barang_list'))

# ============================================================
# ROUTE: DETAIL & SCAN
# ============================================================

@app.route('/barang/detail/<kode>')
def barang_detail(kode):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM barang WHERE kode_barang=%s",(kode,))
    barang = cursor.fetchone()
    if not barang:
        return render_template('404.html'), 404
    cursor.execute("""INSERT INTO riwayat_scan
        (barang_id,kode_barang,nama_barang,ip_scanner,user_agent)
        VALUES (%s,%s,%s,%s,%s)""",
        (barang['id'],kode,barang['nama_barang'],
         request.remote_addr,request.user_agent.string))
    mysql.connection.commit()
    cursor.execute("""SELECT * FROM riwayat_scan WHERE barang_id=%s
                      ORDER BY scanned_at DESC LIMIT 10""",(barang['id'],))
    riwayat = cursor.fetchall()
    cursor.close()
    return render_template('detail.html', barang=barang, riwayat=riwayat)


@app.route('/scanner')
@login_required
def scanner():
    return render_template('scanner.html')


@app.route('/api/barang/<kode>')
def api_barang(kode):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM barang WHERE kode_barang=%s",(kode,))
    barang = cursor.fetchone()
    cursor.close()
    if barang:
        if isinstance(barang.get('tanggal_pengadaan'), date):
            barang['tanggal_pengadaan'] = barang['tanggal_pengadaan'].strftime('%d %B %Y')
        barang['created_at'] = str(barang.get('created_at',''))
        barang['updated_at'] = str(barang.get('updated_at',''))
        return jsonify({'status':'found','data':barang})
    return jsonify({'status':'not_found','message':'Barang tidak ditemukan'}), 404


@app.route('/api/tipe/<kategori>')
def api_tipe(kategori):
    """API: ambil daftar tipe berdasarkan kategori (untuk dropdown dinamis)"""
    tipe_list = KATEGORI_TIPE_MAP.get(kategori, ['Lainnya'])
    return jsonify(tipe_list)

# ============================================================
# ROUTE: RIWAYAT SCAN
# ============================================================

@app.route('/riwayat')
@login_required
def riwayat_scan():
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT r.*,b.nama_barang,b.kondisi FROM riwayat_scan r
                      LEFT JOIN barang b ON r.barang_id=b.id
                      ORDER BY r.scanned_at DESC LIMIT 100""")
    riwayat = cursor.fetchall()
    cursor.close()
    return render_template('riwayat.html', riwayat=riwayat)

# ============================================================
# ROUTE: CETAK LABEL QR
# ============================================================

@app.route('/cetak-label')
@login_required
def cetak_label():
    ids = request.args.get('ids','')
    cursor = mysql.connection.cursor()
    if ids:
        id_list = [i for i in ids.split(',') if i.isdigit()]
        if id_list:
            placeholders = ','.join(['%s']*len(id_list))
            cursor.execute(f"SELECT * FROM barang WHERE id IN ({placeholders})", id_list)
        else:
            cursor.execute("SELECT * FROM barang ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM barang ORDER BY created_at DESC")
    barang_list = cursor.fetchall()
    cursor.close()
    return render_template('cetak_label.html', barang_list=barang_list)

# ============================================================
# ROUTE: EXPORT EXCEL
# ============================================================

@app.route('/export/excel')
@login_required
def export_excel():
    if not EXCEL_OK:
        flash('Library openpyxl belum terinstall. Jalankan: pip install openpyxl','danger')
        return redirect(url_for('barang_list'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM barang ORDER BY kategori, tipe_barang, kode_barang")
    data = cursor.fetchall()
    cursor.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventaris Lab TJKT"

    # Styling
    header_fill   = PatternFill("solid", fgColor="1e3a5f")
    header_font   = Font(bold=True, color="FFFFFF", size=11)
    subhead_fill  = PatternFill("solid", fgColor="4361ee")
    subhead_font  = Font(bold=True, color="FFFFFF", size=10)
    center        = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left          = Alignment(horizontal="left",   vertical="center", wrap_text=True)
    thin_border   = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'),  bottom=Side(style='thin')
    )
    kondisi_colors = {'Baik':'D1FAE5','Rusak Ringan':'FEF3C7','Rusak Berat':'FEE2E2'}

    # ── Judul ──
    ws.merge_cells('A1:K1')
    ws['A1'] = 'DAFTAR INVENTARIS LABORATORIUM TJKT'
    ws['A1'].font      = Font(bold=True, size=14, color="1e3a5f")
    ws['A1'].alignment = center

    ws.merge_cells('A2:K2')
    ws['A2'] = 'SMKN 1 Cikarang Selatan, Bekasi'
    ws['A2'].font      = Font(size=11, color="475569")
    ws['A2'].alignment = center

    ws.merge_cells('A3:K3')
    ws['A3'] = f'Dicetak: {datetime.now().strftime("%d %B %Y, %H:%M")} | Total: {len(data)} item'
    ws['A3'].font      = Font(size=10, italic=True, color="64748b")
    ws['A3'].alignment = center

    ws.row_dimensions[1].height = 28
    ws.row_dimensions[2].height = 20
    ws.row_dimensions[3].height = 18

    # ── Header Kolom ──
    headers = ['No','Kode Barang','Nama Barang','Kategori','Tipe Barang',
               'Merk','Spesifikasi','Kondisi','Jumlah','Tgl Pengadaan','Keterangan']
    col_widths = [5, 22, 28, 14, 14, 14, 35, 14, 8, 16, 25]

    for col, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=5, column=col, value=h)
        cell.font      = subhead_font
        cell.fill      = subhead_fill
        cell.alignment = center
        cell.border    = thin_border
        ws.column_dimensions[cell.column_letter].width = w

    ws.row_dimensions[5].height = 22

    # ── Data Rows ──
    for row_idx, b in enumerate(data, 6):
        row_data = [
            row_idx - 5,
            b['kode_barang'], b['nama_barang'], b['kategori'], b['tipe_barang'],
            b.get('merk',''), b.get('spesifikasi',''), b['kondisi'],
            b['jumlah'],
            b['tanggal_pengadaan'].strftime('%d/%m/%Y') if b.get('tanggal_pengadaan') else '',
            b.get('keterangan','')
        ]
        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col, value=val)
            cell.border    = thin_border
            cell.alignment = center if col in [1,4,5,8,9,10] else left
            # Warna kondisi
            if col == 8:
                color = kondisi_colors.get(str(val), 'FFFFFF')
                cell.fill = PatternFill("solid", fgColor=color)
                cell.font = Font(bold=True, size=10)

        ws.row_dimensions[row_idx].height = 18

    # Freeze header
    ws.freeze_panes = 'A6'

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Inventaris_Lab_TJKT_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ============================================================
# ROUTE: EXPORT PDF
# ============================================================

@app.route('/export/pdf')
@login_required
def export_pdf():
    if not PDF_OK:
        flash('Library reportlab belum terinstall. Jalankan: pip install reportlab','danger')
        return redirect(url_for('barang_list'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM barang ORDER BY kategori, kode_barang")
    data = cursor.fetchall()
    cursor.close()

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                               topMargin=1.5*cm, bottomMargin=1.5*cm,
                               leftMargin=1.5*cm, rightMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elements = []

    # Judul
    title_style = ParagraphStyle('title', fontSize=14, fontName='Helvetica-Bold',
                                 alignment=TA_CENTER, spaceAfter=4)
    sub_style   = ParagraphStyle('sub', fontSize=10, fontName='Helvetica',
                                 alignment=TA_CENTER, spaceAfter=2, textColor=colors.HexColor('#475569'))
    elements.append(Paragraph('DAFTAR INVENTARIS LABORATORIUM TJKT', title_style))
    elements.append(Paragraph('SMKN 1 Cikarang Selatan, Bekasi', sub_style))
    elements.append(Paragraph(
        f'Dicetak: {datetime.now().strftime("%d %B %Y, %H:%M")} | Total: {len(data)} item',
        sub_style))
    elements.append(Spacer(1, 0.4*cm))

    # Header tabel
    col_headers = [['No','Kode Barang','Nama Barang','Kategori','Tipe',
                    'Merk','Kondisi','Jml','Tgl Pengadaan']]
    col_widths_pdf = [1*cm,4.5*cm,5.5*cm,3*cm,3*cm,3*cm,2.8*cm,1.2*cm,3*cm]

    table_data = col_headers
    for i, b in enumerate(data, 1):
        tgl = b['tanggal_pengadaan'].strftime('%d/%m/%Y') if b.get('tanggal_pengadaan') else '-'
        table_data.append([
            str(i), b['kode_barang'], b['nama_barang'],
            b['kategori'], b.get('tipe_barang','-'),
            b.get('merk','-'), b['kondisi'], str(b['jumlah']), tgl
        ])

    kondisi_row_colors = {
        'Baik'         : colors.HexColor('#D1FAE5'),
        'Rusak Ringan' : colors.HexColor('#FEF3C7'),
        'Rusak Berat'  : colors.HexColor('#FEE2E2'),
    }

    t = Table(table_data, colWidths=col_widths_pdf, repeatRows=1)
    style_cmds = [
        ('BACKGROUND',  (0,0),(-1,0), colors.HexColor('#4361ee')),
        ('TEXTCOLOR',   (0,0),(-1,0), colors.white),
        ('FONTNAME',    (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0),(-1,0), 9),
        ('ALIGN',       (0,0),(-1,-1),'CENTER'),
        ('VALIGN',      (0,0),(-1,-1),'MIDDLE'),
        ('FONTSIZE',    (0,1),(-1,-1), 8),
        ('FONTNAME',    (0,1),(-1,-1), 'Helvetica'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#f8faff')]),
        ('GRID',        (0,0),(-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING',  (0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
    ]
    # Warna per baris sesuai kondisi
    for i, b in enumerate(data, 1):
        color = kondisi_row_colors.get(b['kondisi'])
        if color:
            style_cmds.append(('BACKGROUND', (6,i),(6,i), color))
            style_cmds.append(('FONTNAME',   (6,i),(6,i), 'Helvetica-Bold'))

    t.setStyle(TableStyle(style_cmds))
    elements.append(t)

    doc.build(elements)
    buffer.seek(0)

    filename = f"Inventaris_Lab_TJKT_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename,
                     mimetype='application/pdf')

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

# ============================================================
# JALANKAN
# ============================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
