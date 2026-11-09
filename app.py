"""KLIKSTUDIO - Sistem Manajemen & Booking Studio Foto (Khusus Pengelola)."""
from datetime import date, datetime, time
from base64 import b64encode
import html
from pathlib import Path
import sqlite3

import sys
import streamlit as st
import streamlit.runtime

# Otomatis menjalankan server Streamlit jika file dijalankan via 'python app.py' (tombol Run di VS Code/editor)
if __name__ == "__main__" and not streamlit.runtime.exists():
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", __file__] + sys.argv[1:]
    sys.exit(stcli.main())

import database as db

ASSET_DIR = Path(__file__).parent / "assets"


def gambar_data_uri(nama):
    data = b64encode((ASSET_DIR / nama).read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{data}"


LOGO_KAMERA = gambar_data_uri("klikstudio-camera.svg")
LOGO_WORDMARK = gambar_data_uri("klikstudio-wordmark.svg")
LOGO_WORDMARK_PUTIH = gambar_data_uri("klikstudio-wordmark-putih.svg")

st.set_page_config(
    page_title="KlikStudio - Sistem Pengelola Studio",
    page_icon=ASSET_DIR / "klikstudio-camera.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

db.init_db()
PENGELOLA_AKTIF = db.dapatkan_pengelola()

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
IKON_BOOKING = {
    "Menunggu": "🟡 Menunggu",
    "Dikonfirmasi": "🔵 Dikonfirmasi",
    "Selesai": "🟢 Selesai",
    "Dibatalkan": "🔴 Dibatalkan"
}
IKON_SLOT = {
    "Tersedia": "🟢 Tersedia",
    "Terpesan": "🟠 Terpesan",
    "Nonaktif": "⚫ Nonaktif"
}

# ---------------------------------------------------------------------------
# Styling Vintage Profesional
# ---------------------------------------------------------------------------
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,900;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Courier+Prime:wght@400;700&display=swap');

:root {{
    --v-bg: #FAF7F2;
    --v-card: #FFFFFF;
    --v-secondary: #F2EBE0;
    --v-border: #DCD3C7;
    --v-text: #2A231F;
    --v-muted: #6E645D;
    --v-terracotta: #B85D19;
    --v-terracotta-hover: #9E4D12;
    --v-gold: #C8963E;
    --v-espresso: #241E1C;
    --v-sage: #385E43;
    --v-rust: #8F2D2D;
    --v-indigo: #2D4C6F;
}}

html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--v-text);
}}

h1, h2, h3, .vintage-font {{
    font-family: 'Playfair Display', Georgia, serif !important;
    letter-spacing: -0.01em;
    color: var(--v-espresso) !important;
    font-weight: 700;
}}

/* Header Banner Vintage */
.vintage-hero {{
    position: relative;
    background: linear-gradient(135deg, #25201D 0%, #1A1614 100%);
    color: #F8F5EE;
    padding: 2.2rem 2.6rem;
    border-radius: 8px;
    margin-bottom: 1.6rem;
    border: 1px solid #3E3530;
    box-shadow: 0 4px 18px rgba(36, 30, 28, 0.12);
}}

.vintage-hero::before, .vintage-hero::after {{
    content: "";
    position: absolute;
    width: 26px;
    height: 26px;
    border: 2px solid #C8963E;
    pointer-events: none;
}}
.vintage-hero::before {{
    top: 12px;
    left: 12px;
    border-right: 0;
    border-bottom: 0;
}}
.vintage-hero::after {{
    bottom: 12px;
    right: 12px;
    border-left: 0;
    border-top: 0;
}}

.vintage-hero .badge-terminal {{
    display: inline-block;
    background: rgba(200, 150, 62, 0.18);
    color: #E2B874;
    border: 1px solid rgba(200, 150, 62, 0.4);
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    font-weight: 700;
    text-transform: uppercase;
    padding: 0.2rem 0.65rem;
    border-radius: 3px;
    margin-bottom: 0.8rem;
}}

.vintage-hero .merek-logo {{
    display: block;
    height: 50px;
    width: auto;
    max-width: 100%;
}}

.vintage-hero .sub {{
    color: #D3CBC3;
    font-size: 1.02rem;
    line-height: 1.5;
    max-width: 65ch;
    margin-top: 0.5rem;
}}

.vintage-hero .tanggal-row {{
    color: #E2B874;
    font-size: 0.92rem;
    font-weight: 600;
    margin-top: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

/* Metric Cards */
div[data-testid="stMetric"] {{
    background: #FFFFFF !important;
    border: 1px solid #DFD7CC !important;
    border-left: 5px solid #B85D19 !important;
    border-radius: 6px !important;
    padding: 1rem 1.2rem !important;
    box-shadow: 0 2px 6px rgba(60, 45, 30, 0.04) !important;
}}

div[data-testid="stMetric"] label {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: #6E645D !important;
    font-size: 0.86rem !important;
    font-weight: 600 !important;
}}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    font-family: 'Playfair Display', serif !important;
    color: #241E1C !important;
    font-size: 1.85rem !important;
    font-weight: 700 !important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: #F3EDE2 !important;
    border-right: 1px solid #DCD3C7 !important;
}}

.sidebar-brand {{
    padding: 0.4rem 0.2rem 1rem 0.2rem;
    border-bottom: 1px solid #DDD3C4;
    margin-bottom: 1.2rem;
}}

.brand-header {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
}}

.brand-logo {{
    width: 38px;
    height: 38px;
}}

.brand-name {{
    font-family: 'Playfair Display', serif;
    font-weight: 900;
    font-size: 1.45rem;
    letter-spacing: 0.04em;
    color: #241E1C;
    line-height: 1;
}}

.brand-tag {{
    display: inline-block;
    background: #E8DECE;
    color: #7A5726;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 0.2rem 0.5rem;
    border-radius: 3px;
    margin-top: 0.5rem;
    border: 1px solid #D8CBB6;
}}

/* Vintage Karcis / Nota Antrean */
.vintage-ticket {{
    max-width: 460px;
    margin: 0.8rem auto 1.4rem auto;
    background: #FCF9F2;
    color: #241E1C;
    border: 2px solid #362E28;
    border-radius: 8px;
    padding: 1.8rem 2.2rem;
    position: relative;
    box-shadow: 0 4px 14px rgba(45, 35, 25, 0.08);
    font-family: 'Plus Jakarta Sans', sans-serif;
}}

.vintage-ticket-header {{
    text-align: center;
    border-bottom: 2px dashed #9E8E7E;
    padding-bottom: 1rem;
    margin-bottom: 1rem;
}}

.vintage-ticket-header .logo-img {{
    height: 30px;
    width: auto;
    display: block;
    margin: 0 auto 0.6rem auto;
}}

.vintage-ticket-title {{
    font-family: 'Playfair Display', serif;
    font-weight: 900;
    font-size: 1.4rem;
    letter-spacing: 0.04em;
    color: #241E1C;
    margin: 0;
}}

.vintage-ticket-subtitle {{
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    color: #7A6F65;
    text-transform: uppercase;
    margin-top: 0.2rem;
}}

.vintage-queue-badge {{
    text-align: center;
    margin: 1.1rem 0;
}}

.vintage-queue-label {{
    font-size: 0.74rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #6E645D;
    font-weight: 700;
}}

.vintage-queue-num {{
    font-family: 'Playfair Display', serif;
    font-size: 3.5rem;
    font-weight: 900;
    line-height: 1;
    color: #241E1C;
    display: inline-block;
    background: #F3E6CD;
    border: 2px solid #C8963E;
    border-radius: 6px;
    padding: 0.2rem 1.6rem;
    margin-top: 0.35rem;
}}

.vintage-ticket-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
    margin: 1rem 0;
}}

.vintage-ticket-table td {{
    padding: 0.32rem 0;
    vertical-align: top;
}}

.vintage-ticket-table td:first-child {{
    color: #72675E;
    width: 38%;
    font-weight: 500;
}}

.vintage-ticket-table td:last-child {{
    font-weight: 600;
    color: #241E1C;
}}

.vintage-ticket-footer {{
    border-top: 2px dashed #9E8E7E;
    margin-top: 1rem;
    padding-top: 0.75rem;
    font-size: 0.76rem;
    color: #7A6F65;
    text-align: center;
    line-height: 1.4;
}}

/* Vintage Badge / Stamp */
.vintage-stamp {{
    display: inline-block;
    padding: 0.2rem 0.55rem;
    border: 1.5px solid;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
.stamp-konfirmasi {{
    color: #2B4C6F;
    border-color: #2B4C6F;
    background: #EDF3FA;
}}
.stamp-selesai {{
    color: #385E43;
    border-color: #385E43;
    background: #EBF4EE;
}}
.stamp-menunggu {{
    color: #996515;
    border-color: #996515;
    background: #FDF6E8;
}}
.stamp-batal {{
    color: #8F2D2D;
    border-color: #8F2D2D;
    background: #FDF0F0;
}}

/* Vintage Card Container */
.vintage-card {{
    background: #FFFFFF;
    border: 1px solid #DFD7CC;
    border-radius: 6px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 8px rgba(60, 45, 30, 0.04);
}}

.paket-card {{
    background: #FFFFFF;
    border: 1px solid #DCD3C7;
    border-top: 4px solid #B85D19;
    border-radius: 6px;
    padding: 1.2rem;
    height: 100%;
    box-shadow: 0 2px 6px rgba(50, 40, 30, 0.04);
}}

.paket-nama {{
    font-family: 'Playfair Display', serif;
    font-weight: 700;
    font-size: 1.25rem;
    color: #241E1C;
    margin-bottom: 0.25rem;
}}

.paket-harga {{
    font-family: 'Playfair Display', serif;
    font-weight: 800;
    font-size: 1.45rem;
    color: #B85D19;
    margin-bottom: 0.4rem;
}}

.paket-durasi {{
    display: inline-block;
    background: #F3EDE2;
    color: #6E645D;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
}}

.paket-desc {{
    font-size: 0.88rem;
    color: #5B524A;
    line-height: 1.4;
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Bantuan umum
# ---------------------------------------------------------------------------
def rupiah(nilai):
    return "Rp " + f"{int(nilai):,}".replace(",", ".")


def tanggal_indo(iso):
    d = date.fromisoformat(iso)
    return f"{HARI[d.weekday()]}, {d:%d-%m-%Y}"


def ke_time(teks):
    return datetime.strptime(teks, "%H:%M").time()


def tampil_html(teks):
    """Meratakan baris HTML agar tidak dianggap code block oleh Markdown."""
    st.markdown(" ".join(b.strip() for b in teks.splitlines()),
                unsafe_allow_html=True)


def selesai(pesan):
    st.session_state["pesan_sukses"] = pesan
    st.rerun()


PESAN_UNIK = {
    "pelanggan.no_hp": "Nomor telepon sudah terdaftar atas nama pelanggan lain.",
    "paket_foto.nama_paket": "Nama paket sudah digunakan.",
    "jadwal_studio.jam_mulai": "Slot dengan jam mulai tersebut sudah ada pada tanggal itu.",
    "admin.username": "Username sudah digunakan.",
}


def tampil_error(exc):
    teks = str(exc)
    if isinstance(exc, ValueError):
        st.error(teks)
    elif "FOREIGN KEY" in teks:
        st.error("Data masih digunakan oleh relasi lain (misalnya booking yang masih aktif).")
    else:
        for kunci, pesan in PESAN_UNIK.items():
            if kunci in teks:
                st.error(pesan)
                return
        st.error(f"Terjadi kesalahan database: {teks}")


def judul_halaman(judul, keterangan):
    st.markdown(f"<h1 class='vintage-font' style='margin-bottom: 0.15rem;'>{html.escape(judul)}</h1>", unsafe_allow_html=True)
    st.caption(keterangan)
    st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)


def pilih_record(rows, kunci, label, judul, key):
    pilihan = {r[kunci]: r for r in rows}
    identitas = st.selectbox(
        judul,
        list(pilihan),
        format_func=lambda i: label(pilihan[i]),
        key=key
    )
    return pilihan[identitas]


def blok_hapus(deskripsi, key, aksi, pesan):
    st.warning(f"Konfirmasi penghapusan: **{deskripsi}**")
    yakin = st.checkbox("Saya mengonfirmasi tindakan penghapusan data ini", key=f"yakin_{key}")
    if st.button("Hapus Permanen", disabled=not yakin, key=f"hapus_{key}"):
        try:
            aksi()
            selesai(pesan)
        except (ValueError, sqlite3.IntegrityError) as exc:
            tampil_error(exc)


def tabel(rows, kolom, kosong="Belum ada data untuk ditampilkan."):
    """kolom: daftar (judul, fungsi pengambil nilai)."""
    if not rows:
        st.info(kosong)
        return
    data = [{judul: fn(r) for judul, fn in kolom} for r in rows]
    st.dataframe(data, hide_index=True, width="stretch")


KOLOM_BOOKING = [
    ("No. Booking", lambda r: f"#{r['id_booking']}"),
    ("Antrean", lambda r: f"No. {r['nomor_antrean']}" if r["nomor_antrean"] else "-"),
    ("Tanggal", lambda r: tanggal_indo(r["tanggal"])),
    ("Sesi Jam", lambda r: f"{r['jam_mulai']} - {r['jam_selesai']}"),
    ("Pelanggan", lambda r: r["nama_pelanggan"]),
    ("Telepon / WA", lambda r: r["no_hp"]),
    ("Paket", lambda r: r["nama_paket"]),
    ("Harga", lambda r: rupiah(r["harga"])),
    ("Status", lambda r: IKON_BOOKING[r["status_booking"]]),
]


# ---------------------------------------------------------------------------
# Format Nota & WhatsApp
# ---------------------------------------------------------------------------
def teks_nota(n):
    return "\n".join([
        "========================================",
        "          KLIKSTUDIO PHOTOGRAPHY        ",
        "        NOTA & BUKTI BOOKING RESMI      ",
        "========================================",
        f"No. Antrean  : {n['nomor_antrean'] if n['nomor_antrean'] else '-'}",
        f"ID Booking   : #{n['id_booking']}",
        f"Pelanggan    : {n['nama_pelanggan']}",
        f"Telepon/WA   : {n['no_hp']}",
        f"Paket Foto   : {n['nama_paket']} ({n['durasi_menit']} menit)",
        f"Jadwal Sesi  : {tanggal_indo(n['tanggal'])}",
        f"Waktu Sesi   : {n['jam_mulai']} - {n['jam_selesai']} WIB",
        f"Total Biaya  : {rupiah(n['harga'])}",
        f"Status       : {n['status_booking']}",
        f"Diterbitkan  : {n['tanggal_terbit']}",
        f"Petugas      : {n['nama_admin']}",
        "----------------------------------------",
        "Harap hadir 10 menit sebelum sesi foto.",
        "Tunjukkan nota ini kepada petugas studio.",
        "Terima kasih atas kunjungan Anda!",
        "========================================",
    ])


def format_pesan_wa(n):
    antrean_teks = f"*{n['nomor_antrean']}*" if n['nomor_antrean'] else "-(Menunggu Konfirmasi)"
    return f"""*KONFIRMASI BOOKING - KLIKSTUDIO* 📸
Halo kak *{n['nama_pelanggan']}*, terima kasih telah memesan sesi foto di KlikStudio!

Berikut rincian jadwal booking Anda:
━━━━━━━━━━━━━━━━━━━━
🎟️ *Nomor Antrean:* {antrean_teks}
🔖 *ID Booking:* #{n['id_booking']}
📦 *Paket Foto:* {n['nama_paket']} ({n['durasi_menit']} menit)
📅 *Hari/Tanggal:* {tanggal_indo(n['tanggal'])}
⏰ *Waktu Sesi:* {n['jam_mulai']} - {n['jam_selesai']} WIB
💵 *Total Biaya:* {rupiah(n['harga'])}
📌 *Status:* {n['status_booking']}
━━━━━━━━━━━━━━━━━━━━

📍 *Catatan untuk Pelanggan:*
• Mohon hadir di studio paling lambat 10 menit sebelum jam sesi dimulai.
• Jika ada request backdrop atau properti khusus, silakan konfirmasikan kepada kami.
• Tunjukkan pesan ini saat kedatangan di meja kasir/resepsionis KlikStudio.

Sampai jumpa di KlikStudio! ✨"""


def kartu_nota(n):
    e = html.escape
    nomor_antrean_val = n["nomor_antrean"] if n["nomor_antrean"] else "-"
    status_cls = {
        "Dikonfirmasi": "stamp-konfirmasi",
        "Selesai": "stamp-selesai",
        "Menunggu": "stamp-menunggu",
        "Dibatalkan": "stamp-batal"
    }.get(n["status_booking"], "stamp-menunggu")

    baris = [
        ("Nama Pelanggan", n["nama_pelanggan"]),
        ("Telepon / WhatsApp", n["no_hp"]),
        ("Paket Foto", f"{n['nama_paket']} ({n['durasi_menit']} menit)"),
        ("Tanggal Sesi", tanggal_indo(n["tanggal"])),
        ("Waktu Slot", f"{n['jam_mulai']} - {n['jam_selesai']} WIB"),
        ("Total Biaya", rupiah(n["harga"])),
        ("Status", f"<span class='vintage-stamp {status_cls}'>{n['status_booking']}</span>"),
        ("Petugas Studio", n["nama_admin"]),
    ]
    isi = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in baris)

    tampil_html(f"""
        <div class="vintage-ticket">
            <div class="vintage-ticket-header">
                <img class="logo-img" src="{LOGO_WORDMARK}" alt="KlikStudio">
                <div class="vintage-ticket-subtitle">Sistem Manajemen Studio Foto • Tiket Resmi</div>
            </div>
            <div class="vintage-queue-badge">
                <div class="vintage-queue-label">Nomor Antrean Sesi</div>
                <div class="vintage-queue-num">{nomor_antrean_val}</div>
            </div>
            <table class="vintage-ticket-table">
                {isi}
            </table>
            <div class="vintage-ticket-footer">
                Booking #{n['id_booking']} • Diterbitkan: {e(str(n['tanggal_terbit']))}<br>
                Harap tunjukkan nota ini kepada petugas saat sesi foto dimulai.
            </div>
        </div>
    """)


# ---------------------------------------------------------------------------
# Modul 1: Dashboard Studio (Halaman Utama)
# ---------------------------------------------------------------------------
def dashboard():
    hari_ini = date.today()
    tampil_html(f"""
        <div class="vintage-hero">
            <div class="badge-terminal">Portal Operasional Pengelola Studio</div>
            <img class="merek-logo" src="{LOGO_WORDMARK_PUTIH}" alt="KlikStudio">
            <p class="sub">Selamat bertugas, <b>{html.escape(PENGELOLA_AKTIF['nama_admin'])}</b>. Pantau sesi foto harian, ketersediaan slot waktu, dan catat booking pelanggan secara terpadu.</p>
            <div class="tanggal-row">
                📅 {HARI[hari_ini.weekday()]}, {hari_ini:%d-%m-%Y} • Studio Foto Buka & Siap Beroperasi
            </div>
        </div>
    """)

    # Ringkasan KPI
    r = db.ringkasan()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Booking Hari Ini", r["booking_hari_ini"])
    c2.metric("Slot Kosong Hari Ini", r["slot_kosong"])
    c3.metric("Menunggu Konfirmasi", r["per_status"]["Menunggu"])
    c4.metric("Total Pendapatan (Selesai)", rupiah(r["pendapatan"]))

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    # Aksi Cepat Pengelola
    st.markdown("### ⚡ Aksi Cepat Pengelola")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("➕ Catat Booking Baru", use_container_width=True, type="primary"):
            st.session_state["halaman_terpilih"] = "✍️ Catat Booking Baru"
            st.rerun()
    with col_b:
        if st.button("🗓️ Buka Jadwal Operasional", use_container_width=True):
            st.session_state["halaman_terpilih"] = "🗓️ Jadwal & Slot Studio"
            st.rerun()
    with col_c:
        if st.button("🎟️ Lihat Nota & Antrean", use_container_width=True):
            st.session_state["halaman_terpilih"] = "🎟️ Nota & Karcis Antrean"
            st.rerun()

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Tabel Booking Hari Ini
    st.markdown("### 📋 Jadwal Sesi Booking Hari Ini")
    booking_hari_ini = db.daftar_booking(tanggal=hari_ini)
    tabel(booking_hari_ini, KOLOM_BOOKING, "Belum ada booking yang terjadwal untuk hari ini. Gunakan menu Catat Booking Baru.")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Kolom Bawah: Slot Kosong & Grafik Status
    kiri, kanan = st.columns([3, 2])
    with kiri:
        st.markdown("### 🕒 Slot Kosong Hari Ini")
        slot = [s for s in db.daftar_slot_tersedia(0, hari_ini) if s["tanggal"] == hari_ini.isoformat()]
        tabel(
            slot,
            [
                ("Jam Mulai", lambda s: s["jam_mulai"]),
                ("Jam Selesai", lambda s: s["jam_selesai"]),
                ("Durasi Sesi", lambda s: f"{s['durasi_menit']} menit"),
                ("Status", lambda s: IKON_SLOT[s["status_slot"]]),
            ],
            "Tidak ada slot kosong yang tersedia hari ini. Anda dapat menambah slot di menu Jadwal & Slot Studio."
        )

    with kanan:
        st.markdown("### 📊 Distribusi Status Booking")
        st.bar_chart(
            {"Status": list(r["per_status"]), "Jumlah": list(r["per_status"].values())},
            x="Status",
            y="Jumlah",
            color="#B85D19"
        )


# ---------------------------------------------------------------------------
# Modul 2: Catat Booking Baru (Pencatatan oleh Pengelola untuk Pelanggan)
# ---------------------------------------------------------------------------
def halaman_catat_booking():
    judul_halaman(
        "Catat Booking Baru",
        "Formulir khusus pengelola studio untuk mencatat reservasi sesi foto atas nama pelanggan."
    )

    paket = db.daftar_paket()
    if not paket:
        st.warning("⚠️ Belum ada paket foto yang terdaftar. Tambahkan paket terlebih dahulu di menu Paket Foto.")
        return

    n = st.session_state.setdefault("booking_seq", 0)

    st.markdown("#### 1. Data Kontak Pelanggan")
    c1, c2, c3 = st.columns(3)
    nama = c1.text_input("Nama Lengkap Pelanggan *", placeholder="Contoh: Budi Santoso", key=f"in_nama_{n}")
    no_hp = c2.text_input("Nomor Telepon / WhatsApp *", placeholder="Contoh: 081234567890", key=f"in_hp_{n}")
    email = c3.text_input("Alamat Email (Opsional)", placeholder="Contoh: budi@gmail.com", key=f"in_email_{n}")

    lama = db.cari_pelanggan_hp(no_hp)
    if lama:
        st.info(f"💡 Nomor ini sudah terdaftar atas nama **{lama['nama_pelanggan']}**. Booking baru akan otomatis ditautkan ke akun pelanggan ini.")

    st.markdown("#### 2. Paket & Waktu Sesi Foto")
    col_pk, col_tgl, col_slot = st.columns([1.2, 1, 1.2])

    with col_pk:
        pk = pilih_record(
            paket,
            "id_paket",
            lambda r: f"{r['nama_paket']} ({r['durasi_menit']} mnt) - {rupiah(r['harga'])}",
            "Pilih Paket Foto *",
            f"in_paket_{n}"
        )

    slot_tersedia = db.daftar_slot_tersedia(pk["durasi_menit"])
    if not slot_tersedia:
        st.error(f"❌ Tidak ada slot waktu kosong yang cukup untuk durasi paket '{pk['nama_paket']}' ({pk['durasi_menit']} menit). Buka tanggal atau tambah slot di menu Jadwal & Slot Studio.")
        return

    tanggal_opsi = sorted({s["tanggal"] for s in slot_tersedia})
    with col_tgl:
        tanggal = st.selectbox(
            "Pilih Tanggal Sesi *",
            tanggal_opsi,
            format_func=tanggal_indo,
            key=f"in_tgl_{n}"
        )

    with col_slot:
        slot_hari = [x for x in slot_tersedia if x["tanggal"] == tanggal]
        s = pilih_record(
            slot_hari,
            "id_jadwal",
            lambda r: f"{r['jam_mulai']} - {r['jam_selesai']} WIB ({r['durasi_menit']} menit)",
            "Pilih Jam Slot Tersedia *",
            f"in_slot_{n}_{tanggal}"
        )

    st.markdown("#### 3. Catatan & Permintaan Khusus")
    catatan = st.text_area(
        "Catatan Sesi (Opsional)",
        placeholder="Contoh: Permintaan tema vintage, bawa 2 kostum, 3 orang anggota keluarga...",
        key=f"in_catatan_{n}"
    )

    # Ringkasan Pesanan Box
    st.markdown(f"""
        <div class="vintage-card" style="border-left: 5px solid #C8963E;">
            <div style="font-size: 0.82rem; font-weight: 700; color: #7A5726; letter-spacing: 0.08em; text-transform: uppercase;">Konfirmasi Rincian Pemesanan</div>
            <div style="font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: #241E1C; margin: 0.3rem 0;">
                {html.escape(pk['nama_paket'])} • {rupiah(pk['harga'])}
            </div>
            <div style="font-size: 0.92rem; color: #554D46;">
                📅 <b>{tanggal_indo(tanggal)}</b> &nbsp;|&nbsp; 🕒 <b>{s['jam_mulai']} - {s['jam_selesai']} WIB</b> &nbsp;|&nbsp; ⏳ Durasi: <b>{pk['durasi_menit']} menit</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

    b1, b2 = st.columns(2)
    with b1:
        simpan = st.button("💾 Simpan Booking (Status: Menunggu)", key=f"btn_simpan_{n}", use_container_width=True)
    with b2:
        konfirmasi = st.button("⭐ Simpan & Konfirmasi Langsung (Terbitkan Nota & No. Antrean)", type="primary", key=f"btn_konfirm_{n}", use_container_width=True)

    if simpan or konfirmasi:
        try:
            hasil = db.buat_booking(
                PENGELOLA_AKTIF["id_admin"],
                nama,
                no_hp,
                pk["id_paket"],
                s["id_jadwal"],
                catatan,
                email,
                konfirmasi=konfirmasi
            )
            st.session_state["booking_seq"] = n + 1
            if konfirmasi:
                selesai(f"✅ Booking #{hasil['id_booking']} berhasil dicatat & Dikonfirmasi! Nomor Antrean: {hasil['nomor_antrean']}. Nota siap di menu Nota & Karcis Antrean.")
            else:
                selesai(f"✅ Booking #{hasil['id_booking']} berhasil dicatat dengan status Menunggu. Konfirmasi dapat dilakukan di menu Kelola & Riwayat Booking.")
        except (ValueError, sqlite3.IntegrityError) as exc:
            tampil_error(exc)


# ---------------------------------------------------------------------------
# Modul 3: Kelola & Riwayat Booking
# ---------------------------------------------------------------------------
def aksi_status(b):
    if b["status_booking"] not in db.STATUS_BOOKING_AKTIF:
        st.info(f"Booking #{b['id_booking']} berstatus final ({b['status_booking']}) dan tidak dapat diubah lagi.")
        return

    opsi = ["Dikonfirmasi", "Dibatalkan"] if b["status_booking"] == "Menunggu" else ["Selesai", "Dibatalkan"]
    baru = st.selectbox("Perbarui Status Menjadi:", opsi, key=f"st_baru_{b['id_booking']}")

    if baru == "Dibatalkan":
        st.caption("⚠️ Membatalkan booking akan mengembalikan slot waktu menjadi 'Tersedia' kembali.")
    if baru == "Dikonfirmasi":
        st.caption("ℹ️ Konfirmasi akan menetapkan nomor antrean resmi dan menerbitkan nota.")

    if st.button("Simpan Perubahan Status", type="primary", key=f"btn_st_{b['id_booking']}"):
        try:
            hasil = db.ubah_status_booking(b["id_booking"], baru)
            if baru == "Dikonfirmasi":
                selesai(f"Booking #{b['id_booking']} berhasil Dikonfirmasi dengan Nomor Antrean {hasil}!")
            selesai(f"Status booking #{b['id_booking']} berhasil diubah menjadi {baru}.")
        except (ValueError, sqlite3.IntegrityError) as exc:
            tampil_error(exc)


def aksi_edit(b):
    if b["status_booking"] not in db.STATUS_BOOKING_AKTIF:
        st.info("Hanya booking yang masih aktif (Menunggu atau Dikonfirmasi) yang dapat diedit.")
        return

    panjang = db.ke_menit(b["jam_selesai"]) - db.ke_menit(b["jam_mulai"])
    paket = [x for x in db.daftar_paket() if x["durasi_menit"] <= panjang]
    ids = [x["id_paket"] for x in paket]
    info = {x["id_paket"]: x for x in paket}
    idx = ids.index(b["id_paket"]) if b["id_paket"] in ids else 0
    kunci = b["id_booking"]

    with st.form(f"form_edit_bk_{kunci}"):
        c1, c2 = st.columns(2)
        nama = c1.text_input("Nama Pelanggan", value=b["nama_pelanggan"], key=f"ed_nama_{kunci}")
        no_hp = c2.text_input("Nomor Telepon / WA", value=b["no_hp"], key=f"ed_hp_{kunci}")
        pk = st.selectbox(
            "Paket Foto",
            ids,
            index=idx,
            format_func=lambda i: f"{info[i]['nama_paket']} ({info[i]['durasi_menit']} mnt) - {rupiah(info[i]['harga'])}",
            key=f"ed_pk_{kunci}"
        )
        catatan = st.text_area("Catatan Sesi", value=b["catatan"], key=f"ed_catatan_{kunci}")
        simpan = st.form_submit_button("Simpan Perubahan Booking")

    if simpan:
        try:
            db.ubah_booking(kunci, nama, no_hp, pk, catatan)
            selesai(f"Data booking #{kunci} berhasil diperbarui.")
        except (ValueError, sqlite3.IntegrityError) as exc:
            tampil_error(exc)


def halaman_riwayat_booking():
    judul_halaman(
        "Kelola & Riwayat Booking",
        "Pencarian, pemfilteran, perubahan status, dan pengelolaan data booking pelanggan studio."
    )

    c1, c2, c3 = st.columns([1.2, 1.2, 2])
    status = c1.selectbox("Filter Status", ["Semua"] + list(db.STATUS_BOOKING), key="filter_status")
    pakai_tgl = c2.checkbox("Filter Tanggal Tertentu", key="filter_tgl_aktif")
    tanggal = c2.date_input("Tanggal", value=date.today(), key="filter_tgl_val", disabled=not pakai_tgl)
    cari = c3.text_input("🔍 Cari Nama atau Nomor Telepon", key="filter_cari", placeholder="Ketik kata kunci...")

    rows = db.daftar_booking(
        status=None if status == "Semua" else status,
        tanggal=tanggal if pakai_tgl else None,
        cari=cari
    )

    tabel(
        rows,
        KOLOM_BOOKING + [
            ("Catatan", lambda r: r["catatan"] or "-"),
        ],
        "Tidak ada data booking yang sesuai dengan kriteria pencarian."
    )

    if not rows:
        return

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Tindakan pada Booking")

    b = pilih_record(
        rows,
        "id_booking",
        lambda r: f"#{r['id_booking']} • {r['nama_pelanggan']} • {tanggal_indo(r['tanggal'])} {r['jam_mulai']} • [{r['status_booking']}]",
        "Pilih Booking yang Ingin Dikelola",
        "pilih_kelola_bk"
    )

    aksi = st.radio(
        "Pilih Jenis Tindakan:",
        ["Ubah Status", "Edit Data Booking", "Hapus Booking"],
        horizontal=True,
        key="radio_aksi_bk"
    )

    if aksi == "Ubah Status":
        aksi_status(b)
    elif aksi == "Edit Data Booking":
        aksi_edit(b)
    else:
        blok_hapus(
            f"Booking #{b['id_booking']} atas nama {b['nama_pelanggan']} ({b['nama_paket']})",
            f"del_bk_{b['id_booking']}",
            lambda: db.hapus_booking(b["id_booking"]),
            f"Booking #{b['id_booking']} beserta notanya berhasil dihapus."
        )


# ---------------------------------------------------------------------------
# Modul 4: Nota & Karcis Antrean
# ---------------------------------------------------------------------------
def halaman_nota():
    judul_halaman(
        "Nota & Karcis Antrean",
        "Penerbitan, pratinjau tiket vintage, salin format pesan WhatsApp pelanggan, dan unduh berkas nota resmi."
    )

    rows = db.daftar_nota()
    if not rows:
        st.info("ℹ️ Belum ada nota antrean yang terbit. Nota diterbitkan otomatis saat booking dikonfirmasi.")
        return

    n = pilih_record(
        rows,
        "id_booking",
        lambda r: f"Antrean #{r['nomor_antrean']} • Booking #{r['id_booking']} • {r['nama_pelanggan']} ({tanggal_indo(r['tanggal'])})",
        "Pilih Nota Antrean",
        "pilih_nota_view"
    )

    col_view, col_action = st.columns([1.2, 1])

    with col_view:
        kartu_nota(n)

    with col_action:
        st.markdown("#### 📤 Pengiriman & Berkas Nota")
        st.caption("Gunakan format pesan berikut untuk dikirimkan langsung ke pelanggan via WhatsApp atau SMS:")

        pesan_wa = format_pesan_wa(n)
        st.text_area("Teks Pesan WhatsApp (Siap Salin)", value=pesan_wa, height=260, key=f"wa_txt_{n['id_booking']}")

        st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)
        st.download_button(
            "📥 Unduh Nota Digital (.txt)",
            teks_nota(n),
            file_name=f"nota_klikstudio_{n['id_booking']}.txt",
            mime="text/plain",
            use_container_width=True,
            key=f"dl_nota_{n['id_booking']}"
        )


# ---------------------------------------------------------------------------
# Modul 5: Kelola Jadwal & Slot Studio
# ---------------------------------------------------------------------------
def tab_buka_jadwal():
    st.markdown("#### Buka Tanggal Operasional Studio")
    with st.form("form_buka_jadwal"):
        c1, c2, c3 = st.columns(3)
        tanggal = c1.date_input("Tanggal Operasional", value=date.today(), min_value=date.today(), key="jadwal_tgl")
        buka = c2.time_input("Jam Buka Studio", value=time(9, 0), step=900, key="jadwal_buka")
        tutup = c3.time_input("Jam Tutup Studio", value=time(17, 0), step=900, key="jadwal_tutup")

        c4, c5 = st.columns(2)
        durasi = c4.selectbox("Durasi per Sesi Slot (Menit)", [15, 30, 45, 60, 90, 120], index=1, key="jadwal_durasi")
        jeda = c5.selectbox("Jeda Istirahat Antar Slot (Menit)", [0, 5, 10, 15], key="jadwal_jeda")

        submit = st.form_submit_button("Buat Jadwal Operasional Otomatis", type="primary")

    if submit:
        try:
            jumlah = db.buat_jadwal_operasional(
                PENGELOLA_AKTIF["id_admin"],
                tanggal,
                buka,
                tutup,
                durasi,
                jeda
            )
            selesai(f"Berhasil membuat {jumlah} slot waktu untuk tanggal {tanggal_indo(tanggal.isoformat())}.")
        except (ValueError, sqlite3.IntegrityError) as exc:
            tampil_error(exc)


def tab_kontrol_slot():
    ringkas = db.daftar_tanggal()
    st.markdown("#### Ringkasan Tanggal Operasional")
    tabel(
        ringkas,
        [
            ("Tanggal", lambda r: tanggal_indo(r["tanggal"])),
            ("Status", lambda r: ("🟢 Buka" if r["status_operasional"] == "Buka" else "⚫ Tutup")),
            ("Jam Buka", lambda r: r["jam_buka"]),
            ("Jam Tutup", lambda r: r["jam_tutup"]),
            ("Total Slot", lambda r: r["jumlah_slot"]),
            ("Tersedia", lambda r: r["tersedia"]),
            ("Terpesan", lambda r: r["terpesan"]),
            ("Nonaktif", lambda r: r["nonaktif"]),
        ],
        "Belum ada tanggal operasional yang dibuka."
    )

    if not ringkas:
        return

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("#### Pengaturan Slot per Tanggal")

    opsi = sorted(r["tanggal"] for r in ringkas)
    awal = next((i for i, t in enumerate(opsi) if t >= date.today().isoformat()), len(opsi) - 1)
    tanggal_pilih = st.selectbox("Pilih Tanggal:", opsi, index=awal, format_func=tanggal_indo, key="sel_tgl_slot")

    r = next(x for x in ringkas if x["tanggal"] == tanggal_pilih)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Slot", r["jumlah_slot"])
    m2.metric("Slot Tersedia", r["tersedia"])
    m3.metric("Slot Terpesan", r["terpesan"])
    m4.metric("Nonaktif", r["nonaktif"])

    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("Tutup Studio pada Tanggal Ini (Nonaktifkan Slot Kosong)", disabled=r["tersedia"] == 0, key=f"btn_tutup_{tanggal_pilih}"):
        n = db.atur_status_tanggal(tanggal_pilih, "Nonaktif")
        selesai(f"{n} slot ditandai tidak tersedia. Slot yang sudah terpesan tetap aman.")

    if col_btn2.button("Buka Kembali Studio pada Tanggal Ini", disabled=r["nonaktif"] == 0, key=f"btn_buka_{tanggal_pilih}"):
        n = db.atur_status_tanggal(tanggal_pilih, "Tersedia")
        selesai(f"{n} slot berhasil dibuka dan tersedia kembali.")

    slot_list = db.daftar_slot(tanggal_pilih)
    st.markdown("##### Daftar Slot pada Tanggal Ini")
    tabel(
        slot_list,
        [
            ("Jam Mulai", lambda s: s["jam_mulai"]),
            ("Jam Selesai", lambda s: s["jam_selesai"]),
            ("Durasi", lambda s: f"{s['durasi_menit']} mnt"),
            ("Status", lambda s: IKON_SLOT[s["status_slot"]]),
            ("Pemesan", lambda s: s["nama_pelanggan"] or "-"),
        ]
    )

    with st.expander("➕ Tambah Slot Waktu Manual"):
        with st.form(f"form_manual_{tanggal_pilih}"):
            ca, cb = st.columns(2)
            mulai = ca.time_input("Jam Mulai", value=time(9, 0), step=900, key=f"man_mulai_{tanggal_pilih}")
            akhir = cb.time_input("Jam Selesai", value=time(9, 30), step=900, key=f"man_akhir_{tanggal_pilih}")
            tambah = st.form_submit_button("Tambah Slot Ini")
        if tambah:
            try:
                db.tambah_slot(PENGELOLA_AKTIF["id_admin"], tanggal_pilih, mulai, akhir)
                selesai("Slot manual berhasil ditambahkan.")
            except (ValueError, sqlite3.IntegrityError) as exc:
                tampil_error(exc)

    if slot_list:
        with st.expander("🛠️ Ubah Status / Hapus Satu Slot"):
            s_pilih = pilih_record(
                slot_list,
                "id_jadwal",
                lambda x: f"{x['jam_mulai']} - {x['jam_selesai']} WIB ({x['status_slot']})",
                "Pilih Slot:",
                f"sel_satuan_{tanggal_pilih}"
            )
            kunci_s = s_pilih["id_jadwal"]
            terpesan = s_pilih["status_slot"] == "Terpesan"
            tersedia = s_pilih["status_slot"] == "Tersedia"

            c_act1, c_act2 = st.columns(2)
            with c_act1:
                label_btn = "Tandai Tidak Tersedia" if tersedia else "Tandai Tersedia"
                if st.button(label_btn, disabled=terpesan, key=f"tgl_btn_{kunci_s}"):
                    try:
                        db.ubah_status_slot(kunci_s, "Nonaktif" if tersedia else "Tersedia")
                        selesai("Status ketersediaan slot diperbarui.")
                    except (ValueError, sqlite3.IntegrityError) as exc:
                        tampil_error(exc)
            with c_act2:
                blok_hapus(
                    f"Slot {s_pilih['jam_mulai']} - {s_pilih['jam_selesai']}",
                    f"del_slot_{kunci_s}",
                    lambda: db.hapus_slot(kunci_s),
                    "Slot berhasil dihapus."
                )

    with st.expander("🗑️ Hapus Seluruh Tanggal Operasional"):
        blok_hapus(
            f"Seluruh slot pada tanggal {tanggal_indo(tanggal_pilih)}",
            f"del_tgl_{tanggal_pilih}",
            lambda: db.hapus_tanggal(tanggal_pilih),
            "Tanggal operasional berhasil dihapus."
        )


def halaman_kelola_jadwal():
    judul_halaman(
        "Jadwal & Slot Studio",
        "Pengaturan tanggal operasional studio, jam buka-tutup, dan ketersediaan slot sesi foto."
    )
    tab1, tab2 = st.tabs(["🗓️ Buka Jadwal Operasional", "⚙️ Kontrol & Kelola Slot"])
    with tab1:
        tab_buka_jadwal()
    with tab2:
        tab_kontrol_slot()


# ---------------------------------------------------------------------------
# Modul 6: Paket Foto
# ---------------------------------------------------------------------------
def form_paket(row=None):
    identitas = row["id_paket"] if row else "baru"
    prefix = f"pk_form_{identitas}"
    nilai = row or {"nama_paket": "", "durasi_menit": 30, "harga": 75000, "deskripsi": ""}

    with st.form(f"form_{prefix}"):
        c1, c2, c3 = st.columns([2, 1, 1])
        nama = c1.text_input("Nama Paket Foto *", value=nilai["nama_paket"], placeholder="Contoh: Portrait Vintage", key=f"{prefix}_nama")
        durasi = c2.number_input("Durasi Sesi (Menit) *", min_value=5, value=int(nilai["durasi_menit"]), step=5, key=f"{prefix}_durasi")
        harga = c3.number_input("Harga Paket (Rp) *", min_value=0, value=int(nilai["harga"]), step=5000, key=f"{prefix}_harga")
        deskripsi = st.text_area("Deskripsi Paket & Fasilitas", value=nilai["deskripsi"], placeholder="Contoh: Termasuk 10 file cetak, 1 wardrobe, background klasik...", key=f"{prefix}_desc")
        simpan = st.form_submit_button("Simpan Paket Foto", type="primary")

    if simpan:
        try:
            args = (nama, int(durasi), int(harga), deskripsi)
            if row:
                db.ubah_paket(row["id_paket"], *args)
            else:
                db.tambah_paket(*args)
            selesai("Paket foto berhasil disimpan.")
        except (ValueError, sqlite3.IntegrityError) as exc:
            tampil_error(exc)


def halaman_paket():
    judul_halaman(
        "Katalog & Manajemen Paket Foto",
        "Daftar paket sesi foto studio, tarif, durasi, serta penambahan dan pengubahan paket."
    )

    tab_lihat, tab_tambah, tab_kelola = st.tabs(["🏷️ Katalog Paket", "➕ Tambah Paket Baru", "🛠️ Edit / Hapus Paket"])

    paket_list = db.daftar_paket()

    with tab_lihat:
        if not paket_list:
            st.info("Belum ada paket foto yang didaftarkan.")
        else:
            # Tampilan Grid Kartu Vintage
            cols = st.columns(3)
            for i, p in enumerate(paket_list):
                with cols[i % 3]:
                    st.markdown(f"""
                        <div class="paket-card">
                            <div class="paket-nama">{html.escape(p['nama_paket'])}</div>
                            <div class="paket-harga">{rupiah(p['harga'])}</div>
                            <div class="paket-durasi">⏱️ Durasi: {p['durasi_menit']} menit</div>
                            <div class="paket-desc">{html.escape(p['deskripsi']) if p['deskripsi'] else 'Layanan foto profesional studio.'}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            st.markdown("##### Tabel Data Paket")
            tabel(
                paket_list,
                [
                    ("ID", lambda r: r["id_paket"]),
                    ("Nama Paket", lambda r: r["nama_paket"]),
                    ("Durasi", lambda r: f"{r['durasi_menit']} menit"),
                    ("Harga", lambda r: rupiah(r["harga"])),
                    ("Deskripsi", lambda r: r["deskripsi"] or "-"),
                ]
            )

    with tab_tambah:
        st.markdown("#### Tambah Paket Foto Baru")
        form_paket()

    with tab_kelola:
        if not paket_list:
            st.info("Belum ada paket untuk diedit atau dihapus.")
        else:
            st.markdown("#### Edit atau Hapus Paket Foto")
            aksi = st.radio("Tindakan:", ["Edit Data Paket", "Hapus Paket"], horizontal=True, key="aksi_pk_ops")
            p_terpilih = pilih_record(
                paket_list,
                "id_paket",
                lambda r: f"{r['nama_paket']} ({r['durasi_menit']} mnt) - {rupiah(r['harga'])}",
                "Pilih Paket:",
                "pilih_pk_edit_del"
            )
            if aksi == "Edit Data Paket":
                form_paket(p_terpilih)
            else:
                blok_hapus(
                    f"Paket {p_terpilih['nama_paket']}",
                    f"del_pk_{p_terpilih['id_paket']}",
                    lambda: db.hapus_paket(p_terpilih["id_paket"]),
                    "Paket foto berhasil dihapus."
                )


# ---------------------------------------------------------------------------
# Modul 7: Direktori Pelanggan
# ---------------------------------------------------------------------------
def halaman_pelanggan():
    judul_halaman(
        "Direktori Pelanggan",
        "Daftar pelanggan studio yang pernah melakukan booking, riwayat kontak, dan statistik kunjungan."
    )

    cari = st.text_input("🔍 Cari Pelanggan berdasarkan Nama atau Nomor HP:", placeholder="Ketik nama atau nomor...", key="cari_cust")
    pelanggan = db.daftar_pelanggan(cari)

    tabel(
        pelanggan,
        [
            ("ID", lambda r: f"#{r['id_pelanggan']}"),
            ("Nama Pelanggan", lambda r: r["nama_pelanggan"]),
            ("No. Telepon / WA", lambda r: r["no_hp"]),
            ("Email", lambda r: r["email"] or "-"),
            ("Total Booking", lambda r: f"{r.get('total_booking', 0)} kali"),
            ("Terdaftar Pada", lambda r: r["created_at"]),
        ],
        "Belum ada data pelanggan yang sesuai."
    )


# ---------------------------------------------------------------------------
# Navigasi Aplikasi (Langsung Akses ke Halaman Utama Tanpa Login)
# ---------------------------------------------------------------------------
HALAMAN = {
    "📊 Dashboard": dashboard,
    "✍️ Catat Booking Baru": halaman_catat_booking,
    "📋 Kelola & Riwayat Booking": halaman_riwayat_booking,
    "🎟️ Nota & Karcis Antrean": halaman_nota,
    "🗓️ Jadwal & Slot Studio": halaman_kelola_jadwal,
    "🏷️ Paket Foto": halaman_paket,
    "👥 Direktori Pelanggan": halaman_pelanggan,
}

# Sidebar Brand & Info Pengelola
st.sidebar.markdown(f"""
    <div class="sidebar-brand">
        <div class="brand-header">
            <img src="{LOGO_KAMERA}" class="brand-logo" alt="KlikStudio">
            <span class="brand-name">KLIKSTUDIO</span>
        </div>
        <div class="brand-tag">PORTAL OPERATOR & KASIR</div>
    </div>
""", unsafe_allow_html=True)

# Pesan flash notifikasi sukses
if "pesan_sukses" in st.session_state:
    st.success(st.session_state.pop("pesan_sukses"))

# Navigasi Halaman
halaman_default = st.session_state.get("halaman_terpilih", "📊 Dashboard")
pilihan_keys = list(HALAMAN.keys())
index_default = pilihan_keys.index(halaman_default) if halaman_default in pilihan_keys else 0

menu = st.sidebar.radio(
    "Menu Navigasi",
    pilihan_keys,
    index=index_default,
    key="nav_menu"
)
st.session_state["halaman_terpilih"] = menu

st.sidebar.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
st.sidebar.markdown(f"""
    <div style="background: #EAE2D5; padding: 0.8rem 1rem; border-radius: 6px; border: 1px solid #D5C9B7; font-size: 0.82rem; color: #5B5045;">
        <b>Petugas Aktif:</b><br>
        👤 {html.escape(PENGELOLA_AKTIF['nama_admin'])}<br>
        <span style="font-size: 0.76rem; color: #7A6F65;">Mode Operasional Studio Aktif</span>
    </div>
""", unsafe_allow_html=True)

# Eksekusi Tampilan Halaman yang Dipilih
HALAMAN[menu]()
