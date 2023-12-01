import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

# Inisialisasi database SQLite
conn = sqlite3.connect('donation_app.db')
c = conn.cursor()

# Membuat tabel donations
c.execute('''
    CREATE TABLE IF NOT EXISTS donations
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_name TEXT,
    amount INTEGER,
    campaign TEXT,
    payment_method TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)
''')
conn.commit()

# Menambahkan akun admin (username: admin, password: password)
c.execute('''
    CREATE TABLE IF NOT EXISTS admin_accounts
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT)
''')
conn.commit()

# Cek apakah akun admin sudah ada, jika tidak, tambahkan
c.execute('SELECT * FROM admin_accounts WHERE username="admin"')
admin_account = c.fetchone()
if admin_account is None:
    c.execute('INSERT INTO admin_accounts (username, password) VALUES (?, ?)',
              ('admin', 'password'))
    conn.commit()

# Fungsi untuk menambah donasi ke database dengan informasi tambahan campaign dan metode pembayaran
def add_donation(donor_name, amount, campaign, payment_method):
    c.execute('INSERT INTO donations (donor_name, amount, campaign, payment_method) VALUES (?, ?, ?, ?)',
              (donor_name, amount, campaign, payment_method))
    conn.commit()

# Fungsi untuk menampilkan riwayat donasi
def view_donations():
    c.execute('SELECT id, donor_name, amount, campaign, payment_method, timestamp FROM donations ORDER BY timestamp DESC')
    donations = c.fetchall()
    return donations

# Fungsi untuk login admin
def admin_login(username, password):
    cleaned_username = username.strip()
    cleaned_password = password.strip()

    c.execute('SELECT * FROM admin_accounts WHERE username=? AND password=?', (cleaned_username, cleaned_password))
    admin_account = c.fetchone()
    return admin_account is not None

# Fungsi untuk menghapus donasi dari database berdasarkan ID
def delete_donation(donation_id):
    c.execute('DELETE FROM donations WHERE id = ?', (donation_id,))
    conn.commit()

# Halaman utama
def home():
    st.image("3.png", width=500)  # Ganti dengan path/logo yang sesuai
    st.title("SELAMAT DATANG DI DONASI DATA")
    st.write("Pilih peran Anda:")
    choice = st.radio("", ("Admin", "Donatur"))

    if choice == "Admin":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if admin_login(username, password):
                admin_page()
            else:
                st.warning("Login gagal. Coba lagi.")
    elif choice == "Donatur":
        donor_page()


# Fungsi untuk kembali ke halaman utama
def back_to_home():
    home()

# Halaman admin
def admin_page():
    st.title("Admin Dashboard")
    st.subheader("Riwayat Donasi")

    # Mendapatkan riwayat donasi
    donations = view_donations()

    # Membuat DataFrame dari data donasi
    df = pd.DataFrame(donations, columns=["ID", "Donor Name", "Amount", "Campaign", "Payment Method", "Timestamp"])

    # Menambahkan tema tabel yang keren
    st.table(df.style
             .set_table_styles([{'selector': 'thead', 'props': [('background', '#2a2a2a'), ('color', 'white')]},
                               {'selector': 'tbody', 'props': [('background', '#424242'), ('color', 'white')]},
                               {'selector': 'tr:hover', 'props': [('background-color', '#4a4a4a')]}])
             .highlight_max(axis=0, color='#FFDD00')
             .set_properties(**{'text-align': 'center'}))

    # Menambahkan fitur hapus donasi
    st.subheader("Hapus Donasi")

    # Menampilkan ID donasi untuk dipilih
    selected_donation_id= st.selectbox("Pilih ID Donasi yang akan dihapus", df["ID"].tolist(), index=0, key="donation_id")
    
    # Menampilkan tombol "Hapus" dengan konfirmasi modal
    delete_button_label = "Hapus Donasi"  # Provide a label for the button
    if st.button(delete_button_label, key="delete_button"):
        if selected_donation_id:
            # Tampilkan konfirmasi modal
            confirm_delete = st.button("Konfirmasi Hapus", key="confirm_delete")
            if confirm_delete:
                delete_donation(selected_donation_id)
                st.success(f"Donasi dengan ID {selected_donation_id} berhasil dihapus.")
        else:
            st.warning("Silakan pilih ID Donasi yang ingin dihapus.")

    # Menampilkan bar chart jumlah donasi per campaign dengan tema yang lebih keren
    st.subheader("Bar Chart: Jumlah Donasi per Campaign")
    bar_chart_data = df.groupby("Campaign")["Amount"].sum().reset_index()

    # Membuat bar chart menggunakan seaborn dengan tema warna yang berbeda
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x="Campaign", y="Amount", data=bar_chart_data, ax=ax, palette="mako")
    ax.set_xlabel("Campaign", fontsize=14, color="#2a2a2a")
    ax.set_ylabel("Jumlah Donasi", fontsize=14, color="#2a2a2a")
    ax.set_title("Total Donasi per Campaign", fontsize=16, color="#2a2a2a")
    ax.tick_params(axis='x', colors='#2a2a2a')
    ax.tick_params(axis='y', colors='#2a2a2a')
    sns.despine()
    st.pyplot(fig)

    # Menambahkan tombol keluar
    if st.button("Keluar", key="exit_button"):
        st.experimental_rerun()


# Halaman donatur
def donor_page():
    st.title("Halaman Donatur")
    
    # Menampilkan informasi bantuan di sidebar
    st.sidebar.title("Bantuan")
    st.sidebar.write("Jika Anda memerlukan bantuan, silakan hubungi kami:")
    st.sidebar.write("WhatsApp: [0851-73444-166](https://wa.me/6285173444166)")
    st.sidebar.write("Email: [donasidata@gmail.com](mailto:donasidata@gmail.com)")

    donor_name = st.text_input("Nama Donatur")

    # Validasi nama donatur
    if not donor_name:
        st.warning("Nama donatur wajib diisi.")
        return

    amount = st.number_input("Jumlah Donasi (Rp)", min_value=500, step=1)  # Set jumlah minimal ke Rp 500

    # Pilihan Campaign
    campaign_options = ["Pilih Campaign Anda", "Kebakaran", "Bakti Sosial", "Panti Asuhan"]  # Menambahkan opsi default
    campaign = st.selectbox("Pilih Campaign", campaign_options)

    # Validasi pilihan campaign
    if campaign == "Pilih Campaign Anda":
        st.warning("Pilih campaign terlebih dahulu.")
        return

    # Pilihan Metode Pembayaran
    payment_options = ["Pilih Metode Pembayaran Anda", "DANA", "GOPAY"]  # Menambahkan opsi default
    payment_method = st.selectbox("Pilih Metode Pembayaran", payment_options)

    # Validasi pilihan metode pembayaran
    if payment_method == "Pilih Metode Pembayaran Anda":
        st.warning("Pilih metode pembayaran terlebih dahulu.")
        return

    # Tampilkan gambar sesuai metode pembayaran
    if payment_method == "GOPAY":
        st.image("2.jpg", width=300)
        st.info("Silakan transfer menggunakan metode GOPAY (0851-73-444-166) .")
    elif payment_method == "DANA":
        st.image("1.jpg", width=300)
        st.info("Silakan transfer menggunakan metode DANA (0851-73-444-166) .")

    # Tombol "Donasi Sekarang"
    if amount < 500:
        st.warning("Jumlah donasi harus minimal Rp 500.")
    else:
        if st.button("Donasi Sekarang"):
            add_donation(donor_name, amount, campaign, payment_method)
            st.success(f"Terima kasih, {donor_name}! Donasi sebesar Rp {amount:,.0f} untuk campaign {campaign} "
                       f"dengan metode pembayaran {payment_method} telah diterima.")

            # Menampilkan informasi bantuan setelah donasi
            st.subheader("Bantuan")
            st.write("Jika Anda memerlukan bantuan terkait donasi ini, silakan hubungi kami:")
            st.write("WhatsApp: [0851-73444-166](https://wa.me/6285173444166)")
            st.write("Email: [donasidata@gmail.com](mailto:donasidata@gmail.com)")


# Menjalankan aplikasi
if __name__ == "__main__":
    home()
