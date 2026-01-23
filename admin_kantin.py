import streamlit as st
from supabase import create_client
import time
from PIL import Image
import io

# --- KONEKSI DATABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Panel Admin Kantin", layout="wide")
st.title("👮 Panel Admin (Verifikasi & Stok)")

# --- LOGIN PROTEKSI ---
pwd = st.sidebar.text_input("Password Admin", type="password")
if pwd != "admin123":
    st.warning("🔒 Silakan login terlebih dahulu.")
    st.stop()

# --- FITUR PENCARIAN RESI (BARU) ---
st.sidebar.markdown("---")
st.sidebar.header("🔍 Cari Pesanan")
cari_resi = st.sidebar.text_input("Masukkan No. Resi")
filter_data = None

if cari_resi:
    # Cari di database
    res = supabase.table("pesanan").select("*").eq("no_resi", cari_resi).execute()
    filter_data = res.data
    if not filter_data:
        st.sidebar.error("Resi tidak ditemukan.")
    else:
        st.sidebar.success("Pesanan ditemukan!")

# --- FUNGSI KOMPRESI GAMBAR (TETAP DIPERTAHANKAN) ---
def kompres_gambar(upload_file):
    """Mengecilkan ukuran foto agar hemat storage Supabase."""
    try:
        image = Image.open(upload_file)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.thumbnail((600, 600))
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=50, optimize=True)
        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"Gagal kompres: {e}")
        return None

def upload_ke_supabase(file_obj, folder, nama_unik):
    try:
        file_kecil = kompres_gambar(file_obj)
        if file_kecil:
            path = f"{folder}/{nama_unik}.jpg"
            supabase.storage.from_("KANTIN-ASSETS").upload(
                path, file_kecil, {"upsert": "true", "content-type": "image/jpeg"}
            )
            return supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
        return None
    except Exception as e:
        st.error(f"Gagal upload: {e}")
        return None

def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# =========================================
# 1. MANAJEMEN PRODUK (KODE LAMA ANDA - TIDAK BERUBAH)
# =========================================
st.header("📦 Manajemen Produk")
tab1, tab2 = st.tabs(["📝 Edit Barang & Stok", "➕ Tambah Menu Baru"])

# --- TAB 1: EDIT BARANG ---
with tab1:
    res = supabase.table("barang").select("*").order("nama_barang").execute()
    items = res.data
    
    if items:
        col_kiri, col_kanan = st.columns([1, 2])
        with col_kiri:
            st.subheader("Pilih Produk")
            pilihan = st.selectbox("Daftar Menu:", [b['nama_barang'] for b in items], label_visibility="collapsed")
            detail = next((item for item in items if item['nama_barang'] == pilihan), None)
            
            if detail:
                st.info(f"Stok: {detail['stok']} | Harga: {format_rupiah(detail.get('harga', 0))}")
                if detail.get('gambar_url'):
                    st.image(detail['gambar_url'], caption="Foto Saat Ini", use_container_width=True)

        with col_kanan:
            if detail:
                st.subheader(f"Edit: {detail['nama_barang']}")
                with st.form("edit_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_stok =
