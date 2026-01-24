import streamlit as st
from supabase import create_client
import time
from PIL import Image, ImageDraw, ImageFont
import io
import random
import string
import base64
from datetime import datetime, timedelta, timezone

# --- KONEKSI DATABASE ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(URL, KEY)
except:
    st.error("⚠️ Koneksi Database Gagal. Cek Secrets Anda.")
    st.stop()

st.set_page_config(page_title="e-PAS Mart", page_icon="🛍️", layout="wide")

# --- TITIK JANGKAR SCROLL KE ATAS ---
st.markdown('<div id="paling-atas"></div>', unsafe_allow_html=True)

# --- CSS CUSTOM LENGKAP ---
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

    /* 1. GAMBAR & KARTU */
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

    /* 2. GRID 2 KOLOM DI HP */
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

    /* 3. TEKS PRODUK */
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

    /* 4. FLOATING BOTTOM BAR (KERANJANG MELAYANG) */
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

    /* 5. BACK TO TOP (GHOST MODE) */
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

# --- GENERATOR GAMBAR ---
def buat_struk_image(data_pesanan, list_keranjang, total_bayar, resi):
    width, height = 500, 700
    img = Image.new('RGB', (width, height), color='white')
    d = ImageDraw.Draw(img)
    try: font_header = ImageFont.load_default() 
    except: pass
    d.text((160, 20), "e-PAS Mart Lapas", fill="black")
    d.text((150, 40), "Bukti Transaksi Resmi", fill="gray")
    d.line((20, 70, 480, 70), fill="black", width=2)
    y = 90
    d.text((30, y), f"NO. RESI  : {resi}", fill="black"); y+=25
    d.text((30, y), f"TANGGAL   : {time.strftime('%d-%m-%Y %H:%M')}", fill="black"); y+=25
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
    d.text((30, y), "TOTAL BAYAR", fill="black")
    d.text((350, y), format_rupiah(total_bayar), fill=(200, 0, 0))
    y += 50
    d.text((120, y), "TERIMA KASIH ATAS KUNJUNGAN ANDA", fill="gray")
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    return buf.getvalue()

def buat_voucher_image(nama, nominal, resi_asal):
    width, height = 600, 300
    img = Image.new('RGB', (width, height), color='#f0f8ff') 
    d = ImageDraw.Draw(img)
    biru_tua = (0, 85, 255)
    d.rectangle([(10, 10), (width-10, height-10)], outline=biru_tua, width=5)
    d.text((40, 30), "VOUCHER PENGEMBALIAN DANA", fill=biru_tua)
    d.text((40, 120), f"Kepada: {nama}", fill="black")
    d.text((300, 120), "Senilai:", fill="black")
    d.text((300, 145), format_rupiah(nominal), fill=(220, 20, 60))
    d.text((400, 220), f"REF-{resi_asal}", fill=biru_tua)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=95)
    return buf.getvalue()

# --- SESSION STATE ---
if 'keranjang' not in st.session_state: st.session_state.keranjang = []
# State khusus untuk menyimpan nota setelah sukses order
if 'nota_sukses' not in st.session_state: st.session_state.nota_sukses = None

def reset_keranjang(): st.session_state.keranjang = []

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
    st.markdown("<h3 style='text-align: center;'>Belanja Aman & Transparan</h3>", unsafe_allow_html=True)
    st.info("💡 e-PAS Mart menerapkan prinsip **100% Cashless (Non-Tunai)**.")

# =========================================
# 2. PESAN BARANG
# =========================================
elif menu == "🛍️ Pesan Barang":
    st.markdown("<h2 style='margin-bottom:10px;'>🛍️ Etalase</h2>", unsafe_allow_html=True)

    # Hitung total
    total_duit = sum(item['harga'] * item['qty'] for item in st.session_state.keranjang)
    total_qty = sum(item['qty'] for item in st.session_state.keranjang)

    # --- DIALOG KERANJANG ---
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
            st.markdown(f"#### Total: {format_rupiah(total_duit)}")
            if st.button("💳 Lanjut Pembayaran", type="primary", use_container_width=True):
                 st.toast("Silakan klik Tab 'Pembayaran'", icon="✅")

    # --- TABS ---
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

    # === TAB 2: PEMBAYARAN (FIX DOWNLOAD) ===
    with tab_checkout:
        st.header("📝 Konfirmasi")
        
        # --- MODE SUKSES (TAMPILKAN NOTA DI LUAR FORM) ---
        if st.session_state.nota_sukses:
            res_data = st.session_state.nota_sukses
            st.success("✅ Pesanan Berhasil Dikirim!")
            st.markdown(f"**No. Resi:** `{res_data['resi']}`")
            
            # Tampilkan Gambar
            b64 = image_to_base64(res_data['data'])
            st.markdown(f'<img src="data:image/jpeg;base64,{b64}" style="width:250px; border:1px solid #ddd; margin-bottom:10px;">', unsafe_allow_html=True)
            
            c_dl, c_new = st.columns(2)
            with c_dl:
                # Tombol Download AMAN disini karena tidak di dalam st.form
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

        # --- MODE INPUT FORM (JIKA BELUM ADA NOTA) ---
        else:
            if not st.session_state.keranjang:
                st.info("Keranjang kosong.")
            else:
                with st.container(border=True):
                    st.write("**Item:**")
                    for x in st.session_state.keranjang:
                        st.write(f"• {x['qty']}x {x['nama']} ({format_rupiah(x['harga']*x['qty'])})")
                    st.divider()
                    st.markdown(f"### Total: {format_rupiah(total_duit)}")
                    bayar = st.selectbox("Metode Bayar", ["Transfer Bank", "E-Wallet", "🎫 Voucher / Saldo Refund"])
                    if "Voucher" in bayar: st.info("Upload Voucher.")
                    else: st.warning("Transfer sesuai instruksi.")

                    # FORM MULAI DI SINI
                    with st.form("checkout"):
                        pemesan = st.text_input("Nama Pengirim")
                        untuk = st.text_input("Nama WBP + Bin/Binti", placeholder="Contoh: Ali bin Abu")
                        wa = st.text_input("WhatsApp")
                        bukti = st.file_uploader("Upload Bukti", type=['jpg','png'], key="bukti_fix")
                        
                        # TOMBOL SUBMIT (Hanya Proses Data, Tidak Ada Download Disini)
                        if st.form_submit_button("✅ Kirim Pesanan", type="primary"):
                            if not (pemesan and untuk and wa and bukti):
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
                                        data = {
                                            "nama_pemesan": pemesan, "untuk_siapa": untuk, "nomor_wa": wa,
                                            "item_pesanan": items_str, "total_harga": total_duit,
                                            "bukti_transfer": url, "status": "Menunggu Verifikasi",
                                            "cara_bayar": bayar, "no_resi": resi
                                        }
                                        supabase.table("pesanan").insert(data).execute()
                                        for x in st.session_state.keranjang:
                                            curr = supabase.table("barang").select("stok").eq("nama_barang", x['nama']).execute()
                                            if curr.data:
                                                supabase.table("barang").update({"stok": curr.data[0]['stok'] - x['qty']}).eq("nama_barang", x['nama']).execute()

                                        nota = buat_struk_image(data, st.session_state.keranjang, total_duit, resi)
                                        
                                        # SIMPAN HASIL KE STATE & RERUN (Keluar dari Form)
                                        st.session_state.nota_sukses = {
                                            'data': nota,
                                            'resi': resi
                                        }
                                        reset_keranjang()
                                        st.rerun() 
                                        
                                    else: st.error("Gagal upload.")
                                except Exception as e: st.error(f"Error: {e}")

    # --- TOMBOL MELAYANG ---
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

# =========================================
# 3. LACAK PESANAN (LOGIKA TIMER 4 JAM)
# =========================================
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Pesanan")
    resi_in = st.text_input("No. Resi")
    if st.button("Cek"):
        st.session_state.resi_aktif = resi_in
    
    if 'resi_aktif' in st.session_state:
        res = supabase.table("pesanan").select("*").eq("no_resi", st.session_state.resi_aktif).execute()
        if res.data:
            d = res.data[0]
            st.success(f"Status: {d['status']}")
            st.write(f"Item: {d['item_pesanan']}")
            
            if d['status'] == "Menunggu Verifikasi":
                st.divider()
                st.warning("⚠️ Opsi Pembatalan")
                
                try:
                    waktu_pesan_str = d['created_at'].replace('Z', '+00:00')
                    waktu_pesan = datetime.fromisoformat(waktu_pesan_str)
                    waktu_sekarang = datetime.now(timezone.utc)
                    selisih = waktu_sekarang - waktu_pesan
                    batas_waktu = timedelta(hours=4)
                    
                    if selisih >= batas_waktu:
                        st.error("Admin belum merespon dalam 4 jam. Anda berhak membatalkan pesanan.")
                        if st.button("❌ Batalkan & Refund Sekarang"):
                            try:
                                refund = 0
                                for i_str in d['item_pesanan'].split(", "):
                                    q, n = i_str.split("x ", 1)
                                    q = int(q)
                                    cur = supabase.table("barang").select("*").eq("nama_barang", n).execute()
                                    if cur.data:
                                        supabase.table("barang").update({"stok": cur.data[0]['stok']+q}).eq("nama_barang", n).execute()
                                        refund += cur.data[0]['harga']*q
                                
                                supabase.table("pesanan").update({"status": "Dibatalkan"}).eq("id", d['id']).execute()
                                vcr = buat_voucher_image(d['nama_pemesan'], refund, d['no_resi'])
                                b64_v = image_to_base64(vcr)
                                st.markdown(f'<img src="data:image/jpeg;base64,{b64_v}" style="width:100%; border:2px dashed blue;">', unsafe_allow_html=True)
                                st.download_button("Download Voucher", vcr, f"V_{d['no_resi']}.jpg", "image/jpeg")
                                del st.session_state.resi_aktif
                                st.stop()
                            except Exception as e: st.error(f"Gagal: {e}")
                    else:
                        sisa = batas_waktu - selisih
                        jam, sisa_detik = divmod(sisa.seconds, 3600)
                        menit, _ = divmod(sisa_detik, 60)
                        st.info(f"⏳ Tombol batal muncul jika status tetap dalam 4 jam.")
                        st.caption(f"Sisa waktu: **{jam} Jam {menit} Menit**.")
                except Exception as e:
                    st.write(f"Error tanggal: {e}")
        else:
            st.error("Tidak ditemukan.")
