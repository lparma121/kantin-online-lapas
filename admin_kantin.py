import streamlit as st
from supabase import create_client
import time
from PIL import Image
import io

# --- KONEKSI DATABASE ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(URL, KEY)
except:
    st.error("Secret Supabase belum disetting!")
    st.stop()

st.set_page_config(page_title="Panel Admin Kantin", layout="wide", page_icon="👮")

# --- LOGIN PROTEKSI ---
# (Tips: Ganti password ini dengan yang lebih sulit nanti)
pwd = st.sidebar.text_input("🔑 Password Admin", type="password")
if pwd != "admin123":
    st.warning("🔒 Silakan login terlebih dahulu.")
    st.stop()

st.sidebar.success("✅ Login Berhasil")
st.sidebar.markdown("---")

# --- NAVIGASI HALAMAN (Menu Sidebar) ---
menu_admin = st.sidebar.radio("Navigasi Menu", ["📋 Daftar Pesanan", "📦 Manajemen Menu"])

# --- FUNGSI BANTUAN (HELPER) ---
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
        return None

def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# ==============================================================================
# HALAMAN 1: MANAJEMEN MENU (Edit & Tambah Barang)
# ==============================================================================
if menu_admin == "📦 Manajemen Menu":
    st.title("📦 Manajemen Menu Kantin")
    
    tab_edit, tab_tambah = st.tabs(["✏️ Edit Stok & Harga", "➕ Tambah Menu Baru"])

    # --- TAB EDIT ---
    with tab_edit:
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
                            st.markdown("**Ganti Foto**")
                            uploaded_file = st.file_uploader("Upload File Baru", type=['png', 'jpg', 'jpeg'])
                            url_manual = st.text_input("Atau Paste Link URL", value=detail.get('gambar_url', ""))

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

    # --- TAB TAMBAH ---
    with tab_tambah:
        st.subheader("Tambah Menu Baru")
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            with c1:
                nama_baru = st.text_input("Nama Produk")
                harga_baru = st.number_input("Harga (Rp)", min_value=0, step=500, value=5000)
            with c2:
                stok_awal = st.number_input("Stok Awal", min_value=1, value=10)
                img_file = st.file_uploader("Upload Foto", type=['png', 'jpg', 'jpeg'])
                img_url_text = st.text_input("Atau Link URL")
            
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

# ==============================================================================
# HALAMAN 2: DAFTAR PESANAN (Proses, Selesai, Batal)
# ==============================================================================
elif menu_admin == "📋 Daftar Pesanan":
    st.title("📋 Verifikasi & Proses Pesanan")
    
    # --- FITUR PENCARIAN RESI ---
    c_search, c_btn = st.columns([3, 1])
    with c_search:
        cari_resi = st.text_input("🔍 Cari Nomor Resi", placeholder="Ketik nomor resi...")
    with c_btn:
        st.write("") # Spasi
        st.write("") 
        if st.button("🔄 Refresh Data"):
            st.rerun()

    filter_data = None
    if cari_resi:
        res = supabase.table("pesanan").select("*").eq("no_resi", cari_resi).execute()
        filter_data = res.data
        if not filter_data:
            st.error(f"Resi '{cari_resi}' tidak ditemukan.")
        else:
            st.success(f"Ditemukan 1 pesanan untuk resi: {cari_resi}")

    # --- TABS PESANAN ---
    tab1, tab2, tab3, tab4 = st.tabs(["📥 Pesanan Masuk", "📦 Sedang Diproses", "✅ Riwayat Selesai", "❌ Dibatalkan"])

    # FUNGSI RENDER KARTU PESANAN AGAR KODE LEBIH RAPI
    def render_pesanan(p_list, status_tab):
        if not p_list:
            st.info("Tidak ada data.")
            return

        for p in p_list:
            with st.container(border=True):
                cols = st.columns([1, 2, 2])
                with cols[0]:
                    st.subheader(f"#{p['id']}")
                    st.caption(f"Resi: {p.get('no_resi', '-')}")
                    
                    if p.get('bukti_transfer'):
                        st.image(p['bukti_transfer'], caption="Bukti TF", width=150)
                    else:
                        st.error("Belum ada bukti TF")
                    
                    if p.get('nota_url'):
                        st.link_button("🧾 Nota", p['nota_url'])

                with cols[1]:
                    st.write(f"**Pengirim:** {p['nama_pemesan']}")
                    st.write(f"**Penerima:** {p['untuk_siapa']}")
                    st.write(f"**Metode:** {p.get('cara_bayar', '-')}")
                    st.code(f"Isi: {p['item_pesanan']}")

                with cols[2]:
                    with st.form(key=f"form_{p['id']}"):
                        st.write("**Tindakan:**")
                        opsi = ["Menunggu Verifikasi", "Pembayaran Valid (Diproses)", "Selesai"]
                        
                        # Set Default Index sesuai status sekarang
                        try:
                            idx = opsi.index(p['status'])
                        except:
                            idx = 0 
                        
                        st_baru = st.selectbox("Update Status", opsi, index=idx, key=f"s_{p['id']}")
                        
                        foto = None
                        if st_baru == "Selesai":
                            st.caption("📷 Foto penyerahan barang:")
                            foto = st.camera_input("Ambil Foto", key=f"c_{p['id']}")
                        
                        btn_proses = st.form_submit_button("Simpan & Proses")
                        
                        if btn_proses:
                            u_data = {"status": st_baru}
                            
                            # Logika simpan foto jika status selesai
                            if st_baru == "Selesai":
                                if foto:
                                    f_name = f"serah_{p['no_resi'] if p.get('no_resi') else p['id']}"
                                    url_foto = upload_ke_supabase(foto, "bukti_serah", f_name)
                                    if url_foto:
                                        u_data["foto_penerima"] = url_foto
                                        supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                        
                                        # Kirim Link WA
                                        no_hp = p.get('nomor_wa', '')
                                        if no_hp and no_hp.startswith('0'): no_hp = '62' + no_hp[1:]
                                        msg = f"Halo, Pesanan Resi {p.get('no_resi')} SUDAH DITERIMA oleh {p['untuk_siapa']}. Terima kasih."
                                        link_wa = f"https://wa.me/{no_hp}?text={msg.replace(' ', '%20')}"
                                        
                                        st.success("✅ Pesanan Selesai!")
                                        st.link_button("📲 Kabari via WA", link_wa)
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error("Gagal upload foto.")
                                else:
                                    st.error("⚠️ Foto penyerahan wajib diambil!")
                            else:
                                supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                st.success(f"Status diubah: {st_baru}")
                                time.sleep(1)
                                st.rerun()

    # --- LOGIKA ISI TAB ---
    
    # Jika sedang mencari resi, abaikan tabs dan tampilkan hasil
    if filter_data:
        st.warning("Menampilkan hasil pencarian:")
        render_pesanan(filter_data, "Search")
    
    else:
      # TAB 1: PESANAN MASUK (Menunggu Verifikasi)
        with tab1:
            st.header("📥 Pesanan Baru Masuk")
            
            # Ambil data
            res = supabase.table("pesanan").select("*").eq("status", "Menunggu Verifikasi").order("id", desc=True).execute()
            
            if not res.data:
                st.info("✅ Tidak ada antrian pesanan baru.")
            else:
                for p in res.data:
                    with st.container(border=True):
                        cols = st.columns([1, 2, 2])
                        
                        # KOLOM 1: BUKTI TRANSFER
                        with cols[0]:
                            st.subheader(f"#{p['id']}")
                            st.caption(f"Resi: {p.get('no_resi', '-')}")
                            
                            if p.get('bukti_transfer'):
                                st.image(p['bukti_transfer'], caption="Cek Bukti TF", width=150)
                                st.link_button("🔍 Zoom Gambar", p['bukti_transfer'])
                            else:
                                st.error("❌ TIDAK ADA BUKTI")
                                st.caption("Hati-hati penipuan!") 
                        
                        # KOLOM 2: DETAIL PESANAN
                        with cols[1]:
                            st.write(f"**Pengirim:** {p['nama_pemesan']}")
                            st.write(f"**Penerima:** {p['untuk_siapa']}")
                            st.info(f"Metode: {p.get('cara_bayar', '-')}")
                            st.code(f"Isi: {p['item_pesanan']}")

                        # KOLOM 3: TINDAKAN ADMIN (VERSI EXPANDER - LEBIH STABIL)
                        with cols[2]:
                            st.write("---")
                            st.write("**Keputusan:**")
                            
                            # 1. TOMBOL TERIMA (Hijau)
                            if st.button("✅ TERIMA PESANAN", key=f"acc_{p['id']}", type="primary", use_container_width=True):
                                supabase.table("pesanan").update({"status": "Pembayaran Valid (Diproses)"}).eq("id", p['id']).execute()
                                st.success("Pesanan diterima!")
                                time.sleep(1)
                                st.rerun()
                            
                            st.write("") # Spasi sedikit
                            
                            # 2. PENGAMAN HAPUS (Menu Lipat)
                            # Tombol hapus sembunyi di dalam sini. Admin harus klik panah dulu baru bisa hapus.
                            with st.expander("🗑️ Opsi Tolak / Hapus"):
                                st.warning("⚠️ **Yakin hapus pesanan ini?**")
                                st.caption("Data akan hilang permanen dan tidak bisa dikembalikan.")
                                
                                # Tombol Merah "Kill Switch"
                                if st.button("🔥 YA, HAPUS SEKARANG", key=f"del_fix_{p['id']}", use_container_width=True):
                                    supabase.table("pesanan").delete().eq("id", p['id']).execute()
                                    st.error("Data berhasil dihapus.")
                                    time.sleep(1)
                                    st.rerun()
        # TAB 2: SEDANG DIPROSES
        with tab2:
            st.header("📦 Sedang Disiapkan / Diproses")
            res = supabase.table("pesanan").select("*").eq("status", "Pembayaran Valid (Diproses)").order("id", desc=True).execute()
            render_pesanan(res.data, "Proses")

        # TAB 3: SELESAI
        with tab3:
            st.header("✅ Riwayat Selesai")
            # Limit 20 terakhir agar tidak berat
            res = supabase.table("pesanan").select("*").eq("status", "Selesai").order("id", desc=True).limit(20).execute()
            
            if res.data:
                for p in res.data:
                    with st.expander(f"✅ {p['no_resi']} - {p['untuk_siapa']}"):
                        st.write(f"Item: {p['item_pesanan']}")
                        if p.get('foto_penerima'):
                            st.image(p['foto_penerima'], caption="Bukti Serah Terima", width=200)
                        else:
                            st.write("Tidak ada foto bukti serah.")
            else:
                st.info("Belum ada riwayat selesai.")

      # TAB 4: RIWAYAT PEMBATALAN & CEK VOUCHER (ANTI-FRAUD)
        with tab4:
            st.header("🎫 Audit Keamanan Voucher")
            
            st.error("""
            🛑 **PENTING UNTUK ADMIN:**
            Sebelum menerima Voucher, **WAJIB CEK 'BUKTI TF ASLI'** di kolom kanan!
            Jangan terima Voucher jika Pesanan Asalnya ternyata **struk palsu/sampah**, meskipun status Vouchernya Aktif.
            """)
            
            c_cek, c_info = st.columns([3, 1])
            with c_cek:
                cek_kode = st.text_input("🔍 Scan Kode Resi / Voucher")

            query = supabase.table("pesanan").select("*").in_("status", ["Dibatalkan", "Voucher Sudah Dipakai"]).order("id", desc=True)
            
            if cek_kode:
                bersih_kode = cek_kode.replace("REF-", "").strip()
                query = query.eq("no_resi", bersih_kode)
            
            res_batal = query.execute()
            items = res_batal.data

            if not items:
                st.info("Data tidak ditemukan.")
            else:
                for d in items:
                    # LOGIKA WARNA STATUS
                    if d['status'] == "Dibatalkan":
                        status_text = "VOUCHER BELUM DIPAKAI"
                        bg_color = "#07213d" # biru tua
                        border_color = "green"
                    else:
                        status_text = "SUDAH TERPAKAI"
                        bg_color = "#fff5f5" # Merah muda
                        border_color = "red"
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 2px solid {border_color}; padding: 10px; border-radius: 10px; background-color: {bg_color}; margin-bottom: 10px;">
                            <h3 style="margin:0;">{d['no_resi']}</h3>
                            <b>STATUS: {status_text}</b>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_kiri, col_kanan = st.columns([1.5, 1])
                        
                        # DATA PESANAN
                        with col_kiri:
                            st.write(f"👤 **Pemilik:** {d['nama_pemesan']}")
                            st.write(f"📦 **Item Asli:** `{d['item_pesanan']}`")
                            st.caption(f"📅 Tanggal: {d.get('created_at', '-')[:16]}")
                            
                            # TOMBOL EKSEKUSI (MODIFIKASI: ADA TOMBOL TOLAK)
                            if d['status'] == "Dibatalkan":
                                st.write("---")
                                st.markdown("**👇 TINDAKAN ADMIN:**")
                                st.write("Cek mutasi bank. Apakah uangnya benar-benar masuk?")
                                
                                # Bagi menjadi 2 kolom tombol
                                c_sah, c_tolak = st.columns(2)
                                
                                # --- TOMBOL 1: SAHKAN (Terima) ---
                                with c_sah:
                                    if st.button("✅ SAHKAN (Valid)", key=f"claim_{d['id']}", type="primary", use_container_width=True):
                                        # Ubah status jadi Terpakai (Valid)
                                        supabase.table("pesanan").update({"status": "Voucher Sudah Dipakai"}).eq("id", d['id']).execute()
                                        st.success("Voucher berhasil divalidasi!")
                                        time.sleep(1)
                                        st.rerun()
                                
                                # --- TOMBOL 2: TOLAK (Hanguskan) ---
                                with c_tolak:
                                    if st.button("🚫 TOLAK (Fraud)", key=f"deny_{d['id']}", use_container_width=True):
                                        # Ubah status jadi Ditolak (Supaya kode mati & tidak bisa dipakai lagi)
                                        supabase.table("pesanan").update({"status": "Voucher Ditolak / Hangus"}).eq("id", d['id']).execute()
                                        st.error("Voucher telah DIHANGUSKAN/DITOLAK.")
                                        time.sleep(1)
                                        st.rerun()

                        # BUKTI TRANSFER (THE MOMENT OF TRUTH)
                        with col_kanan:
                            st.write("🔍 **BUKTI TRANSFER ASAL:**")
                            if d.get('bukti_transfer'):
                                st.image(d['bukti_transfer'], use_container_width=True)
                                st.caption("👆 Cek gambar ini! Asli atau Palsu?")
                            else:
                                st.error("❌ TIDAK ADA BUKTI TRANSFER!")
                                st.error("JANGAN TERIMA VOUCHER INI!")
                        
                        st.divider()
