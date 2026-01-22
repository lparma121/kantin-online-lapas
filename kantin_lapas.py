import streamlit as st
from supabase import create_client
import uuid
from datetime import datetime

# --- KONFIGURASI SUPABASE ---
URL = st.secrets["https://gdvphhymxlhuarvxwvtm.supabase.co"]
KEY = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdkdnBoaHlteGxodWFydnh3dnRtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkwMjU0MTEsImV4cCI6MjA4NDYwMTQxMX0.qOU1CIFxeZ64HJDmlaGX3yhr20kMn5Q8MJ2sy_b7__k"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Kantin Online Lapas", layout="wide")

# --- FUNGSI HELPER ---
def get_data_barang():
    res = supabase.table("barang").select("*").execute()
    return res.data

# --- SIDEBAR NAVIGASI & LOGIN ---
st.sidebar.title("🍱 Menu Utama")

# Pilihan menu standar
menu_options = ["🏠 Beranda", "🛒 Pesan Barang", "🔍 Lacak Pesanan", "👮 Area Petugas"]
menu = st.sidebar.radio("Pilih Halaman:", menu_options)

# Tambahan: Login Petugas jika memilih menu Area Petugas
authenticated = False
if menu == "👮 Area Petugas":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 Login Petugas")
    password_petugas = st.sidebar.text_input("Masukkan Password", type="password")
    
    # Silakan ganti "admin123" dengan password pilihan Anda
    if password_petugas == "admin123":
        authenticated = True
        st.sidebar.success("Akses Diberikan")
    elif password_petugas != "":
        st.sidebar.error("Password Salah")

# --- 1. HALAMAN BERANDA ---
if menu == "🏠 Beranda":
    st.title("Selamat Datang di Kantin Online Lapas")
    st.write("Layanan ini memudahkan keluarga untuk memesan kebutuhan WBP dari rumah secara transparan.")

# --- 2. HALAMAN PESAN BARANG ---
elif menu == "🛒 Pesan Barang":
    st.title("Formulir Pesanan Keluarga")
    
    # Ambil daftar barang dari database
    daftar_barang = get_data_barang()
    
    with st.form("form_order"):
        col1, col2 = st.columns(2)
        with col1:
            nama_pemesan = st.text_input("Nama Anda (Keluarga)")
            untuk_siapa = st.text_input("Nama WBP (Penerima)")
        with col2:
            cara_bayar = st.selectbox("Metode Pembayaran", ["Transfer Bank", "E-Wallet", "Tunai di Loket"])
            pilihan = st.multiselect("Pilih Barang", [b['nama_barang'] for b in daftar_barang])
        
        catatan = st.text_area("Catatan Tambahan")
        submitted = st.form_submit_button("Kirim Pesanan Sekarang")
        
        if submitted:
            if nama_pemesan and untuk_siapa and pilihan:
                # Simpan ke Supabase
                data = {
                    "nama_pemesan": nama_pemesan,
                    "untuk_siapa": untuk_siapa,
                    "item_pesanan": ", ".join(pilihan),
                    "cara_bayar": cara_bayar,
                    "status": "Menunggu Antrian"
                }
                res = supabase.table("pesanan").insert(data).execute()
                id_baru = res.data[0]['id']
                st.success(f"✅ Pesanan Berhasil! Mohon simpan NOMOR PESANAN Anda: #{id_baru}")
            else:
                st.error("Mohon lengkapi semua data.")

# --- 3. HALAMAN LACAK PESANAN ---
elif menu == "🔍 Lacak Pesanan":
    st.title("Pelacakan Pesanan")
    id_cari = st.number_input("Masukkan Nomor Pesanan (#)", min_value=1, step=1)
    
    if st.button("Cek Status"):
        res = supabase.table("pesanan").select("*").eq("id", id_cari).execute()
        if res.data:
            order = res.data[0]
            st.info(f"Status Saat Ini: **{order['status']}**")
            
            if order['foto_penerima']:
                st.write("📸 Bukti Penerimaan:")
                st.image(order['foto_penerima'])
            else:
                st.warning("Foto bukti penerimaan belum tersedia.")
        else:
            st.error("Nomor pesanan tidak ditemukan.")

# --- 4. HALAMAN PETUGAS (DENGAN PROTEKSI) ---
elif menu == "👮 Area Petugas":
    if not authenticated:
        st.title("👮 Area Petugas")
        st.warning("Silakan masukkan password di sidebar untuk mengakses halaman ini.")
        st.image("https://illustrations.popsy.co/gray/lock.svg", width=300) # Opsional: Tambah ilustrasi kunci
    else:
        st.title("Panel Petugas Kantin")
        st.write("Selamat bertugas, Petugas Kantin.")
        
        # --- (Sisanya adalah kode petugas Anda yang sebelumnya) ---
        res = supabase.table("pesanan").select("*").neq("status", "Selesai").execute()

        # ... kode tampilkan pesanan, update status, dan kamera ...
