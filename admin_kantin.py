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

# --- FITUR PENCARIAN RESI ---
st.sidebar.markdown("---")
st.sidebar.header("🔍 Cari Pesanan")
cari_resi = st.sidebar.text_input("Masukkan No. Resi")
filter_data = None

if cari_resi:
    res = supabase.table("pesanan").select("*").eq("no_resi", cari_resi).execute()
    filter_data = res.data
    if not filter_data:
        st.sidebar.error("Resi tidak ditemukan.")
    else:
        st.sidebar.success("Pesanan ditemukan!")

# --- FUNGSI KOMPRESI GAMBAR ---
def kompres_gambar(upload_file):
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
# 1. MANAJEMEN PRODUK
# =========================================
st.header("📦 Manajemen Produk")
tab1, tab2, tab3, tab4 = st.tabs(["📥 Pesanan Masuk", "📦 Sedang Diproses", "✅ Riwayat Selesai", "❌ Dibatalkan"])

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
                # FORM EDIT
                with st.form("edit_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_stok = st.number_input("Update Stok", value=detail['stok'], min_value=0)
                        new_harga = st.number_input("Update Harga (Rp)", value=int(detail.get('harga', 0)), min_value=0, step=500)
                    with c2:
                        st.markdown("**Ganti Foto**")
                        uploaded_file = st.file_uploader("Upload File Baru", type=['png', 'jpg', 'jpeg'])
                        url_manual = st.text_input("Atau Paste Link URL", value=detail.get('gambar_url', ""))

                    # TOMBOL SUBMIT HARUS MENJOROK KE DALAM FORM
                    btn_update = st.form_submit_button("💾 Simpan Perubahan")
                    
                    if btn_update:
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
    # FORM TAMBAH
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        with c1:
            nama_baru = st.text_input("Nama Produk")
            harga_baru = st.number_input("Harga (Rp)", min_value=0, step=500, value=5000)
        with c2:
            stok_awal = st.number_input("Stok Awal", min_value=1, value=10)
            img_file = st.file_uploader("Upload Foto", type=['png', 'jpg', 'jpeg'])
            img_url_text = st.text_input("Atau Link URL")
        
        # TOMBOL SUBMIT HARUS MENJOROK KE DALAM FORM
        submitted = st.form_submit_button("➕ Tambahkan")
        
        if submitted:
            if nama_baru:
                try:
                    final_url = ""
                    if img_file:
                        f_name = f"new_{int(time.time())}"
                        final_url = upload_ke_supabase(img_file, "produk", f_name)
                    elif img_url_text:
                        final_url = img_url_text
                    
                    # Perbaikan variabel di sini
                    new_data = {
                        "nama_barang": nama_baru, 
                        "stok": stok_awal, 
                        "harga": harga_baru, 
                        "gambar_url": final_url
                    }
                    supabase.table("barang").insert(new_data).execute()
                    st.success(f"🎉 {nama_baru} berhasil ditambahkan!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Nama produk wajib diisi!")

st.markdown("---")

# =========================================
# 2. ANTRIAN PESANAN
# =========================================
st.header("📋 Verifikasi & Proses Pesanan")

if st.button("🔄 Refresh Data Pesanan"):
    st.rerun()

if filter_data:
    st.info(f"🔍 Hasil Pencarian Resi: **{cari_resi}**")
    data_pesanan = filter_data
else:
    res_p = supabase.table("pesanan").select("*").neq("status", "Selesai").neq("status", "Dibatalkan").order("id", desc=True).execute()
    data_pesanan = res_p.data

if data_pesanan:
    for p in data_pesanan:
        with st.container(border=True):
            cols = st.columns([1, 2, 2])
            
            with cols[0]:
                st.subheader(f"#{p['id']}")
                st.caption(f"Resi: {p.get('no_resi', '-')}")
                
                if p['status'] == "Menunggu Verifikasi":
                    st.warning(f"⚠️ {p['status']}")
                elif p['status'] == "Selesai":
                    st.success(f"✅ {p['status']}")
                else:
                    st.info(f"⚡ {p['status']}")
                
                if p.get('bukti_transfer'):
                    st.link_button("📄 Cek Bukti Transfer", p['bukti_transfer'])
                else:
                    st.error("Belum ada bukti TF")
                
                if p.get('nota_url'):
                    st.link_button("🧾 Lihat Nota", p['nota_url'])

            with cols[1]:
                st.write(f"**Pengirim:** {p['nama_pemesan']}")
                st.write(f"**Penerima:** {p['untuk_siapa']}")
                st.write(f"**Metode:** {p.get('cara_bayar', '-')}")
                st.info(f"📦 Isi: {p['item_pesanan']}")

            with cols[2]:
                # FORM UPDATE STATUS
                with st.form(key=f"form_{p['id']}"):
                    st.write("**Tindakan:**")
                    
                    opsi = ["Menunggu Verifikasi", "Pembayaran Valid (Diproses)", "Selesai"]
                    idx = 0
                    if p['status'] == "Pembayaran Valid (Diproses)": idx = 1
                    elif p['status'] == "Selesai": idx = 2
                    
                    st_baru = st.selectbox("Update Status", opsi, index=idx, key=f"s_{p['id']}")
                    
                    foto = None
                    if st_baru == "Selesai":
                        st.caption("Wajib ambil foto bukti penyerahan:")
                        foto = st.camera_input("Kamera", key=f"c_{p['id']}")
                    
                    # TOMBOL SUBMIT HARUS MENJOROK KE DALAM FORM
                    btn_proses = st.form_submit_button("Simpan & Proses")
                    
                    if btn_proses:
                        u_data = {"status": st_baru}
                        
                        if st_baru == "Selesai":
                            if foto:
                                f_name = f"serah_{p['no_resi'] if p.get('no_resi') else p['id']}"
                                url_foto = upload_ke_supabase(foto, "bukti_serah", f_name)
                                
                                if url_foto:
                                    u_data["foto_penerima"] = url_foto
                                    supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                    
                                    no_hp = p['nomor_wa']
                                    if no_hp.startswith('0'): no_hp = '62' + no_hp[1:]
                                    resi_teks = p.get('no_resi', f"#{p['id']}")
                                    msg = f"Halo, Pesanan Resi {resi_teks} SUDAH DITERIMA oleh {p['untuk_siapa']}. Terima kasih."
                                    link_wa = f"https://wa.me/{no_hp}?text={msg.replace(' ', '%20')}"
                                    
                                    st.success("✅ Pesanan Selesai!")
                                    st.link_button("📲 Kabari via WA", link_wa)
                                else:
                                    st.error("Gagal upload foto.")
                            else:
                                st.error("⚠️ Foto penyerahan wajib diambil!")
                        else:
                            supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                            st.success(f"Status diubah: {st_baru}")
                            time.sleep(1)
                            st.rerun()
else:
    st.info("✅ Tidak ada antrian pesanan.")

# =========================================
# TAB 4: RIWAYAT PEMBATALAN (Untuk Cek Refund)
# =========================================
with tab4:
    st.header("❌ Pesanan Dibatalkan WBP/Keluarga")
    st.info("Halaman ini untuk mengecek pesanan yang dibatalkan guna keperluan **Pengembalian Dana (Refund)** atau **Pencatatan Saldo**.")
    
    # Ambil data yang statusnya 'Dibatalkan'
    res_batal = supabase.table("pesanan").select("*").eq("status", "Dibatalkan").order("created_at", desc=True).execute()
    items = res_batal.data

    if not items:
        st.write("Belum ada data pembatalan.")
    else:
        for d in items:
            # Gunakan Expander agar rapi
            with st.expander(f"🚫 {d['nama_pemesan']} ➝ {d['untuk_siapa']} | Resi: {d['no_resi']}"):
                c1, c2 = st.columns(2)
                
                with c1:
                    st.write("Realisasi Item:")
                    st.code(d['item_pesanan'])
                    st.caption(f"No WA: {d['nomor_wa']}")
                    st.caption(f"Metode: {d['cara_bayar']}")
                
                with c2:
                    st.write("**Bukti Transfer Awal:**")
                    if d['bukti_transfer']:
                        st.image(d['bukti_transfer'], width=200)
                    else:
                        st.warning("Tidak ada bukti transfer")

                st.divider()
                
                # --- OPSI TINDAKAN ADMIN ---
                st.write("**Tindakan Admin:**")
                col_act1, col_act2 = st.columns(2)
                
                with col_act1:
                    # Tombol Hapus Permanen (Jika masalah uang sudah kelar)
                    if st.button("🗑️ Hapus Data", key=f"del_{d['id']}"):
                        supabase.table("pesanan").delete().eq("id", d['id']).execute()
                        st.success("Data berhasil dihapus dari arsip.")
                        st.rerun()
                
                with col_act2:
                    # Tombol Tandai Sudah Direfund (Opsional: Ubah status jadi 'Refunded')
                    if st.button("💰 Tandai Sudah Refund/Saldo", key=f"ref_{d['id']}"):
                        # Kita ubah statusnya jadi 'Selesai (Refund)' agar tidak menumpuk di sini
                        # Atau biarkan saja di sini tapi beri tanda (tergantung selera)
                        # Di sini saya contohkan hapus saja, atau Anda bisa buat status baru 'Refunded'
                        st.toast("Admin harus mencatat manual di buku kas.")
