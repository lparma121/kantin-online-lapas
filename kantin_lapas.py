import streamlit as st
from supabase import create_client

# --- KONEKSI DATABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Kantin Online Lapas", layout="wide")

# --- NAVIGASI ---
st.sidebar.title("🍱 Menu Keluarga")

# --- HALAMAN BERANDA ---
if menu == "🏠 Beranda":
    st.title("🍱 Kantin Online Lapas")
    st.write("Layanan pemesanan kebutuhan WBP secara praktis dan transparan.")
    st.info("Pilih menu di samping untuk mulai memesan.")

# --- HALAMAN PESAN BARANG ---
elif menu == "🛒 Pesan Barang":
    st.title("Formulir Pesanan")
    res_b = supabase.table("barang").select("*").gt("stok", 0).execute()
    daftar_barang = res_b.data
    
    if not daftar_barang:
        st.warning("Maaf, stok barang sedang kosong.")
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
                    
                    st.success(f"✅ Berhasil! Nomor Pesanan: #{id_p}")
                else:
                    st.error("Lengkapi semua data.")

# --- HALAMAN LACAK ---
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Pesanan")
    id_cari = st.number_input("ID Pesanan", min_value=1, step=1)
    if st.button("Cek Status"):
        res = supabase.table("pesanan").select("*").eq("id", id_cari).execute()
        if res.data:
            st.info(f"Status: **{res.data[0]['status']}**")
            if res.data[0]['foto_penerima']:
                st.image(res.data[0]['foto_penerima'], caption="Bukti Penyerahan")
        else:
            st.error("ID Pesanan tidak ditemukan.")

