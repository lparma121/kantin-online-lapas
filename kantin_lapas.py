import streamlit as st
from supabase import create_client
import time

# --- KONEKSI DATABASE ---
# Pastikan secrets Anda sudah benar di Streamlit Cloud
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Kantin Lapas Online", page_icon="🍱", layout="wide")

# --- CSS CUSTOM (TAMPILAN CANTIK & STICKY) ---
# Perhatikan: Bagian ini harus dimulai rata kiri (tanpa spasi di awal baris st.markdown)
st.markdown("""
<style>
    /* Mengubah warna tombol */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
    }
    
    /* Card Style untuk Produk */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Harga Style */
    .harga-tag {
        color: #d9534f;
        font-size: 16px;
        font-weight: bold;
    }

    /* --- LOGIKA STICKY (MENGAMBANG) --- */
    /* Target Kolom Ke-2 (Form Checkout) */
    div[data-testid="column"]:nth-of-type(2) {
        position: sticky;
        top: 60px; /* Jarak dari atap layar */
        align-self: start; 
        
        /* Desain Panel Checkout */
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #ddd;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
        z-index: 999;
    }

    /* Perbaikan agar di HP (Layar kecil) tidak sticky */
    @media (max-width: 640px) {
        div[data-testid="column"]:nth-of-type(2) {
            position: static;
            top: auto;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI FORMAT RUPIAH ---
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# --- SESSION STATE KERANJANG ---
if 'keranjang' not in st.session_state:
    st.session_state.keranjang = []

def tambah_ke_keranjang(item, harga):
    st.session_state.keranjang.append({"nama": item, "harga": harga})
    st.toast(f"🛒 {item} masuk keranjang!")

def reset_keranjang():
    st.session_state.keranjang = []

# --- SIDEBAR KERANJANG ---
with st.sidebar:
    st.title("🛒 Keranjang")
    if len(st.session_state.keranjang) > 0:
        total_harga = 0
        for i, item in enumerate(st.session_state.keranjang):
            st.write(f"{i+1}. {item['nama']} - **{format_rupiah(item['harga'])}**")
            total_harga += item['harga']
        st.divider()
        st.subheader(f"Total: {format_rupiah(total_harga)}")
        if st.button("❌ Kosongkan"):
            reset_keranjang()
            st.rerun()
    else:
        st.info("Keranjang kosong.")

# --- NAVIGASI ---
menu = st.sidebar.radio("Navigasi", ["🏠 Beranda", "🛍️ Pesan Barang", "🔍 Lacak Pesanan"])

# =========================================
# 1. HALAMAN BERANDA
# =========================================
if menu == "🏠 Beranda":
    st.image("https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
    st.title("Selamat Datang di Kantin Online Lapas Arga Makmur")
    st.markdown("### *Aman, Cepat, dan Transparan.*")
    col1, col2, col3 = st.columns(3)
    with col1: st.info("📦 **Stok Terjamin**")
    with col2: st.success("⚡ **Proses Cepat**")
    with col3: st.warning("🛡️ **Transparan**")

# =========================================
# 2. HALAMAN BELANJA (LAYOUT STICKY)
# =========================================
elif menu == "🛍️ Pesan Barang":
    
    # MEMBAGI LAYAR JADI 2 KOLOM
    col_etalase, col_checkout = st.columns([2.5, 1.2], gap="large")

    # --- KOLOM KIRI: DAFTAR PRODUK ---
    with col_etalase:
        st.title("🛍️ Etalase Menu")
        res_b = supabase.table("barang").select("*").gt("stok", 0).order('nama_barang').execute()
        items = res_b.data
        
        if not items:
            st.warning("Maaf, stok habis.")
        else:
            # Grid produk (3 kolom di dalam kolom kiri)
            grid_cols = st.columns(3)
            for i, item in enumerate(items):
                with grid_cols[i % 3]:
                    with st.container(border=True):
                        img_url = item['gambar_url'] if item.get('gambar_url') else "https://cdn-icons-png.flaticon.com/512/2515/2515263.png"
                        st.image(img_url, use_container_width=True)
                        st.write(f"**{item['nama_barang']}**")
                        
                        harga = item.get('harga', 0)
                        st.markdown(f"<div class='harga-tag'>{format_rupiah(harga)}</div>", unsafe_allow_html=True)
                        st.caption(f"Stok: {item['stok']}")
                        
                        if st.button("➕ Beli", key=f"btn_{item['id']}"):
                            tambah_ke_keranjang(item['nama_barang'], harga)
                            st.rerun()

    # --- KOLOM KANAN: FORM CHECKOUT (STICKY) ---
    with col_checkout:
        st.header("📝 Data Pengiriman")
        st.write("Lengkapi data di bawah ini:")
        
        # Logic Form
        if len(st.session_state.keranjang) == 0:
            st.info("⚠️ Pilih barang di sebelah kiri untuk mulai memesan.")
        else:
            with st.container(border=True):
                st.caption(f"Item di keranjang: {len(st.session_state.keranjang)}")
                st.markdown(f"### Total: {format_rupiah(sum(item['harga'] for item in st.session_state.keranjang))}")
                st.divider()

                with st.form("checkout_form"):
                    pemesan = st.text_input("Nama Keluarga (Pengirim)")
                    untuk = st.text_input("Nama WBP (Penerima)")
                    wa = st.text_input("No. WhatsApp", placeholder="0812xxxx")
                    bayar = st.selectbox("Metode Bayar", ["Transfer Bank", "Tunai di Loket"])
                    
                    st.markdown("---")
                    submit = st.form_submit_button("✅ KIRIM PESANAN", type="primary")
                    
                    if submit:
                        if pemesan and untuk and wa:
                            list_barang = [b['nama'] for b in st.session_state.keranjang]
                            str_barang = ", ".join(list_barang)
                            
                            d_pesan = {
                                "nama_pemesan": pemesan,
                                "untuk_siapa": untuk,
                                "item_pesanan": str_barang,
                                "cara_bayar": bayar,
                                "status": "Menunggu Antrian",
                                "nomor_wa": wa
                            }
                            
                            # Insert DB
                            res_in = supabase.table("pesanan").insert(d_pesan).execute()
                            id_p = res_in.data[0]['id']

                            # Update Stok
                            for nama_brg in list_barang:
                                curr = supabase.table("barang").select("stok").eq("nama_barang", nama_brg).execute()
                                if curr.data:
                                    stok_baru = curr.data[0]['stok'] - 1
                                    supabase.table("barang").update({"stok": stok_baru}).eq("nama_barang", nama_brg).execute()
                            
                            reset_keranjang()
                            st.success(f"Pesanan #{id_p} Berhasil!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Nama & WA wajib diisi!")

# =========================================
# 3. HALAMAN LACAK
# =========================================
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Status Pesanan")
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        id_cari = st.number_input("ID Pesanan", min_value=1, step=1)
    with col_btn:
        tombol_cari = st.button("Cek Status", use_container_width=True)

    if tombol_cari:
        res = supabase.table("pesanan").select("*").eq("id", id_cari).execute()
        if res.data:
            data = res.data[0]
            st.info(f"Pesanan untuk: **{data['untuk_siapa']}**")
            status_map = {"Menunggu Antrian": 30, "Diproses": 60, "Selesai": 100}
            st.progress(status_map.get(data['status'], 10), text=f"Status: {data['status']}")
            
            if data['status'] == "Selesai" and data['foto_penerima']:
                st.image(data['foto_penerima'], caption="Bukti Foto")
        else:
            st.error("Data tidak ditemukan.")
