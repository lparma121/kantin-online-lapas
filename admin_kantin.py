import streamlit as st
from supabase import create_client
import time
from PIL import Image
import io

# --- KONEKSI DATABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Admin Kantin", layout="wide")
st.title("👮 Panel Admin & Verifikasi")

# --- LOGIN ---
pwd = st.sidebar.text_input("Password", type="password")
if pwd != "admin123": st.warning("🔒 Login dulu."); st.stop()

# --- FUNGSI KOMPRES & UPLOAD ---
def kompres_upload(file_obj, folder, nama_file):
    try:
        img = Image.open(file_obj).convert("RGB")
        img.thumbnail((600, 600))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=50)
        path = f"{folder}/{nama_file}"
        supabase.storage.from_("KANTIN-ASSETS").upload(path, buf.getvalue(), {"upsert": "true", "content-type": "image/jpeg"})
        return supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
    except: return None

# =========================================
# 1. PENCARIAN RESI (FITUR BARU)
# =========================================
st.sidebar.header("🔍 Cari Pesanan")
cari_resi = st.sidebar.text_input("Input Nomor Resi")
filter_data = None

if cari_resi:
    res = supabase.table("pesanan").select("*").eq("no_resi", cari_resi).execute()
    filter_data = res.data
    if not filter_data: st.sidebar.error("Resi tidak ditemukan.")

# =========================================
# 2. DAFTAR PESANAN MASUK
# =========================================
st.header("📋 Verifikasi & Proses Pesanan")

if st.button("🔄 Refresh Data"): st.rerun()

# Jika sedang mencari resi, pakai data filter. Jika tidak, ambil yg belum selesai.
if filter_data:
    data_tampil = filter_data
    st.info(f"Menampilkan hasil pencarian: {cari_resi}")
else:
    # Ambil pesanan yang belum Selesai
    res_p = supabase.table("pesanan").select("*").neq("status", "Selesai").order("id", desc=True).execute()
    data_tampil = res_p.data

if data_tampil:
    for p in data_tampil:
        with st.container(border=True):
            cols = st.columns([1, 2, 2])
            
            # KOLOM 1: INFO UTAMA
            with cols[0]:
                st.subheader(f"#{p['id']}")
                st.caption(f"Resi: {p.get('no_resi', '-')}")
                st.markdown(f"**{p['status']}**")
                
                # Tombol Lihat Bukti Transfer
                if p.get('bukti_transfer'):
                    st.link_button("📄 Lihat Bukti Transfer", p['bukti_transfer'])
                else:
                    st.warning("Bukti TF tidak ada")

            # KOLOM 2: DETAIL
            with cols[1]:
                st.write(f"**Pengirim:** {p['nama_pemesan']}")
                st.write(f"**Penerima:** {p['untuk_siapa']}")
                st.info(f"Isi: {p['item_pesanan']}")

            # KOLOM 3: AKSI ADMIN
            with cols[2]:
                with st.form(key=f"f_{p['id']}"):
                    st.write("Update Status:")
                    # Opsi status disesuaikan flow baru
                    opsi_status = ["Menunggu Verifikasi", "Pembayaran Valid (Diproses)", "Selesai"]
                    # Coba set default index
                    idx = 0
                    if p['status'] == "Pembayaran Valid (Diproses)": idx = 1
                    
                    st_baru = st.selectbox("Pilih Status", opsi_status, index=idx, key=f"s_{p['id']}")
                    
                    # Kamera Bukti Penyerahan (Hanya jika Selesai)
                    foto_serah = st.camera_input("Foto Penyerahan", key=f"c_{p['id']}") if st_baru == "Selesai" else None
                    
                    if st.form_submit_button("Simpan Perubahan"):
                        u_data = {"status": st_baru}
                        
                        if st_baru == "Selesai":
                            if foto_serah:
                                url_serah = kompres_upload(foto_serah, "bukti_serah", f"serah_{p['no_resi']}.jpg")
                                if url_serah:
                                    u_data["foto_penerima"] = url_serah
                                    supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                    st.success("✅ Pesanan Selesai!")
                                    
                                    # Kirim WA Lengkap
                                    hp = p['nomor_wa']
                                    if hp.startswith('0'): hp = '62' + hp[1:]
                                    msg = f"Halo, Pesanan Resi {p['no_resi']} SUDAH DITERIMA oleh {p['untuk_siapa']}. Terima kasih."
                                    st.link_button("📲 Kabari via WA", f"https://wa.me/{hp}?text={msg.replace(' ', '%20')}")
                            else:
                                st.error("Wajib foto penyerahan!")
                        else:
                            # Update status biasa (misal verifikasi pembayaran)
                            supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                            st.success("Status diupdate!")
                            time.sleep(1)
                            st.rerun()
else:
    st.info("Tidak ada pesanan aktif.")

st.markdown("---")
with st.expander("📦 Manajemen Stok Barang"):
    # (Masukkan kode manajemen stok Anda yg lama di sini jika mau)
    st.write("Gunakan kode stok dari file sebelumnya untuk bagian ini.")
