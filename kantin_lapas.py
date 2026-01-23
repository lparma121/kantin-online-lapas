import streamlit as st
from supabase import create_client
import time

# --- KONEKSI DATABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Kantin Lapas Online", page_icon="🍱", layout="wide")

# --- CSS CUSTOM (AGAR KOLOM KANAN TIDAK BERGERAK) ---
st.markdown("""
<style>
    /* 1. Tombol yang lebih cantik */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
    }
    
    /* 2. Card Style untuk Kotak Produk */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* 3. Style Harga Warna Merah */
    .harga-tag {
        color: #d9534f;
        font-size: 16px;
        font-weight: bold;
    }

    /* 4. LOGIKA STICKY (PENTING!) */
    /* Kode ini mencari kolom kedua (checkout) dan menguncinya */
    div[data-testid="column"]:nth-of-type(2) {
        position: sticky;
        top: 80px; /* Jarak berhenti dari atas layar */
        align-self: start; /* Pastikan tingginya tidak dipaksa sama dengan kolom kiri */
        
        /* Hiasan Panel Checkout */
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
        z-index: 100;
    }

    /* 5. Khusus HP: Matikan fitur sticky agar tidak menutupi layar */
    @media (max-width: 640px) {
        div[data-testid="column"]:nth-of-type(2) {
            position: static;
            top: auto;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI FORMAT RUPIAH ---
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# --- SESSION STATE KERANJANG ---
if 'keranjang' not in st.session_state:
    st.session_state.keranjang = []

def tambah_ke_keranjang(item, harga):
    st.session_state.keranjang.append({"nama": item,
