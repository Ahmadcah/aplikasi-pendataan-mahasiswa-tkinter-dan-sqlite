"""
Aplikasi Data Mahasiswa - Tkinter + SQLite
Praktikum: Membuat Aplikasi Penyimpanan Data Mahasiswa Berbasis Tkinter dan SQLite

Fitur:
  - Simpan (INSERT), tampil (SELECT), ubah (UPDATE), hapus (DELETE)
  - Validasi kolom wajib, NIM unik, angkatan harus 4 digit angka
  - Pencarian berdasarkan nama atau NIM (tugas pengembangan 1)
  - Kolom angkatan + migrasi database lama (tugas pengembangan 2)
"""
import sqlite3
import tkinter as tk
from contextlib import contextmanager
from tkinter import ttk, messagebox

DB_NAME = "mahasiswa.db"

DAFTAR_PRODI = ["Informatika", "Sistem Informasi", "Manajemen", "Akuntansi"]


# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------
@contextmanager
def koneksi():
    """Membuka koneksi, menyimpan perubahan, lalu selalu menutupnya."""
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def buat_tabel():
    """Membuat tabel jika belum ada, lalu memigrasi database lama
    yang belum memiliki kolom angkatan."""
    with koneksi() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mahasiswa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                nim TEXT NOT NULL UNIQUE,
                prodi TEXT NOT NULL,
                alamat TEXT,
                angkatan INTEGER
            )
        """)
        # Migrasi: database lama (tanpa angkatan) ditambah kolomnya,
        # data lama tetap aman dan angkatannya bernilai NULL.
        kolom_ada = [r[1] for r in conn.execute("PRAGMA table_info(mahasiswa)")]
        if "angkatan" not in kolom_ada:
            conn.execute("ALTER TABLE mahasiswa ADD COLUMN angkatan INTEGER")


buat_tabel()

# ---------------------------------------------------------------------------
# ANTARMUKA
# ---------------------------------------------------------------------------
root = tk.Tk()
root.title("Aplikasi Data Mahasiswa")
root.geometry("980x640")

# --- Formulir ---
form = ttk.LabelFrame(root, text="Formulir Mahasiswa", padding=12)
form.pack(fill="x", padx=15, pady=12)

ttk.Label(form, text="Nama").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_nama = ttk.Entry(form, width=30)
entry_nama.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(form, text="NIM").grid(row=0, column=2, padx=5, pady=5, sticky="w")
entry_nim = ttk.Entry(form, width=30)
entry_nim.grid(row=0, column=3, padx=5, pady=5)

ttk.Label(form, text="Program Studi").grid(row=1, column=0, padx=5, pady=5, sticky="w")
combo_prodi = ttk.Combobox(form, values=DAFTAR_PRODI, state="readonly", width=27)
combo_prodi.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(form, text="Alamat").grid(row=1, column=2, padx=5, pady=5, sticky="w")
entry_alamat = ttk.Entry(form, width=30)
entry_alamat.grid(row=1, column=3, padx=5, pady=5)

ttk.Label(form, text="Angkatan").grid(row=2, column=0, padx=5, pady=5, sticky="w")
entry_angkatan = ttk.Entry(form, width=30)
entry_angkatan.grid(row=2, column=1, padx=5, pady=5)

# --- Pencarian ---
cari_frame = ttk.LabelFrame(root, text="Pencarian (nama atau NIM)", padding=8)
cari_frame.pack(fill="x", padx=15, pady=(0, 6))

var_cari = tk.StringVar()
entry_cari = ttk.Entry(cari_frame, textvariable=var_cari, width=40)
entry_cari.pack(side="left", padx=5)

# --- Tabel (Treeview) ---
kolom = ("id", "nama", "nim", "prodi", "alamat", "angkatan")
tabel = ttk.Treeview(root, columns=kolom, show="headings")
for key, judul in [("id", "ID"), ("nama", "Nama"), ("nim", "NIM"),
                   ("prodi", "Program Studi"), ("alamat", "Alamat"),
                   ("angkatan", "Angkatan")]:
    tabel.heading(key, text=judul)
tabel.column("id", width=50, anchor="center")
tabel.column("nama", width=170)
tabel.column("nim", width=120)
tabel.column("prodi", width=150)
tabel.column("alamat", width=230)
tabel.column("angkatan", width=80, anchor="center")

scroll = ttk.Scrollbar(root, orient="vertical", command=tabel.yview)
tabel.configure(yscrollcommand=scroll.set)
# Tombol dipasang lebih dulu di bagian bawah agar selalu terlihat
baris_tombol = ttk.Frame(root)
baris_tombol.pack(side="bottom", fill="x", padx=15, pady=8)
scroll.pack(side="right", fill="y", padx=(0, 15), pady=8)
tabel.pack(fill="both", expand=True, padx=(15, 0), pady=8)


# ---------------------------------------------------------------------------
# LOGIKA
# ---------------------------------------------------------------------------
def tampilkan_data(kata_kunci=""):
    """SELECT semua data (atau yang cocok dengan kata kunci) ke Treeview."""
    for item in tabel.get_children():
        tabel.delete(item)
    kata_kunci = kata_kunci.strip()
    with koneksi() as conn:
        if kata_kunci:
            pola = f"%{kata_kunci}%"
            rows = conn.execute(
                """SELECT id, nama, nim, prodi, alamat, angkatan
                   FROM mahasiswa
                   WHERE nama LIKE ? OR nim LIKE ?
                   ORDER BY id DESC""",
                (pola, pola),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, nama, nim, prodi, alamat, angkatan
                   FROM mahasiswa ORDER BY id DESC"""
            ).fetchall()
    for row in rows:
        # NULL pada alamat/angkatan ditampilkan sebagai teks kosong
        tabel.insert("", tk.END, values=["" if v is None else v for v in row])


def bersihkan_form():
    entry_nama.delete(0, tk.END)
    entry_nim.delete(0, tk.END)
    combo_prodi.set("")
    entry_alamat.delete(0, tk.END)
    entry_angkatan.delete(0, tk.END)
    entry_nama.focus_set()


def ambil_form():
    """Membaca & memvalidasi formulir.
    Mengembalikan (nama, nim, prodi, alamat, angkatan) atau None jika tidak valid."""
    nama = entry_nama.get().strip()
    nim = entry_nim.get().strip()
    prodi = combo_prodi.get().strip()
    alamat = entry_alamat.get().strip()
    angkatan_txt = entry_angkatan.get().strip()

    if not nama or not nim or not prodi:
        messagebox.showwarning("Validasi", "Nama, NIM, dan Program Studi wajib diisi.")
        return None

    angkatan = None
    if angkatan_txt:
        if not (angkatan_txt.isdigit() and len(angkatan_txt) == 4):
            messagebox.showwarning("Validasi", "Angkatan harus berupa 4 digit angka, contoh: 2025.")
            return None
        angkatan = int(angkatan_txt)
    return nama, nim, prodi, alamat, angkatan


def simpan_data():
    """INSERT data baru."""
    data = ambil_form()
    if data is None:
        return
    try:
        with koneksi() as conn:
            conn.execute(
                """INSERT INTO mahasiswa (nama, nim, prodi, alamat, angkatan)
                   VALUES (?, ?, ?, ?, ?)""",
                data,
            )
        messagebox.showinfo("Berhasil", "Data berhasil disimpan.")
        tampilkan_data(var_cari.get())
        bersihkan_form()
    except sqlite3.IntegrityError:
        messagebox.showerror("NIM Duplikat", "NIM sudah terdaftar.")
    except sqlite3.Error as error:
        messagebox.showerror("Kesalahan Database", str(error))


def hapus_data():
    """DELETE baris terpilih setelah konfirmasi."""
    pilihan = tabel.selection()
    if not pilihan:
        messagebox.showwarning("Pilih Data", "Pilih baris yang akan dihapus.")
        return
    data = tabel.item(pilihan[0], "values")
    record_id = int(data[0])
    if not messagebox.askyesno("Konfirmasi", f"Hapus data {data[1]}?"):
        return
    with koneksi() as conn:
        conn.execute("DELETE FROM mahasiswa WHERE id = ?", (record_id,))
    tampilkan_data(var_cari.get())
    bersihkan_form()


def isi_form_dari_tabel(event=None):
    """Memuat record terpilih ke form. Data dibaca ulang dari database
    agar NIM berawalan nol (misalnya 00123) tidak berubah."""
    pilihan = tabel.selection()
    if not pilihan:
        return
    record_id = int(tabel.item(pilihan[0], "values")[0])
    with koneksi() as conn:
        row = conn.execute(
            "SELECT nama, nim, prodi, alamat, angkatan FROM mahasiswa WHERE id = ?",
            (record_id,),
        ).fetchone()
    if row is None:
        return
    bersihkan_form()
    entry_nama.insert(0, row[0])
    entry_nim.insert(0, row[1])
    combo_prodi.set(row[2])
    entry_alamat.insert(0, row[3] or "")
    entry_angkatan.insert(0, "" if row[4] is None else str(row[4]))


def ubah_data():
    """UPDATE record terpilih (acuan: id, bukan NIM)."""
    pilihan = tabel.selection()
    if not pilihan:
        messagebox.showwarning("Pilih Data", "Pilih data yang akan diubah.")
        return
    record_id = int(tabel.item(pilihan[0], "values")[0])
    data = ambil_form()
    if data is None:
        return
    try:
        with koneksi() as conn:
            conn.execute(
                """UPDATE mahasiswa
                   SET nama = ?, nim = ?, prodi = ?, alamat = ?, angkatan = ?
                   WHERE id = ?""",
                (*data, record_id),
            )
        tampilkan_data(var_cari.get())
        bersihkan_form()
        messagebox.showinfo("Berhasil", "Data berhasil diperbarui.")
    except sqlite3.IntegrityError:
        messagebox.showerror("NIM Duplikat", "NIM sudah digunakan data lain.")
    except sqlite3.Error as error:
        messagebox.showerror("Kesalahan Database", str(error))


def cari_data():
    tampilkan_data(var_cari.get())


def reset_pencarian():
    var_cari.set("")
    tampilkan_data()


def refresh():
    tampilkan_data(var_cari.get())


# ---------------------------------------------------------------------------
# TOMBOL & EVENT
# ---------------------------------------------------------------------------
ttk.Button(cari_frame, text="Cari", command=cari_data).pack(side="left", padx=4)
ttk.Button(cari_frame, text="Tampilkan Semua", command=reset_pencarian).pack(side="left", padx=4)
entry_cari.bind("<Return>", lambda e: cari_data())

ttk.Button(baris_tombol, text="Simpan Data", command=simpan_data).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Ubah Data", command=ubah_data).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Refresh", command=refresh).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Bersihkan Form", command=bersihkan_form).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Hapus Data Terpilih", command=hapus_data).pack(side="right", padx=4)

tabel.bind("<<TreeviewSelect>>", isi_form_dari_tabel)

tampilkan_data()

if __name__ == "__main__":
    root.mainloop()
