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
        d.text((350, y), harga, fill
