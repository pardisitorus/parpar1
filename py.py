import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64

# Inisialisasi database SQLite
conn = sqlite3.connect('donation_app.db')
c = conn.cursor()

# Membuat tabel jika belum ada
c.execute('''
          CREATE TABLE IF NOT EXISTS donations
          (id INTEGER PRIMARY KEY AUTOINCREMENT,
          donor_name TEXT,
          amount INTEGER,
          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)
          ''')
conn.commit()

# Fungsi untuk menambah donasi ke database
def add_donation(donor_name, amount):
    c.execute('INSERT INTO donations (donor_name, amount) VALUES (?, ?)',
              (donor_name, amount))
    conn.commit()

# Fungsi untuk menampilkan riwayat donasi
def view_donations():
    c.execute('SELECT * FROM donations ORDER BY timestamp DESC')
    donations = c.fetchall()
    return donations

# Fungsi untuk login admin
def admin_login(username, password):
    return username == "admin" and password == "admin"

# Fungsi untuk mengunduh data dalam format CSV
def download_csv(data):
    df = pd.DataFrame(data, columns=["ID", "Donor Name", "Amount", "Timestamp"])
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="donation_history.csv">Download CSV</a>'
    return href

# Halaman utama
def home():
    st.title("Selamat Datang di Website Donasi Online")
    st.image("path/to/logo.png", width=200)  # Ganti dengan path/logo yang sesuai
    st.write("Pilih peran Anda:")
    choice = st.radio("", ("Admin", "Donatur"))

    if choice == "Admin":
        username = st.text_input("Username:")
        password = st.text_input("Password:", type="password")
        if st.button("Login"):
            if admin_login(username, password):
                admin_page()
            else:
                st.warning("Login gagal. Coba lagi.")
    elif choice == "Donatur":
        donor_page()

# Halaman admin
def admin_page():
    st.title("Halaman Admin")
    st.subheader("Riwayat Donasi")
    donations = view_donations()
    
    # Tampilkan dalam bentuk tabel
    df = pd.DataFrame(donations, columns=["ID", "Donor Name", "Amount", "Timestamp"])
    st.table(df)

    # Tambahkan tombol untuk mengunduh data CSV
    st.markdown(download_csv(donations), unsafe_allow_html=True)

# Halaman donatur
def donor_page():
    st.title("Halaman Donatur")
    donor_name = st.text_input("Nama Donatur")
    amount = st.number_input("Jumlah Donasi", min_value=1)

    if st.button("Donasi Sekarang"):
        add_donation(donor_name, amount)
        st.success(f"Terima kasih, {donor_name}! Donasi sebesar ${amount} telah diterima.")

# Menjalankan aplikasi
if _name_ == "_main_":
    home()