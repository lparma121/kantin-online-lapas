import streamlit as st
from supabase import create_client
import uuid

# --- 1. KONEKSI DATABASE (MENGGUNAKAN SECRETS) ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Kantin Online Lapas", layout="wide")

# --- 2. NAVIGASI SIDEBAR & PROTEKSI ---
st.sidebar.title("🍱 Menu Utama")
menu = st.sidebar.radio("Pilih Halaman:", ["🏠 Beranda", "🛒 Pesan Barang", "🔍 Lacak Pesanan", "👮 Area Petugas"])

authenticated = False
if menu == "👮 Area Petugas":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 Login Petugas")
    pwd = st.sidebar.text_input("Password", type="password")
    if pwd == "admin123": # <--- Ganti password petugas di sini
        authenticated = True

# --- 3. HALAMAN BERANDA ---
if menu == "🏠 Beranda":
    st.title("🍱 Selamat Datang di Kantin Online Lapas")
    st.write("Layanan pemesanan kebutuhan WBP secara transparan dan akuntabel.")
    st.info("Silakan pilih menu di samping untuk mulai.")

# --- 4. HALAMAN PESAN BARANG (KELUARGA) ---
elif menu == "🛒 Pesan Barang":
    st.title("Formulir Pesanan")
    
    # Ambil barang yang stoknya masih tersedia
    res_b = supabase.table("barang").select("*").gt("stok", 0).execute()
    daftar_barang = res_b.data
    
    if not daftar_barang:
        st.warning("Maaf, saat ini belum ada stok barang tersedia.")
    else:
        with st.form("order_form"):
            c1, c2 = st.columns(2)
            with c1:
                pemesan = st.text_input("Nama Keluarga")
                untuk = st.text_input("Nama WBP (Penerima)")
            with c2:
                bayar = st.selectbox("Metode Bayar", ["Transfer", "E-Wallet", "Tunai"])
                pilihan = st.multiselect("Pilih Barang", [b['nama_barang'] for b in daftar_barang])
            
            submit = st.form_submit_button("Kirim Pesanan Sekarang")
            
            if submit:
                if pemesan and untuk and pilihan:
                    # A. Simpan data pesanan
                    d_pesan = {
                        "nama_pemesan": pemesan,
                        "untuk_siapa": untuk,
                        "item_pesanan": ", ".join(pilihan),
                        "cara_bayar": bayar,
                        "status": "Menunggu Antrian"
                    }
                    res_in = supabase.table("pesanan").insert(d_pesan).execute()
                    id_p = res_in.data[0]['id']

                    # B. Kurangi stok barang otomatis
                    for item in pilihan:
                        data_stok = supabase.table("barang").select("stok").eq("nama_barang", item).execute()
                        if data_stok.data:
                            stok_baru = data_stok.data[0]['stok'] - 1
                            supabase.table("barang").update({"stok": stok_baru}).eq("nama_barang", item).execute()
                    
                    st.success(f"✅ Pesanan Berhasil! Catat ID Pesanan Anda: #{id_p}")
                else:
                    st.error("Mohon lengkapi semua data.")

# --- 5. HALAMAN LACAK PESANAN (KELUARGA) ---
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Status Pesanan")
    id_cari = st.number_input("Masukkan Nomor Pesanan (#)", min_value=1, step=1)
    if st.button("Cek Status"):
        res_l = supabase.table("pesanan").select("*").eq("id", id_cari).execute()
        if res_l.data:
            p = res_l.data[0]
            st
