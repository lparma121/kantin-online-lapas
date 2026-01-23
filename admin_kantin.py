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
st.title("👮 Panel Admin & Stok (Hemat Kuota)")

# --- FUNGSI PENTING: KOMPRESI GAMBAR ---
def kompres_gambar(upload_file):
    """
    Mengecilkan ukuran foto drastis (dari 3MB -> ~40KB)
    agar hemat storage Supabase.
    """
    try:
        # Buka gambar menggunakan Pillow
        image = Image.open(upload_file)
        
        # 1. Ubah ke RGB (jaga-jaga jika format PNG transparan)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        # 2. Resize (Kecilkan dimensi gambar max 600 pixel)
        max_size = (600, 600)
        image.thumbnail(max_size)
        
        # 3. Simpan ke Buffer dengan Kualitas Rendah (JPEG Quality 50)
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=50, optimize=True)
        
        # Kembalikan data bytes yang sudah dikompres
        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"Gagal kompres: {e}")
        return None

# --- FUNGSI UPLOAD KE SUPABASE ---
def upload_ke_supabase(file_bytes, nama_path):
    try:
        # Upload data bytes yang sudah dikompres
        supabase.storage.from_("KANTIN-ASSETS").upload(
            nama_path, 
            file_bytes, 
            {"upsert": "true", "content-type": "image/jpeg"} # Pakai JPEG biar kecil
        )
        return supabase.storage.from_("KANTIN-ASSETS").get_public_url(nama_path)
    except Exception as e:
        st.error(f"Gagal upload: {e}")
        return None

# --- LOGIN ---
pwd = st.sidebar.text_input("Password Admin", type="password")
if pwd != "admin123":
    st.warning("🔒 Silakan login.")
    st.stop()

# =========================================
# MANAJEMEN ANTRIAN (Bagian yang sering upload foto)
# =========================================
st.header("📋 Antrian Pesanan")

# Tombol Refresh
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
                    
                    # Kamera Input
                    foto = st.camera_input("Bukti Penyerahan", key=f"c_{p['id']}")
                    
                    if st.form_submit_button("Simpan & Kirim"):
                        u_data = {"status": st_baru}
                        
                        if st_baru == "Selesai":
                            if foto:
                                # PROSES KOMPRESI BERJALAN DISINI
                                foto_kecil = kompres_gambar(foto)
                                
                                if foto_kecil:
                                    # Gunakan timestamp biar nama file unik & cache tidak nyangkut
                                    nama_file = f"bukti_{p['id']}_{int(time.time())}.jpg"
                                    
                                    # Upload foto yg sudah kecil
                                    url_foto = upload_ke_supabase(foto_kecil, nama_file)
                                    
                                    if url_foto:
                                        u_data["foto_penerima"] = url_foto
                                        supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                        
                                        # Link WA
                                        no_hp = p['nomor_wa']
                                        if no_hp.startswith('0'): no_hp = '62' + no_hp[1:]
                                        msg = f"Halo, pesanan #{p['id']} sudah diterima. Terima kasih."
                                        link_wa = f"https://wa.me/{no_hp}?text={msg.replace(' ', '%20')}"
                                        
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
