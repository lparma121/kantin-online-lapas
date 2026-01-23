import streamlit as st
from supabase import create_client
import time
from PIL import Image, ImageDraw, ImageFont
import io
import random
import string

# --- KONEKSI DATABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Kantin Lapas Online", page_icon="🍱", layout="wide")

# --- CSS CUSTOM ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    div[data-testid="stVerticalBlock"] > div { background-color: #f9f9f9; border-radius: 10px; padding: 10px; }
    .harga-tag { color: #d9534f; font-size: 16px; font-weight: bold; }
    
    /* Sticky Checkout */
    div[data-testid="column"]:nth-of-type(2) {
        position: sticky; top: 80px; align-self: start;
        background-color: #ffffff; padding: 20px; border-radius: 15px;
        border: 1px solid #e0e0e0; box-shadow: 0px 4px 10px rgba(0,0,0,0.05); z-index: 100;
    }
    @media (max-width: 640px) { div[data-testid="column"]:nth-of-type(2) { position: static; top: auto; } }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI FORMAT RUPIAH ---
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# --- FUNGSI GENERATE RESI ---
def generate_resi():
    # Format: KANTIN-TGL-ACAK (Contoh: KANTIN-2301-X7Z9)
    tanggal = time.strftime("%d%m")
    acak = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"KANTIN-{tanggal}-{acak}"

# --- FUNGSI MEMBUAT GAMBAR NOTA (STRUK) ---
def buat_struk_image(data_pesanan, list_keranjang, total_bayar, resi):
    # Buat Kanvas Putih Panjang
    width, height = 500, 700
    img = Image.new('RGB', (width, height), color='white')
    d = ImageDraw.Draw(img)
    
    # Load Font (Default)
    try:
        # Gunakan font default sistem jika tidak ada font khusus
        font_header = ImageFont.load_default() 
        font_body = ImageFont.load_default()
    except:
        pass

    # Warna
    black = (0, 0, 0)
    gray = (100, 100, 100)
    
    # Header
    d.text((160, 20), "KANTIN LAPAS ONLINE", fill=black, align="center")
    d.text((150, 40), "Bukti Transaksi Resmi", fill=gray, align="center")
    d.line((20, 70, 480, 70), fill=black, width=2)
    
    # Detail Info
    y = 90
    d.text((30, y), f"NO. RESI  : {resi}", fill=black); y+=25
    d.text((30, y), f"TANGGAL   : {time.strftime('%d-%m-%Y %H:%M')}", fill=black); y+=25
    d.text((30, y), f"PENGIRIM  : {data_pesanan['nama_pemesan']}", fill=black); y+=25
    d.text((30, y), f"PENERIMA  : {data_pesanan['untuk_siapa']}", fill=black); y+=25
    
    d.line((20, y+10, 480, y+10), fill=gray, width=1)
    y += 30
    
    # List Barang
    d.text((30, y), "ITEM PESANAN:", fill=black); y+=25
    for item in list_keranjang:
        nama = item['nama'][:30] # Potong jika kepanjangan
        harga = format_rupiah(item['harga'])
        d.text((30, y), f"- {nama}", fill=black)
        d.text((350, y), harga, fill=black)
        y += 25
        
    d.line((20, y+10, 480, y+10), fill=black, width=2)
    y += 30
    
    # Total
    d.text((30, y), "TOTAL BAYAR", fill=black)
    d.text((350, y), format_rupiah(total_bayar), fill=(200, 0, 0)) # Merah
    y += 50
    
    # Footer
    d.text((120, y), "TERIMA KASIH ATAS KUNJUNGAN ANDA", fill=gray)
    d.text((150, y+20), "Simpan resi ini untuk pelacakan", fill=gray)
    
    # Simpan ke Buffer
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    return buf.getvalue()

# --- FUNGSI UPLOAD ---
def upload_file(file_bytes, folder, nama_file):
    try:
        path = f"{folder}/{nama_file}"
        supabase.storage.from_("KANTIN-ASSETS").upload(path, file_bytes, {"upsert": "true", "content-type": "image/jpeg"})
        return supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
    except Exception as e:
        return None

# --- SESSION STATE KERANJANG ---
if 'keranjang' not in st.session_state: st.session_state.keranjang = []

def tambah_ke_keranjang(item, harga):
    st.session_state.keranjang.append({"nama": item, "harga": harga})
    st.toast(f"🛒 {item} masuk keranjang!")

def reset_keranjang(): st.session_state.keranjang = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛒 Keranjang")
    if len(st.session_state.keranjang) > 0:
        total = sum(i['harga'] for i in st.session_state.keranjang)
        st.write(f"Item: {len(st.session_state.keranjang)} | Total: **{format_rupiah(total)}**")
        if st.button("❌ Kosongkan"): reset_keranjang(); st.rerun()
    else: st.info("Kosong.")

# --- NAVIGASI ---
menu = st.sidebar.radio("Navigasi", ["🏠 Beranda", "🛍️ Pesan Barang", "🔍 Lacak Pesanan"])

# =========================================
# 1. BERANDA
# =========================================
# =========================================
# 1. HALAMAN BERANDA
# =========================================
if menu == "🏠 Beranda":
    # KITA GUNAKAN 3 KOLOM: 
    # Kolom kiri & kanan kosong, kolom tengah isi gambar
    # Angka [1, 2, 1] berarti kolom tengah 2x lebih lebar dari sisi-sisinya
    c_kiri, c_tengah, c_kanan = st.columns([1, 2, 1])
    
    with c_tengah:
        # Gambar masuk di tengah
        st.image("https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
    
    st.title("Selamat Datang di Kantin Online Lapas Arga Makmur")
    st.markdown("### *Aman, Cepat, dan Transparan.*")
    
    c1, c2, c3 = st.columns(3)
    with c1: st.info("📦 **Stok Terjamin**")
    with c2: st.success("⚡ **Proses Cepat**")
    with c3: st.warning("🛡️ **Transparan**")

# =========================================
# 2. PESAN BARANG (UPLOAD BUKTI & RESI)
# =========================================
elif menu == "🛍️ Pesan Barang":
    col_etalase, col_checkout = st.columns([2.5, 1.2], gap="large")

    with col_etalase:
        st.title("🛍️ Etalase Menu")
        res_b = supabase.table("barang").select("*").gt("stok", 0).order('nama_barang').execute()
        items = res_b.data
        if items:
            cols = st.columns(3)
            for i, item in enumerate(items):
                with cols[i % 3]:
                    with st.container(border=True):
                        img = item['gambar_url'] if item.get('gambar_url') else "https://cdn-icons-png.flaticon.com/512/2515/2515263.png"
                        st.image(img, use_container_width=True)
                        st.write(f"**{item['nama_barang']}**")
                        st.caption(f"{format_rupiah(item['harga'])} | Stok: {item['stok']}")
                        if st.button("➕ Beli", key=f"b_{item['id']}"):
                            tambah_ke_keranjang(item['nama_barang'], item['harga'])
                            st.rerun()

    with col_checkout:
        st.header("📝 Checkout")
        
        if not st.session_state.keranjang:
            st.info("Keranjang kosong.")
        else:
            with st.container(border=True):
                total_duit = sum(i['harga'] for i in st.session_state.keranjang)
                st.markdown(f"### Total: {format_rupiah(total_duit)}")
                st.divider()

                with st.form("form_pesan"):
                    pemesan = st.text_input("Nama Pengirim")
                    untuk = st.text_input("Nama WBP (Penerima)")
                    wa = st.text_input("WhatsApp")
                    
                    bayar = st.selectbox("Metode Pembayaran", ["Transfer Bank (BRI/BCA)", "E-Wallet (DANA/Gopay)"])
                    
                    st.info("ℹ️ Silakan Transfer ke: **BRI 1234-5678-900 (Koperasi)**")
                    
                    # INPUT BUKTI TRANSFER
                    bukti_tf = st.file_uploader("📤 Upload Bukti Transfer (Wajib)", type=['jpg', 'png', 'jpeg'])

                    submit = st.form_submit_button("✅ KIRIM PESANAN", type="primary")
                    
                    if submit:
                        if pemesan and untuk and wa and bukti_tf:
                            # 1. Generate Nomor Resi
                            no_resi = generate_resi()
                            
                            # 2. Upload Bukti Transfer
                            file_bukti = bukti_tf.getvalue()
                            url_bukti = upload_file(file_bukti, "bukti_transfer", f"tf_{no_resi}.jpg")
                            
                            # 3. Buat Gambar Nota (Struk)
                            file_nota = buat_struk_image(
                                {"nama_pemesan": pemesan, "untuk_siapa": untuk}, 
                                st.session_state.keranjang, 
                                total_duit, 
                                no_resi
                            )
                            url_nota = upload_file(file_nota, "nota", f"nota_{no_resi}.jpg")
                            
                            # 4. Simpan ke Database
                            list_items = ", ".join([b['nama'] for b in st.session_state.keranjang])
                            data_db = {
                                "nama_pemesan": pemesan, "untuk_siapa": untuk,
                                "item_pesanan": list_items, "cara_bayar": bayar,
                                "status": "Menunggu Verifikasi", "nomor_wa": wa,
                                "no_resi": no_resi,
                                "bukti_transfer": url_bukti,
                                "nota_url": url_nota
                            }
                            supabase.table("pesanan").insert(data_db).execute()
                            
                            # 5. Kurangi Stok
                            for b in st.session_state.keranjang:
                                cur = supabase.table("barang").select("stok").eq("nama_barang", b['nama']).execute()
                                if cur.data:
                                    supabase.table("barang").update({"stok": cur.data[0]['stok']-1}).eq("nama_barang", b['nama']).execute()

                            reset_keranjang()
                            
                            # TAMPILAN SUKSES & DOWNLOAD RESI
                            st.success("🎉 Pesanan Berhasil!")
                            st.write(f"Nomor Resi: **{no_resi}**")
                            
                            # Tampilkan Nota untuk didownload
                            st.image(file_nota, caption="Nota Resmi", width=300)
                            st.download_button("📥 Download Nota (JPG)", data=file_nota, file_name=f"{no_resi}.jpg", mime="image/jpeg")
                            
                        else:
                            st.error("Mohon lengkapi semua data & upload bukti transfer!")

# =========================================
# 3. LACAK PESANAN (PAKAI NO RESI)
# =========================================
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Status Pesanan")
    resi_input = st.text_input("Masukkan Nomor Resi (Contoh: KANTIN-2301-X7Z9)")
    
    if st.button("🔍 Cek Resi"):
        if resi_input:
            # Cari berdasarkan kolom no_resi
            res = supabase.table("pesanan").select("*").eq("no_resi", resi_input).execute()
            if res.data:
                d = res.data[0]
                st.success(f"Pesanan Ditemukan: {d['no_resi']}")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Penerima:** {d['untuk_siapa']}")
                    st.write(f"**Item:** {d['item_pesanan']}")
                with c2:
                    st.write(f"**Status Terkini:**")
                    # Progress Bar logic
                    stat = d['status']
                    val = 10 if stat == "Menunggu Verifikasi" else 50 if stat == "Diproses" else 100
                    st.progress(val, text=stat)
                
                if d['status'] == "Selesai" and d['foto_penerima']:
                    st.divider()
                    st.image(d['foto_penerima'], caption="Bukti Foto Penyerahan")
            else:
                st.error("Nomor Resi tidak ditemukan.")


