import streamlit as st
from supabase import create_client
import time
from PIL import Image, ImageDraw, ImageFont
import io
import random
import string
import base64
from datetime import datetime, timedelta, timezone
import streamlit.components.v1 as components

# --- KONEKSI DATABASE ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(URL, KEY)
except:
    st.error("⚠️ Koneksi Database Gagal. Cek Secrets Anda.")
    st.stop()

# --- SETTING JAM OPERASIONAL (WIB) ---
JAM_BUKA = 00
JAM_TUTUP = 19

waktu_skrg_wib = datetime.now(timezone.utc) + timedelta(hours=7)
jam_skrg = waktu_skrg_wib.hour

# LOGIKA TUTUP TOKO
if jam_skrg < JAM_BUKA or jam_skrg >= JAM_TUTUP:
    st.markdown(f"""
    <div style='text-align: center; padding: 50px;'>
        <h1>🚫 MAAF, KANTIN TUTUP</h1>
        <p style='font-size: 18px;'>
            Layanan e-PAS Mart hanya beroperasi pada pukul: <br>
            <b>{JAM_BUKA:02d}.00 - {JAM_TUTUP:02d}.00 WIB</b>
        </p>
        <div style='background-color: #ffebee; color: #c62828; padding: 15px; border-radius: 10px; margin-top: 20px;'>
            Silakan kembali lagi besok pagi ya! 😊
        </div>
        <br>
        <p style='font-size: 12px; color: gray;'>Waktu Server Saat Ini: {waktu_skrg_wib.strftime('%H:%M')} WIB</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop() 

st.set_page_config(page_title="e-PAS Mart", page_icon="🛍️", layout="wide")

# --- TITIK JANGKAR SCROLL KE ATAS ---
st.markdown('<div id="paling-atas"></div>', unsafe_allow_html=True)

# --- CSS TAMPILAN (CLEAN & LIGHT) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Poppins', sans-serif; }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 8rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    /* GAMBAR & KARTU */
    div[data-testid="stImage"] img {
        width: 100% !important;
        aspect-ratio: 1/1; 
        object-fit: cover !important;
        border-radius: 8px 8px 0 0 !important;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0px !important;
        background: white; border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #eee; overflow: hidden;
    }

    /* GRID 2 KOLOM DI HP */
    @media (max-width: 640px) {
        div[data-testid="column"] {
            width: 50% !important; flex: 0 0 50% !important;
            max-width: 50% !important; padding: 0 4px !important;
        }
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        .stButton > button {
            font-size: 12px !important; padding: 4px 0 !important;
            height: 30px !important; min-height: 30px !important;
        }
    }

    /* TEKS PRODUK */
    .info-box { padding: 8px; }
    .nama-produk { 
        font-size: 13px; font-weight: 600; color: #333;
        line-height: 1.3; height: 34px; 
        overflow: hidden; display: -webkit-box; 
        -webkit-line-clamp: 2; -webkit-box-orient: vertical; 
        margin-bottom: 4px;
    }
    .harga-produk { color: #00AAFF; font-weight: 700; font-size: 14px; }
    .stok-produk { font-size: 10px; color: #888; margin-bottom: 8px; }

    /* FLOATING BOTTOM BAR */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.floating-bar-marker) {
        position: fixed; bottom: 15px; left: 2.5%; width: 95%; z-index: 999999;
        background: white; box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        border-radius: 15px; border: 1px solid #00AAFF;
        padding: 10px 15px !important; margin: 0 !important;
        display: flex; align-items: center;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.floating-bar-marker) button {
        border-radius: 50px !important; height: 40px !important;
        background-color: #00AAFF !important; border: none !important;
    }

    /* BACK TO TOP (GHOST MODE) */
    .back-to-top {
        position: fixed; bottom: 30px; right: 20px;
        width: 45px; height: 45px; border-radius: 50%;
        background-color: rgba(0, 170, 255, 0.3);
        color: rgba(255, 255, 255, 0.9) !important;
        text-align: center; line-height: 45px; font-size: 22px;
        text-decoration: none; z-index: 999990;
        backdrop-filter: blur(2px); transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.4);
    }
    .back-to-top:hover {
        background-color: #00AAFF; color: white !important;
        transform: translateY(-5px); opacity: 1;
    }
    .back-to-top.naik { bottom: 100px !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI BANTUAN ---
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

def generate_resi():
    tanggal = time.strftime("%d%m")
    acak = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"KANTIN-{tanggal}-{acak}"

def image_to_base64(img_bytes):
    return base64.b64encode(img_bytes).decode()

def upload_file_bytes(file_bytes, folder, nama_file):
    try:
        path = f"{folder}/{nama_file}"
        supabase.storage.from_("KANTIN-ASSETS").upload(path, file_bytes, {"upsert": "true", "content-type": "image/jpeg"})
        return supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
    except Exception: return None

def cek_voucher(kode):
    res = supabase.table("vouchers").select("*").eq("kode_voucher", kode).eq("is_active", True).execute()
    if res.data:
        return res.data[0] # Mengembalikan data voucher {id, saldo, dll}
    return None

# --- JURUS JAVA SCRIPT: KLIK UNTUK COPY RESI ---
def tampilkan_resi_copy_otomatis(resi_text):
    html_code = f"""
    <div onclick="copyText()" style="
        cursor: pointer;
        background-color: #f0f8ff;
        border: 2px dashed #00AAFF;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        transition: 0.3s;
        margin-bottom: 10px;
    " onmouseover="this.style.backgroundColor='#e3f2fd'" onmouseout="this.style.backgroundColor='#f0f8ff'">
        <div style="font-size: 12px; color: #555; margin-bottom: 5px;">KLIK KOTAK UNTUK SALIN RESI</div>
        <div style="font-size: 24px; font-weight: bold; color: #00AAFF; letter-spacing: 1px;">{resi_text}</div>
        <div id="pesan_copy" style="font-size: 11px; color: green; height: 15px; margin-top:5px;"></div>
    </div>

    <script>
    function copyText() {{
        navigator.clipboard.writeText("{resi_text}");
        document.getElementById("pesan_copy").innerHTML = "✅ BERHASIL DISALIN!";
        setTimeout(function() {{
            document.getElementById("pesan_copy").innerHTML = "";
        }}, 2000);
    }}
    </script>
    """
    components.html(html_code, height=100)

# --- FUNGSI BARU: KOTAK TOTAL TRANSFER BISA DI-COPY ---
def tampilkan_total_copy_otomatis(total_rp, total_raw, kode_unik):
    html_code = f"""
    <div onclick="salinNominal()" style="
        background-color: #e3f2fd; 
        padding: 15px; 
        border-radius: 10px; 
        border: 2px dashed #00AAFF; 
        text-align: center; 
        cursor: pointer;
        transition: 0.2s;
        margin-bottom: 20px;
    " onmouseover="this.style.backgroundColor='#bbdefb'" onmouseout="this.style.backgroundColor='#e3f2fd'">
        
        <p style="margin:0; color: #555; font-size: 13px;">Total Belanja + Kode Unik (<b style="color:red">{kode_unik}</b>)</p>
        <h3 style="margin:5px 0; color: #00AAFF;">TOTAL TRANSFER:</h3>
        
        <h2 style="margin:0; color: #000; font-family: sans-serif;">{total_rp} <span style="font-size:16px">📋</span></h2>
        
        <div style="font-size: 11px; color: #00AAFF; font-weight:bold; margin-top:5px;">[KLIK UNTUK SALIN NOMINAL]</div>
        <div id="notif_nominal" style="font-size: 11px; color: green; height: 15px; margin-top:2px;"></div>
    </div>

    <script>
    function salinNominal() {{
        // Menyalin angka murni (tanpa Rp dan titik)
        navigator.clipboard.writeText("{total_raw}");
        
        document.getElementById("notif_nominal").innerHTML = "✅ Nominal {total_raw} berhasil disalin!";
        setTimeout(function() {{
            document.getElementById("notif_nominal").innerHTML = "";
        }}, 3000);
    }}
    </script>
    """
    components.html(html_code, height=160)

# --- GENERATOR GAMBAR (WIB) ---
def buat_struk_image(data_pesanan, list_keranjang, total_bayar, resi):
    # Tambahkan margin padding agar teks tidak terlalu mepet ke pinggir
    width, height = 500, 800 # Tambah tinggi sedikit
    img = Image.new('RGB', (width, height), color='white')
    d = ImageDraw.Draw(img)
    try: font_header = ImageFont.load_default() 
    except: pass
    d.text((160, 20), "e-PAS Mart Lapas", fill="black")
    d.text((150, 40), "Bukti Transaksi Resmi", fill="gray")
    d.line((20, 70, 480, 70), fill="black", width=2)
    y = 90
    
    # --- LOGIKA TANGGAL WIB (UTC + 7) ---
    waktu_skrg = datetime.now(timezone.utc) + timedelta(hours=7)
    str_waktu = waktu_skrg.strftime('%d-%m-%Y %H:%M')
    
    d.text((30, y), f"NO. RESI  : {resi}", fill="black"); y+=25
    d.text((30, y), f"TANGGAL   : {str_waktu} WIB", fill="black"); y+=25
    d.text((30, y), f"PENGIRIM  : {data_pesanan['nama_pemesan']}", fill="black"); y+=25
    d.text((30, y), f"PENERIMA  : {data_pesanan['untuk_siapa']}", fill="black"); y+=25
    d.line((20, y+10, 480, y+10), fill="gray", width=1)
    y += 30
    d.text((30, y), "ITEM PESANAN:", fill="black"); y += 25
    for item in list_keranjang:
        nama = item['nama'][:40]
        sub_detail = f"  {item['qty']} x {format_rupiah(item['harga'])}"
        total_per_item = format_rupiah(item['harga'] * item['qty'])
        d.text((30, y), f"- {nama}", fill="black")
        y += 20 # Turun sedikit untuk detail harga
        d.text((30, y), sub_detail, fill="gray") # Harga satuan warna abu-abu
        d.text((350, y), total_per_item, fill="black") # Total harga sejajar dengan sub_detail
        y += 30 # Beri jarak untuk item berikutnya
    d.line((20, y+10, 480, y+10), fill="black", width=2)
    y += 30
    d.text((30, y), "TOTAL TRANSFER", fill="black")
    d.text((350, y), format_rupiah(total_bayar), fill=(200, 0, 0))
    y += 50
    d.text((120, y), "TERIMA KASIH ATAS KUNJUNGAN ANDA", fill="gray")
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    return buf.getvalue()

def buat_voucher_image(nama, nominal, resi_asal):
    width, height = 650, 350
    # Warna background soft blue/gelas
    img = Image.new('RGB', (width, height), color='#FFFFFF') 
    d = ImageDraw.Draw(img)
    
    biru_tua = (0, 51, 153)
    biru_muda = (235, 245, 255)
    merah_aksen = (220, 20, 60)

    # 1. Background & Border
    d.rectangle([(0, 0), (width, height)], fill=biru_muda) # Background luar
    d.rectangle([(20, 20), (width-20, height-20)], outline=biru_tua, width=3) # Border utama
    d.rectangle([(30, 30), (width-30, height-30)], outline=biru_tua, width=1) # Border dalam halus

    # 2. Header Section
    d.rectangle([(31, 31), (width-31, 80)], fill=biru_tua) # Bar judul
    d.text((180, 45), "VOUCHER PENGEMBALIAN DANA (REFUND)", fill="white")
    d.text((230, 62), "e-PAS Mart Lapas Arga Makmur", fill="#ADD8E6")

    # 3. Body Content
    y_body = 110
    d.text((60, y_body), "Diberikan Kepada :", fill="gray")
    d.text((60, y_body + 25), f"{nama.upper()}", fill="black") # Nama pemesan Bold-ish
    
    d.text((60, y_body + 70), "Nilai Refund :", fill="gray")
    # Teks Nominal Besar
    nominal_teks = format_rupiah(nominal)
    d.text((60, y_body + 95), nominal_teks, fill=merah_aksen)

    # 4. Keamanan & Referensi (Sisi Kanan)
    d.line((400, 110, 400, 250), fill=biru_tua, width=1) # Garis pemisah vertikal
    
    d.text((420, 110), "KODE REFERENSI:", fill="gray")
    d.text((420, 130), f"REF-{resi_asal}", fill="black")
    
    d.text((420, 170), "TANGGAL TERBIT:", fill="gray")
    d.text((420, 190), datetime.now(timezone.utc).strftime('%d/%m/%Y'), fill="black")

    # 5. Instruksi Penggunaan (Footer)
    d.rectangle([(31, 270), (width-31, 319)], fill="#F0F0F0")
    instruksi = "CARA PAKAI: Upload foto voucher ini pada menu 'Metode Bayar' saat pesanan berikutnya.\nStatus: Berlaku sebagai saldo tunai di e-PAS Mart."
    d.text((50, 280), instruksi, fill="#333333")

    # 6. Watermark Digital (Mencegah duplikasi gampang)
    d.text((500, 325), "OFFICIAL DIGITAL TICKET", fill="#D3D3D3")

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=95)
    return buf.getvalue()

# --- SESSION STATE ---
if 'keranjang' not in st.session_state: st.session_state.keranjang = []
if 'nota_sukses' not in st.session_state: st.session_state.nota_sukses = None
# Init Kode Unik jika belum ada
if 'kode_unik' not in st.session_state: st.session_state.kode_unik = random.randint(101, 999)

def reset_keranjang(): 
    st.session_state.keranjang = []
    st.session_state.kode_unik = random.randint(101, 999) # Reset kode unik juga

# --- SIDEBAR ---
with st.sidebar:
    st.title("e-PAS Mart")
    menu = st.sidebar.radio("Navigasi", ["🏠 Beranda", "🛍️ Pesan Barang", "🔍 Lacak Pesanan"])

# =========================================
# 1. BERANDA (UPDATED: ADA ULASAN)
# =========================================
if menu == "🏠 Beranda":
    c_kiri, c_tengah, c_kanan = st.columns([0.1, 3, 0.1])
    with c_tengah:
        st.markdown("""
        <img src="https://gdvphhymxlhuarvxwvtm.supabase.co/storage/v1/object/public/KANTIN-ASSETS/banner/unnamed.jpg" 
             style="width: 100%; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        """, unsafe_allow_html=True)
    
    st.write("") 
    st.markdown("""
    <div style='text-align: center; font-size: 18px;'>
        Selamat datang di era baru pelayanan <b>Lapas Arga Makmur</b>.<br>
        Belanja Aman, Transparan, dan Tanpa Uang Tunai.
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.info("💡 **Mengapa e-PAS Mart berbeda?** Karena kami menerapkan prinsip **100% Cashless (Non-Tunai)**.")
    st.subheader("✨ Keunggulan e-PAS Mart")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("### 💳")
            st.markdown("**Sistem Pembayaran Digital**")
            st.caption("Tidak ada lagi uang fisik yang beredar. WBP menggunakan saldo virtual.")
    with col2:
        with st.container(border=True):
            st.markdown("### 🛡️")
            st.markdown("**Cegah Pungli & Aman**")
            st.caption("Tanpa uang tunai, potensi penyimpangan dan kejahatan diminimalisir.")
    with col3:
        with st.container(border=True):
            st.markdown("### 📝")
            st.markdown("**Tercatat & Terpantau**")
            st.caption("Keluarga lebih tenang karena dana terpantau jelas penggunaannya.")
    
    # --- FITUR BARU: MENAMPILKAN ULASAN TERBARU ---
    st.write("")
    st.write("")
    st.subheader("💬 Apa Kata Mereka?")
    
    # Ambil 3 ulasan terbaru yang tidak kosong (rating tidak null)
    try:
        res_ulasan = supabase.table("pesanan").select("nama_pemesan, rating, ulasan").not_.is_("rating", "null").order("created_at", desc=True).limit(3).execute()
        
        if res_ulasan.data:
            cols = st.columns(len(res_ulasan.data))
            for i, u in enumerate(res_ulasan.data):
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"**{u['nama_pemesan']}**")
                        st.markdown(f"{'⭐' * u['rating']}")
                        if u['ulasan']:
                            st.caption(f"\"{u['ulasan']}\"")
                        else:
                            st.caption("*Tanpa komentar*")
        else:
            st.caption("Belum ada ulasan. Jadilah yang pertama memberikan ulasan!")
            
    except Exception as e:
        st.error("Gagal memuat ulasan.")
        
    st.success("🚀 **e-PAS Mart:** Langkah maju Lapas Arga Makmur mewujudkan lingkungan yang bersih, modern, dan berintegritas.")

# =========================================
# 2. PESAN BARANG
# =========================================
elif menu == "🛍️ Pesan Barang":
    st.markdown("<h2 style='margin-bottom:10px;'>🛍️ Etalase</h2>", unsafe_allow_html=True)

    total_duit = sum(item['harga'] * item['qty'] for item in st.session_state.keranjang)
    total_qty = sum(item['qty'] for item in st.session_state.keranjang)

    @st.dialog("🛒 Keranjang Belanja")
    def show_cart_modal():
        if not st.session_state.keranjang:
            st.info("Keranjang masih kosong.")
        else:
            for i, item in enumerate(st.session_state.keranjang):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 1], vertical_alignment="center")
                    c1.markdown(f"**{item['nama']}**")
                    c2.caption(f"{item['qty']} x {format_rupiah(item['harga'])}")
                    if c3.button("🗑️", key=f"del_m_{i}"):
                        del st.session_state.keranjang[i]
            st.divider()
            st.markdown(f"#### Total Barang: {format_rupiah(total_duit)}")
            if st.button("💳 Lanjut Pembayaran", type="primary", use_container_width=True):
                 st.toast("Silakan klik Tab 'Pembayaran'", icon="✅")

    tab_menu, tab_checkout = st.tabs(["🍔 Pilih Menu", "💳 Pembayaran"])

    # === TAB 1: ETALASE ===
    with tab_menu:
        @st.dialog("Masukkan Jumlah")
        def popup_add(item):
            c1, c2 = st.columns([1, 2])
            with c1:
                img = item['gambar_url'] if item.get('gambar_url') else "https://cdn-icons-png.flaticon.com/512/2515/2515263.png"
                st.image(img, use_container_width=True)
            with c2:
                st.write(f"**{item['nama_barang']}**")
                st.caption(f"Stok: {item['stok']}")
            
            curr = sum(x['qty'] for x in st.session_state.keranjang if x['nama'] == item['nama_barang'])
            jumlah = st.number_input("Qty:", 0, item['stok'], value=curr if curr>0 else 1)
            
            if st.button("Simpan", type="primary", use_container_width=True):
                st.session_state.keranjang = [x for x in st.session_state.keranjang if x['nama'] != item['nama_barang']]
                if jumlah > 0:
                    st.session_state.keranjang.append({
                        "id": item['id'], "nama": item['nama_barang'], "harga": item['harga'], "qty": jumlah
                    })
                st.rerun()

        @st.fragment
        def kartu_produk(item):
            with st.container(border=True):
                img = item['gambar_url'] if item.get('gambar_url') else "https://cdn-icons-png.flaticon.com/512/2515/2515263.png"
                st.image(img, use_container_width=True)
                
                st.markdown(f"""
                <div class="info-box">
                    <div class="nama-produk">{item['nama_barang']}</div>
                    <div class="harga-produk">{format_rupiah(item['harga'])}</div>
                    <div class="stok-produk">Stok: {item['stok']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                qty_ada = sum(x['qty'] for x in st.session_state.keranjang if x['nama'] == item['nama_barang'])
                lbl = f"✅ {qty_ada} di Troli" if qty_ada > 0 else "Beli +"
                typ = "primary" if qty_ada > 0 else "secondary"
                
                if st.button(lbl, key=f"btn_{item['id']}", type=typ, use_container_width=True):
                    popup_add(item)

        res = supabase.table("barang").select("*").gt("stok", 0).order('nama_barang').execute()
        items = res.data
        if items:
            rows = [items[i:i + 2] for i in range(0, len(items), 2)]
            for row in rows:
                cols = st.columns(2)
                for i, item in enumerate(row):
                    with cols[i]: kartu_produk(item)
            st.write("\n"*5)
        else:
            st.info("Barang habis.")

    # === TAB 2: PEMBAYARAN ===
with tab_checkout:
    st.header("📝 Konfirmasi & Pembayaran")
    
    # LOGIKA TAMPILAN: JIKA SUKSES -> NOTA | JIKA BELUM -> FORM
    if st.session_state.nota_sukses:
        # --- TAMPILAN SUKSES ---
        res_data = st.session_state.nota_sukses
        st.success("✅ Pesanan Berhasil Dikirim!")
        
        # --- FITUR KHUSUS: KOTAK COPY OTOMATIS (JS) ---
        tampilkan_resi_copy_otomatis(res_data['resi'])
        
        b64 = image_to_base64(res_data['data'])
        st.markdown(f'<img src="data:image/jpeg;base64,{b64}" style="width:250px; border:1px solid #ddd; margin-bottom:10px;">', unsafe_allow_html=True)
        
        c_dl, c_new = st.columns(2)
        with c_dl:
            st.download_button(
                label="📥 Download Nota",
                data=res_data['data'],
                file_name=f"{res_data['resi']}.jpg",
                mime="image/jpeg",
                type="primary",
                use_container_width=True
            )
        with c_new:
            if st.button("🔄 Belanja Lagi", use_container_width=True):
                st.session_state.nota_sukses = None
                st.rerun()
        st.info("Simpan resi ini untuk melacak status pesanan.")
        
    else:
        # --- TAMPILAN FORM ---
        if not st.session_state.keranjang:
            st.info("Keranjang kosong.")
        else:
            # 1. FITUR BARU: INPUT VOUCHER DIGITAL
            st.subheader("🎫 Gunakan Voucher Refund")
            with st.container(border=True):
                kode_input = st.text_input("Masukkan Kode Voucher", placeholder="Contoh: REF-1234")
                
                # Inisialisasi saldo voucher di session state
                if 'saldo_voucher' not in st.session_state:
                    st.session_state.saldo_voucher = 0
                    st.session_state.voucher_id_aktif = None

                if kode_input:
                    # Cek ke database tabel 'vouchers'
                    res_v = supabase.table("vouchers").select("*").eq("kode_voucher", kode_input).eq("is_active", True).execute()
                    if res_v.data:
                        v_data = res_v.data[0]
                        st.session_state.saldo_voucher = v_data['saldo']
                        st.session_state.voucher_id_aktif = v_data['id']
                        st.success(f"✅ Voucher Aktif: {format_rupiah(v_data['saldo'])}")
                    else:
                        st.error("❌ Kode Voucher tidak valid atau sudah digunakan.")
                        st.session_state.saldo_voucher = 0
                        st.session_state.voucher_id_aktif = None
                else:
                    st.session_state.saldo_voucher = 0
                    st.session_state.voucher_id_aktif = None

            # 2. HITUNG TOTAL AKHIR (Dikurangi Voucher)
            total_barang = total_duit 
            if 'kode_unik' not in st.session_state:
                st.session_state.kode_unik = random.randint(101, 999)
            
            # Rumus: (Total Barang + Kode Unik) - Saldo Voucher
            total_setelah_voucher = (total_barang + st.session_state.kode_unik) - st.session_state.saldo_voucher
            total_bayar_final = max(0, total_setelah_voucher) # Tidak boleh minus

            with st.container(border=True):
                st.write("**Ringkasan Pesanan:**")
                for x in st.session_state.keranjang:
                    st.write(f"• {x['qty']}x {x['nama']} ({format_rupiah(x['harga']*x['qty'])})")
                
                if st.session_state.saldo_voucher > 0:
                    st.write(f"🔹 Potongan Voucher: -{format_rupiah(st.session_state.saldo_voucher)}")
                
                st.divider()
                
                # --- TAMPILAN TOTAL DENGAN FITUR COPY ---
                angka_murni = str(total_bayar_final) 
                tampilkan_total_copy_otomatis(
                    format_rupiah(total_bayar_final), 
                    angka_murni,                       
                    st.session_state.kode_unik
                )
                
                st.caption("⚠️ **PENTING:** Mohon transfer **TEPAT** sesuai nominal di atas.")

                bayar = st.selectbox("Metode Bayar", ["Transfer Bank", "E-Wallet", "🎫 Voucher (Gunakan Kode di Atas)"])
                if "Transfer" in bayar: st.warning("🏦 **BRI: 1234-5678-900 (Koperasi Lapas)**")
                elif "E-Wallet" in bayar: st.warning("📱 **DANA: 0812-3456-7890 (Admin Kantin)**")

                with st.form("checkout"):
                    pemesan = st.text_input("Nama Pengirim")
                    untuk = st.text_input("Nama WBP + Bin/Binti", placeholder="Contoh: Ali bin Abu")
                    wa = st.text_input("WhatsApp")
                    
                    # Jika total bayar 0 karena voucher, bukti transfer opsional
                    if total_bayar_final == 0:
                        st.info("💡 Saldo voucher mencukupi. Anda tidak perlu transfer, cukup upload foto apa saja atau screenshot voucher ini.")
                    
                    bukti = st.file_uploader("Upload Bukti", type=['jpg','png'], key="bukti_fix")
                    
                    if st.form_submit_button("✅ Kirim Pesanan", type="primary"):
                        if bukti and bukti.size > 5 * 1024 * 1024:
                            st.error("⚠️ File terlalu besar! Maksimal 5MB.")
                        elif not (pemesan and untuk and wa and bukti):
                            st.error("Data tidak lengkap!")
                        elif "bin" not in untuk.lower() and "binti" not in untuk.lower():
                            st.error("Wajib pakai Bin/Binti!")
                        else:
                            try:
                                f_bytes = bukti.getvalue()
                                fname = f"tf_{int(time.time())}.jpg"
                                url = upload_file_bytes(f_bytes, "bukti_transfer", fname)
                                if url:
                                    items_str = ", ".join([f"{x['qty']}x {x['nama']}" for x in st.session_state.keranjang])
                                    resi = generate_resi()
                                    waktu_sekarang_iso = datetime.now(timezone.utc).isoformat()
                                    
                                    data = {
                                        "nama_pemesan": pemesan, "untuk_siapa": untuk, "nomor_wa": wa,
                                        "item_pesanan": items_str, 
                                        "total_harga": total_bayar_final,
                                        "bukti_transfer": url, "status": "Menunggu Verifikasi",
                                        "cara_bayar": bayar, "no_resi": resi,
                                        "created_at": waktu_sekarang_iso
                                    }
                                    supabase.table("pesanan").insert(data).execute()
                                    
                                    # Update Stok
                                    for x in st.session_state.keranjang:
                                        curr = supabase.table("barang").select("stok").eq("nama_barang", x['nama']).execute()
                                        if curr.data:
                                            supabase.table("barang").update({"stok": curr.data[0]['stok'] - x['qty']}).eq("nama_barang", x['nama']).execute()

                                    # 3. FITUR BARU: HANGUSKAN VOUCHER SETELAH DIPAKAI
                                    if st.session_state.voucher_id_aktif:
                                        supabase.table("vouchers").update({"is_active": False}).eq("id", st.session_state.voucher_id_aktif).execute()
                                        st.session_state.saldo_voucher = 0
                                        st.session_state.voucher_id_aktif = None

                                    nota = buat_struk_image(data, st.session_state.keranjang, total_bayar_final, resi)
                                    st.session_state.nota_sukses = { 'data': nota, 'resi': resi }
                                    reset_keranjang()
                                    st.rerun()
                                else: st.error("Gagal upload.")
                            except Exception as e: st.error(f"Error: {e}")

# =========================================
# 3. LACAK PESANAN (RATING & KOMENTAR)
# =========================================
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Pesanan")
    st.info("💡 Tips: Anda cukup memasukkan **4 Huruf/Angka Terakhir** dari Resi (Contoh: **RK88**) atau Resi Lengkap.")
    
    resi_in = st.text_input("Masukkan Kode Resi")
    
    # Tombol Cek
    if st.button("Cek Status"):
        if resi_in:
            st.session_state.resi_aktif = resi_in.strip() 
        else:
            st.warning("Mohon isi kode resi.")

    # Logika Pencarian
    if 'resi_aktif' in st.session_state and st.session_state.resi_aktif:
        keyword = st.session_state.resi_aktif
        res = supabase.table("pesanan").select("*").ilike("no_resi", f"%{keyword}").execute()
        
        if res.data:
            # Ambil data terbaru
            data_found = sorted(res.data, key=lambda x: x['id'], reverse=True)
            d = data_found[0] 
            
            st.divider()
            st.write(f"📦 **Pesanan Ditemukan:** `{d['no_resi']}`")
            
            # --- STATUS BAR ---
            status_color = "blue"
            if d['status'] == "Selesai": status_color = "green"
            elif "Dibatalkan" in d['status'] or "Ditolak" in d['status']: status_color = "red"
            
            st.markdown(f"""
            <div style="padding:15px; border-radius:10px; background-color:{'#e8f5e9' if status_color=='green' else '#ffebee' if status_color=='red' else '#e3f2fd'}; border:1px solid {status_color};">
                <h3 style="margin:0; color:{status_color};">{d['status']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.write(f"**Item:** {d['item_pesanan']}")
            st.caption(f"Pemesan: {d['nama_pemesan']} | Penerima: {d['untuk_siapa']}")
            
            # --- FOTO SERAH TERIMA ---
            foto_url = d.get('foto_penerima') 
            st.write("---") 
            
            if foto_url:
                st.success("📸 **Bukti Serah Terima Barang:**")
                st.image(foto_url, width=300, caption=f"Diterima oleh: {d['untuk_siapa']}")
            else:
                if d['status'] == "Selesai":
                    st.warning("⚠️ Status pesanan 'Selesai', tetapi Admin belum mengunggah foto bukti.")

            # --- LOGIKA TOMBOL BATAL & GENERATE VOUCHER DIGITAL ---
            if d['status'] == "Menunggu Verifikasi":
                st.info("ℹ️ **Info:** Tombol batalkan pesanan akan muncul otomatis jika 4 jam belum diproses.")
                try:
                    waktu_str = d.get('created_at')
                    if not waktu_str: waktu_pesan = datetime.now(timezone.utc)
                    else: waktu_pesan = datetime.fromisoformat(waktu_str.replace('Z', '+00:00'))
                    
                    if (datetime.now(timezone.utc) - waktu_pesan) >= timedelta(hours=4):
                        st.error("Waktu tunggu 4 jam terlewati.")
                        if st.button("❌ Batalkan & Refund Sekarang"):
                            try:
                                refund = 0
                                # Kembalikan Stok
                                for i_str in d['item_pesanan'].split(", "):
                                    if "x " in i_str: q_str, n = i_str.split("x ", 1); q = int(q_str)
                                    else: q = 1; n = i_str 
                                    cur = supabase.table("barang").select("*").eq("nama_barang", n).execute()
                                    if cur.data:
                                        supabase.table("barang").update({"stok": cur.data[0]['stok']+q}).eq("nama_barang", n).execute()
                                        refund += cur.data[0]['harga']*q
                                
                                # Update Status Pesanan
                                supabase.table("pesanan").update({"status": "Dibatalkan"}).eq("id", d['id']).execute()
                                
                                # --- FITUR VOUCHER DIGITAL BARU ---
                                # 1. Buat kode voucher unik
                                kode_vcr = f"REF-{random.randint(1000, 9999)}"
                                # 2. Simpan kode ke tabel 'vouchers' agar bisa diinput di TAB 2
                                supabase.table("vouchers").insert({
                                    "kode_voucher": kode_vcr,
                                    "saldo": refund,
                                    "nama_penerima": d['nama_pemesan'],
                                    "is_active": True
                                }).execute()
                                
                                # 3. Buat Gambar Voucher untuk didownload
                                vcr_img = buat_voucher_image(d['nama_pemesan'], refund, kode_vcr)
                                b64_v = image_to_base64(vcr_img)
                                
                                st.success(f"✅ Pesanan Dibatalkan. Kode Voucher Refund Anda: **{kode_vcr}**")
                                st.markdown(f'<img src="data:image/jpeg;base64,{b64_v}" style="width:100%; border:2px dashed blue;">', unsafe_allow_html=True)
                                st.download_button("📥 Download Voucher", vcr_img, f"V_{kode_vcr}.jpg", "image/jpeg")
                                
                                del st.session_state.resi_aktif
                                st.rerun()
                            except Exception as e: 
                                st.error(f"Gagal membatalkan: {e}")
                except: pass

            # --- LOGIKA ULASAN ---
            elif d['status'] == "Selesai":
                st.subheader("⭐ Berikan Ulasan")
                if d.get('rating') is None:
                    with st.form("form_ulasan"):
                        pil = st.selectbox("Rating", ["5 - Puas", "4 - Baik", "3 - Cukup", "2 - Kurang", "1 - Kecewa"])
                        kom = st.text_area("Komentar")
                        if st.form_submit_button("Kirim"):
                            rate_val = int(pil.split(" - ")[0])
                            supabase.table("pesanan").update({"rating": rate_val, "ulasan": kom}).eq("id", d['id']).execute()
                            st.success("Terima kasih!")
                            st.rerun()
                else:
                    st.info("✅ Ulasan terkirim.")
                    st.write(f"Rating: {'⭐'*d['rating']}")
                    if d.get('ulasan'): st.write(f"Komentar: {d['ulasan']}")
        else:
            st.error("Resi tidak ditemukan.")








