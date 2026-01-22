import streamlit as st
from supabase import create_client
import time

# --- KONEKSI DATABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Kantin Lapas Online", page_icon="🍱", layout="wide")

# --- CSS CUSTOM UNTUK TAMPILAN CANTIK ---
st.markdown("""
<style>
    /* Mengubah warna tombol */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
    }
    /* Card Style */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 10px;
    }
    /* Harga Style */
    .harga-tag {
        color: #d9534f;
        font-size: 18px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI FORMAT RUPIAH ---
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# --- INISIALISASI KERANJANG BELANJA (SESSION STATE) ---
if 'keranjang' not in st.session_state:
    st.session_state.keranjang = []

# --- FUNGSI TAMBAH KE KERANJANG ---
def tambah_ke_keranjang(item, harga):
    st.session_state.keranjang.append({"nama": item, "harga": harga})
    st.toast(f"🛒 {item} masuk keranjang!")

# --- FUNGSI RESET KERANJANG ---
def reset_keranjang():
    st.session_state.keranjang = []

# --- SIDEBAR: KERANJANG BELANJA ---
with st.sidebar:
    st.title("🛒 Keranjang Belanja")
    
    if len(st.session_state.keranjang) > 0:
        total_harga = 0
        for i, item in enumerate(st.session_state.keranjang):
            st.write(f"{i+1}. {item['nama']} - **{format_rupiah(item['harga'])}**")
            total_harga += item['harga']
        
        st.divider()
        st.subheader(f"Total: {format_rupiah(total_harga)}")
        
        if st.button("❌ Kosongkan Keranjang"):
            reset_keranjang()
            st.rerun()
    else:
        st.info("Keranjang masih kosong.")
        st.write("Silakan pilih menu di tab **Pesan Barang**.")

# --- NAVIGASI UTAMA ---
menu = st.sidebar.radio("Navigasi", ["🏠 Beranda", "🛍️ Pesan Barang", "🔍 Lacak Pesanan"])

# =========================================
# 1. HALAMAN BERANDA (HERO SECTION)
# =========================================
if menu == "🏠 Beranda":
    # Banner Gambar (Gunakan URL gambar pemandangan/kantin yang bagus)
    st.image("https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
    
    st.title("Selamat Datang di Kantin Online Lapas")
    st.markdown("### *Aman, Cepat, dan Transparan.*")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📦 **Stok Terjamin**\n\nSelalu update real-time dari petugas.")
    with col2:
        st.success("⚡ **Proses Cepat**\n\nPesan langsung sampai ke WBP.")
    with col3:
        st.warning("🛡️ **Transparan**\n\nLacak status pesanan & bukti foto.")

    st.markdown("---")
    st.write("Silakan pilih menu **🛍️ Pesan Barang** di sebelah kiri untuk mulai berbelanja untuk keluarga tercinta.")

# =========================================
# 2. HALAMAN BELANJA (GRID LAYOUT)
# =========================================
elif menu == "🛍️ Pesan Barang":
    st.title("Etalase Kantin")
    
    # Ambil Data Barang dari Supabase
    res_b = supabase.table("barang").select("*").gt("stok", 0).order('nama_barang').execute()
    items = res_b.data
    
    if not items:
        st.warning("Maaf, kantin sedang tutup atau stok habis.")
    else:
        # --- TAMPILAN GRID PRODUK ---
        # Kita buat grid 3 kolom
        cols = st.columns(3)
        
        for i, item in enumerate(items):
            with cols[i % 3]: # Logika agar barang mengisi kolom 1, 2, 3 lalu ke bawah
                with st.container(border=True):
                    # Gambar Placeholder jika url kosong
                    img_url = item['gambar_url'] if item.get('gambar_url') else "https://cdn-icons-png.flaticon.com/512/2515/2515263.png"
                    
                    st.image(img_url, use_container_width=True)
                    st.subheader(item['nama_barang'])
                    
                    # Menampilkan Harga & Stok
                    harga_display = item.get('harga', 0)
                    st.markdown(f"<div class='harga-tag'>{format_rupiah(harga_display)}</div>", unsafe_allow_html=True)
                    st.caption(f"Sisa Stok: {item['stok']}")
                    
                    # Tombol Beli
                    if st.button("➕ Tambah", key=f"btn_{item['id']}"):
                        tambah_ke_keranjang(item['nama_barang'], harga_display)
                        st.rerun()

    # --- FORM CHECKOUT DI BAWAH ---
    st.markdown("---")
    st.header("📝 Data Pengiriman")
    
    if len(st.session_state.keranjang) == 0:
        st.warning("⚠️ Masukkan minimal satu barang ke keranjang untuk memesan.")
    else:
        with st.form("checkout_form"):
            c1, c2 = st.columns(2)
            with c1:
                pemesan = st.text_input("Nama Anda (Keluarga)")
                untuk = st.text_input("Nama WBP (Penerima)")
            with c2:
                wa = st.text_input("Nomor WhatsApp Aktif")
                bayar = st.selectbox("Metode Pembayaran", ["Transfer Bank", "Tunai di Loket"])
            
            st.write(f"**Total yang harus dibayar: {format_rupiah(sum(item['harga'] for item in st.session_state.keranjang))}**")
            
            submit = st.form_submit_button("✅ Kirim Pesanan Sekarang")
            
            if submit:
                if pemesan and untuk and wa:
                    # Gabungkan item pesanan jadi string
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
                    
                    # Insert ke DB
                    res_in = supabase.table("pesanan").insert(d_pesan).execute()
                    id_p = res_in.data[0]['id']

                    # Kurangi Stok
                    for nama_brg in list_barang:
                        curr = supabase.table("barang").select("stok").eq("nama_barang", nama_brg).execute()
                        if curr.data:
                            stok_baru = curr.data[0]['stok'] - 1
                            supabase.table("barang").update({"stok": stok_baru}).eq("nama_barang", nama_brg).execute()
                    
                    # Reset Keranjang & Sukses
                    reset_keranjang()
                    st.success(f"🎉 Pesanan Berhasil! ID Pesanan Anda: #{id_p}")
                    st.balloons()
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("Mohon lengkapi Nama dan Nomor WA.")

# =========================================
# 3. HALAMAN LACAK
# =========================================
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Status Pesanan")
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        id_cari = st.number_input("Masukkan Nomor ID Pesanan", min_value=1, step=1, label_visibility="collapsed", placeholder="Contoh: 15")
    with col_btn:
        tombol_cari = st.button("🔍 Cek Sekarang", use_container_width=True)

    if tombol_cari:
        res = supabase.table("pesanan").select("*").eq("id", id_cari).execute()
        if res.data:
            data = res.data[0]
            st.info(f"📦 Pesanan untuk: **{data['untuk_siapa']}**")
            
            # Progress Bar Sederhana
            status_map = {"Menunggu Antrian": 30, "Diproses": 60, "Selesai": 100}
            prog = status_map.get(data['status'], 10)
            st.progress(prog, text=f"Status: {data['status']}")
            
            if data['status'] == "Selesai" and data['foto_penerima']:
                st.success("Pesanan telah diterima!")
                st.image(data['foto_penerima'], caption="Bukti Foto Penyerahan")
            elif data['status'] == "Selesai":
                 st.success("Pesanan telah selesai (Menunggu upload foto).")
        else:
            st.error("❌ Data tidak ditemukan. Cek kembali nomor ID Anda.")
