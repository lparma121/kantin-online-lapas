import streamlit as st
from supabase import create_client
import time
from PIL import Image, ImageDraw, ImageFont
import io
import random
import string

# --- KONEKSI DATABASE ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(URL, KEY)
except:
    st.error("⚠️ Koneksi Database Gagal. Cek Secrets Anda.")
    st.stop()

st.set_page_config(page_title="e-PAS Mart | Belanja Cepat & Aman", page_icon="🛍️", layout="wide")

# --- TITIK JANGKAR SCROLL KE ATAS ---
st.markdown('<div id="paling-atas"></div>', unsafe_allow_html=True)

# --- CSS CUSTOM FINAL V4 (ANTI-STACKING HP) ---
st.markdown("""
<style>
    /* 1. GLOBAL */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Poppins', sans-serif; }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    /* 2. TOMBOL GLOBAL */
    .stButton>button {
        width: 100%;
        border-radius: 8px !important;
        font-weight: 600 !important;
        background: linear-gradient(90deg, #00AAFF 0%, #0077CC 100%);
        color: white !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        height: auto !important;
        padding: 5px 10px;
    }

    /* 3. GAMBAR & KARTU */
    div[data-testid="stImage"] img {
        width: 100% !important;
        object-fit: cover !important;
        border-radius: 8px 8px 0 0 !important;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
        padding: 10px !important;
    }

    .nama-produk { 
        font-weight: 600; color: #2c3e50;
        overflow: hidden; display: -webkit-box; 
        -webkit-line-clamp: 2; -webkit-box-orient: vertical; 
        margin-top: 5px; margin-bottom: 5px;
        line-height: 1.2;
    }

    /* === KHUSUS LAPTOP === */
    @media (min-width: 641px) {
        div[data-testid="stImage"] img { height: 160px !important; }
    }

    /* === KHUSUS HP (INTI PERBAIKAN) === */
    @media (max-width: 640px) {
        /* A. Gambar Kecil */
        div[data-testid="stImage"] img { height: 110px !important; }
        .nama-produk { font-size: 13px !important; height: 35px !important; }

        /* B. PAKSA KOLOM SEJAJAR (NO WRAP) */
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
            flex-direction: row !important; /* Paksa baris ke samping */
            flex-wrap: nowrap !important;   /* Dilarang turun baris */
            gap: 4px !important;            /* Jarak antar tombol tipis */
        }

        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"] {
            min-width: 0px !important; /* INI KUNCINYA: Hapus batas minimal lebar */
            width: 33% !important;     /* Bagi 3 rata */
            flex: 1 !important;        /* Flexible */
        }
        
        /* C. Tombol HP didesain ulang */
        .stButton>button {
            padding: 0px !important;    /* Hapus padding dalam tombol */
            height: 32px !important;    /* Tinggi tombol fix */
            min-height: 32px !important;
            font-size: 14px !important;
            line-height: 32px !important;
            margin: 0 !important;
        }
        
        div[data-testid="column"] button:contains("−") {
            background: #eef2f5 !important;
            color: #333 !important;
        }
    }
    
    /* 4. FLOATING CART */
    .floating-total {
        position: fixed; bottom: 15px; left: 2.5%; width: 95%;
        background: rgba(255, 255, 255, 0.98);
        padding: 10px; border-radius: 12px;
        border: 1px solid #00AAFF;
        box-shadow: 0px 4px 15px rgba(0,170,255,0.2);
        z-index: 99999; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI BANTUAN ---
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

def generate_resi():
    tanggal = time.strftime("%d%m")
    acak = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"KANTIN-{tanggal}-{acak}"

# --- FUNGSI 1: MEMBUAT GAMBAR NOTA ---
def buat_struk_image(data_pesanan, list_keranjang, total_bayar, resi):
    width, height = 500, 700
    img = Image.new('RGB', (width, height), color='white')
    d = ImageDraw.Draw(img)
    
    try: font_header = ImageFont.load_default() 
    except: pass
    
    black = (0, 0, 0)
    gray = (100, 100, 100)
    
    d.text((160, 20), "e-PAS Mart Lapas Arga Makmur", fill=black)
    d.text((150, 40), "Bukti Transaksi Resmi", fill=gray)
    d.line((20, 70, 480, 70), fill=black, width=2)
    
    y = 90
    d.text((30, y), f"NO. RESI  : {resi}", fill=black); y+=25
    d.text((30, y), f"TANGGAL   : {time.strftime('%d-%m-%Y %H:%M')}", fill=black); y+=25
    d.text((30, y), f"PENGIRIM  : {data_pesanan['nama_pemesan']}", fill=black); y+=25
    d.text((30, y), f"PENERIMA  : {data_pesanan['untuk_siapa']}", fill=black); y+=25
    d.line((20, y+10, 480, y+10), fill=gray, width=1)
    y += 30
    
    d.text((30, y), "ITEM PESANAN:", fill=black); y+=25
    for item in list_keranjang:
        nama = item['nama'][:30]
        harga = format_rupiah(item['harga'])
        d.text((30, y), f"- {nama}", fill=black)
        d.text((350, y), harga, fill=black)
        y += 25
        
    d.line((20, y+10, 480, y+10), fill=black, width=2)
    y += 30
    
    d.text((30, y), "TOTAL BAYAR", fill=black)
    d.text((350, y), format_rupiah(total_bayar), fill=(200, 0, 0))
    y += 50
    d.text((120, y), "TERIMA KASIH ATAS KUNJUNGAN ANDA", fill=gray)
    
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    return buf.getvalue()

# --- FUNGSI 2: MEMBUAT VOUCHER REFUND ---
def buat_voucher_image(nama, nominal, resi_asal):
    width, height = 600, 300
    img = Image.new('RGB', (width, height), color='#f0f8ff') 
    d = ImageDraw.Draw(img)
    
    try: 
        font_judul = ImageFont.truetype("arial.ttf", 36)
        font_tek = ImageFont.truetype("arial.ttf", 18)
        font_nominal = ImageFont.truetype("arial.ttf", 40)
        font_kode = ImageFont.truetype("arial.ttf", 24)
    except: 
        font_judul = ImageFont.load_default()
        font_tek = ImageFont.load_default()
        font_nominal = ImageFont.load_default()
        font_kode = ImageFont.load_default()
    
    biru_tua = (0, 85, 255)
    hitam = (0, 0, 0)
    merah = (220, 20, 60)
    abu = (100, 100, 100)

    d.rectangle([(10, 10), (width-10, height-10)], outline=biru_tua, width=5)
    
    d.text((40, 30), "VOUCHER PENGEMBALIAN DANA", fill=biru_tua, font=font_judul)
    d.text((40, 75), "e-PAS Mart Lapas Arga Makmur", fill=abu, font=font_tek)
    d.line((40, 100, 560, 100), fill=abu, width=1)
    
    d.text((40, 120), "Diberikan Kepada:", fill=hitam, font=font_tek)
    d.text((40, 145), nama, fill=hitam, font=font_kode)
    
    d.text((300, 120), "Senilai:", fill=hitam, font=font_tek)
    d.text((300, 145), format_rupiah(nominal), fill=merah, font=font_nominal)
    
    d.text((40, 220), "*Gunakan gambar ini sebagai bukti bayar pesanan berikutnya.", fill=abu, font=font_tek)
    
    kode_unik = f"REF-{resi_asal}"
    d.rectangle([(380, 210), (580, 250)], fill=biru_tua)
    d.text((400, 220), kode_unik, fill="white", font=font_tek)
    
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=95)
    return buf.getvalue()

# --- FUNGSI UPLOAD ---
def upload_file_bytes(file_bytes, folder, nama_file):
    try:
        path = f"{folder}/{nama_file}"
        supabase.storage.from_("KANTIN-ASSETS").upload(path, file_bytes, {"upsert": "true", "content-type": "image/jpeg"})
        return supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
    except Exception as e: return None

# --- SESSION STATE KERANJANG ---
if 'keranjang' not in st.session_state: st.session_state.keranjang = []

def tambah_ke_keranjang(item, harga):
    st.session_state.keranjang.append({"nama": item, "harga": harga})

def kurangi_dari_keranjang(nama_item):
    for index, item in enumerate(st.session_state.keranjang):
        if item['nama'] == nama_item:
            del st.session_state.keranjang[index]
            break

def reset_keranjang(): st.session_state.keranjang = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛒 Keranjang")
    if len(st.session_state.keranjang) > 0:
        total = sum(i['harga'] for i in st.session_state.keranjang)
        st.caption("Daftar item:")
        
        item_counts = {}
        item_prices = {}
        for x in st.session_state.keranjang:
            item_counts[x['nama']] = item_counts.get(x['nama'], 0) + 1
            item_prices[x['nama']] = x['harga']
            
        for nama, qty in item_counts.items():
            st.write(f"{qty}x {nama}")
            
        st.divider()
        st.write(f"Total: **{format_rupiah(total)}**")
        if st.button("❌ Kosongkan"): reset_keranjang(); st.rerun()
    else: st.info("Kosong.")

# --- NAVIGASI ---
menu = st.sidebar.radio("Navigasi", ["🏠 Beranda", "🛍️ Pesan Barang", "🔍 Lacak Pesanan"])

# =========================================
# 1. BERANDA
# =========================================
if menu == "🏠 Beranda":
    c_kiri, c_tengah, c_kanan = st.columns([0.5, 3, 0.5])
    with c_tengah:
        st.image("https://gdvphhymxlhuarvxwvtm.supabase.co/storage/v1/object/public/KANTIN-ASSETS/banner/unnamed.jpg", use_container_width=True)
    
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
    st.success("🚀 **e-PAS Mart:** Langkah maju Lapas Arga Makmur mewujudkan lingkungan yang bersih, modern, dan berintegritas.")

# =========================================
# 2. PESAN BARANG
# =========================================
elif menu == "🛍️ Pesan Barang":
    total_duit = sum(i['harga'] for i in st.session_state.keranjang)
    
    # --- CSS BUTTON BACK TO TOP ---
    st.markdown("""
        <style>
            .back-to-top {
                position: fixed; bottom: 90px; right: 20px;
                background-color: #00AAFF; color: white !important;
                width: 50px; height: 50px; border-radius: 50%;
                text-align: center; line-height: 50px; font-size: 24px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3); z-index: 999999;
                text-decoration: none; display: block; border: 2px solid white;
            }
            .back-to-top:hover { background-color: #0088cc; transform: scale(1.1); }
        </style>
        <a href="#paling-atas" class="back-to-top" target="_self">⬆️</a>
    """, unsafe_allow_html=True)

    # --- CSS FLOATING BAR ---
    if total_duit > 0:
        st.markdown(f"""
        <style>
            .floating-total {{
                position: fixed; bottom: 0; left: 0; width: 100%;
                background-color: #ffffff; padding: 15px;
                border-top: 3px solid #00AAFF; box-shadow: 0px -4px 10px rgba(0,0,0,0.1);
                z-index: 99999; text-align: center; font-size: 18px; font-weight: bold; color: #333;
            }}
        </style>
        <div class="floating-total">
            🛒 Total: {format_rupiah(total_duit)} <br>
            <span style="font-size:12px; font-weight:normal; color: #555;">(Klik Tab '💳 Pembayaran' di atas untuk lanjut)</span>
        </div>
        """, unsafe_allow_html=True)

    tab_menu, tab_checkout = st.tabs(["🍔 Pilih Menu", "💳 Pembayaran"])

    # === TAB 1: ETALASE MENU (SUDAH DIPERBAIKI) ===
    with tab_menu:
        st.markdown("""
        <style>
            div[data-testid="stImage"] img { height: 150px !important; object-fit: cover !important; border-radius: 10px 10px 0 0 !important; }
            .nama-produk { font-size: 14px; font-weight: bold; line-height: 1.2; height: 35px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 5px; }
        </style>
        """, unsafe_allow_html=True)

        st.header("🛍️ Etalase")
        
        # --- DEFINISI FUNGSI FRAGMENT ---
        @st.fragment
        def kartu_produk_live(item):
            with st.container(border=True):
                # 1. Gambar
                img = item['gambar_url'] if item.get('gambar_url') else "https://cdn-icons-png.flaticon.com/512/2515/2515263.png"
                st.image(img, use_container_width=True)
                
                # 2. Judul & Info
                st.markdown(f"""
                <div class="nama-produk">{item['nama_barang']}</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="color:#00AAFF; font-weight:700; font-size:15px;">{format_rupiah(item['harga'])}</div>
                    <div style="font-size:10px; color:#555; background:#f0f2f6; padding: 3px 6px; border-radius:4px;">
                        Stok: {item['stok']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 3. Tombol (+ -)
                qty_di_keranjang = sum(1 for x in st.session_state.keranjang if x['nama'] == item['nama_barang'])
                
                c_min, c_val, c_plus = st.columns([1, 1, 1], gap="small")
                
                with c_min:
                    if st.button("−", key=f"min_{item['id']}"): 
                        if qty_di_keranjang > 0:
                            kurangi_dari_keranjang(item['nama_barang'])
                            st.rerun()
                with c_val:
                    st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:16px; line-height:35px;'>{qty_di_keranjang}</div>", unsafe_allow_html=True)
                with c_plus:
                    if st.button("➕", key=f"plus_{item['id']}"):
                        if qty_di_keranjang < item['stok']:
                            tambah_ke_keranjang(item['nama_barang'], item['harga'])
                            st.rerun()
                        else:
                            st.toast("Habis!", icon="⚠️")
        
        # --- (BAGIAN INI YANG HILANG SEBELUMNYA) LOAD DATA & TAMPILKAN ---
        res_b = supabase.table("barang").select("*").gt("stok", 0).order('nama_barang').execute()
        items = res_b.data
        
        if items:
            cols = st.columns(2) # Grid 2 Kolom
            for i, item in enumerate(items):
                with cols[i % 2]:
                    kartu_produk_live(item)
            
            st.write("\n" * 8) # Spasi agar tidak ketutup tombol floating
        else:
            st.info("Belum ada barang tersedia.")
        # -----------------------------------------------------------------

    # === TAB 2: CHECKOUT ===
    with tab_checkout:
        st.header("📝 Konfirmasi Pesanan")
        
        if not st.session_state.keranjang:
            st.info("Keranjang masih kosong.")
        else:
            with st.container(border=True):
                st.write("**Rincian Barang:**")
                item_counts = {}
                item_prices = {}
                for x in st.session_state.keranjang:
                    item_counts[x['nama']] = item_counts.get(x['nama'], 0) + 1
                    item_prices[x['nama']] = x['harga']
                
                for nama, qty in item_counts.items():
                    subtotal = qty * item_prices[nama]
                    st.write(f"• {qty}x {nama} = **{format_rupiah(subtotal)}**")
                
                st.divider()
                st.markdown(f"### Total Bayar: {format_rupiah(total_duit)}")
                st.divider()
                
                st.write("**Metode Pembayaran:**")
                bayar = st.selectbox("Pilih Metode", 
                                     ["Transfer Bank (BRI/BCA)", "E-Wallet (DANA/Gopay)", "🎫 Voucher / Saldo Refund"], 
                                     label_visibility="collapsed")
                
                if "Transfer Bank" in bayar:
                    st.warning("🏦 **Bank BRI**\nNo. Rek: **1234-5678-900**\nAn. Koperasi Lapas")
                elif "E-Wallet" in bayar:
                    st.warning("📱 **DANA / Gopay**\nNomor: **0812-3456-7890**\nAn. Admin Kantin")
                elif "Voucher" in bayar:
                    st.info("🎫 **Bayar Pakai Voucher**\nUpload Gambar Voucher sebagai pengganti transfer.")

                st.write("**Data Pemesan:**")
                with st.form("form_pesan"):
                    pemesan = st.text_input("Nama Pengirim (Keluarga)")
                    
                    untuk = st.text_input(
                        "Nama WBP (Penerima) + Bin/Binti", 
                        placeholder="Contoh: Ali bin Abu Talib",
                        help="WAJIB menyertakan nama ayah (Bin/Binti) agar pesanan tidak salah kamar/orang."
                    )
                    
                    wa = st.text_input("Nomor WhatsApp Aktif")
                    
                    label_upload = "Upload Bukti Transfer / Gambar Voucher"
                    st.write(f"**{label_upload}:**")
                    
                    bukti_tf = st.file_uploader(label_upload, type=['jpg', 'png', 'jpeg'], label_visibility="collapsed", key="upload_bukti_fix")
                    
                    st.markdown("---")
                    submit = st.form_submit_button("✅ KIRIM PESANAN SEKARANG", type="primary")

                    if submit:
                        # 1. Validasi
                        nama_cek = untuk.lower()
                        if "bin" not in nama_cek and "binti" not in nama_cek:
                            st.error("⚠️ Mohon sertakan 'Bin' atau 'Binti' pada nama WBP!")
                            st.stop()
                        
                        if not pemesan or not wa:
                            st.warning("⚠️ Harap lengkapi Nama Pengirim dan Nomor WhatsApp.")
                            st.stop()
                        if not bukti_tf:
                            st.warning("⚠️ Anda belum mengupload Bukti Transfer / Voucher.")
                            st.stop()
                            
                        # 2. Proses Simpan
                        try:
                            file_bytes = bukti_tf.getvalue()
                            nama_file = f"tf_{int(time.time())}.jpg"
                            url_bukti = upload_file_bytes(file_bytes, "bukti_transfer", nama_file)
                            
                            if not url_bukti:
                                st.error("Gagal upload gambar. Coba lagi.")
                                st.stop()

                            item_str = ", ".join([f"{qty}x {nama}" for nama, qty in item_counts.items()])
                            no_resi = generate_resi()
                            
                            data_insert = {
                                "nama_pemesan": pemesan,
                                "untuk_siapa": untuk,
                                "nomor_wa": wa,
                                "item_pesanan": item_str,
                                "total_harga": total_duit,
                                "bukti_transfer": url_bukti,
                                "status": "Menunggu Verifikasi",
                                "cara_bayar": bayar,
                                "no_resi": no_resi
                            }
                            
                            supabase.table("pesanan").insert(data_insert).execute()
                            
                            # Kurangi Stok
                            for nama, qty in item_counts.items():
                                curr = supabase.table("barang").select("stok").eq("nama_barang", nama).execute()
                                if curr.data:
                                    stok_baru = curr.data[0]['stok'] - qty
                                    supabase.table("barang").update({"stok": stok_baru}).eq("nama_barang", nama).execute()

                            # Generate Nota
                            file_nota = buat_struk_image(data_insert, st.session_state.keranjang, total_duit, no_resi)

                            reset_keranjang()
                            st.success("🎉 Pesanan Berhasil Dikirim!")
                            st.markdown("**👇 Salin Nomor Resi Ini:**")
                            st.code(no_resi, language=None)
                            st.image(file_nota, caption="Nota Resmi", width=300)
                            st.download_button("📥 Download Nota (JPG)", data=file_nota, file_name=f"{no_resi}.jpg", mime="image/jpeg")
                            
                        except Exception as e:
                            st.error(f"Terjadi kesalahan sistem: {e}")

# =========================================
# 3. LACAK PESANAN
# =========================================
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Status Pesanan")
    
    resi_input = st.text_input("Masukkan Nomor Resi")
    if st.button("🔍 Cek Resi"):
        st.session_state['resi_aktif'] = resi_input
    
    if 'resi_aktif' in st.session_state and st.session_state['resi_aktif']:
        resi_dicari = st.session_state['resi_aktif']
        res = supabase.table("pesanan").select("*").eq("no_resi", resi_dicari).execute()
        
        if res.data:
            d = res.data[0]
            st.success(f"Pesanan Ditemukan: {d['no_resi']}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Penerima:** {d['untuk_siapa']}")
                st.write(f"**Item:** {d['item_pesanan']}")
            with c2:
                st.write(f"**Status Terkini:**")
                stat = d['status']
                val = 10 if stat == "Menunggu Verifikasi" else 50 if stat == "Pembayaran Valid (Diproses)" else 100
                st.progress(val, text=stat)
            
            if d['status'] == "Selesai" and d.get('foto_penerima'):
                st.divider()
                st.image(d['foto_penerima'], caption="Bukti Foto Penyerahan")
            
            # --- FITUR BATALKAN PESANAN ---
            if d['status'] == "Menunggu Verifikasi":
                st.divider()
                st.warning("⚠️ Pesanan ini belum diproses admin. Anda dapat membatalkannya.")
                st.info("Sistem akan membuatkan Voucher Saldo untuk pesanan berikutnya.")
                
                if st.button("❌ Batalkan & Buat Voucher", type="primary", key="btn_batal"):
                    try:
                        total_refund = 0
                        items_list = d['item_pesanan'].split(", ")
                        for item_str in items_list:
                            parts = item_str.split("x ", 1)
                            if len(parts) == 2:
                                qty_batal = int(parts[0])
                                nama_batal = parts[1]
                                curr = supabase.table("barang").select("stok", "harga").eq("nama_barang", nama_batal).execute()
                                if curr.data:
                                    dt_brg = curr.data[0]
                                    supabase.table("barang").update({"stok": dt_brg['stok'] + qty_batal}).eq("nama_barang", nama_batal).execute()
                                    total_refund += (dt_brg['harga'] * qty_batal)

                        supabase.table("pesanan").update({"status": "Dibatalkan"}).eq("id", d['id']).execute()
                        gambar_voucher = buat_voucher_image(d['nama_pemesan'], total_refund, d['no_resi'])
                        
                        st.balloons()
                        st.success("✅ Pesanan Dibatalkan!")
                        st.image(gambar_voucher, caption="Voucher Pengganti Uang", width=400)
                        st.download_button("📥 Download Voucher (JPG)", data=gambar_voucher, file_name=f"VOUCHER_{d['no_resi']}.jpg", mime="image/jpeg")
                        
                        if 'resi_aktif' in st.session_state: del st.session_state['resi_aktif']
                        st.stop()
                    except Exception as e:
                        st.error(f"Gagal membatalkan. Error: {e}")
        else:
            st.error("Nomor Resi tidak ditemukan.")
