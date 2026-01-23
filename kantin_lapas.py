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

st.set_page_config(page_title="e-PAS Mart | Belanja Cepat & Aman", page_icon="🛍️", layout="wide")

# --- CSS CUSTOM ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    div[data-testid="stVerticalBlock"] > div { background-color: #f9f9f9; border-radius: 10px; padding: 10px; }
    .harga-tag { color: #d9534f; font-size: 16px; font-weight: bold; }
    
    /* Sticky Checkout */
    div[data-testid="column"]:nth-of-type(2) {
        position: sticky; top: 80px; align-self: start;
        background-color: #ffffff; padding: 20px; border-radius: 15px;
        border: 1px solid #e0e0e0; box-shadow: 0px 4px 10px rgba(0,0,0,0.05); z-index: 100;
    }
    
    .qty-display {
        text-align: center; font-size: 20px; font-weight: bold; margin-top: 5px;
    }
    
    @media (max-width: 640px) { div[data-testid="column"]:nth-of-type(2) { position: static; top: auto; } }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI FORMAT RUPIAH ---
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# --- FUNGSI GENERATE RESI ---
def generate_resi():
    tanggal = time.strftime("%d%m")
    acak = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"KANTIN-{tanggal}-{acak}"

# --- FUNGSI MEMBUAT GAMBAR NOTA ---
def buat_struk_image(data_pesanan, list_keranjang, total_bayar, resi):
    width, height = 500, 700
    img = Image.new('RGB', (width, height), color='white')
    d = ImageDraw.Draw(img)
    try: font_header = ImageFont.load_default() 
    except: pass
    
    black = (0, 0, 0)
    gray = (100, 100, 100)
    
    d.text((160, 20), "KANTIN LAPAS ONLINE", fill=black)
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

# --- FUNGSI UPLOAD ---
def upload_file(file_bytes, folder, nama_file):
    try:
        path = f"{folder}/{nama_file}"
        supabase.storage.from_("KANTIN-ASSETS").upload(path, file_bytes, {"upsert": "true", "content-type": "image/jpeg"})
        return supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
    except Exception as e: return None

# --- SESSION STATE KERANJANG ---
if 'keranjang' not in st.session_state: st.session_state.keranjang = []

# --- LOGIKA TAMBAH (PLUS) ---
def tambah_ke_keranjang(item, harga):
    st.session_state.keranjang.append({"nama": item, "harga": harga})

# --- LOGIKA KURANG (MINUS) ---
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
    # UBAH DISINI: Angka [0.5, 3, 0.5] membuat gambar lebih lebar agar tulisan terbaca
    c_kiri, c_tengah, c_kanan = st.columns([0.5, 3, 0.5])
    
    with c_tengah:
        # GANTI "LINK_DARI_SUPABASE_DISINI" dengan link yang Anda copy tadi
        st.image("https://gdvphhymxlhuarvxwvtm.supabase.co/storage/v1/object/public/KANTIN-ASSETS/banner/unnamed.jpg", use_container_width=True)
    
    # Judul teks di bawahnya bisa dihapus atau disederhanakan karena sudah ada di banner
    # st.markdown("<h1 style='text-align: center;'>e-PAS Mart Lapas Arga Makmur</h1>", unsafe_allow_html=True) 
    
    # Langsung ke sub-judul atau intro
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
# 2. PESAN BARANG (MODEL TABS UNTUK HP)
# =========================================
elif menu == "🛍️ Pesan Barang":
    # Hitung total duit dulu untuk keperluan floating bar
    total_duit = sum(i['harga'] for i in st.session_state.keranjang)
    
    # --- CSS UNTUK FLOATING BAR (TOTAL HARGA MELAYANG DI BAWAH) ---
    if total_duit > 0:
        st.markdown(f"""
        <style>
            .floating-total {{
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background-color: #ffffff;
                padding: 15px;
                border-top: 3px solid #00AAFF;
                box-shadow: 0px -4px 10px rgba(0,0,0,0.1);
                z-index: 99999;
                text-align: center;
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }}
        </style>
        <div class="floating-total">
            🛒 Total: {format_rupiah(total_duit)} <br>
            <span style="font-size:12px; font-weight:normal; color: #555;">(Klik Tab '💳 Pembayaran' di atas untuk lanjut)</span>
        </div>
        """, unsafe_allow_html=True)

    # --- MEMBUAT TABS ---
    tab_menu, tab_checkout = st.tabs(["🍔 Pilih Menu", "💳 Pembayaran"])

   # === TAB 1: ETALASE MENU (Desain Mobile App) ===
    with tab_menu:
        # --- CSS KHUSUS AGAR GAMBAR RAPI DI HP ---
        st.markdown("""
        <style>
            /* Memaksa gambar menjadi rasio kotak (Square) & Ujung tumpul */
            div[data-testid="stImage"] img {
                height: 150px !important; /* Tinggi gambar fix */
                object-fit: cover !important; /* Potong gambar biar pas */
                border-radius: 10px 10px 0 0 !important;
            }
            
            /* Desain Kartu Produk */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                padding: 10px !important;
                margin-bottom: 10px;
            }
            
            /* Mengecilkan font nama barang di HP */
            .nama-produk {
                font-size: 14px;
                font-weight: bold;
                line-height: 1.2;
                height: 35px; /* Batasi tinggi teks 2 baris */
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                margin-bottom: 5px;
            }
        </style>
        """, unsafe_allow_html=True)

        st.header("🛍️ Etalase")
        
        # Ambil data barang
        res_b = supabase.table("barang").select("*").gt("stok", 0).order('nama_barang').execute()
        items = res_b.data
        
        if items:
            # KITA KUNCI JADI 2 KOLOM (Standar Aplikasi HP)
            # Jangan pakai 3 atau 4, itu terlalu kecil untuk jari tangan di HP
            cols = st.columns(2) 
            
            for i, item in enumerate(items):
                with cols[i % 2]:
                    # Container Border = True (Efek Kartu)
                    with st.container(border=True):
                        
                        # 1. GAMBAR
                        img = item['gambar_url'] if item.get('gambar_url') else "https://cdn-icons-png.flaticon.com/512/2515/2515263.png"
                        st.image(img, use_container_width=True)
                        
                        # 2. NAMA & HARGA (Pakai HTML biar font pas di HP)
                        st.markdown(f"""
                        <div class="nama-produk">{item['nama_barang']}</div>
                        <div style="color:#d9534f; font-weight:bold; font-size:13px;">{format_rupiah(item['harga'])}</div>
                        <div style="font-size:11px; color:grey;">Stok: {item['stok']}</div>
                        """, unsafe_allow_html=True)
                        
                        # 3. TOMBOL (+ -)
                        # Hitung keranjang
                        qty_di_keranjang = sum(1 for x in st.session_state.keranjang if x['nama'] == item['nama_barang'])
                        
                        c_min, c_val, c_plus = st.columns([1, 1, 1])
                        
                        with c_min:
                            # Tombol Minus Tipis
                            if st.button("−", key=f"min_{item['id']}"): 
                                if qty_di_keranjang > 0:
                                    kurangi_dari_keranjang(item['nama_barang'])
                                    st.rerun()
                        
                        with c_val:
                            # Angka ditengah
                            st.markdown(f"<div style='text-align:center; font-weight:bold; padding-top:5px;'>{qty_di_keranjang}</div>", unsafe_allow_html=True)
                        
                        with c_plus:
                            # Tombol Plus Tebal
                            if st.button("➕", key=f"plus_{item['id']}"):
                                if qty_di_keranjang < item['stok']:
                                    tambah_ke_keranjang(item['nama_barang'], item['harga'])
                                    st.rerun()
                                else:
                                    st.toast("Stok Habis!", icon="⚠️")
            
            # Spasi bawah agar tidak tertutup floating bar
            st.write("\n" * 6)
    # === TAB 2: CHECKOUT / PEMBAYARAN ===
    with tab_checkout:
        st.header("📝 Konfirmasi Pesanan")
        
        if not st.session_state.keranjang:
            st.info("Keranjang masih kosong. Silakan pilih menu di Tab sebelah.")
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
                bayar = st.selectbox("Pilih Bank/E-Wallet", ["Transfer Bank (BRI/BCA)", "E-Wallet (DANA/Gopay)"], label_visibility="collapsed")
                
                if "Transfer Bank" in bayar:
                    st.warning("""
                    🏦 **Bank BRI**
                    No. Rek: **1234-5678-900**
                    An. Koperasi Lapas
                    """)
                else:
                    st.warning("""
                    📱 **DANA / Gopay**
                    Nomor: **0812-3456-7890**
                    An. Admin Kantin
                    """)

                st.write("**Data Pemesan:**")
                with st.form("form_pesan"):
                    pemesan = st.text_input("Nama Pengirim (Keluarga)")
                    untuk = st.text_input("Nama WBP (Penerima)")
                    wa = st.text_input("Nomor WhatsApp Aktif")
                    
                    st.write("**Upload Bukti Transfer:**")
                    bukti_tf = st.file_uploader("Upload Foto", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
                    
                    st.markdown("---")
                    submit = st.form_submit_button("✅ KIRIM PESANAN SEKARANG", type="primary")
                    
                if submit:
                    if pemesan and untuk and wa and bukti_tf:
                        no_resi = generate_resi()
                        file_bukti = bukti_tf.getvalue()
                        url_bukti = upload_file(file_bukti, "bukti_transfer", f"tf_{no_resi}.jpg")
                        
                        file_nota = buat_struk_image(
                            {"nama_pemesan": pemesan, "untuk_siapa": untuk}, 
                            st.session_state.keranjang, 
                            total_duit, 
                            no_resi
                        )
                        url_nota = upload_file(file_nota, "nota", f"nota_{no_resi}.jpg")
                        
                        list_items_str = []
                        for nama, qty in item_counts.items():
                            list_items_str.append(f"{qty}x {nama}")
                        final_items_str = ", ".join(list_items_str)
                        
                        data_db = {
                            "nama_pemesan": pemesan, "untuk_siapa": untuk,
                            "item_pesanan": final_items_str, "cara_bayar": bayar,
                            "status": "Menunggu Verifikasi", "nomor_wa": wa,
                            "no_resi": no_resi,
                            "bukti_transfer": url_bukti,
                            "nota_url": url_nota
                        }
                        supabase.table("pesanan").insert(data_db).execute()
                        
                        # Kurangi Stok
                        for item_name in item_counts:
                            qty_to_reduce = item_counts[item_name]
                            cur = supabase.table("barang").select("stok").eq("nama_barang", item_name).execute()
                            if cur.data:
                                current_stok = cur.data[0]['stok']
                                supabase.table("barang").update({"stok": current_stok - qty_to_reduce}).eq("nama_barang", item_name).execute()

                        reset_keranjang()
                        st.success("🎉 Pesanan Berhasil Dikirim!")
                        
                        st.markdown("**👇 Salin Nomor Resi Ini:**")
                        st.code(no_resi, language=None)
                        st.caption("Simpan resi ini untuk melacak status pesanan Anda.")
                        
                        st.divider()
                        st.image(file_nota, caption="Nota Resmi", width=300)
                        st.download_button("📥 Download Nota (JPG)", data=file_nota, file_name=f"{no_resi}.jpg", mime="image/jpeg")
                    else:
                        st.error("Mohon lengkapi semua data & upload bukti transfer!")

# =========================================
# 3. LACAK PESANAN (PERBAIKAN LOGIKA TOMBOL)
# =========================================
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Status Pesanan")
    
    # 1. Input Resi
    resi_input = st.text_input("Masukkan Nomor Resi")
    
    # 2. Tombol Cek (Simpan resi ke Session State agar tidak hilang saat refresh)
    if st.button("🔍 Cek Resi"):
        st.session_state['resi_aktif'] = resi_input
    
    # 3. Logika Tampilan (Berdasarkan Session State, bukan tombol Cek lagi)
    if 'resi_aktif' in st.session_state and st.session_state['resi_aktif']:
        resi_dicari = st.session_state['resi_aktif']
        
        # Ambil data dari database
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
                
                # Gunakan key unik agar tidak bentrok
                if st.button("❌ Batalkan Pesanan Ini", type="primary", key="btn_batal"):
                    try:
                        # 1. Kembalikan Stok Barang
                        if d.get('item_pesanan'):
                            items_list = d['item_pesanan'].split(", ")
                            for item_str in items_list:
                                # Parsing format "2x Nasi Goreng"
                                parts = item_str.split("x ", 1)
                                if len(parts) == 2:
                                    qty_batal = int(parts[0])
                                    nama_batal = parts[1]
                                    
                                    # Ambil stok sekarang
                                    curr = supabase.table("barang").select("stok").eq("nama_barang", nama_batal).execute()
                                    if curr.data:
                                        stok_skrg = curr.data[0]['stok']
                                        # Update stok (+ qty_batal)
                                        supabase.table("barang").update({"stok": stok_skrg + qty_batal}).eq("nama_barang", nama_batal).execute()
                        
                        # 2. Update Status jadi 'Dibatalkan'
                        supabase.table("pesanan").update({"status": "Dibatalkan"}).eq("id", d['id']).execute()
                        
                        st.success("✅ Pesanan berhasil dibatalkan. Stok barang telah dikembalikan.")
                        
                        # Hapus session state agar tampilan kereset
                        del st.session_state['resi_aktif']
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Gagal membatalkan. Error: {e}")
        else:
            # Jika dicari tapi tidak ketemu
            if resi_input: 
                st.error("Nomor Resi tidak ditemukan.")




