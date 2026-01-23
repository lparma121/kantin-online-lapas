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

https://gdvphhymxlhuarvxwvtm.supabase.co/storage/v1/object/public/KANTIN-ASSETS/banner/unnamed.jpg

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
                        # Gambar
                        img = item['gambar_url'] if item.get('gambar_url') else "https://cdn-icons-png.flaticon.com/512/2515/2515263.png"
                        st.image(img, use_container_width=True)
                        st.write(f"**{item['nama_barang']}**")
                        st.caption(f"{format_rupiah(item['harga'])} | Stok: {item['stok']}")
                        
                        # Hitung Jumlah di Keranjang
                        qty_di_keranjang = sum(1 for x in st.session_state.keranjang if x['nama'] == item['nama_barang'])
                        
                        # Tombol - 0 +
                        c_min, c_val, c_plus = st.columns([1, 1, 1])
                        
                        with c_min:
                            if st.button("➖", key=f"min_{item['id']}"):
                                if qty_di_keranjang > 0:
                                    kurangi_dari_keranjang(item['nama_barang'])
                                    st.rerun()
                        
                        with c_val:
                            st.markdown(f"<div class='qty-display'>{qty_di_keranjang}</div>", unsafe_allow_html=True)
                            
                        with c_plus:
                            if st.button("➕", key=f"plus_{item['id']}"):
                                if qty_di_keranjang < item['stok']:
                                    tambah_ke_keranjang(item['nama_barang'], item['harga'])
                                    st.rerun()
                                else:
                                    st.toast("Stok Habis!", icon="⚠️")

    with col_checkout:
        st.header("📝 Checkout")
        
        if not st.session_state.keranjang:
            st.info("Keranjang kosong. Silakan pilih menu di sebelah kiri.")
        else:
            with st.container(border=True):
                st.write("**Rincian Pesanan:**")
                item_counts = {}
                item_prices = {}
                for x in st.session_state.keranjang:
                    item_counts[x['nama']] = item_counts.get(x['nama'], 0) + 1
                    item_prices[x['nama']] = x['harga']
                
                for nama, qty in item_counts.items():
                    subtotal = qty * item_prices[nama]
                    st.caption(f"- {qty}x {nama} ({format_rupiah(subtotal)})")
                
                st.divider()
                total_duit = sum(i['harga'] for i in st.session_state.keranjang)
                st.markdown(f"### Total: {format_rupiah(total_duit)}")
                st.divider()

                st.write("**Pilih Metode Pembayaran:**")
                bayar = st.selectbox("Metode", ["Transfer Bank (BRI/BCA)", "E-Wallet (DANA/Gopay)"], label_visibility="collapsed")
                
                if "Transfer Bank" in bayar:
                    st.info("""
                    🏦 **Transfer Bank BRI**
                    No. Rek: **1234-5678-900**
                    An. Koperasi Lapas
                    """)
                else:
                    st.info("""
                    📱 **E-Wallet (DANA/Gopay)**
                    Nomor: **0812-3456-7890**
                    An. Admin Kantin
                    """)

                with st.form("form_pesan"):
                    pemesan = st.text_input("Nama Pengirim")
                    untuk = st.text_input("Nama WBP (Penerima)")
                    wa = st.text_input("WhatsApp")
                    st.write("**Bukti Transfer:**")
                    bukti_tf = st.file_uploader("Upload Foto/Screenshot", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
                    st.markdown("---")
                    submit = st.form_submit_button("✅ KIRIM PESANAN", type="primary")
                    
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
# 3. LACAK PESANAN (FITUR BATALKAN PESANAN)
# =========================================
elif menu == "🔍 Lacak Pesanan":
    st.title("Lacak Status Pesanan")
    resi_input = st.text_input("Masukkan Nomor Resi")
    
    if st.button("🔍 Cek Resi"):
        if resi_input:
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
                    stat = d['status']
                    val = 10 if stat == "Menunggu Verifikasi" else 50 if stat == "Pembayaran Valid (Diproses)" else 100
                    st.progress(val, text=stat)
                
                if d['status'] == "Selesai" and d['foto_penerima']:
                    st.divider()
                    st.image(d['foto_penerima'], caption="Bukti Foto Penyerahan")
                
                # --- FITUR BATALKAN PESANAN ---
                if d['status'] == "Menunggu Verifikasi":
                    st.divider()
                    st.warning("⚠️ Pesanan ini belum diproses admin. Anda dapat membatalkannya.")
                    
                    if st.button("❌ Batalkan Pesanan Ini", type="primary"):
                        try:
                            # 1. Parsing item string (cth: "2x Nasi, 1x Es") untuk kembalikan stok
                            items_list = d['item_pesanan'].split(", ")
                            for item_str in items_list:
                                parts = item_str.split("x ", 1)
                                if len(parts) == 2:
                                    qty_batal = int(parts[0])
                                    nama_batal = parts[1]
                                    
                                    # Kembalikan Stok
                                    curr = supabase.table("barang").select("stok").eq("nama_barang", nama_batal).execute()
                                    if curr.data:
                                        stok_skrg = curr.data[0]['stok']
                                        supabase.table("barang").update({"stok": stok_skrg + qty_batal}).eq("nama_barang", nama_batal).execute()
                            
                            # 2. Hapus Pesanan
                            supabase.table("pesanan").delete().eq("id", d['id']).execute()
                            
                            st.success("✅ Pesanan berhasil dibatalkan. Stok barang telah dikembalikan.")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal membatalkan: {e}")
                            
            else:
                st.error("Nomor Resi tidak ditemukan.")

