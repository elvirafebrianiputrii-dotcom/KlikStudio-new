"""Jalankan sekali pada database latihan kosong untuk mengisi data contoh."""
from datetime import date, timedelta

import database as db

db.init_db()
if db.daftar_paket() or db.daftar_tanggal() or db.daftar_booking():
    print("Database sudah berisi data. Tidak ada data yang diubah.")
else:
    pengelola = db.dapatkan_pengelola()
    id_admin = pengelola["id_admin"]

    pas = db.tambah_paket(
        "Pas Foto", 15, 35000, "Pas foto 3x4 dan 4x6, 4 lembar cetak.")
    self_photo = db.tambah_paket(
        "Self Photo", 30, 75000, "Foto mandiri 1-2 orang, 10 foto edit.")
    db.tambah_paket(
        "Family Session", 60, 250000, "Foto keluarga hingga 6 orang.")

    hari_ini = date.today()
    db.buat_jadwal_operasional(id_admin, hari_ini, "09:00", "17:00", 30)
    db.buat_jadwal_operasional(
        id_admin, hari_ini + timedelta(days=1), "09:00", "17:00", 60)
    db.buat_jadwal_operasional(
        id_admin, hari_ini + timedelta(days=2), "10:00", "16:00", 30, 10)

    slot = db.daftar_slot_tersedia(0, hari_ini)
    slot_hari_ini = [s for s in slot if s["tanggal"] == hari_ini.isoformat()]
    db.buat_booking(id_admin, "Budi Santoso", "081234567801", self_photo,
                    slot_hari_ini[0]["id_jadwal"],
                    "Foto untuk keperluan CV.", "budi@contoh.id",
                    konfirmasi=True)
    db.buat_booking(id_admin, "Sari Lestari", "081234567802", pas,
                    slot_hari_ini[1]["id_jadwal"])
    print("Tiga paket, tiga tanggal operasional, dan dua booking contoh "
          "berhasil ditambahkan.")