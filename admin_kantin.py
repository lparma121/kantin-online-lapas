import streamlit as st
from supabase import create_client
import time

# --- KONEKSI DATABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Panel Petugas", layout="wide")

st.title("👮 Panel Pengelolaan Petugas")

# --- PROTEKSI LOGIN ---
pwd = st.sidebar.text_input("Password Petugas", type="password")
if pwd != "admin123":
    st.warning("🔒 Halaman terkunci. Masukkan password admin.")
    st.stop()

# =========================================
# 1. BAGIAN MANAJEMEN STOK (FITUR BARU)
# =========================================
with st.expander("📦 Manajemen Stok & Menu", expanded=True):
    # Ambil data terbaru
    s_res = supabase.table("barang").select("*").order("nama_barang").execute()
    data_barang = s_res.data
    
    # Tampilkan Tabel
    col_tabel, col_form = st.columns([1.5, 1])
    
    with col_tabel:
        st.subheader("Data Saat Ini")
        if data_barang:
            # Menampilkan data lebih rapi dengan dataframe
            st.dataframe(data_barang, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data barang.")

    with col_form:
        st.subheader("⚙️ Kelola Stok")
        tab1, tab2 = st.tabs(["📝 Update Stok", "➕ Tambah Barang Baru"])
        
        # TAB 1: UPDATE STOK YANG SUDAH ADA
        with tab1:
            if data_barang:
                list_nama = [b['nama_barang'] for b in data_barang]
                pilih_item = st.selectbox("Pilih Barang", list_nama)
                
                # Cari stok saat ini untuk default value
                stok_sekarang = next((item['stok'] for item in data_barang if item['nama_barang'] == pilih_item), 0)
                
                st.write(f"Stok saat ini: **{stok_sekarang}**")
                stok_baru = st.number_input("Ubah Menjadi:", min_value=0, value=stok_sekarang, step=1)
                
                if st.button("Simpan Perubahan Stok"):
                    supabase.table("barang").update({"stok": stok_baru}).eq("nama_barang", pilih_item).execute()
                    st.success(f"Stok {pilih_item} berhasil diupdate!")
                    time.sleep(1) # Jeda sebentar biar notif terbaca
                    st.rerun()
            else:
                st.warning("Data kosong.")

        # TAB 2: TAMBAH BARANG BARU
        with tab2:
            with st.form("tambah_barang"):
                nama_baru = st.text_input("Nama Barang Baru")
                stok_awal = st.number_input("Stok Awal", min_value=1, step=1)
                submit_baru = st.form_submit_button("Tambah ke Database")
                
                if submit_baru:
                    if nama_baru:
                        # Cek apakah nama sudah ada (opsional, tapi bagus untuk mencegah duplikat)
                        cek = supabase.table("barang").select("*").eq("nama_barang", nama_baru).execute()
                        if cek.data:
                            st.error("Nama barang sudah ada!")
                        else:
                            supabase.table("barang").insert({"nama_barang": nama_baru, "stok": stok_awal}).execute()
                            st.success(f"✅ {nama_baru} berhasil ditambahkan!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error("Nama barang tidak boleh kosong.")

st.markdown("---")

# =========================================
# 2. BAGIAN ANTRIAN PESANAN
# =========================================
st.header("📋 Antrian Pesanan")

# Auto-refresh tombol (opsional) agar petugas mudah cek pesanan baru
if st.button("🔄 Refresh Data Pesanan"):
    st.rerun()

res_p = supabase.table("pesanan").select("*").neq("status", "Selesai").order("id").execute()

if res_p.data:
    for p in res_p.data:
        # Beri warna beda dikit biar enak dilihat
        with st.container(border=True):
            cols = st.columns([3, 2])
            with cols[0]:
                st.subheader(f"Order #{p['id']}")
                st.markdown(f"**Pemesan:** {p['nama_pemesan']} ({p['nomor_wa']})")
                st.markdown(f"**Untuk WBP:** {p['untuk_siapa']}")
                st.info(f"🛒 **Isi:** {p['item_pesanan']}")
            
            with cols[1]:
                with st.form(key=f"form_{p['id']}"):
                    st.write("Tindakan:")
                    st_baru = st.selectbox("Update Status", ["Menunggu Antrian", "Diproses", "Selesai"], key=f"sel_{p['id']}")
                    
                    # Logika Foto hanya muncul jika pilih Selesai (secara UI logic)
                    # Tapi karena form Streamlit statis, kita tampilkan saja inputnya
                    st.caption("Khusus status 'Selesai', wajib ambil foto:")
                    foto = st.camera_input("Bukti Penyerahan", key=f"cam_{p['id']}")
                    
                    if st.form_submit_button("Simpan & Kirim WA"):
                        u_data = {"status": st_baru}
                        
                        # LOGIKA PROSES
                        sukses = False
                        if st_baru == "Selesai":
                            if foto:
                                try:
                                    path = f"
