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
                        new_stok = st.number_input("Update Stok", value=detail['stok'], min_value=0)
                        new_harga = st.number_input("Update Harga (Rp)", value=int(detail.get('harga', 0)), min_value=0, step=500)
                    with c2:
                        st.markdown("**Ganti Foto (Otomatis Dikompres)**")
                        uploaded_file = st.file_uploader("Upload File Baru", type=['png', 'jpg', 'jpeg'])
                        url_manual = st.text_input("Atau Paste Link URL", value=detail.get('gambar_url', ""))

                    if st.form_submit_button("💾 Simpan Perubahan"):
                        update_data = {"stok": new_stok, "harga": new_harga}
                        if uploaded_file:
                            f_name = f"produk_{detail['id']}_{int(time.time())}"
                            url_baru = upload_ke_supabase(uploaded_file, "produk", f_name)
                            if url_baru: update_data["gambar_url"] = url_baru
                        elif url_manual != detail.get('gambar_url'):
                            update_data["gambar_url"] = url_manual
                        
                        supabase.table("barang").update(update_data).eq("id", detail['id']).execute()
                        st.success("✅ Data berhasil diperbarui!")
                        time.sleep(1)
                        st.rerun()

                with st.expander(f"🗑️ Hapus Menu '{detail['nama_barang']}'"):
                    if st.button("Hapus Permanen", key="hapus_btn"):
                        supabase.table("barang").delete().eq("id", detail['id']).execute()
                        st.error("Produk dihapus.")
                        time.sleep(1)
                        st.rerun()

# --- TAB 2: TAMBAH BARANG ---
with tab2:
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        with c1:
            nama_baru = st.text_input("Nama Produk")
            harga_baru = st.number_input("Harga (Rp)", min_value=0, step=500, value=5000)
        with c2:
            stok_awal = st.number_input("Stok Awal", min_value=1, value=10)
            img_file = st.file_uploader("Upload Foto", type=['png', 'jpg', 'jpeg'])
            img_url_text = st.text_input("Atau Link URL")
        
        if st.form_submit_button("➕ Tambahkan"):
            if nama_baru:
                final_url = ""
                if img_file:
                    f_name = f"new_{int(time.time())}"
                    final_url = upload_ke_supabase(img_file, "produk", f_name)
                elif img_url_text:
                    final_url = img_url_text
                
                new_data = {"nama_barang": nama_baru, "stok": stok_awal, "harga": harga_baru, "gambar_url": final_url}
                supabase.table("barang").insert(new_data).execute()
                st.success(f"🎉 {nama_baru} berhasil ditambahkan!")
                time.sleep(1)
                st.rerun()

st.markdown("---")

# =========================================
# 2. ANTRIAN PESANAN (UPDATE FITUR BARU)
# =========================================
st.header("📋 Verifikasi & Proses Pesanan")

if st.button("🔄 Refresh Data Pesanan"):
    st.rerun()

# LOGIKA DATA: Apakah pakai filter pencarian resi atau ambil semua yang belum selesai?
if filter_data:
    st.info(f"🔍 Menampilkan hasil pencarian untuk Resi: **{cari_resi}**")
    data_pesanan = filter_data
else:
    # Ambil semua yang belum status 'Selesai', urutkan dari terbaru
    res_p = supabase.table("pesanan").select("*").neq("status", "Selesai").order("id", desc=True).execute()
    data_pesanan = res_p.data

if data_pesanan:
    for p in data_pesanan:
        with st.container(border=True):
            cols = st.columns([1, 2, 2])
            
            # --- KOLOM 1: INFO UTAMA ---
            with cols[0]:
                st.subheader(f"#{p['id']}")
                st.caption(f"Resi: {p.get('no_resi', '-')}")
                
                # Warna Status
                if p['status'] == "Menunggu Verifikasi":
                    st.warning(f"⚠️ {p['status']}")
                elif p['status'] == "Selesai":
                    st.success(f"✅ {p['status']}")
                else:
                    st.info(f"⚡ {p['status']}")
                
                # TOMBOL LIHAT BUKTI TF
                if p.get('bukti_transfer'):
                    st.link_button("📄 Cek Bukti Transfer", p['bukti_transfer'])
                else:
                    st.error("Belum ada bukti TF")
                    
                # TOMBOL LIHAT NOTA
                if p.get('nota_url'):
                    st.link_button("🧾 Lihat Nota", p['nota_url'])

            # --- KOLOM 2: DETAIL ---
            with cols[1]:
                st.write(f"**Pengirim:** {p['nama_pemesan']}")
                st.write(f"**Penerima:** {p['untuk_siapa']}")
                st.write(f"**Metode:** {p.get('cara_bayar', '-')}")
                st.info(f"📦 Isi: {p['item_pesanan']}")

            # --- KOLOM 3: AKSI ADMIN ---
            with cols[2]:
                with st.form(key=f"form_{p['id']}"):
                    st.write("**Tindakan:**")
                    
                    # Logic dropdown index agar sesuai status sekarang
                    opsi = ["Menunggu Verifikasi", "Pembayaran Valid (Diproses)", "Selesai"]
                    idx = 0
                    if p['status'] == "Pembayaran Valid (Diproses)": idx = 1
                    elif p['status'] == "Selesai": idx = 2
                    
                    st_baru = st.selectbox("Update Status", opsi, index=idx, key=f"s_{p['id']}")
                    
                    # Hanya tampilkan kamera jika pilih SELESAI
                    foto = None
                    if st_baru == "Selesai":
                        st.caption("Wajib ambil foto bukti penyerahan:")
                        foto = st.camera_input("Kamera", key=f"c_{p['id']}")
                    
                    if st.form_submit_button("Simpan & Proses"):
                        u_data = {"status": st_baru}
                        
                        if st_baru == "Selesai":
                            if foto:
                                # Upload BUKTI PENYERAHAN dengan Kompresi
                                f_name = f"serah_{p['no_resi'] if p.get('no_resi') else p['id']}"
                                url_foto = upload_ke_supabase(foto, "bukti_serah", f_name)
                                
                                if url_foto:
                                    u_data["foto_penerima"] = url_foto
                                    supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                    
                                    # Kirim WA
                                    no_hp = p['nomor_wa']
                                    if no_hp.startswith('0'): no_hp = '62' + no_hp[1:]
                                    resi_teks = p.get('no_resi', f"#{p['id']}")
                                    msg = f"Halo, Pesanan dengan Resi {resi_teks} SUDAH DITERIMA oleh {p['untuk_siapa']}. Terima kasih."
                                    link_wa = f"https://wa.me/{no_hp}?text={msg.replace(' ', '%20')}"
                                    
                                    st.success("✅ Pesanan Selesai & Foto Terupload!")
                                    st.link_button("📲 Kabari via WA", link_wa)
                                else:
                                    st.error("Gagal upload foto.")
                            else:
                                st.error("⚠️ Foto penyerahan wajib diambil!")
                        else:
                            # Update status biasa (misal verifikasi pembayaran)
                            supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                            st.success(f"Status diubah menjadi: {st_baru}")
                            time.sleep(1)
                            st.rerun()
else:
    st.info("✅ Tidak ada antrian pesanan.")
