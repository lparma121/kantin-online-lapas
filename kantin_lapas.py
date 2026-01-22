import streamlit as st
from supabase import create_client
import uuid
from datetime import datetime

# --- KONFIGURASI SUPABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
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
    
    # Ambil daftar barang yang stoknya > 0
    res_barang = supabase.table("barang").select("*").gt("stok", 0).execute()
    daftar_barang = res_barang.data
    
    with st.form("form_order"):
        col1, col2 = st.columns(2)
        with col1:
            nama_pemesan = st.text_input("Nama Anda (Keluarga)")
            untuk_siapa = st.text_input("Nama WBP (Penerima)")
        with col2:
            cara_bayar = st.selectbox("Metode Pembayaran", ["Transfer Bank", "E-Wallet", "Tunai di Loket"])
            pilihan = st.multiselect("Pilih Barang", [b['nama_barang'] for b in daftar_barang])
        
        submitted = st.form_submit_button("Kirim Pesanan Sekarang")
        
        # BARIS DI BAWAH INI HARUS MENJOROK KE DALAM (Indented)
        if submitted:
            if nama_pemesan and untuk_siapa and pilihan:
                # 1. Simpan Data Pesanan
                data_pesan = {
                    "nama_pemesan": nama_pemesan,
                    "untuk_siapa": untuk_siapa,
                    "item_pesanan": ", ".join(pilihan),
                    "cara_bayar": cara_bayar,
                    "status": "Menunggu Antrian"
                }
                res = supabase.table("pesanan").insert(data_pesan).execute()
                id_baru = res.data[0]['id']

                # 2. LOGIKA STOK OTOMATIS
                for item in pilihan:
                    # Ambil stok saat ini dari database
                    barang_data = supabase.table("barang").select("stok").eq("nama_barang", item).execute()
                    if barang_data.data:
                        stok_sekarang = barang_data.data[0]['stok']
                        # Kurangi stok 1
                        supabase.table("barang").update({"stok": stok_sekarang - 1}).eq("nama_barang", item).execute()
                
                st.success(f"✅ Pesanan Berhasil! Nomor Pesanan Anda: #{id_baru}")
            else:
                st.error("Mohon lengkapi semua data dan pilih minimal satu barang.")

        # 2. LOGIKA STOK OTOMATIS
        for item in pilihan:
            # Ambil stok saat ini
            barang_data = supabase.table("barang").select("stok").eq("nama_barang", item).execute()
            if barang_data.data:
                stok_sekarang = barang_data.data[0]['stok']
                if stok_sekarang > 0:
                    # Kurangi stok sebanyak 1
                    supabase.table("barang").update({"stok": stok_sekarang - 1}).eq("nama_barang", item).execute()
        
        st.success(f"✅ Pesanan Berhasil! Stok telah diperbarui. Nomor Pesanan: #{id_baru}")
    else:
        st.error("Mohon lengkapi data dan pilih barang.")

# Modifikasi fungsi ambil data barang
def get_data_barang_tersedia():
    # Hanya ambil barang yang stoknya lebih dari 0
    res = supabase.table("barang").select("*").gt("stok", 0).execute()
    return res.data

# Lalu di bagian pilihan multiselect:
daftar_barang = get_data_barang_tersedia()
pilihan = st.multiselect("Pilih Barang (Hanya yang tersedia)", [b['nama_barang'] for b in daftar_barang])
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
        # ... (kode login)
    else:
        st.title("Panel Petugas Kantin")
        
        # Tampilkan Tabel Stok Singkat
        with st.expander("📦 Cek Stok Barang"):
            all_items = supabase.table("barang").select("nama_barang", "stok").execute()
            st.table(all_items.data)
        
        # ... (sisa kode petugas lainnya)
        
        # --- (Sisanya adalah kode petugas Anda yang sebelumnya) ---
        res = supabase.table("pesanan").select("*").neq("status", "Selesai").execute()

        # ... kode tampilkan pesanan, update status, dan kamera ...



