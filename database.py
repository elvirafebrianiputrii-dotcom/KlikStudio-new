"""Operasi database KLIKSTUDIO: 6 tabel (admin, pelanggan, paket_foto,
jadwal_studio, booking, nota_antrean)."""
from contextlib import contextmanager
from datetime import date, datetime, time
from pathlib import Path
import hashlib
import hmac
import secrets
import sqlite3

DB_PATH = Path(__file__).resolve().with_name("klikstudio_app.db")

STATUS_BOOKING = ("Menunggu", "Dikonfirmasi", "Selesai", "Dibatalkan")
STATUS_BOOKING_AKTIF = ("Menunggu", "Dikonfirmasi")
STATUS_SLOT = ("Tersedia", "Terpesan", "Nonaktif")


# ---------------------------------------------------------------------------
# Koneksi dan struktur tabel
# ---------------------------------------------------------------------------
@contextmanager
def koneksi():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with koneksi() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id_admin INTEGER PRIMARY KEY,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password TEXT NOT NULL,
                nama_admin TEXT NOT NULL,
                CHECK (length(trim(username)) > 0),
                CHECK (length(trim(nama_admin)) > 0)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pelanggan (
                id_pelanggan INTEGER PRIMARY KEY,
                id_admin INTEGER NOT NULL,
                nama_pelanggan TEXT NOT NULL,
                no_hp TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
                    DEFAULT (datetime('now', 'localtime')),
                CHECK (length(trim(nama_pelanggan)) > 0),
                CHECK (length(trim(no_hp)) > 0),
                FOREIGN KEY (id_admin) REFERENCES admin(id_admin)
                    ON DELETE RESTRICT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS paket_foto (
                id_paket INTEGER PRIMARY KEY,
                nama_paket TEXT NOT NULL COLLATE NOCASE UNIQUE,
                durasi_menit INTEGER NOT NULL,
                harga NUMERIC NOT NULL,
                deskripsi TEXT NOT NULL DEFAULT '',
                CHECK (length(trim(nama_paket)) > 0),
                CHECK (typeof(durasi_menit) = 'integer'
                       AND durasi_menit > 0),
                CHECK (harga >= 0)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jadwal_studio (
                id_jadwal INTEGER PRIMARY KEY,
                id_admin INTEGER NOT NULL,
                tanggal TEXT NOT NULL,
                jam_mulai TEXT NOT NULL,
                jam_selesai TEXT NOT NULL,
                status_slot TEXT NOT NULL DEFAULT 'Tersedia',
                UNIQUE (tanggal, jam_mulai),
                CHECK (date(tanggal) = tanggal),
                CHECK (jam_mulai GLOB '[0-2][0-9]:[0-5][0-9]'),
                CHECK (jam_selesai GLOB '[0-2][0-9]:[0-5][0-9]'),
                CHECK (jam_mulai < jam_selesai),
                CHECK (status_slot IN ('Tersedia', 'Terpesan', 'Nonaktif')),
                FOREIGN KEY (id_admin) REFERENCES admin(id_admin)
                    ON DELETE RESTRICT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS booking (
                id_booking INTEGER PRIMARY KEY,
                id_admin INTEGER NOT NULL,
                id_pelanggan INTEGER NOT NULL,
                id_paket INTEGER NOT NULL,
                id_jadwal INTEGER NOT NULL,
                status_booking TEXT NOT NULL DEFAULT 'Menunggu',
                catatan TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
                    DEFAULT (datetime('now', 'localtime')),
                CHECK (status_booking IN
                       ('Menunggu', 'Dikonfirmasi', 'Selesai', 'Dibatalkan')),
                FOREIGN KEY (id_admin) REFERENCES admin(id_admin)
                    ON DELETE RESTRICT,
                FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan)
                    ON DELETE RESTRICT,
                FOREIGN KEY (id_paket) REFERENCES paket_foto(id_paket)
                    ON DELETE RESTRICT,
                FOREIGN KEY (id_jadwal) REFERENCES jadwal_studio(id_jadwal)
                    ON DELETE RESTRICT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nota_antrean (
                id_nota INTEGER PRIMARY KEY,
                id_booking INTEGER NOT NULL UNIQUE,
                nomor_antrean INTEGER NOT NULL,
                tanggal_terbit TEXT NOT NULL
                    DEFAULT (datetime('now', 'localtime')),
                CHECK (typeof(nomor_antrean) = 'integer'
                       AND nomor_antrean > 0),
                FOREIGN KEY (id_booking) REFERENCES booking(id_booking)
                    ON DELETE RESTRICT
            )
        """)
        if conn.execute("SELECT COUNT(*) FROM admin").fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO admin (username, password, nama_admin) "
                "VALUES (?, ?, ?)",
                ("admin", hash_password("admin123"), "Administrator"))


# ---------------------------------------------------------------------------
# Validasi dan format
# ---------------------------------------------------------------------------
def teks_wajib(nilai, label):
    hasil = str(nilai).strip() if nilai is not None else ""
    if not hasil:
        raise ValueError(f"{label} wajib diisi.")
    return hasil


def bilangan_bulat(nilai, label, minimum=0):
    if type(nilai) is not int or nilai < minimum:
        raise ValueError(f"{label} harus bilangan bulat minimal {minimum}.")
    return nilai


def format_jam(nilai, label="Jam"):
    if isinstance(nilai, time):
        return nilai.strftime("%H:%M")
    teks = teks_wajib(nilai, label)
    try:
        return datetime.strptime(teks, "%H:%M").strftime("%H:%M")
    except ValueError:
        raise ValueError(f"{label} harus berformat JJ:MM.") from None


def format_tanggal(nilai, label="Tanggal"):
    if isinstance(nilai, datetime):
        return nilai.date().isoformat()
    if isinstance(nilai, date):
        return nilai.isoformat()
    teks = teks_wajib(nilai, label)
    try:
        return datetime.strptime(teks, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError(f"{label} harus berformat TTTT-BB-HH.") from None


def ke_menit(jam):
    h, m = jam.split(":")
    return int(h) * 60 + int(m)


def dari_menit(menit):
    return f"{menit // 60:02d}:{menit % 60:02d}"


def durasi_slot(row):
    return ke_menit(row["jam_selesai"]) - ke_menit(row["jam_mulai"])


# ---------------------------------------------------------------------------
# ADMIN
# ---------------------------------------------------------------------------
def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 120_000)
    return f"{salt}${digest.hex()}"


def cek_password(password, tersimpan):
    try:
        salt, _ = tersimpan.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), tersimpan)


def dapatkan_pengelola():
    """Mengambil identitas pengelola studio untuk operasional tanpa login."""
    with koneksi() as conn:
        r = conn.execute(
            "SELECT id_admin, username, nama_admin FROM admin ORDER BY id_admin ASC LIMIT 1"
        ).fetchone()
        if r:
            return {"id_admin": r["id_admin"], "username": r["username"],
                    "nama_admin": r["nama_admin"]}
        cur = conn.execute(
            "INSERT INTO admin (username, password, nama_admin) "
            "VALUES (?, ?, ?)",
            ("pengelola", hash_password("klikstudio"), "Pengelola Studio"))
        return {"id_admin": cur.lastrowid, "username": "pengelola",
                "nama_admin": "Pengelola Studio"}


def login(username, password):
    username = str(username or "").strip()
    with koneksi() as conn:
        r = conn.execute("SELECT * FROM admin WHERE username = ?",
                         (username,)).fetchone()
    if r and cek_password(password or "", r["password"]):
        return {"id_admin": r["id_admin"], "username": r["username"],
                "nama_admin": r["nama_admin"]}
    return None


def tambah_admin(username, password, nama):
    username = teks_wajib(username, "Username")
    nama = teks_wajib(nama, "Nama admin")
    password = teks_wajib(password, "Password")
    if len(password) < 6:
        raise ValueError("Password minimal 6 karakter.")
    with koneksi() as conn:
        cur = conn.execute(
            "INSERT INTO admin (username, password, nama_admin) "
            "VALUES (?, ?, ?)", (username, hash_password(password), nama))
        return cur.lastrowid


def ubah_password(id_admin, lama, baru):
    baru = teks_wajib(baru, "Password baru")
    if len(baru) < 6:
        raise ValueError("Password baru minimal 6 karakter.")
    with koneksi() as conn:
        r = conn.execute("SELECT password FROM admin WHERE id_admin = ?",
                         (id_admin,)).fetchone()
        if r is None or not cek_password(lama or "", r["password"]):
            raise ValueError("Password lama tidak sesuai.")
        conn.execute("UPDATE admin SET password = ? WHERE id_admin = ?",
                     (hash_password(baru), id_admin))


# ---------------------------------------------------------------------------
# PAKET_FOTO (Kelola Studio)
# ---------------------------------------------------------------------------
def _validasi_paket(nama, durasi, harga, deskripsi):
    nama = teks_wajib(nama, "Nama paket")
    bilangan_bulat(durasi, "Durasi", 1)
    bilangan_bulat(harga, "Harga", 0)
    return nama, str(deskripsi or "").strip()


def tambah_paket(nama, durasi, harga, deskripsi=""):
    nama, deskripsi = _validasi_paket(nama, durasi, harga, deskripsi)
    with koneksi() as conn:
        cur = conn.execute("""
            INSERT INTO paket_foto
                (nama_paket, durasi_menit, harga, deskripsi)
            VALUES (?, ?, ?, ?)
        """, (nama, durasi, harga, deskripsi))
        return cur.lastrowid


def ubah_paket(id_paket, nama, durasi, harga, deskripsi=""):
    nama, deskripsi = _validasi_paket(nama, durasi, harga, deskripsi)
    with koneksi() as conn:
        conn.execute("""
            UPDATE paket_foto
            SET nama_paket = ?, durasi_menit = ?, harga = ?, deskripsi = ?
            WHERE id_paket = ?
        """, (nama, durasi, harga, deskripsi, id_paket))


def hapus_paket(id_paket):
    with koneksi() as conn:
        conn.execute("DELETE FROM paket_foto WHERE id_paket = ?",
                     (id_paket,))


def daftar_paket():
    with koneksi() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM paket_foto ORDER BY harga, nama_paket")]


# ---------------------------------------------------------------------------
# JADWAL_STUDIO (Kelola Studio): tanggal operasional, jam, ketersediaan slot
# ---------------------------------------------------------------------------
def _slot_hari(conn, tanggal, kecuali=None):
    return [(ke_menit(r["jam_mulai"]), ke_menit(r["jam_selesai"]))
            for r in conn.execute(
                "SELECT jam_mulai, jam_selesai FROM jadwal_studio "
                "WHERE tanggal = ? AND id_jadwal <> ?",
                (tanggal, kecuali or -1))]


def _bentrok(ada, mulai, selesai):
    return any(mulai < b and selesai > a for a, b in ada)


def _tanggal_operasional(tanggal):
    tanggal = format_tanggal(tanggal)
    if tanggal < date.today().isoformat():
        raise ValueError("Tanggal operasional tidak boleh di masa lalu.")
    return tanggal


def buat_jadwal_operasional(id_admin, tanggal, buka, tutup, durasi, jeda=0):
    """Membuka tanggal operasional: jam buka-tutup dibagi menjadi slot.
    Mengembalikan jumlah slot baru (slot yang bentrok dilewati)."""
    if id_admin is None:
        id_admin = dapatkan_pengelola()["id_admin"]
    tanggal = _tanggal_operasional(tanggal)
    buka = format_jam(buka, "Jam buka")
    tutup = format_jam(tutup, "Jam tutup")
    if buka >= tutup:
        raise ValueError("Jam tutup harus lebih akhir dari jam buka.")
    bilangan_bulat(durasi, "Durasi slot", 5)
    bilangan_bulat(jeda, "Jeda antar slot", 0)
    with koneksi() as conn:
        ada = _slot_hari(conn, tanggal)
        mulai, batas, dibuat = ke_menit(buka), ke_menit(tutup), 0
        while mulai + durasi <= batas:
            selesai = mulai + durasi
            if not _bentrok(ada, mulai, selesai):
                conn.execute("""
                    INSERT INTO jadwal_studio
                        (id_admin, tanggal, jam_mulai, jam_selesai)
                    VALUES (?, ?, ?, ?)
                """, (id_admin, tanggal, dari_menit(mulai),
                      dari_menit(selesai)))
                dibuat += 1
            mulai = selesai + jeda
        if dibuat == 0:
            raise ValueError("Tidak ada slot baru. Rentang jam terlalu "
                             "pendek atau sudah terisi slot lain.")
        return dibuat


def tambah_slot(id_admin, tanggal, mulai, selesai):
    if id_admin is None:
        id_admin = dapatkan_pengelola()["id_admin"]
    tanggal = _tanggal_operasional(tanggal)
    mulai = format_jam(mulai, "Jam mulai")
    selesai = format_jam(selesai, "Jam selesai")
    if mulai >= selesai:
        raise ValueError("Jam selesai harus lebih akhir dari jam mulai.")
    with koneksi() as conn:
        if _bentrok(_slot_hari(conn, tanggal),
                    ke_menit(mulai), ke_menit(selesai)):
            raise ValueError("Slot bertabrakan dengan slot lain "
                             "pada tanggal tersebut.")
        cur = conn.execute("""
            INSERT INTO jadwal_studio
                (id_admin, tanggal, jam_mulai, jam_selesai)
            VALUES (?, ?, ?, ?)
        """, (id_admin, tanggal, mulai, selesai))
        return cur.lastrowid


def ubah_slot(id_jadwal, mulai, selesai):
    mulai = format_jam(mulai, "Jam mulai")
    selesai = format_jam(selesai, "Jam selesai")
    if mulai >= selesai:
        raise ValueError("Jam selesai harus lebih akhir dari jam mulai.")
    with koneksi() as conn:
        s = conn.execute("SELECT * FROM jadwal_studio WHERE id_jadwal = ?",
                         (id_jadwal,)).fetchone()
        if s is None:
            raise ValueError("Slot tidak ditemukan.")
        if s["status_slot"] == "Terpesan":
            raise ValueError("Slot terpesan tidak dapat diubah jamnya. "
                             "Batalkan booking terlebih dahulu.")
        if _bentrok(_slot_hari(conn, s["tanggal"], id_jadwal),
                    ke_menit(mulai), ke_menit(selesai)):
            raise ValueError("Slot bertabrakan dengan slot lain "
                             "pada tanggal tersebut.")
        conn.execute("UPDATE jadwal_studio SET jam_mulai = ?, "
                     "jam_selesai = ? WHERE id_jadwal = ?",
                     (mulai, selesai, id_jadwal))


def ubah_status_slot(id_jadwal, status):
    if status not in ("Tersedia", "Nonaktif"):
        raise ValueError("Status slot hanya dapat Tersedia atau Nonaktif.")
    with koneksi() as conn:
        r = conn.execute("SELECT status_slot FROM jadwal_studio "
                         "WHERE id_jadwal = ?", (id_jadwal,)).fetchone()
        if r is None:
            raise ValueError("Slot tidak ditemukan.")
        if r["status_slot"] == "Terpesan":
            raise ValueError("Slot sedang terpesan. "
                             "Batalkan booking terlebih dahulu.")
        conn.execute("UPDATE jadwal_studio SET status_slot = ? "
                     "WHERE id_jadwal = ?", (status, id_jadwal))


def atur_status_tanggal(tanggal, status):
    """Tutup/buka seluruh slot pada satu tanggal.
    status 'Nonaktif': slot Tersedia dinonaktifkan (studio tutup).
    status 'Tersedia': slot Nonaktif diaktifkan kembali (studio buka)."""
    tanggal = format_tanggal(tanggal)
    if status not in ("Tersedia", "Nonaktif"):
        raise ValueError("Status harus Tersedia atau Nonaktif.")
    asal = "Nonaktif" if status == "Tersedia" else "Tersedia"
    with koneksi() as conn:
        cur = conn.execute("UPDATE jadwal_studio SET status_slot = ? "
                           "WHERE tanggal = ? AND status_slot = ?",
                           (status, tanggal, asal))
        return cur.rowcount


def hapus_slot(id_jadwal):
    with koneksi() as conn:
        conn.execute("DELETE FROM jadwal_studio WHERE id_jadwal = ?",
                     (id_jadwal,))


def hapus_tanggal(tanggal):
    """Menghapus semua slot satu tanggal. Ditolak jika ada riwayat booking."""
    tanggal = format_tanggal(tanggal)
    with koneksi() as conn:
        terpakai = conn.execute("""
            SELECT COUNT(*) FROM booking AS b
            JOIN jadwal_studio AS j ON b.id_jadwal = j.id_jadwal
            WHERE j.tanggal = ?
        """, (tanggal,)).fetchone()[0]
        if terpakai:
            raise ValueError("Tanggal ini memiliki riwayat booking dan "
                             "tidak dapat dihapus. Nonaktifkan slotnya.")
        conn.execute("DELETE FROM jadwal_studio WHERE tanggal = ?",
                     (tanggal,))


def daftar_tanggal():
    """Ringkasan operasional per tanggal."""
    with koneksi() as conn:
        rows = [dict(r) for r in conn.execute("""
            SELECT tanggal, MIN(jam_mulai) AS jam_buka,
                MAX(jam_selesai) AS jam_tutup, COUNT(*) AS jumlah_slot,
                SUM(status_slot = 'Tersedia') AS tersedia,
                SUM(status_slot = 'Terpesan') AS terpesan,
                SUM(status_slot = 'Nonaktif') AS nonaktif
            FROM jadwal_studio GROUP BY tanggal ORDER BY tanggal DESC
        """)]
    for r in rows:
        r["status_operasional"] = ("Buka" if r["tersedia"] + r["terpesan"]
                                   else "Tutup")
    return rows


def daftar_slot(tanggal):
    tanggal = format_tanggal(tanggal)
    with koneksi() as conn:
        rows = [dict(r) for r in conn.execute("""
            SELECT j.*, p.nama_pelanggan, b.id_booking
            FROM jadwal_studio AS j
            LEFT JOIN booking AS b ON b.id_jadwal = j.id_jadwal
                AND b.status_booking <> 'Dibatalkan'
            LEFT JOIN pelanggan AS p ON p.id_pelanggan = b.id_pelanggan
            WHERE j.tanggal = ? ORDER BY j.jam_mulai
        """, (tanggal,))]
    for r in rows:
        r["durasi_menit"] = durasi_slot(r)
    return rows


def daftar_slot_tersedia(min_menit=0, dari_tanggal=None):
    dari_tanggal = format_tanggal(dari_tanggal or date.today())
    with koneksi() as conn:
        rows = [dict(r) for r in conn.execute("""
            SELECT * FROM jadwal_studio
            WHERE status_slot = 'Tersedia' AND tanggal >= ?
            ORDER BY tanggal, jam_mulai
        """, (dari_tanggal,))]
    hasil = []
    for r in rows:
        r["durasi_menit"] = durasi_slot(r)
        if r["durasi_menit"] >= min_menit:
            hasil.append(r)
    return hasil


# ---------------------------------------------------------------------------
# PELANGGAN
# ---------------------------------------------------------------------------
def _validasi_pelanggan(nama, no_hp, email):
    nama = teks_wajib(nama, "Nama pelanggan")
    no_hp = teks_wajib(no_hp, "Nomor telepon").replace(" ", "")
    if not no_hp.lstrip("+").isdigit() or len(no_hp) < 8:
        raise ValueError("Nomor telepon harus berisi angka, minimal 8 digit.")
    email = str(email or "").strip()
    if email and ("@" not in email or "." not in email.split("@")[-1]):
        raise ValueError("Format email tidak valid.")
    return nama, no_hp, email


def cari_pelanggan_hp(no_hp):
    no_hp = str(no_hp or "").replace(" ", "").strip()
    if not no_hp:
        return None
    with koneksi() as conn:
        r = conn.execute("SELECT * FROM pelanggan WHERE no_hp = ?",
                         (no_hp,)).fetchone()
    return dict(r) if r else None


def daftar_pelanggan(cari=None):
    sql = """
        SELECT p.*, a.nama_admin,
               COUNT(b.id_booking) AS total_booking
        FROM pelanggan AS p
        JOIN admin AS a ON p.id_admin = a.id_admin
        LEFT JOIN booking AS b ON b.id_pelanggan = p.id_pelanggan
    """
    params = ()
    if cari and cari.strip():
        sql += " WHERE p.nama_pelanggan LIKE ? OR p.no_hp LIKE ?"
        params = (f"%{cari.strip()}%",) * 2
    sql += " GROUP BY p.id_pelanggan ORDER BY p.nama_pelanggan"
    with koneksi() as conn:
        return [dict(r) for r in conn.execute(sql, params)]


# ---------------------------------------------------------------------------
# BOOKING dan NOTA_ANTREAN
# ---------------------------------------------------------------------------
def _terbitkan_nota(conn, id_booking, id_jadwal):
    ada = conn.execute("SELECT nomor_antrean FROM nota_antrean "
                       "WHERE id_booking = ?", (id_booking,)).fetchone()
    if ada:
        return ada["nomor_antrean"]
    nomor = conn.execute("""
        SELECT COALESCE(MAX(n.nomor_antrean), 0) + 1
        FROM nota_antrean AS n
        JOIN booking AS b ON n.id_booking = b.id_booking
        JOIN jadwal_studio AS j ON b.id_jadwal = j.id_jadwal
        WHERE j.tanggal = (SELECT tanggal FROM jadwal_studio
                           WHERE id_jadwal = ?)
    """, (id_jadwal,)).fetchone()[0]
    conn.execute("INSERT INTO nota_antrean (id_booking, nomor_antrean) "
                 "VALUES (?, ?)", (id_booking, nomor))
    return nomor


def buat_booking(id_admin, nama, no_hp, id_paket, id_jadwal,
                 catatan="", email="", konfirmasi=False):
    """Menyimpan booking. Pelanggan dicari lewat nomor telepon; jika belum
    ada, dibuat baru. Dengan konfirmasi=True, status langsung Dikonfirmasi
    dan nota antrean diterbitkan."""
    if id_admin is None:
        id_admin = dapatkan_pengelola()["id_admin"]
    nama, no_hp, email = _validasi_pelanggan(nama, no_hp, email)
    catatan = str(catatan or "").strip()
    with koneksi() as conn:
        conn.execute("BEGIN IMMEDIATE")
        slot = conn.execute("SELECT * FROM jadwal_studio "
                            "WHERE id_jadwal = ?", (id_jadwal,)).fetchone()
        if slot is None:
            raise ValueError("Slot waktu tidak ditemukan.")
        if slot["status_slot"] != "Tersedia":
            raise ValueError("Slot waktu sudah tidak tersedia "
                             "atau bentrok dengan booking lain.")
        paket = conn.execute("SELECT * FROM paket_foto WHERE id_paket = ?",
                             (id_paket,)).fetchone()
        if paket is None:
            raise ValueError("Paket foto tidak ditemukan.")
        if durasi_slot(slot) < paket["durasi_menit"]:
            raise ValueError(
                f"Paket {paket['nama_paket']} membutuhkan "
                f"{paket['durasi_menit']} menit, slot hanya "
                f"{durasi_slot(slot)} menit.")
        p = conn.execute("SELECT id_pelanggan FROM pelanggan "
                         "WHERE no_hp = ?", (no_hp,)).fetchone()
        pelanggan_baru = p is None
        if pelanggan_baru:
            id_pelanggan = conn.execute("""
                INSERT INTO pelanggan
                    (id_admin, nama_pelanggan, no_hp, email)
                VALUES (?, ?, ?, ?)
            """, (id_admin, nama, no_hp, email)).lastrowid
        else:
            id_pelanggan = p["id_pelanggan"]
        status = "Dikonfirmasi" if konfirmasi else "Menunggu"
        id_booking = conn.execute("""
            INSERT INTO booking (id_admin, id_pelanggan, id_paket,
                                 id_jadwal, status_booking, catatan)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (id_admin, id_pelanggan, id_paket, id_jadwal, status,
              catatan)).lastrowid
        conn.execute("UPDATE jadwal_studio SET status_slot = 'Terpesan' "
                     "WHERE id_jadwal = ?", (id_jadwal,))
        nomor = (_terbitkan_nota(conn, id_booking, id_jadwal)
                 if konfirmasi else None)
        return {"id_booking": id_booking, "nomor_antrean": nomor,
                "pelanggan_baru": pelanggan_baru}


def konfirmasi_booking(id_booking):
    """Menunggu -> Dikonfirmasi, lalu menerbitkan nota antrean."""
    with koneksi() as conn:
        conn.execute("BEGIN IMMEDIATE")
        b = conn.execute("SELECT * FROM booking WHERE id_booking = ?",
                         (id_booking,)).fetchone()
        if b is None:
            raise ValueError("Booking tidak ditemukan.")
        if b["status_booking"] != "Menunggu":
            raise ValueError("Hanya booking berstatus Menunggu "
                             "yang dapat dikonfirmasi.")
        conn.execute("UPDATE booking SET status_booking = 'Dikonfirmasi' "
                     "WHERE id_booking = ?", (id_booking,))
        return _terbitkan_nota(conn, id_booking, b["id_jadwal"])


def ubah_status_booking(id_booking, status):
    """Dikonfirmasi -> Selesai, atau booking aktif -> Dibatalkan."""
    if status == "Dikonfirmasi":
        return konfirmasi_booking(id_booking)
    if status not in ("Selesai", "Dibatalkan"):
        raise ValueError("Perubahan status tidak diizinkan.")
    with koneksi() as conn:
        b = conn.execute("SELECT * FROM booking WHERE id_booking = ?",
                         (id_booking,)).fetchone()
        if b is None:
            raise ValueError("Booking tidak ditemukan.")
        if b["status_booking"] not in STATUS_BOOKING_AKTIF:
            raise ValueError(f"Booking berstatus {b['status_booking']} "
                             "bersifat final.")
        if status == "Selesai" and b["status_booking"] != "Dikonfirmasi":
            raise ValueError("Konfirmasi booking terlebih dahulu "
                             "sebelum menandainya selesai.")
        conn.execute("UPDATE booking SET status_booking = ? "
                     "WHERE id_booking = ?", (status, id_booking))
        if status == "Dibatalkan":
            conn.execute("UPDATE jadwal_studio SET status_slot = 'Tersedia' "
                         "WHERE id_jadwal = ?", (b["id_jadwal"],))


def ubah_booking(id_booking, nama, no_hp, id_paket, catatan=""):
    """Mengubah data pelanggan, paket, dan catatan booking aktif.
    Perubahan nama/telepon berlaku pada data pelanggan tersebut."""
    nama, no_hp, _ = _validasi_pelanggan(nama, no_hp, "")
    catatan = str(catatan or "").strip()
    with koneksi() as conn:
        b = conn.execute("""
            SELECT b.status_booking, b.id_pelanggan,
                   j.jam_mulai, j.jam_selesai
            FROM booking AS b
            JOIN jadwal_studio AS j ON b.id_jadwal = j.id_jadwal
            WHERE b.id_booking = ?
        """, (id_booking,)).fetchone()
        if b is None:
            raise ValueError("Booking tidak ditemukan.")
        if b["status_booking"] not in STATUS_BOOKING_AKTIF:
            raise ValueError("Hanya booking aktif yang dapat diedit.")
        paket = conn.execute("SELECT * FROM paket_foto WHERE id_paket = ?",
                             (id_paket,)).fetchone()
        if paket is None:
            raise ValueError("Paket foto tidak ditemukan.")
        if durasi_slot(b) < paket["durasi_menit"]:
            raise ValueError("Durasi paket melebihi panjang slot booking.")
        conn.execute("UPDATE pelanggan SET nama_pelanggan = ?, no_hp = ? "
                     "WHERE id_pelanggan = ?",
                     (nama, no_hp, b["id_pelanggan"]))
        conn.execute("UPDATE booking SET id_paket = ?, catatan = ? "
                     "WHERE id_booking = ?", (id_paket, catatan, id_booking))


def hapus_booking(id_booking):
    with koneksi() as conn:
        b = conn.execute("SELECT * FROM booking WHERE id_booking = ?",
                         (id_booking,)).fetchone()
        if b is None:
            raise ValueError("Booking tidak ditemukan.")
        conn.execute("DELETE FROM nota_antrean WHERE id_booking = ?",
                     (id_booking,))
        conn.execute("DELETE FROM booking WHERE id_booking = ?",
                     (id_booking,))
        if b["status_booking"] in STATUS_BOOKING_AKTIF:
            conn.execute("UPDATE jadwal_studio SET status_slot = 'Tersedia' "
                         "WHERE id_jadwal = ?", (b["id_jadwal"],))


def daftar_booking(status=None, tanggal=None, cari=None):
    sql = """
        SELECT b.*, p.nama_pelanggan, p.no_hp, p.email,
            pk.nama_paket, pk.durasi_menit, pk.harga,
            j.tanggal, j.jam_mulai, j.jam_selesai, a.nama_admin,
            n.id_nota, n.nomor_antrean, n.tanggal_terbit
        FROM booking AS b
        JOIN pelanggan AS p ON b.id_pelanggan = p.id_pelanggan
        JOIN paket_foto AS pk ON b.id_paket = pk.id_paket
        JOIN jadwal_studio AS j ON b.id_jadwal = j.id_jadwal
        JOIN admin AS a ON b.id_admin = a.id_admin
        LEFT JOIN nota_antrean AS n ON n.id_booking = b.id_booking
    """
    kondisi, params = [], []
    if status:
        kondisi.append("b.status_booking = ?")
        params.append(status)
    if tanggal:
        kondisi.append("j.tanggal = ?")
        params.append(format_tanggal(tanggal))
    if cari and cari.strip():
        kondisi.append("(p.nama_pelanggan LIKE ? OR p.no_hp LIKE ?)")
        params.extend([f"%{cari.strip()}%"] * 2)
    if kondisi:
        sql += " WHERE " + " AND ".join(kondisi)
    sql += " ORDER BY j.tanggal DESC, j.jam_mulai"
    with koneksi() as conn:
        return [dict(r) for r in conn.execute(sql, params)]


def daftar_nota():
    return [r for r in daftar_booking() if r["id_nota"]]


def ringkasan():
    hari_ini = date.today().isoformat()
    with koneksi() as conn:
        pelanggan = conn.execute(
            "SELECT COUNT(*) FROM pelanggan").fetchone()[0]
        booking_hari_ini = conn.execute("""
            SELECT COUNT(*) FROM booking AS b
            JOIN jadwal_studio AS j ON b.id_jadwal = j.id_jadwal
            WHERE j.tanggal = ? AND b.status_booking <> 'Dibatalkan'
        """, (hari_ini,)).fetchone()[0]
        slot_kosong = conn.execute(
            "SELECT COUNT(*) FROM jadwal_studio "
            "WHERE tanggal = ? AND status_slot = 'Tersedia'",
            (hari_ini,)).fetchone()[0]
        pendapatan = conn.execute("""
            SELECT COALESCE(SUM(pk.harga), 0) FROM booking AS b
            JOIN paket_foto AS pk ON b.id_paket = pk.id_paket
            WHERE b.status_booking = 'Selesai'
        """).fetchone()[0]
        per_status = {s: 0 for s in STATUS_BOOKING}
        for r in conn.execute("SELECT status_booking, COUNT(*) AS n "
                              "FROM booking GROUP BY status_booking"):
            per_status[r["status_booking"]] = r["n"]
    return {"pelanggan": pelanggan, "booking_hari_ini": booking_hari_ini,
            "slot_kosong": slot_kosong, "pendapatan": int(pendapatan),
            "per_status": per_status}


if __name__ == "__main__":
    init_db()
    print(f"Database siap di {DB_PATH}")