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

# --- CSS TAMPILAN ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Poppins', sans-serif; }
    .block-container { padding-top: 1rem !important; padding-bottom: 8rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] { padding: 0px !important; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #eee; overflow: hidden; }
    .info-box { padding: 8px; }
    .nama-produk { font-size: 13px; font-weight: 600; color: #333; line-height: 1.3; height: 34px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 4px; }
    .harga-produk { color: #00AAFF; font-weight: 700; font-size: 14px; }
    .stok-produk { font-size: 10px; color: #888; margin-bottom: 8px; }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.floating-bar-marker) { position: fixed; bottom: 15px; left: 2.5%; width: 95%; z-index: 999999; background: white; box-shadow: 0 5px 20px rgba(0,0,0,0.2); border-radius: 15px; border: 1px solid #00AAFF; padding: 10px 15px !important; margin: 0 !important; display: flex; align-items: center; }
    .back-to-top { position: fixed; bottom: 30px; right: 20px; width: 45px; height: 45px; border-radius: 50%; background-color: rgba(0, 170, 255, 0.3); color: white !important; text-align: center; line-height: 45px; font-size: 22px; text-decoration: none; z-index: 999990; backdrop-filter: blur(2px); transition: all 0.3s ease; border: 1px solid rgba(255, 255, 255, 0.4); }
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

def generate_kode_voucher():
    huruf = ''.join(random.choices(string.ascii_uppercase, k=4))
    angka = ''.join(random.choices(string.digits, k=4))
    return f"V-{huruf}-{angka}"

def cek_voucher_db(kode):
    try:
        res = supabase.table("vouchers").select("*").eq("kode_voucher", kode).eq("status", "AKTIF").execute()
        return (True, res.data[0]) if res.data else (False, None)
    except: return False, None

def image_to_base64(img_bytes):
    return base64.b64encode(img_bytes).decode()

def upload_file_bytes(file_bytes, folder, nama_file):
    try:
        path = f"{folder}/{nama_file}"
        supabase.storage.from_("KANTIN-ASSETS").upload(path, file_bytes, {"upsert": "true", "content-type": "image/jpeg"})
        return supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
    except Exception: return None

def tampilkan_copy_text(text, label="SALIN"):
    html_code = f"""
    <div onclick="copyText_{text}()" style="cursor: pointer; background-color: #e3f2fd; border: 1px dashed #00AAFF; border-radius: 5px; padding: 10px; text-align: center; margin-bottom: 10px;">
        <div style="font-size: 12px; color: #555;">KLIK UNTUK {label}</div>
        <div style="font-size: 18px; font-weight: bold; color: #00AAFF;">{text}</div>
        <div id="pesan_copy_{text}" style="font-size: 10px; color: green; height: 12px;"></div>
    </div>
    <script>
    function copyText_{text}() {{
        navigator.clipboard.writeText("{text}");
        document.getElementById("pesan_copy_{text}").innerHTML = "✅ Tersalin!";
        setTimeout(function() {{ document.getElementById("pesan_copy_{text}").innerHTML = ""; }}, 2000);
    }}
    </script>
    """
    components.html(html_code, height=80)

def tampilkan_total_copy_otomatis(total_rp, total_raw, kode_unik):
    html_code = f"""
    <div onclick="salinNominal()" style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; border: 2px dashed #00AAFF; text-align: center; cursor: pointer; transition: 0.2s; margin-bottom: 20px;">
        <p style="margin:0; color: #555; font-size: 13px;">Total Belanja + Kode Unik (<b style="color:red">{kode_unik}</b>)</p>
        <h3 style="margin:5px 0; color: #00AAFF;">TOTAL TRANSFER:</h3>
        <h2 style="margin:0; color: #000; font-family: sans-serif;">{total_rp} <span style="font-size:16px">📋</span></h2>
        <div style="font-size: 11px; color: #00AAFF; font-weight:bold; margin-top:5px;">[KLIK UNTUK SALIN NOMINAL]</div>
        <div id="notif_nominal" style="font-size: 11px; color: green; height: 15px; margin-top:2px;"></div>
    </div>
    <script>
    function salinNominal() {{
        navigator.clipboard.writeText("{total_raw}");
        document.getElementById("notif_nominal").innerHTML = "✅ Nominal {total_raw} berhasil disalin!";
        setTimeout(function() {{ document.getElementById("notif_nominal").innerHTML = ""; }}, 3000);
    }}
    </script>
    """
    components.html(html_code, height=160)

def buat_struk_image(data_pesanan, list_keranjang, total_bayar, resi, potongan_voucher=0):
    width, height = 500, 750
    img = Image.new('RGB', (width, height), color='white')
    d = ImageDraw.Draw(img)
    d.text((160, 20), "e-PAS Mart Lapas", fill="black")
    y = 90
    waktu_skrg = datetime.now(timezone.utc) + timedelta(hours=7)
    d.text((30, y), f"NO. RESI  : {resi}", fill="black"); y+=25
    d.text((30, y), f"PENGIRIM  : {data_pesanan['nama_pemesan']}", fill="black"); y+=25
    d.text((30, y), f"PENERIMA  : {data_pesanan['untuk_siapa']}", fill="black"); y+=50
    for item in list_keranjang:
        d.text((30, y), f"- {item['nama'][:30]}", fill="black")
        d.text((350, y), format_rupiah(item['harga']), fill="black")
        y += 25
    y += 20
    if potongan_voucher > 0:
        d.text((30, y), "VOUCHER", fill="black")
        d.text((350, y), f"-{format_rupiah(potongan_voucher)}", fill="green"); y+=25
    d.text((30, y), "TOTAL TRANSFER", fill="black")
    d.text((350, y), format_rupiah(total_bayar), fill=(200, 0, 0))
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

total_duit = sum(item['harga'] * item['qty'] for item in st.session_state.keranjang)
total_qty = sum(item['qty'] for item in st.session_state.keranjang)

# --- SIDEBAR ---
with st.sidebar:
    st.title("e-PAS Mart")
    menu = st.radio("Navigasi", ["🏠 Beranda", "🛍️ Pesan Barang", "🔍 Lacak Pesanan"])

# =========================================
# 1. BERANDA
# =========================================
if menu == "🏠 Beranda":
    st.markdown('<img src="https://gdvphhymxlhuarvxwvtm.supabase.co/storage/v1/object/public/KANTIN-ASSETS/banner/unnamed.jpg" style="width: 100%; border-radius: 15px; margin-bottom: 20px;">', unsafe_allow_html=True)
    st.info("💡 **Fitur Baru:** Punya Voucher Refund? Masukkan kodenya saat pembayaran!")
    st.success("🚀 **e-PAS Mart:** Langkah maju Lapas Arga Makmur mewujudkan lingkungan yang bersih dan modern.")

# =========================================
# 2. PESAN BARANG
# =========================================
elif menu == "🛍️ Pesan Barang":
    st.markdown("<h2 style='margin-bottom:10px;'>🛍️ Etalase</h2>", unsafe_allow_html=True)

    @st.dialog("🛒 Keranjang Belanja")
    def show_cart_modal():
        if not st.session_state.keranjang: st.info("Keranjang kosong.")
        else:
            for i, item in enumerate(st.session_state.keranjang):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.markdown(f"**{item['nama']}**")
                    c2.caption(f"{item['qty']} x {format_rupiah(item['harga'])}")
                    if c3.button("🗑️", key=f"del_{i}"):
                        del st.session_state.keranjang[i]
                        st.rerun()
            st.divider()
            if st.button("💳 Lanjut Pembayaran", type="primary", use_container_width=True): st.rerun()

    tab_menu, tab_checkout = st.tabs(["🍔 Pilih Menu", "💳 Pembayaran"])

    with tab_menu:
        res = supabase.table("barang").select("*").gt("stok", 0).order('nama_barang').execute()
        items = res.data
        if items:
            cols = st.columns(2)
            for i, item in enumerate(items):
                with cols[i % 2]:
                    with st.container(border=True):
                        st.image(item.get('gambar_url', "https://cdn-icons-png.flaticon.com/512/2515/2515263.png"), use_container_width=True)
                        st.markdown(f"<div class='nama-produk'>{item['nama_barang']}</div><div class='harga-produk'>{format_rupiah(item['harga'])}</div>", unsafe_allow_html=True)
                        if st.button(f"Beli", key=f"add_{item['id']}", use_container_width=True):
                            st.session_state.keranjang.append({"id": item['id'], "nama": item['nama_barang'], "harga": item['harga'], "qty": 1})
                            st.rerun()
        else: st.info("Barang habis.")

    # === TAB 2: PEMBAYARAN (SYSTEM VOUCHER OTOMATIS) ===
    with tab_checkout:
        st.header("📝 Konfirmasi & Pembayaran")
        
        if st.session_state.nota_sukses:
            res_data = st.session_state.nota_sukses
            st.success("✅ Pesanan Berhasil Dikirim!")
            tampilkan_copy_text(res_data['resi'], "SALIN RESI")
            b64 = image_to_base64(res_data['data'])
            st.markdown(f'<img src="data:image/jpeg;base64,{b64}" style="width:250px; border:1px solid #ddd;">', unsafe_allow_html=True)
            if st.button("🔄 Belanja Lagi"):
                st.session_state.nota_sukses = None
                st.rerun()
        else:
            if not st.session_state.keranjang:
                st.info("Keranjang kosong.")
            else:
                # 1. LOGIKA VOUCHER & TOTAL
                nominal_potongan = 0
                sisa_tagihan = total_duit
                
                with st.expander("🎫 Punya Kode Voucher Refund?", expanded=True):
                    col_v1, col_v2 = st.columns([3, 1])
                    with col_v1: input_v = st.text_input("Kode Voucher", key="input_v")
                    with col_v2:
                        st.write(""); st.write("")
                        if st.button("Gunakan"):
                            valid, data_v = cek_voucher_db(input_v.strip())
                            if valid: 
                                st.session_state.voucher_aktif = data_v
                                st.rerun()
                            else: st.error("Salah/Habis")

                    if st.session_state.voucher_aktif:
                        v = st.session_state.voucher_aktif
                        st.success(f"Voucher Aktif: {v['kode_voucher']}")
                        nominal_potongan = min(v['nominal'], total_duit)
                        sisa_tagihan = total_duit - nominal_potongan
                        if st.button("❌ Lepas"):
                            st.session_state.voucher_aktif = None
                            st.rerun()

                # Hitung Kode Unik
                total_transfer = 0
                if sisa_tagihan > 0:
                    total_transfer = sisa_tagihan + st.session_state.kode_unik

                st.divider()
                st.write("**Rincian Pembayaran:**")
                c1, c2 = st.columns(2)
                c1.write(f"Total Belanja: {format_rupiah(total_duit)}")
                if nominal_potongan > 0: c1.write(f"Potongan Voucher: -{format_rupiah(nominal_potongan)}")
                
                # 2. PILIH METODE BAYAR (DI LUAR FORM)
                metode_bayar = "Full Voucher"
                if total_transfer > 0:
                    c1.write(f"Kode Unik: +{st.session_state.kode_unik}")
                    tampilkan_total_copy_otomatis(format_rupiah(total_transfer), str(total_transfer), st.session_state.kode_unik)
                    st.write("---")
                    metode_bayar = st.selectbox("Pilih Metode Transfer Sisa", ["Transfer Bank (BRI)", "E-Wallet (DANA)"])
                    if "BRI" in metode_bayar: st.warning("🏦 **BRI: 1234-5678-900 (Koperasi Lapas)**")
                    else: st.warning("📱 **DANA: 0812-3456-7890 (Admin Kantin)**")
                else:
                    st.success("✨ LUNAS DENGAN VOUCHER")

                # 3. FORM IDENTITAS
                with st.form("checkout"):
                    pemesan = st.text_input("Nama Pengirim")
                    untuk = st.text_input("Nama WBP + Bin/Binti")
                    wa = st.text_input("WhatsApp")
                    bukti = st.file_uploader("Upload Bukti", type=['jpg','png']) if total_transfer > 0 else None

                    if st.form_submit_button("✅ Proses Pesanan Sekarang", type="primary"):
                        if not (pemesan and untuk and wa): st.error("Lengkapi data!")
                        elif total_transfer > 0 and not bukti: st.error("Upload bukti transfer!")
                        else:
                            try:
                                url_bukti = upload_file_bytes(bukti.getvalue(), "bukti_transfer", f"tf_{int(time.time())}.jpg") if bukti else ""
                                resi = generate_resi()
                                data_insert = {
                                    "nama_pemesan": pemesan, "untuk_siapa": untuk, "nomor_wa": wa,
                                    "item_pesanan": ", ".join([f"{x['qty']}x {x['nama']}" for x in st.session_state.keranjang]),
                                    "total_harga": total_transfer, "bukti_transfer": url_bukti, 
                                    "status": "Menunggu Verifikasi", "cara_bayar": metode_bayar, "no_resi": resi,
                                    "voucher_used": st.session_state.voucher_aktif['kode_voucher'] if st.session_state.voucher_aktif else None,
                                    "potongan_voucher": nominal_potongan
                                }
                                supabase.table("pesanan").insert(data_insert).execute()
                                
                                # Update Voucher
                                if st.session_state.voucher_aktif:
                                    sisa_v = st.session_state.voucher_aktif['nominal'] - nominal_potongan
                                    supabase.table("vouchers").update({"nominal": sisa_v, "status": "AKTIF" if sisa_v > 0 else "HABIS"}).eq("kode_voucher", st.session_state.voucher_aktif['kode_voucher']).execute()
                                
                                nota = buat_struk_image(data_insert, st.session_state.keranjang, total_transfer, resi, nominal_potongan)
                                st.session_state.nota_sukses = {'data': nota, 'resi': resi}
                                reset_keranjang()
                                st.rerun()
                            except Exception as e: st.error(f"Sistem Error: {e}")

# =========================================
# 3. LACAK PESANAN (LOGIKA LAMA TETAP SAMA)
# =========================================
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Pesanan")
    resi_in = st.text_input("Masukkan Kode Resi")
    if st.button("Cek Status"):
        res = supabase.table("pesanan").select("*").ilike("no_resi", f"%{resi_in}%").execute()
        if res.data:
            d = res.data[0]
            st.info(f"Status: {d['status']}")
            st.write(f"Item: {d['item_pesanan']}")
        else: st.error("Tidak ditemukan")

# Floating UI
if total_duit > 0:
    st.markdown(f'<a href="#paling-atas" class="back-to-top naik">⬆️</a>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<span class="floating-bar-marker"></span>', unsafe_allow_html=True)
        c_f1, c_f2 = st.columns([2, 1])
        c_f1.write(f"Total: {format_rupiah(total_duit)}")
        if c_f2.button("🛒 Troli", type="primary"): show_cart_modal()
else:
    st.markdown(f'<a href="#paling-atas" class="back-to-top">⬆️</a>', unsafe_allow_html=True)
