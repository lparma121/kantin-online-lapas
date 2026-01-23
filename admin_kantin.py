import streamlit as st
from supabase import create_client
import time

# --- KONEKSI DATABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Panel Admin Kantin", layout="wide")
st.title("👮 Panel Admin & Stok")

# --- LOGIN PROTEKSI ---
pwd = st.sidebar.text_input("Password Admin", type="password")
if pwd != "admin123":
    st.warning("🔒 Silakan login terlebih dahulu.")
    st.stop()

# --- FUNGSI BANTUAN: UPLOAD GAMBAR ---
def upload_gambar(file, nama_unik):
    """Mengupload gambar ke bucket KANTIN-ASSETS di folder 'produk/'"""
    try:
        path = f"produk/{nama_unik}"
        supabase.storage.from_("KANTIN-ASSETS").upload(
            path, 
            file.getvalue(), 
            {"upsert": "true", "content-type": file.type}
        )
        return supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
    except Exception as e:
        st.error(f"Gagal upload gambar: {e}")
        return None

# --- FUNGSI FORMAT RUPIAH ---
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# =========================================
# 1. MANAJEMEN PRODUK (FITUR BARU)
# =========================================
st.header("📦 Manajemen Produk")
tab1, tab2 = st.tabs(["📝 Edit Barang & Stok", "➕ Tambah Menu Baru"])

# --- TAB 1: EDIT BARANG ---
with tab1:
    # Ambil data terbaru
    res = supabase.table("barang").select("*").order("nama_barang").execute()
    items = res.data
    
    if items:
        col_kiri, col_kanan = st.columns([1, 2])
        
        with col_kiri:
            st.subheader("Pilih Produk")
            pilihan = st.selectbox("Daftar Menu:", [b['nama_barang'] for b in items], label_visibility="collapsed")
            
            # Ambil detail barang yang dipilih
            detail = next((item for item in items if item['nama_barang'] == pilihan), None)
            
            if detail:
                st.info(f"Stok: {detail['stok']} | Harga: {format_rupiah(detail.get('harga', 0))}")
                # Preview Gambar Kecil
                if detail.get('gambar_url'):
                    st.image(detail['gambar_url'], caption="Foto Saat Ini", use_container_width=True)
                else:
                    st.warning("Belum ada foto.")

        with col_kanan:
            if detail:
                st.subheader(f"Edit: {detail['nama_barang']}")
                with st.form("edit_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_stok = st.number_input("Update Stok", value=detail['stok'], min_value=0)
                        new_harga = st.number_input("Update Harga (Rp)", value=int(detail.get('harga', 0)), min_value=0, step=500)
                    
                    with c2:
                        st.markdown("**Ganti Foto Produk**")
                        uploaded_file = st.file_uploader("Upload File (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
                        url_manual = st.text_input("Atau Paste Link URL Gambar", value=detail.get('gambar_url', ""))

                    btn_update = st.form_submit_button("💾 Simpan Perubahan")
                    
                    if btn_update:
                        update_data = {"stok": new_stok, "harga": new_harga}
                        
                        # Logika Upload Gambar
                        if uploaded_file:
                            # Buat nama file unik pakai timestamp
                            file_name = f"produk_{detail['id']}_{int(time.time())}.png"
                            url_baru = upload_gambar(uploaded_file, file_name)
                            if url_baru:
                                update_data["gambar_url"] = url_baru
                        elif url_manual != detail.get('gambar_url'):
                            update_data["gambar_url"] = url_manual
                        
                        # Eksekusi Update
                        supabase.table("barang").update(update_data).eq("id", detail['id']).execute()
                        st.success(f"✅ Data {pilihan} berhasil diperbarui!")
                        time.sleep(1)
                        st.rerun()

                # Tombol Hapus Produk
                with st.expander(f"🗑️ Hapus Menu '{detail['nama_barang']}'"):
                    st.warning("Peringatan: Menu yang dihapus tidak bisa dikembalikan.")
                    if st.button("Hapus Permanen", key="hapus_btn"):
                        supabase.table("barang").delete().eq("id", detail['id']).execute()
                        st.error("Produk telah dihapus.")
                        time.sleep(1)
                        st.rerun()

# --- TAB 2: TAMBAH BARANG ---
with tab2:
    st.subheader("Input Menu Baru")
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        with c1:
            nama_baru = st.text_input("Nama Produk (Wajib)")
            harga_baru = st.number_input("Harga (Rp)", min_value=0, step=500, value=5000)
        with c2:
            stok_awal = st.number_input("Stok Awal", min_value=1, value=10)
            img_file = st.file_uploader("Upload Foto Produk", type=['png', 'jpg', 'jpeg'])
            img_url_text = st.text_input("Atau Link URL Gambar")
        
        submit_add = st.form_submit_button("➕ Tambahkan ke Database")
        
        if submit_add:
            if nama_baru:
                # Cek duplikat nama
                cek = supabase.table("barang").select("id").eq("nama_barang", nama_baru).execute()
                if cek.data:
                    st.error("Produk dengan nama ini sudah ada!")
                else:
                    final_url = ""
                    # Handle Gambar
                    if img_file:
                        f_name = f"new_{int(time.time())}.png"
                        final_url = upload_gambar(img_file, f_name)
                    elif img_url_text:
                        final_url = img_url_text
                    
                    # Insert Data
                    new_data = {
                        "nama_barang": nama_baru,
                        "stok": stok_awal,
                        "harga": harga_baru,
                        "gambar_url": final_url
                    }
                    supabase.table("barang").insert(new_data).execute()
                    st.success(f"🎉 {nama_baru} berhasil ditambahkan ke menu!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Nama produk tidak boleh kosong.")

st.markdown("---")

# =========================================
# 2. ANTRIAN PESANAN (TETAP ADA)
# =========================================
st.header("📋 Antrian Pesanan Masuk")
if st.button("🔄 Refresh Data Pesanan"):
    st.rerun()

res_p = supabase.table("pesanan").select("*").neq("status", "Selesai").order("id").execute()

if res_p.data:
    for p in res_p.data:
        with st.container(border=True):
            cols = st.columns([3, 2])
            with cols[0]:
                st.subheader(f"Order #{p['id']}")
                st.markdown(f"**Pemesan:** {p['nama_pemesan']} ({p['nomor_wa']})")
                st.markdown(f"**Untuk:** {p['untuk_siapa']}")
                st.info(f"🛒 **Isi:** {p['item_pesanan']}")
                st.caption(f"Metode: {p.get('cara_bayar', '-')}")
            
            with cols[1]:
                with st.form(key=f"form_{p['id']}"):
                    st.write("Tindakan:")
                    st_baru = st.selectbox("Update Status", ["Menunggu Antrian", "Diproses", "Selesai"], key=f"sel_{p['id']}")
                    
                    # Input Foto hanya relevan jika selesai
                    foto = st.camera_input("Bukti Penyerahan", key=f"cam_{p['id']}")
                    
                    if st.form_submit_button("Simpan & Kirim WA"):
                        u_data = {"status": st_baru}
                        
                        if st_baru == "Selesai":
                            if foto:
                                try:
                                    path = f"bukti_{p['id']}.png"
                                    # Upload bukti
                                    supabase.storage.from_("KANTIN-ASSETS").upload(path, foto.getvalue(), {"upsert": "true", "content-type": "image/png"})
                                    u_data["foto_penerima"] = supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
                                    
                                    # Update DB
                                    supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                    
                                    # Kirim WA
                                    no_hp = p['nomor_wa']
                                    if no_hp.startswith('0'): no_hp = '62' + no_hp[1:]
                                    pesan_wa = f"Halo {p['nama_pemesan']}, pesanan #{p['id']} untuk {p['untuk_siapa']} SUDAH DISERAHKAN. Terima kasih."
                                    wa_url = f"https://wa.me/{no_hp}?text={pesan_wa.replace(' ', '%20')}"
                                    
                                    st.success("✅ Pesanan Selesai!")
                                    st.link_button("📲 Kirim WhatsApp", wa_url)
                                except Exception as e:
                                    st.error(f"Gagal: {e}")
                            else:
                                st.error("⚠️ Wajib ambil foto bukti penyerahan!")
                        else:
                            supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                            st.success("Status diperbarui!")
                            time.sleep(1)
                            st.rerun()
else:
    st.info("✅ Tidak ada antrian pesanan saat ini.")
