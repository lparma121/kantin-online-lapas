import streamlit as st
from supabase import create_client

# --- KONEKSI DATABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Panel Petugas", layout="wide")

st.title("👮 Panel Pengelolaan Petugas")

# Proteksi Login di halaman ini saja
pwd = st.sidebar.text_input("Password Petugas", type="password")
if pwd != "admin123": # Ganti password Anda
    st.warning("Halaman ini hanya untuk petugas. Silakan masukkan password di sidebar.")
    st.stop()

# --- KONTEN PETUGAS ---
# Dashboard Stok
with st.expander("📦 Monitor Stok Kantin"):
    s_res = supabase.table("barang").select("nama_barang", "stok").execute()
    st.table(s_res.data)

# Antrian Pesanan
res_p = supabase.table("pesanan").select("*").neq("status", "Selesai").execute()

if res_p.data:
    for p in res_p.data:
        with st.expander(f"Order #{p['id']} - {p['untuk_siapa']}"):
            st.write(f"Isi: {p['item_pesanan']}")
            
            with st.form(key=f"form_{p['id']}"):
                st_baru = st.selectbox("Update Status", ["Menunggu Antrian", "Diproses", "Selesai"])
                foto = st.camera_input("Ambil Foto Penyerahan")
                
                if st.form_submit_button("Simpan & Kirim Notifikasi"):
                    u_data = {"status": st_baru}
                    
                    if st_baru == "Selesai":
                        if foto:
                            path = f"bukti_{p['id']}.png"
                            supabase.storage.from_("KANTIN-ASSETS").upload(path, foto.getvalue(), {"upsert": "true"})
                            u_data["foto_penerima"] = supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
                            
                            supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                            
                            # Link WA
                            no_hp = p['nomor_wa']
                            if no_hp.startswith('0'): no_hp = '62' + no_hp[1:]
                            pesan_wa = f"Halo {p['nama_pemesan']}, pesanan #{p['id']} untuk {p['untuk_siapa']} TELAH SELESAI. Terima kasih."
                            wa_url = f"https://wa.me/{no_hp}?text={pesan_wa.replace(' ', '%20')}"
                            
                            st.success("✅ Berhasil!")
                            st.link_button("📲 Kirim WhatsApp", wa_url)
                        else:
                            st.error("Wajib ambil foto untuk status Selesai!")
                    else:
                        supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                        st.rerun()
else:
    st.info("Tidak ada antrian pesanan.")
