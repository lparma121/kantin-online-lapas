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
    .block-container { padding-top: 1rem !important; padding-bottom: 8rem !important; }
    .nama-produk { font-size: 13px; font-weight: 600; color: #333; height: 34px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    .harga-produk { color: #00AAFF; font-weight: 700; font-size: 14px; }
    .back-to-top { position: fixed; bottom: 30px; right: 20px; width: 45px; height: 45px; border-radius: 50%; background-color: rgba(0, 170, 255, 0.3); color: white !important; text-align: center; line-height: 45px; font-size: 22px; z-index: 999990; backdrop-filter: blur(2px); }
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

# --- JAVASCRIPT COPY UTILS ---
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
    <div onclick="salinNominal()" style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; border: 2px dashed #00AAFF; text-align: center; cursor: pointer;">
        <p style="margin:0; color: #555; font-size: 13px;">Total Belanja + Kode Unik (<b style="color:red">{kode_unik}</b>)</p>
        <h2 style="margin:0; color: #000;">{total_rp} 📋</h2>
        <div id="notif_nominal" style="font-size: 11px; color: green; height: 15px;"></div>
    </div>
    <script>
    function salinNominal() {{
        navigator.clipboard.writeText("{total_raw}");
        document.getElementById("notif_nominal").innerHTML = "✅ Nominal disalin!";
        setTimeout(function() {{ document.getElementById("notif_nominal").innerHTML = ""; }}, 3000);
    }}
    </script>
    """
    components.html(html_code, height=130)

# --- GENERATOR GAMBAR NOTA ---
def buat_struk_image(data_pesanan, list_keranjang, total_bayar, resi, potongan_voucher=0):
    width, height = 500, 750
    img = Image.new('RGB', (width, height), color='white')
    d = ImageDraw.Draw(img)
    d.text((160, 20), "e-PAS Mart Lapas Arga Makmur", fill="black")
    y = 90
    d.text((30, y), f"NO. RESI  : {resi}", fill="black"); y+=25
    d.text((30, y), f"PENGIRIM  : {data_pesanan['nama_pemesan']}", fill="black"); y+=25
    d.text((30, y), f"PENERIMA  : {data_pesanan['untuk_siapa']}", fill="black"); y+=40
    for item in list_keranjang:
        d.text((30, y), f"- {item['nama'][:25]} x{item['qty']}", fill="black")
        d.text((350, y), format_rupiah(item['harga']*item['qty']), fill="black")
        y += 25
    y += 20
    if potongan_voucher > 0:
        d.text((30, y), "POTONGAN VOUCHER", fill="green")
        d.text((350, y), f"-{format_rupiah(potongan_voucher)}", fill="green"); y+=25
    d.text((30, y), "TOTAL BAYAR", fill="black")
    d.text((350, y), format_rupiah(total_bayar), fill="red")
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
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
    st.markdown('<img src="https://gdvphhymxlhuarvxwvtm.supabase.co/storage/v1/object/public/KANTIN-ASSETS/banner/unnamed.jpg" style="width: 100%; border-radius: 15px;">', unsafe_allow_html=True)
    st.subheader("💬 Apa Kata Mereka?")
    try:
        res_u = supabase.table("pesanan").select("nama_pemesan, rating, ulasan").not_.is_("rating", "null").order("created_at", desc=True).limit(3).execute()
        if res_u.data:
            cols = st.columns(3)
            for i, u in enumerate(res_u.data):
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"**{u['nama_pemesan']}**\n\n{'⭐'*u['rating']}\n\n*{u['ulasan']}*")
    except: st.caption("Belum ada ulasan.")

# =========================================
# 2. PESAN BARANG
# =========================================
elif menu == "🛍️ Pesan Barang":
    st.markdown("## 🛍️ Etalase")
    
    tab_menu, tab_checkout = st.tabs(["🍔 Pilih Menu", "💳 Pembayaran"])

    with tab_menu:
        res_b = supabase.table("barang").select("*").gt("stok", 0).order('nama_barang').execute()
        if res_b.data:
            cols = st.columns(2)
            for i, item in enumerate(res_b.data):
                with cols[i % 2]:
                    with st.container(border=True):
                        # --- PERBAIKAN DI SINI ---
                        # Pastikan URL gambar ada dan valid, jika tidak pakai gambar default
                        url_gambar = item.get('gambar_url')
                        if not url_gambar or url_gambar == "":
                            url_gambar = "https://cdn-icons-png.flaticon.com/512/2515/2515263.png"
                        
                        try:
                            st.image(url_gambar, use_container_width=True)
                        except:
                            # Jika URL-nya rusak/error saat dimuat, tampilkan placeholder
                            st.image("https://cdn-icons-png.flaticon.com/512/2515/2515263.png", use_container_width=True)
                        # -------------------------

                        st.markdown(f"<div class='nama-produk'>{item['nama_barang']}</div><div class='harga-produk'>{format_rupiah(item['harga'])}</div>", unsafe_allow_html=True)
                        if st.button("Tambah +", key=f"add_{item['id']}", use_container_width=True):
                            st.session_state.keranjang.append({"id": item['id'], "nama": item['nama_barang'], "harga": item['harga'], "qty": 1})
                            st.toast(f"{item['nama_barang']} ditambah!")
                            st.rerun()
    # === TAB 2: PEMBAYARAN (VOUCHER REFUND OTOMATIS) ===
    with tab_checkout:
        st.header("📝 Konfirmasi & Pembayaran")
        
        if st.session_state.nota_sukses:
            res_data = st.session_state.nota_sukses
            st.success("✅ Pesanan Berhasil!")
            tampilkan_copy_text(res_data['resi'], "SALIN RESI")
            st.image(image_to_base64(res_data['data']), width=280)
            if st.button("🔄 Belanja Lagi"):
                st.session_state.nota_sukses = None
                st.rerun()
        else:
            if not st.session_state.keranjang:
                st.info("Keranjang kosong.")
            else:
                # ------------------------------------------
                # 1. LOGIKA VOUCHER & TOTAL
                # ------------------------------------------
                nominal_potongan = 0
                sisa_tagihan = total_duit
                
                with st.expander("🎫 Punya Kode Voucher Refund?", expanded=True):
                    col_v1, col_v2 = st.columns([3, 1])
                    with col_v1:
                        input_v = st.text_input("Masukkan Kode Voucher", key="input_voucher_box")
                    with col_v2:
                        st.write(""); st.write("")
                        if st.button("Gunakan"):
                            is_valid, data_v = cek_voucher_db(input_v.strip())
                            if is_valid:
                                st.session_state.voucher_aktif = data_v
                                st.toast("Voucher Berhasil Dipasang!", icon="✅")
                                st.rerun()
                            else: st.error("Kode Voucher Salah / Habis")

                    if st.session_state.voucher_aktif:
                        v = st.session_state.voucher_aktif
                        saldo_voucher = v['nominal']
                        st.success(f"✅ **Voucher Terpasang:** {v['kode_voucher']}")
                        st.info(f"Saldo Voucher: {format_rupiah(saldo_voucher)}")
                        
                        nominal_potongan = min(saldo_voucher, total_duit)
                        sisa_tagihan = total_duit - nominal_potongan
                        
                        if st.button("❌ Lepas Voucher"):
                            st.session_state.voucher_aktif = None
                            st.rerun()

                # Hitung Kode Unik
                total_transfer = 0
                if sisa_tagihan > 0:
                    total_transfer = sisa_tagihan + st.session_state.kode_unik

                st.divider()
                st.write("**Rincian Pembayaran:**")
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"Total Belanja: {format_rupiah(total_duit)}")
                    if nominal_potongan > 0:
                        st.write(f"Potongan Voucher: -{format_rupiah(nominal_potongan)}")
                    
                    if total_transfer > 0:
                        st.write(f"Kode Unik: +{st.session_state.kode_unik}")
                        tampilkan_total_copy_otomatis(format_rupiah(total_transfer), str(total_transfer), st.session_state.kode_unik)
                    else:
                        st.markdown("<h3 style='color:green;'>✨ LUNAS DENGAN VOUCHER</h3>", unsafe_allow_html=True)

                # ------------------------------------------
                # 2. PILIH METODE BAYAR & FORM
                # ------------------------------------------
                metode_bayar = "Full Voucher"
                if total_transfer > 0:
                    st.write("---")
                    metode_bayar = st.selectbox("Pilih Metode Transfer Sisa", ["Transfer Bank (BRI)", "E-Wallet (DANA)"])
                    if "BRI" in metode_bayar: st.warning("🏦 **BRI: 1234-5678-900 (Koperasi Lapas)**")
                    else: st.warning("📱 **DANA: 0812-3456-7890 (Admin Kantin)**")

                with st.form("checkout_form"):
                    pemesan = st.text_input("Nama Pengirim")
                    untuk = st.text_input("Nama WBP + Bin/Binti")
                    wa = st.text_input("WhatsApp")
                    bukti = st.file_uploader("Upload Bukti Sisa Bayar", type=['jpg','png']) if total_transfer > 0 else None

                    if st.form_submit_button("✅ Proses Pesanan Sekarang", type="primary"):
                        if not (pemesan and untuk and wa): st.error("Lengkapi data diri!")
                        elif total_transfer > 0 and not bukti: st.error("Upload bukti transfer sisa!")
                        else:
                            try:
                                url_bukti = upload_file_bytes(bukti.getvalue(), "bukti_transfer", f"tf_{int(time.time())}.jpg") if bukti else ""
                                resi = generate_resi()
                                
                                # 1. Update Saldo Voucher di Database
                                if st.session_state.voucher_aktif:
                                    sisa_saldo_v = st.session_state.voucher_aktif['nominal'] - nominal_potongan
                                    status_v = "AKTIF" if sisa_saldo_v > 0 else "HABIS"
                                    supabase.table("vouchers").update({"nominal": sisa_saldo_v, "status": status_v}).eq("kode_voucher", st.session_state.voucher_aktif['kode_voucher']).execute()

                                # 2. Insert Pesanan
                                data_ins = {
                                    "nama_pemesan": pemesan, "untuk_siapa": untuk, "nomor_wa": wa,
                                    "item_pesanan": ", ".join([f"{x['qty']}x {x['nama']}" for x in st.session_state.keranjang]),
                                    "total_harga": total_transfer, "bukti_transfer": url_bukti, "status": "Menunggu Verifikasi",
                                    "cara_bayar": metode_bayar, "no_resi": resi,
                                    "voucher_used": st.session_state.voucher_aktif['kode_voucher'] if st.session_state.voucher_aktif else None,
                                    "potongan_voucher": nominal_potongan, "created_at": datetime.now(timezone.utc).isoformat()
                                }
                                supabase.table("pesanan").insert(data_ins).execute()

                                # 3. Update Stok
                                for x in st.session_state.keranjang:
                                    cur_s = supabase.table("barang").select("stok").eq("nama_barang", x['nama']).execute()
                                    if cur_s.data: supabase.table("barang").update({"stok": cur_s.data[0]['stok'] - x['qty']}).eq("nama_barang", x['nama']).execute()

                                st.session_state.nota_sukses = {'data': buat_struk_image(data_ins, st.session_state.keranjang, total_transfer, resi, nominal_potongan), 'resi': resi}
                                reset_keranjang()
                                st.rerun()
                            except Exception as e: st.error(f"Error: {e}")

# =========================================
# 3. LACAK PESANAN (REFUND OTOMATIS 4 JAM)
# =========================================
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Pesanan")
    resi_in = st.text_input("Masukkan Kode Resi (4 Digit Terakhir)")
    if st.button("Cek Status"):
        res = supabase.table("pesanan").select("*").ilike("no_resi", f"%{resi_in.strip()}%").execute()
        if res.data:
            d = res.data[0]
            st.divider()
            st.write(f"📦 Resi: `{d['no_resi']}`")
            st.markdown(f"### Status: **{d['status']}**")
            
            # Logika Refund Otomatis jika > 4 Jam
            if d['status'] == "Menunggu Verifikasi":
                waktu_buat = datetime.fromisoformat(d['created_at'].replace('Z', '+00:00'))
                selisih = datetime.now(timezone.utc) - waktu_buat
                if selisih >= timedelta(hours=4):
                    st.error("⚠️ Pesanan belum diproses lebih dari 4 jam.")
                    if st.button("❌ Batalkan & Refund ke Voucher"):
                        try:
                            # Hitung nominal refund (Uang Transfer + Potongan Voucher sebelumnya)
                            # Sederhananya: Kembalikan daya beli senilai total belanja murni
                            total_refund = d['total_harga'] + d['potongan_voucher']
                            kode_v_baru = generate_kode_voucher()
                            
                            # Masukkan ke tabel vouchers
                            supabase.table("vouchers").insert({
                                "kode_voucher": kode_v_baru, "nominal": total_refund, 
                                "status": "AKTIF", "pemilik": d['nama_pemesan']
                            }).execute()
                            
                            # Update Status Pesanan
                            supabase.table("pesanan").update({"status": "Dibatalkan (Refund Voucher)"}).eq("id", d['id']).execute()
                            
                            st.success("✅ Berhasil Dibatalkan!")
                            st.info(f"Saldo Anda telah kembali dalam bentuk Voucher: **{kode_v_baru}**")
                            tampilkan_copy_text(kode_v_baru, "SALIN KODE VOUCHER")
                        except Exception as e: st.error(f"Gagal Refund: {e}")
            
            if d['status'] == "Selesai":
                if d.get('foto_penerima'): st.image(d['foto_penerima'], width=300, caption="Bukti Terima")
                if d.get('rating') is None:
                    with st.form("ulasan"):
                        r = st.slider("Rating", 1, 5, 5)
                        u = st.text_area("Komentar")
                        if st.form_submit_button("Kirim"):
                            supabase.table("pesanan").update({"rating": r, "ulasan": u}).eq("id", d['id']).execute()
                            st.rerun()
        else: st.error("Pesanan tidak ditemukan.")

# Floating Bar
if total_duit > 0:
    st.markdown('<a href="#paling-atas" class="back-to-top naik">⬆️</a>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<span class="floating-bar-marker"></span>', unsafe_allow_html=True)
        c_f1, c_f2 = st.columns([1.5, 1])
        c_f1.write(f"Total: {format_rupiah(total_duit)}")
        if c_f2.button("🛒 Lihat Troli", type="primary"): st.rerun()

