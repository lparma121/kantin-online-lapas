import streamlit as st
from supabase import create_client
import uuid

# --- 1. KONEKSI DATABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Kantin Online Lapas", layout="wide")

# --- 2. NAVIGASI ---
st.sidebar.title("🍱 Menu Utama")
menu = st.sidebar.radio("Pilih Halaman:", ["🏠 Beranda", "🛒 Pesan Barang", "🔍 Lacak Pesanan", "👮 Area Petugas"])

authenticated = False
if menu == "👮 Area Petugas":
    st.sidebar.markdown("---")
    pwd = st.sidebar.text_input("Password Petugas", type="password")
    if pwd == "admin123":
        authenticated = True

# --- 3. HALAMAN BERANDA ---
if menu == "🏠 Beranda":
    st.title("🍱 Kantin Online Lapas")
    st.write("Layanan digital terpadu untuk pemesanan kebutuhan WBP.")

# --- 4. HALAMAN PESAN BARANG ---
elif menu == "🛒 Pesan Barang":
    st.title("Formulir Pesanan")
    res_b = supabase.table("barang").select("*").gt("stok", 0).execute()
    daftar_barang = res_b.data
    
    if not daftar_barang:
        st.warning("Stok barang sedang kosong.")
    else:
        with st.form("order_form"):
            c1, c2 = st.columns(2)
            with c1:
                pemesan = st.text_input("Nama Keluarga")
                untuk = st.text_input("Nama WBP")
                wa = st.text_input("Nomor WhatsApp (Contoh: 08123...)")
            with c2:
                bayar = st.selectbox("Metode Bayar", ["Transfer", "Tunai"])
                pilihan = st.multiselect("Pilih Barang", [b['nama_barang'] for b in daftar_barang])
            
            submit = st.form_submit_button("Kirim Pesanan")
            
            if submit:
                if pemesan and untuk and pilihan and wa:
                    d_pesan = {
                        "nama_pemesan": pemesan, "untuk_siapa": untuk, 
                        "item_pesanan": ", ".join(pilihan), "cara_bayar": bayar, 
                        "status": "Menunggu Antrian", "nomor_wa": wa
                    }
                    res_in = supabase.table("pesanan").insert(d_pesan).execute()
                    id_p = res_in.data[0]['id']

                    for item in pilihan:
                        curr = supabase.table("barang").select("stok").eq("nama_barang", item).execute()
                        if curr.data:
                            stok_baru = curr.data[0]['stok'] - 1
                            supabase.table("barang").update({"stok": stok_baru}).eq("nama_barang", item).execute()
                    
                    st.success(f"✅ Berhasil! ID Pesanan: #{id_p}")
                else:
                    st.error("Mohon lengkapi semua data.")

# --- 5. HALAMAN LACAK ---
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Pesanan")
    id_cari = st.number_input("ID Pesanan", min_value=1, step=1)
    if st.button("Cek"):
        res = supabase.table("pesanan").select("*").eq("id", id_cari).execute()
        if res.data:
            st.info(f"Status: {res.data[0]['status']}")
            if res.data[0]['foto_penerima']:
                st.image(res.data[0]['foto_penerima'])
        else:
            st.error("Data tidak ditemukan.")

# --- PERBAIKAN AREA PETUGAS ---
elif menu == "👮 Area Petugas":
    if not authenticated:
        st.warning("Masukkan password di sidebar.")
    else:
        st.title("Panel Petugas")
        res_p = supabase.table("pesanan").select("*").neq("status", "Selesai").execute()
        
        if res_p.data:
            for p in res_p.data:
                # Gunakan form agar aplikasi tidak refresh otomatis saat ambil foto
                with st.expander(f"Order #{p['id']} - {p['untuk_siapa']}"):
                    with st.form(key=f"form_{p['id']}"):
                        st_baru = st.selectbox("Update Status", ["Menunggu Antrian", "Diproses", "Selesai"])
                        
                        # Kamera diletakkan di dalam form
                        foto = st.camera_input("Ambil Foto Penyerahan")
                        
                        submit_petugas = st.form_submit_button("Simpan & Kirim Notifikasi")
                        
                        if submit_petugas:
                            u_data = {"status": st_baru}
                            
                            # Cek apakah foto berhasil diambil
                            if st_baru == "Selesai" and foto is not None:
                                path = f"bukti_{p['id']}.png"
                                # Proses unggah ke storage
                                supabase.storage.from_("kantin-assets").upload(path, foto.getvalue(), {"upsert": "true"})
                                u_data["foto_penerima"] = supabase.storage.from_("kantin-assets").get_public_url(path)
                                
                                # Simpan perubahan ke database
                                supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                
                                # Siapkan Link WA
                                pesan_wa = f"Halo {p['nama_pemesan']}, pesanan #{p['id']} untuk {p['untuk_siapa']} TELAH DITERIMA petugas. Terima kasih."
                                no_hp = p['nomor_wa']
                                if no_hp.startswith('0'): no_hp = '62' + no_hp[1:]
                                wa_url = f"https://wa.me/{no_hp}?text={pesan_wa.replace(' ', '%20')}"
                                
                                st.success("Data & Foto Berhasil Tersimpan!")
                                st.link_button("📲 Kirim WhatsApp Sekarang", wa_url)
                            elif st_baru == "Selesai" and foto is None:
                                st.error("Foto wajib diambil jika status Selesai!")
                            else:
                                # Update status biasa tanpa foto
                                supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                st.rerun()
        else:
            st.info("Belum ada antrian pesanan.")

