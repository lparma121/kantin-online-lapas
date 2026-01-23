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
st.title("👮 Panel Admin (Fitur Lengkap & Hemat Kuota)")

# --- LOGIN PROTEKSI ---
pwd = st.sidebar.text_input("Password Admin", type="password")
if pwd != "admin123":
    st.warning("🔒 Silakan login terlebih dahulu.")
    st.stop()

# --- FUNGSI PENTING: KOMPRESI GAMBAR ---
def kompres_gambar(upload_file):
    """Mengecilkan ukuran foto agar hemat storage Supabase."""
    try:
        # Buka gambar
        image = Image.open(upload_file)
        
        # Ubah ke RGB (jaga-jaga jika PNG transparan)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        # Resize (Kecilkan dimensi max 600px)
        image.thumbnail((600, 600))
        
        # Simpan ke Buffer sebagai JPEG Quality 50
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=50, optimize=True)
        
        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"Gagal kompres: {e}")
        return None

# --- FUNGSI UPLOAD KE SUPABASE (DENGAN KOMPRESI) ---
def upload_ke_supabase(file_obj, folder, nama_unik):
    try:
        # Lakukan kompresi dulu
        file_kecil = kompres_gambar(file_obj)
        
        if file_kecil:
            path = f"{folder}/{nama_unik}.jpg" # Paksa jadi .jpg
            supabase.storage.from_("KANTIN-ASSETS").upload(
                path, 
                file_kecil, 
                {"upsert": "true", "content-type": "image/jpeg"}
            )
            return supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
        return None
    except Exception as e:
        st.error(f"Gagal upload: {e}")
        return None

# --- FUNGSI FORMAT RUPIAH ---
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# =========================================
# 1. MANAJEMEN PRODUK
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
                        
                        # Upload dengan Kompresi
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

                # Hapus Produk
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
                    # Upload dengan Kompresi
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
# 2. ANTRIAN PESANAN
# =========================================
st.header("📋 Antrian Pesanan Masuk")
if st.button("🔄 Refresh Data"):
    st.rerun()

res_p = supabase.table("pesanan").select("*").neq("status", "Selesai").order("id").execute()

if res_p.data:
    for p in res_p.data:
        with st.container(border=True):
            cols = st.columns([3, 2])
            with cols[0]:
                st.subheader(f"Order #{p['id']}")
                st.write(f"**Pemesan:** {p['nama_pemesan']} -> **{p['untuk_siapa']}**")
                st.info(f"Isi: {p['item_pesanan']}")
            
            with cols[1]:
                with st.form(key=f"form_{p['id']}"):
                    st_baru = st.selectbox("Status", ["Menunggu Antrian", "Diproses", "Selesai"], key=f"s_{p['id']}")
                    foto = st.camera_input("Bukti Penyerahan", key=f"c_{p['id']}")
                    
                    if st.form_submit_button("Simpan & Kirim"):
                        u_data = {"status": st_baru}
                        if st_baru == "Selesai":
                            if foto:
                                # Upload BUKTI dengan Kompresi
                                f_name = f"bukti_{p['id']}_{int(time.time())}"
                                url_foto = upload_ke_supabase(foto, "", f_name) # folder root
                                
                                if url_foto:
                                    u_data["foto_penerima"] = url_foto
                                    supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                    
                                    no_hp = p['nomor_wa']
                                    if no_hp.startswith('0'): no_hp = '62' + no_hp[1:]
                                    link_wa = f"https://wa.me/{no_hp}?text=Pesanan%20#{p['id']}%20Selesai.%20Terima%20kasih."
                                    
                                    st.success("✅ Terkirim (Hemat Kuota!)")
                                    st.link_button("Kirim WA", link_wa)
                                else:
                                    st.error("Gagal upload.")
                            else:
                                st.error("Foto wajib ada!")
                        else:
                            supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                            st.success("Status diupdate.")
                            time.sleep(1)
                            st.rerun()
else:
    st.info("Tidak ada antrian.")
