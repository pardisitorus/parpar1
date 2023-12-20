import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import base64

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

# Folder untuk menyimpan bukti donasi
output_folder = "donation_receipts"
os.makedirs(output_folder, exist_ok=True)

# Fungsi untuk membuat bukti donasi dengan latar belakang "4.png"
def generate_invoice_image(donation_id, donor_name, amount, campaign, payment_method):
    # Load the background image
    background_path = "4.png"
    background = Image.open(background_path).convert("RGBA")

    # Create a drawing object
    draw = ImageDraw.Draw(background)

    # Set the font (replace "arial.ttf" with the path to your font file)
    font_path = "arial.ttf"
    font_size = 36  # Increased font size
    font = ImageFont.truetype(font_path, font_size)

    # Customize the content of the invoice
    title_text = "Donation Receipt"
    
    # Calculate the position for centering the text
    title_text_bbox = draw.textbbox((0, 0), title_text, font=font)
    title_text_size = (title_text_bbox[2] - title_text_bbox[0], title_text_bbox[3] - title_text_bbox[1])
    center_x = (background.width - title_text_size[0]) // 2
    center_y = (background.height - title_text_size[1]) // 2

    # Draw the title text in the center
    draw.text((center_x, center_y), title_text, fill='black', font=font)

    draw.text((50, center_y + 50), f"Donation ID: {donation_id}", fill='black', font=font)
    draw.text((50, center_y + 100), f"Donor Name: {donor_name}", fill='black', font=font)
    draw.text((50, center_y + 150), f"Amount: Rp {amount:,.0f}", fill='black', font=font)
    draw.text((50, center_y + 200), f"Campaign: {campaign}", fill='black', font=font)
    draw.text((50, center_y + 250), f"Payment Method: {payment_method}", fill='black', font=font)

    # Convert RGBA to RGB
    background = background.convert("RGB")

    # Save the image
    img_path = os.path.join(output_folder, f"donation_receipt_{donation_id}.jpg")
    background.save(img_path)

    return img_path



# Fungsi untuk menampilkan bukti donasi di Streamlit
def display_donation_receipt(donation_id, donor_name, amount, campaign, payment_method):
    invoice_path = generate_invoice_image(donation_id, donor_name, amount, campaign, payment_method)

    st.success(f"Terima kasih, {donor_name}! Donasi sebesar Rp {amount:,.0f} untuk campaign {campaign} "
               f"dengan metode pembayaran {payment_method} telah diterima.")

    st.subheader("Donation Receipt:")
    st.image(invoice_path, caption=f"Donation Receipt #{donation_id}", use_column_width=True)

    # Tambahkan link unduh bukti donasi
    download_link = f'<a href="{invoice_path}" download="donation_receipt_{donation_id}.jpg">Download Donation Receipt</a>'
    st.markdown(download_link, unsafe_allow_html=True)

# Fungsi untuk menambah donasi ke database dengan informasi tambahan campaign dan metode pembayaran
def add_donation(donor_name, amount, campaign, payment_method):
    c.execute('INSERT INTO donations (donor_name, amount, campaign, payment_method) VALUES (?, ?, ?, ?)',
              (donor_name, amount, campaign, payment_method))
    conn.commit()

    # Mendapatkan ID donasi terakhir
    c.execute('SELECT id FROM donations ORDER BY timestamp DESC LIMIT 1')
    last_donation_id = c.fetchone()
    donation_id = last_donation_id[0] + 1 if last_donation_id else 1

    # Menampilkan bukti donasi
    display_donation_receipt(donation_id, donor_name, amount, campaign, payment_method)

# Tambahkan tema Streamlit
st.set_page_config(
    page_title="Donasi Data",
    page_icon="3.png",  # Ganti dengan emoji hati atau ikon lain yang sesuai
    layout="wide"
)

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

# Halaman utama
def home():
    st.image("3.png", width=300)  # Ganti dengan path/logo yang sesuai
    st.title("SELAMAT DATANG DI DONASI DATA!")
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
    st.dataframe(df.style
                  .set_table_styles([{'selector': 'thead', 'props': [('background', '#2a2a2a'), ('color', 'white')]},
                                    {'selector': 'tbody', 'props': [('background', '#424242'), ('color', 'white')]},
                                    {'selector': 'tr:hover', 'props': [('background-color', '#4a4a4a')]}])
                  .highlight_max(axis=0, color='#FFDD00')
                  .set_properties(**{'text-align': 'center'}))

   

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

    # menambahkan info 
    st.sidebar.title("INFO DONASI")

    st.sidebar.text ("🌐 DOTA (DONASI DATA)")
    st.sidebar.write("Selamat datang di Program Donasi Data Bersama Untuk Masa Depan! 🤝🌍 Dukunglah upaya kami untuk memberikan dampak positif pada panti asuhan kecelakaan, panti asuhan, dan kegiatan bakti sosial melalui pengumpulan dan distribusi donasi  Berikut adalah tujuan utama kami:")
    st.sidebar.write("1.PANTI ASUHAN KECELAKAAN: 🏠 Mendukung anak-anak di panti asuhan kecelakaan dengan menyediakan data untuk mendukung pendidikan, kesehatan, dan kebahagiaan mereka.")
    st.sidebar.write("2.PANTI ASUHAN: 👨‍👩‍👧‍👦 Memberdayakan panti asuhan dengan data yang mendukung kebutuhan harian, pendidikan, dan perkembangan anak-anak di bawah perawatan mereka.")
    st.sidebar.write("3.BAKTI SOSIAL: 🤲 Menyediakan data bagi organisasi bakti sosial untuk merencanakan dan mengimplementasikan kegiatan yang memberikan manfaat kepada masyarakat yang membutuhkan.")
    donor_name = st.text_input("Nama Donatur")

    # Validasi nama donatur
    if not donor_name:
        st.warning("Nama donatur wajib diisi.")
        return
    
    amount = st.number_input("Jumlah Donasi (Rp)", min_value=1000, step=1)  # Set jumlah minimal ke Rp 500

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

            # Menampilkan informasi bantuan setelah donasi
            st.subheader("Bantuan")
            st.write("Jika ada kendala , silakan hubungi kami 😊😊😊:")
            st.write("WhatsApp: [0851-73444-166](https://wa.me/6285173444166)")
            st.write("Email: [donasidata@gmail.com](mailto:donasidata@gmail.com)")

# Menjalankan aplikasi
if __name__ == "__main__":
    home()
