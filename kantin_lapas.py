import streamlit as st
from supabase import create_client
import uuid

# --- 1. KONFIGURASI SUPABASE (SECRETS) ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Kantin Online Lapas", layout="wide")

# --- 2. SIDEBAR & LOGIN ---
st.sidebar.title("🍱 Menu Utama")
menu = st.sidebar.radio("Pilih Halaman:", ["🏠 Beranda", "🛒 Pesan Barang", "🔍 Lacak Pesanan", "👮 Area Petugas"])

authenticated = False
if menu == "👮 Area Petugas":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 Login Petugas")
    password_petugas = st.sidebar.text_input("Password", type="password")
    if password_petugas == "admin123": # Ganti password di sini
        authenticated = True

# --- 3. HALAMAN BERANDA ---
if menu == "🏠 Beranda":
    st.title("🍱 Selamat Datang di Kantin Online Lapas")
    st.write("Layanan digital untuk memudahkan keluarga memesan kebutuhan WBP.")
    st.info("Gunakan menu di samping untuk mulai memesan atau melacak pesanan.")

# --- 4. HALAMAN PESAN BARANG ---
elif menu == "🛒 Pesan Barang":
    st.title("Formulir Pesanan")
    
    # Ambil barang yang stoknya > 0
    res_barang = supabase.table("barang").select("*").gt("stok", 0).execute()
    daftar_barang = res_barang.data
    
    if not daftar_barang:
        st.warning("Maaf, stok barang di kantin sedang kosong.")
    else:
        with st.form("form_order"):
            col1, col2 = st.columns(2)
            with col1:
                nama_pemesan = st.text_input("Nama Keluarga")
                untuk_siapa = st.text_input("Nama WBP (Penerima)")
            with col2:
                cara_bayar = st.selectbox("Metode Bayar", ["Transfer", "E-Wallet", "Tunai"])
                pilihan = st.multiselect("Pilih Barang", [b['nama_barang'] for b in daftar_barang])
            
            submitted = st.form_submit_button("Kirim Pesanan")
            
            if submitted:
                if nama_pemesan and untuk_siapa and pilihan:
                    # Simpan Pesanan
                    data_pesan = {
                        "nama_pemesan": nama_pemesan,
                        "untuk_siapa": untuk_siapa,
                        "item_pesanan": ", ".join(pilihan),
                        "cara_bayar": cara_bayar,
                        "status": "Menunggu Antrian"
                    }
                    res = supabase.table("pesanan").
