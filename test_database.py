"""Pengujian otomatis operasi database KLIKSTUDIO (file sementara)."""
from datetime import date, timedelta
from pathlib import Path
import sqlite3
import tempfile
import unittest

import database as db


class TesDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lama = db.DB_PATH
        db.DB_PATH = Path(self.tmp.name) / "uji.db"
        db.init_db()
        self.admin = db.login("admin", "admin123")["id_admin"]
        self.paket = db.tambah_paket("Self Photo", 30, 75000, "x")
        self.hari = date.today()
        db.buat_jadwal_operasional(
            self.admin, self.hari, "09:00", "11:00", 30)
        self.slot = db.daftar_slot_tersedia()[0]["id_jadwal"]

    def tearDown(self):
        db.DB_PATH = self.lama
        self.tmp.cleanup()

    def pesan(self, **kw):
        data = dict(nama="Budi", no_hp="081234567801", id_paket=self.paket,
                    id_jadwal=self.slot)
        data.update(kw)
        return db.buat_booking(self.admin, **data)

    def test_login_dan_password(self):
        self.assertIsNone(db.login("admin", "salah"))
        self.assertIsNotNone(db.login("ADMIN", "admin123"))
        db.ubah_password(self.admin, "admin123", "rahasia1")
        self.assertIsNotNone(db.login("admin", "rahasia1"))

    def test_validasi_dan_duplikat(self):
        with self.assertRaises(ValueError):
            db.tambah_paket("  ", 30, 1000)
        with self.assertRaises(ValueError):
            db.tambah_paket("Baru", 0, 1000)
        with self.assertRaises(sqlite3.IntegrityError):
            db.tambah_paket("self photo", 30, 1000)
        with self.assertRaises(ValueError):
            self.pesan(nama=" ")
        with self.assertRaises(ValueError):
            self.pesan(no_hp="abc")

    def test_operasional_dan_bentrok(self):
        self.assertEqual(len(db.daftar_slot(self.hari)), 4)
        with self.assertRaises(ValueError):
            db.tambah_slot(self.admin, self.hari, "09:15", "09:45")
        with self.assertRaises(ValueError):
            db.buat_jadwal_operasional(
                self.admin, self.hari - timedelta(days=1),
                "09:00", "10:00", 30)
        ring = db.daftar_tanggal()[0]
        self.assertEqual((ring["jumlah_slot"], ring["status_operasional"]),
                         (4, "Buka"))

    def test_booking_menunggu_lalu_konfirmasi(self):
        h = self.pesan()
        self.assertIsNone(h["nomor_antrean"])
        self.assertTrue(h["pelanggan_baru"])
        self.assertEqual(db.daftar_nota(), [])
        self.assertEqual(db.konfirmasi_booking(h["id_booking"]), 1)
        self.assertEqual(len(db.daftar_nota()), 1)
        with self.assertRaises(ValueError):
            db.konfirmasi_booking(h["id_booking"])

    def test_slot_tidak_bisa_dipesan_dua_kali(self):
        self.pesan()
        with self.assertRaises(ValueError):
            self.pesan(nama="Lain", no_hp="081234567802")

    def test_pelanggan_dipakai_ulang(self):
        self.pesan()
        slot2 = db.daftar_slot_tersedia()[0]["id_jadwal"]
        h = self.pesan(id_jadwal=slot2, nama="Budi S")
        self.assertFalse(h["pelanggan_baru"])
        self.assertEqual(len(db.daftar_pelanggan()), 1)

    def test_pembatalan_melepas_slot(self):
        h = self.pesan(konfirmasi=True)
        self.assertEqual(len(db.daftar_slot_tersedia()), 3)
        db.ubah_status_booking(h["id_booking"], "Dibatalkan")
        self.assertEqual(len(db.daftar_slot_tersedia()), 4)
        with self.assertRaises(ValueError):
            db.ubah_status_booking(h["id_booking"], "Selesai")

    def test_selesai_perlu_konfirmasi(self):
        h = self.pesan()
        with self.assertRaises(ValueError):
            db.ubah_status_booking(h["id_booking"], "Selesai")
        db.konfirmasi_booking(h["id_booking"])
        db.ubah_status_booking(h["id_booking"], "Selesai")
        self.assertEqual(db.ringkasan()["pendapatan"], 75000)

    def test_durasi_paket_melebihi_slot(self):
        panjang = db.tambah_paket("Family", 60, 250000)
        with self.assertRaises(ValueError):
            self.pesan(id_paket=panjang)

    def test_relasi_dilindungi(self):
        self.pesan()
        with self.assertRaises(sqlite3.IntegrityError):
            db.hapus_paket(self.paket)
        with self.assertRaises(sqlite3.IntegrityError):
            db.hapus_slot(self.slot)
        with self.assertRaises(ValueError):
            db.hapus_tanggal(self.hari)

    def test_tutup_dan_buka_tanggal(self):
        self.pesan()
        self.assertEqual(db.atur_status_tanggal(self.hari, "Nonaktif"), 3)
        self.assertEqual(db.daftar_slot_tersedia(), [])
        self.assertEqual(db.atur_status_tanggal(self.hari, "Tersedia"), 3)
        with self.assertRaises(ValueError):
            db.ubah_status_slot(self.slot, "Nonaktif")

    def test_hapus_booking_melepas_slot(self):
        h = self.pesan(konfirmasi=True)
        db.hapus_booking(h["id_booking"])
        self.assertEqual(db.daftar_nota(), [])
        self.assertEqual(len(db.daftar_slot_tersedia()), 4)

    def test_nomor_antrean_per_tanggal(self):
        besok = self.hari + timedelta(days=1)
        db.buat_jadwal_operasional(self.admin, besok, "09:00", "10:00", 30)
        self.assertEqual(self.pesan(konfirmasi=True)["nomor_antrean"], 1)
        slot2 = db.daftar_slot_tersedia()[0]["id_jadwal"]
        self.assertEqual(self.pesan(id_jadwal=slot2, konfirmasi=True)
                         ["nomor_antrean"], 2)
        slot_besok = [s for s in db.daftar_slot_tersedia()
                      if s["tanggal"] == besok.isoformat()][0]["id_jadwal"]
        self.assertEqual(self.pesan(id_jadwal=slot_besok, konfirmasi=True)
                         ["nomor_antrean"], 1)

    def test_apostrof_aman(self):
        self.pesan(nama="Kertas O'Neil")
        self.assertEqual(db.daftar_pelanggan()[0]["nama_pelanggan"],
                         "Kertas O'Neil")


if __name__ == "__main__":
    unittest.main()