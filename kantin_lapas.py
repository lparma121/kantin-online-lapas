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
JAM_BUKA = 7
JAM_TUTUP = 22

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

    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0px !important;
        background: white; border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #eee; overflow: hidden;
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

    /* BACK TO TOP */
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

# --- FUNGSI BARU: VOUCHER SYSTEM ---
def generate_kode_voucher():
    huruf = ''.join(random.choices(string.ascii_uppercase, k=4))
    angka = ''.join(random.choices(string.digits, k=4))
    return f"V-{huruf}-{angka}"

def cek_voucher_db(kode):
    try:
        res = supabase.table("vouchers").select("*").eq("kode_voucher", kode).eq("status", "AKTIF").execute()
        if res.data:
            return True, res.data[0]
        else:
            return False, None
    except:
        return False, None

def image_to_base64(img_bytes):
    return base64.b64encode(img_bytes).decode()

def upload_file_bytes(file_bytes, folder, nama_file):
    try:
        path = f"{folder}/{nama_file}"
        supabase.storage.from_("KANTIN-ASSETS").upload(path, file_bytes, {"upsert": "true", "content-type": "image/jpeg"})
        return supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
    except Exception: return None

# --- [FIXED] JURUS COPY PASTE STABIL (GUNAKAN ST.CODE) ---
def tampilkan_copy_text(text, label="SALIN"):
    st.caption(f"👇 {label}:")
    st.code(text, language="text")

def tampilkan_total_copy_otomatis(total_rp, total_raw, kode_unik):
    st.markdown(f"""
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; border: 2px dashed #00AAFF; text-align: center; margin-bottom: 5px;">
        <p style="margin:0; color: #555; font-size: 13px;">Total Belanja + Kode Unik (<b style="color:red">{kode_unik}</b>)</p>
        <h3 style="margin:5px 0; color: #00AAFF;">TOTAL TRANSFER:</h3>
        <h2 style="margin:0; color: #000; font-family: sans-serif;">{total_rp}</h2>
    </div>
    """, unsafe_allow_html=True)
    st.caption("👇 Salin nominal transfer:")
    st.code(total_raw, language="text")

# --- GENERATOR GAMBAR NOTA ---
def buat_struk_image(data_pesanan, list_keranjang, total_bayar, resi, potongan_voucher=0):
    width, height = 500, 750
    img = Image.new('RGB', (width, height), color='white')
    d = ImageDraw.Draw(img)
    try: font_header = ImageFont.load_default() 
    except: pass
    d.text((160, 20), "e-PAS Mart Lapas", fill="black")
    d.text((150, 40), "Bukti Transaksi Resmi", fill="gray")
    d.line((20, 70, 480, 70), fill="black", width=2)
    y = 90
    
    waktu_skrg = datetime.now(timezone.utc) + timedelta(hours=7)
    str_waktu = waktu_skrg.strftime('%d-%m-%Y %H:%M')
    
    d.text((30, y), f"NO. RESI  : {resi}", fill="black"); y+=25
    d.text((30, y), f"TANGGAL   : {str_waktu} WIB", fill="black"); y+=25
    d.text((30, y), f"PENGIRIM  : {data_pesanan['nama_pemesan']}", fill="black"); y+=25
    d.text((30, y), f"PENERIMA  : {data_pesanan['untuk_siapa']}", fill="black"); y+=25
    d.line((20, y+10, 480, y+10), fill="gray", width=1)
    y += 30
    d.text((30, y), "ITEM PESANAN:", fill="black"); y+=25
    for item in list_keranjang:
        nama = item['nama'][:30]
        harga = format_rupiah(item['harga'])
        d.text((30, y), f"- {nama}", fill="black")
        d.text((350, y), harga, fill="black")
        y += 25
    d.line((20, y+10, 480, y+10), fill="black", width=2)
    y += 30
    
    if potongan_voucher > 0:
        d.text((30, y), "VOUCHER", fill="black")
        d.text((350, y), f"-{format_rupiah(potongan_voucher)}", fill="green"); y+=25
    
    d.text((30, y), "TOTAL TRANSFER", fill="black")
    d.text((350, y), format_rupiah(total_bayar), fill=(200, 0, 0))
    y += 50
    d.text((120, y), "TERIMA KASIH ATAS KUNJUNGAN ANDA", fill="gray")
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    return buf.getvalue()

# --- SESSION STATE ---
if 'keranjang' not in st.session_state: st.session_state.keranjang = []
if 'nota_sukses' not in st.session_state: st.session_state.nota_sukses = None
if 'kode_unik' not in st.session_state: st.session_state.kode_unik = random.randint(101, 999)
if 'voucher_aktif' not in st.session_state: st.session_state.voucher_aktif = None

def reset_keranjang(): 
    st.session_state.keranjang = []
    st.session_state.kode_unik = random.randint(101, 999)
    st.session_state.voucher_aktif = None

# =========================================================
# GLOBAL CALCULATION
# =========================================================
total_duit = sum(item['harga'] * item['qty'] for item in st.session_state.keranjang)
total_qty = sum(item['qty'] for item in st.session_state.keranjang)
# =========================================================

# --- SIDEBAR ---
with st.sidebar:
    st.title("e-PAS Mart")
    menu = st.sidebar.radio("Navigasi", ["🏠 Beranda", "🛍️ Pesan Barang", "🔍 Lacak Pesanan"])

# =========================================
# 1. BERANDA
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
    st.info("💡 **Fitur Baru:** Punya Voucher Refund? Masukkan kodenya saat pembayaran, saldo akan otomatis terpotong!")
    
    st.write("")
    st.subheader("💬 Apa Kata Mereka?")
    try:
        res_ulasan = supabase.table("pesanan").select("nama_pemesan, rating, ulasan").not_.is_("rating", "null").order("created_at", desc=True).limit(3).execute()
        if res_ulasan.data:
            cols = st.columns(len(res_ulasan.data))
            for i, u in enumerate(res_ulasan.data):
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"**{u['nama_pemesan']}**")
                        st.markdown(f"{'⭐' * u['rating']}")
                        if u['ulasan']: st.caption(f"\"{u['ulasan']}\"")
        else:
            st.caption("Belum ada ulasan.")
    except Exception as e:
        st.error("Gagal memuat ulasan.")
    st.success("🚀 **e-PAS Mart:** Langkah maju Lapas Arga Makmur mewujudkan lingkungan yang bersih, modern, dan berintegritas.")

# =========================================
# 2. PESAN BARANG
# =========================================
elif menu == "🛍️ Pesan Barang":
    st.markdown("<h2 style='margin-bottom:10px;'>🛍️ Etalase</h2>", unsafe_allow_html=True)

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
                        st.rerun()
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

    # === TAB 2: PEMBAYARAN (SYSTEM VOUCHER OTOMATIS) ===
    with tab_checkout:
        st.header("📝 Konfirmasi & Pembayaran")
        
        # LOGIKA TAMPILAN: JIKA SUKSES -> NOTA
        if st.session_state.nota_sukses:
            res_data = st.session_state.nota_sukses
            st.success("✅ Pesanan Berhasil Dikirim!")
            
            # --- TAMPILKAN RESI (DENGAN ST.CODE) ---
            tampilkan_copy_text(res_data['resi'], "NOMOR RESI")
            st.write("") 
            
            c_dl, c_new = st.columns(2)
            with c_dl:
                st.download_button(
                    label="📥 Simpan Nota",
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
            st.info("Mohon simpan resi ini untuk melacak status pesanan Anda.")
            
        else:
            if not st.session_state.keranjang:
                st.info("Keranjang kosong.")
            else:
                # ------------------------------------------
                # 1. LOGIKA VOUCHER & TOTAL
                # ------------------------------------------
                nominal_potongan = 0
                sisa_tagihan = total_duit
                
                # Input Voucher
                with st.expander("🎫 Punya Kode Voucher Refund?", expanded=True):
                    col_v1, col_v2 = st.columns([3, 1])
                    with col_v1:
                        input_v = st.text_input("Masukkan Kode Voucher (Contoh: V-AAAA-1234)", key="input_voucher_box")
                    with col_v2:
                        st.write("")
                        st.write("")
                        if st.button("Gunakan"):
                            is_valid, data_v = cek_voucher_db(input_v.strip())
                            if is_valid:
                                st.session_state.voucher_aktif = data_v
                                st.toast("Voucher Berhasil Dipasang!", icon="✅")
                                st.rerun()
                            else:
                                st.error("Kode Voucher Salah / Sudah Habis")

                    if st.session_state.voucher_aktif:
                        v = st.session_state.voucher_aktif
                        saldo_voucher = v['nominal']
                        st.success(f"✅ **Voucher Terpasang:** {v['kode_voucher']}")
                        st.info(f"Saldo Voucher: {format_rupiah(saldo_voucher)}")
                        
                        if saldo_voucher >= total_duit:
                            nominal_potongan = total_duit
                            sisa_tagihan = 0 
                        else:
                            nominal_potongan = saldo_voucher
                            sisa_tagihan = total_duit - saldo_voucher
                        
                        if st.button("❌ Lepas Voucher"):
                            st.session_state.voucher_aktif = None
                            st.rerun()

                # Hitung Kode Unik
                if sisa_tagihan > 0:
                    if 'kode_unik' not in st.session_state: st.session_state.kode_unik = random.randint(101, 999)
                    total_transfer = sisa_tagihan + st.session_state.kode_unik
                else:
                    total_transfer = 0 

                st.divider()
                st.write("**Rincian Pembayaran:**")
                c1, c2 = st.columns(2)
                c1.write(f"Total Belanja: {format_rupiah(total_duit)}")
                
                if nominal_potongan > 0:
                    c1.write(f"Potongan Voucher: -{format_rupiah(nominal_potongan)}")
                
                # ------------------------------------------
                # 2. PILIH METODE BAYAR (DI LUAR FORM)
                # ------------------------------------------
                metode_bayar = "Full Voucher" # Default jika lunas
                
                if total_transfer > 0:
                    c1.write(f"Kode Unik: +{st.session_state.kode_unik}")
                    tampilkan_total_copy_otomatis(format_rupiah(total_transfer), str(total_transfer), st.session_state.kode_unik)
                    
                    st.caption("⚠️ **PENTING:** Mohon transfer **TEPAT** sampai 3 digit terakhir.")
                    st.write("---")
                    
                    # [FIX] Selectbox dengan pilihan spesifik
                    opsi_pembayaran = [
                        "Transfer Bank (BRI)", 
                        "E-Wallet (DANA)", 
                        "E-Wallet (OVO)", 
                        "E-Wallet (GoPay)"
                    ]
                    
                    metode_bayar = st.selectbox("Pilih Metode Transfer Sisa", opsi_pembayaran)
                    
                    # [FIX] Logika tampilan satu per satu
                    if "BRI" in metode_bayar:
                        st.warning("🏦 **BRI: 1234-5678-900 (Koperasi Lapas)**\n\nSilakan transfer sesuai **TOTAL TRANSFER** di atas.")
                    elif "DANA" in metode_bayar:
                        st.warning("📱 **DANA: 0812-3456-7890 (Admin Kantin)**\n\nSilakan transfer sesuai **TOTAL TRANSFER** di atas.")
                    elif "OVO" in metode_bayar:
                        st.warning("💜 **OVO: 0812-3456-7890 (Admin Kantin)**\n\nSilakan transfer sesuai **TOTAL TRANSFER** di atas.")
                    elif "GoPay" in metode_bayar:
                        st.warning("🟢 **GoPay: 0812-3456-7890 (Admin Kantin)**\n\nSilakan transfer sesuai **TOTAL TRANSFER** di atas.")
                else:
                    st.markdown("""
                    <div style="background-color:#e8f5e9; padding:15px; border-radius:10px; text-align:center; border:1px solid green;">
                        <h3 style="margin:0; color:green;">✨ LUNAS DENGAN VOUCHER</h3>
                        <small>Tidak perlu transfer uang.</small>
                    </div>
                    """, unsafe_allow_html=True)

                # ------------------------------------------
                # 3. FORM IDENTITAS & SUBMIT
                # ------------------------------------------
                with st.form("checkout"):
                    pemesan = st.text_input("Nama Pengirim")
                    untuk = st.text_input("Nama WBP + Bin/Binti", placeholder="Contoh: Ali bin Abu")
                    wa = st.text_input("WhatsApp")
                    
                    bukti = None
                    if total_transfer > 0:
                        bukti = st.file_uploader("Upload Bukti Transfer Sisa", type=['jpg','png'], key="bukti_fix")

                    if st.form_submit_button("✅ Proses Pesanan Sekarang", type="primary"):
                        if not (pemesan and untuk and wa):
                            st.error("Data diri belum lengkap!")
                        elif total_transfer > 0 and not bukti:
                            st.error("Wajib upload bukti transfer untuk sisa tagihan!")
                        else:
                            try:
                                url_bukti = ""
                                if bukti:
                                    f_bytes = bukti.getvalue()
                                    fname = f"tf_{int(time.time())}.jpg"
                                    url_bukti = upload_file_bytes(f_bytes, "bukti_transfer", fname)
                                
                                items_str = ", ".join([f"{x['qty']}x {x['nama']}" for x in st.session_state.keranjang])
                                resi = generate_resi()
                                waktu_sekarang_iso = datetime.now(timezone.utc).isoformat()
                                
                                # Data Insert
                                data_insert = {
                                    "nama_pemesan": pemesan, "untuk_siapa": untuk, "nomor_wa": wa,
                                    "item_pesanan": items_str, 
                                    "total_harga": total_transfer if total_transfer > 0 else 0, 
                                    "bukti_transfer": url_bukti, "status": "Menunggu Verifikasi",
                                    "cara_bayar": metode_bayar, "no_resi": resi,
                                    "created_at": waktu_sekarang_iso,
                                    "voucher_used": st.session_state.voucher_aktif['kode_voucher'] if st.session_state.voucher_aktif else None,
                                    "potongan_voucher": nominal_potongan
                                }
                                supabase.table("pesanan").insert(data_insert).execute()
                                
                                # Update Stok
                                for x in st.session_state.keranjang:
                                    curr = supabase.table("barang").select("stok").eq("nama_barang", x['nama']).execute()
                                    if curr.data:
                                        supabase.table("barang").update({"stok": curr.data[0]['stok'] - x['qty']}).eq("nama_barang", x['nama']).execute()

                                # Update Saldo Voucher
                                if st.session_state.voucher_aktif:
                                    kode_v = st.session_state.voucher_aktif['kode_voucher']
                                    sisa_saldo_baru = st.session_state.voucher_aktif['nominal'] - nominal_potongan
                                    status_v = "AKTIF" if sisa_saldo_baru > 0 else "HABIS"
                                    supabase.table("vouchers").update({
                                        "nominal": sisa_saldo_baru, 
                                        "status": status_v
                                    }).eq("kode_voucher", kode_v).execute()

                                # Nota & Reset
                                nota = buat_struk_image(data_insert, st.session_state.keranjang, total_transfer, resi, nominal_potongan)
                                st.session_state.nota_sukses = { 'data': nota, 'resi': resi }
                                reset_keranjang()
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error Sistem: {e}")

# =========================================
# 3. LACAK PESANAN
# =========================================
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Pesanan")
    st.info("💡 Tips: Masukkan 4 digit terakhir resi.")
    resi_in = st.text_input("Masukkan Kode Resi")
    if st.button("Cek Status"):
        if resi_in: st.session_state.resi_aktif = resi_in.strip()

    if 'resi_aktif' in st.session_state and st.session_state.resi_aktif:
        keyword = st.session_state.resi_aktif
        res = supabase.table("pesanan").select("*").ilike("no_resi", f"%{keyword}").execute()
        
        if res.data:
            data_found = sorted(res.data, key=lambda x: x['id'], reverse=True)
            d = data_found[0] 
            st.divider()
            st.write(f"📦 **Pesanan Ditemukan:** `{d['no_resi']}`")
            
            status_color = "green" if d['status'] == "Selesai" else "red" if "Dibatalkan" in d['status'] or "Ditolak" in d['status'] else "blue"
            st.markdown(f"""<div style="padding:10px; background-color:{'#e8f5e9' if status_color=='green' else '#ffebee' if status_color=='red' else '#e3f2fd'}; border:1px solid {status_color}; border-radius:5px;"><h3 style="margin:0; color:{status_color};">{d['status']}</h3></div>""", unsafe_allow_html=True)
            
            st.write(f"**Item:** {d['item_pesanan']}")
            st.caption(f"Pemesan: {d['nama_pemesan']}")
            
            # --- FOTO SERAH TERIMA ---
            foto_url = d.get('foto_penerima')
            st.write("---")
            if foto_url:
                st.success("📸 **Bukti Serah Terima:**")
                st.image(foto_url, width=300)
            elif d['status'] == "Selesai":
                st.warning("⚠️ Foto serah terima sedang diunggah.")

            # LOGIKA REFUND OTOMATIS
            if d['status'] == "Menunggu Verifikasi":
                st.divider()
                st.info("Tombol pembatalan muncul setelah 4 jam.")
                try:
                    waktu_str = d.get('created_at')
                    if not waktu_str: waktu_pesan = datetime.now(timezone.utc)
                    else: waktu_pesan = datetime.fromisoformat(waktu_str.replace('Z', '+00:00'))
                    
                    if (datetime.now(timezone.utc) - waktu_pesan) >= timedelta(hours=4):
                        st.error("Waktu tunggu habis.")
                        if st.button("❌ Batalkan & Simpan Saldo ke Voucher"):
                            try:
                                refund_nominal = 0
                                for i_str in d['item_pesanan'].split(", "):
                                    if "x " in i_str: q_str, n = i_str.split("x ", 1); q = int(q_str)
                                    else: q = 1; n = i_str 
                                    cur = supabase.table("barang").select("*").eq("nama_barang", n).execute()
                                    if cur.data:
                                        supabase.table("barang").update({"stok": cur.data[0]['stok']+q}).eq("nama_barang", n).execute()
                                        refund_nominal += cur.data[0]['harga']*q
                                
                                nominal_potongan_lama = d.get('potongan_voucher', 0) or 0
                                total_refund = refund_nominal # Kembalikan nilai barang
                                
                                kode_baru = generate_kode_voucher()
                                data_voucher = {
                                    "kode_voucher": kode_baru,
                                    "nominal": total_refund, 
                                    "status": "AKTIF",
                                    "pemilik": d['nama_pemesan']
                                }
                                supabase.table("vouchers").insert(data_voucher).execute()
                                supabase.table("pesanan").update({"status": "Dibatalkan (Refund Voucher)"}).eq("id", d['id']).execute()
                                
                                st.success("✅ Berhasil Dibatalkan!")
                                st.markdown(f"""
                                <div style="background-color:#fff3cd; padding:20px; border-radius:10px; text-align:center; border:2px dashed orange;">
                                    <p>Saldo Anda telah diamankan ke Voucher:</p>
                                    <h1 style="color:#d35400; font-family:monospace; font-size:30px; letter-spacing: 2px;">{kode_baru}</h1>
                                    <p>Saldo: <b>{format_rupiah(total_refund)}</b></p>
                                    <small>Simpan kode ini!</small>
                                </div>
                                """, unsafe_allow_html=True)
                                tampilkan_copy_text(kode_baru, "SALIN KODE VOUCHER")
                                del st.session_state.resi_aktif
                                st.stop()
                            except Exception as e: st.error(f"Gagal Refund: {e}")
                except: pass

            elif d['status'] == "Selesai":
                st.divider()
                st.subheader("⭐ Berikan Ulasan")
                if d.get('rating') is None:
                    with st.form("form_ulasan"):
                        pil = st.selectbox("Rating", ["5 - Puas", "4 - Baik", "3 - Cukup", "2 - Kurang", "1 - Kecewa"])
                        kom = st.text_area("Komentar")
                        if st.form_submit_button("Kirim"):
                            rate_val = int(pil.split(" - ")[0])
                            supabase.table("pesanan").update({"rating": rate_val, "ulasan": kom}).eq("id", d['id']).execute()
                            st.success("Terima kasih!"); st.rerun()
                else:
                    st.info("✅ Ulasan terkirim.")
                    st.write(f"Rating: {'⭐'*d['rating']}")
        else:
            st.error("Tidak ditemukan.")

class_tambahan = "naik" if total_duit > 0 else ""
st.markdown(f'<a href="#paling-atas" class="back-to-top {class_tambahan}">⬆️</a>', unsafe_allow_html=True)

if total_duit > 0:
    with st.container(border=True):
        st.markdown('<span class="floating-bar-marker"></span>', unsafe_allow_html=True)
        c_float_1, c_float_2 = st.columns([1.5, 1], vertical_alignment="center")
        with c_float_1:
            st.markdown(f"<div style='font-size:14px; font-weight:bold; color:#333;'>Total: {format_rupiah(total_duit)}</div>", unsafe_allow_html=True)
            st.caption(f"{total_qty} Barang")
        with c_float_2:
            if st.button("🛒 Lihat Troli", type="primary", use_container_width=True):
                show_cart_modal()

