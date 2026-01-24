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
        background: rgba(2
