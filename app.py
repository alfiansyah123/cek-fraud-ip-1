import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import pandas as pd

# --- KONFIGURASI HALAMAN WEBSITE ---
st.set_page_config(page_title="IP Fraud Checker", page_icon="🛡️")

st.title("🛡️ IP Fraud Checker - Ccp Engine")
st.markdown("""
**Versi Cloud Hosting (Via ScraperAPI)**
Hanya IP dengan Score 0 (Clean) yang akan disimpan.
""")

# --- SIDEBAR KONFIGURASI ---
st.sidebar.header("Konfigurasi API")
# Masukkan API Key default Anda di sini jika ingin otomatis
DEFAULT_API_KEY = "6b3af5fa676dfad17873b78c6e1117f1" 
api_key_input = st.sidebar.text_input("Masukkan ScraperAPI Key", value=DEFAULT_API_KEY, type="password")

st.sidebar.info("Daftar di [ScraperAPI.com](https://www.scraperapi.com) untuk dapat key gratis (1000 request).")

# --- FUNGSI REQUEST VIA SCRAPERAPI ---
def get_fraud_score(ip, api_key):
    # Kita tidak nembak langsung ke Scamalytics, tapi lewat ScraperAPI
    target_url = f"https://scamalytics.com/ip/{ip}"
    
    # Settingan Payload ScraperAPI
    payload = {
        'api_key': api_key,
        'url': target_url, 
        'country_code': 'us', # Pura-pura akses dari Amerika
        'device_type': 'desktop' # Pura-pura jadi PC Desktop
    }

    try:
        # Kirim request ke ScraperAPI (bukan ke Scamalytics langsung)
        response = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
        
        # Cek jika quota habis atau error auth
        if response.status_code == 403:
            return "AUTH_ERROR" # Key salah atau kuota habis
        
        if response.status_code != 200:
            return "ERROR"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- LOGIKA PARSING SAMA SEPERTI SEBELUMNYA ---
        # Mencari Score
        score_div = soup.find('div', class_='score')
        score_text = score_div.get_text().strip() if score_div else ""
        
        if not score_text:
             for elem in soup.find_all(string=True):
                if "Fraud Score:" in elem:
                    score_text = elem
                    break
        
        # Ambil angka dengan Regex
        match = re.search(r'(\d+)', score_text)
        if match:
            return int(match.group(1))
        return None

    except Exception as e:
        return None

# --- BAGIAN UTAMA WEBSITE ---

# 1. Upload File
uploaded_file = st.file_uploader("Upload file list IP (.txt)", type=["txt"])

if uploaded_file is not None:
    # Membaca file yang diupload
    stringio = uploaded_file.getvalue().decode("utf-8")
    ip_list = [line.strip() for line in stringio.splitlines() if line.strip()]
    
    st.write(f"Total IP ditemukan: **{len(ip_list)}**")

    # Tombol Mulai
    if st.button("Mulai Pengecekan 🚀"):
        
        if not api_key_input:
            st.error("⚠️ Harap masukkan ScraperAPI Key di menu sebelah kiri (Sidebar)!")
        else:
            # Tempat menyimpan hasil
            clean_ips = []
            
            # Membuat Progress Bar & Status Text
            progress_bar = st.progress(0)
            status_text = st.empty()
            table_placeholder = st.empty()
            
            total_ips = len(ip_list)
            
            for i, ip in enumerate(ip_list):
                # Update status
                status_text.text(f"Sedang mengecek [{i+1}/{total_ips}]: {ip} via Proxy ...")
                
                # Cek Score (Panggil fungsi baru)
                score = get_fraud_score(ip, api_key_input)
                
                # Logika Hasil
                status_msg = ""
                if score == "AUTH_ERROR":
                    st.error("Gagal! API Key salah atau Kuota ScraperAPI habis.")
                    break # Stop looping
                elif score == "ERROR":
                    status_msg = "Error/Gagal Load"
                elif score is not None:
                    status_msg = f"Score: {score}"
                    if score == 0:
                        clean_ips.append(ip)
                        status_msg += " ✅"
                    else:
                        status_msg += " ❌"
                
                # Update Progress Bar
                progress_bar.progress((i + 1) / total_ips)
                
                # Tampilkan tabel hasil sementara (hanya yang clean)
                if clean_ips:
                    df = pd.DataFrame(clean_ips, columns=["Clean IP Address (Score 0)"])
                    table_placeholder.dataframe(df, height=200)

                # JEDA WAKTU (Tidak perlu lama-lama karena pakai Proxy Rotation)
                # ScraperAPI cukup kuat, tapi kita kasih jeda dikit biar sopan
                time.sleep(1) 
                
            status_text.success("Pengecekan Selesai!")
            
            # --- HASIL AKHIR ---
            st.divider()
            st.subheader("Hasil Pengecekan")
            st.write(f"Ditemukan **{len(clean_ips)}** IP Bersih.")
            
            if clean_ips:
                # Membuat string untuk didownload
                result_text = "\n".join(clean_ips)
                
                st.download_button(
                    label="📥 Download List IP Bersih (.txt)",
                    data=result_text,
                    file_name="clean_ips_result.txt",
                    mime="text/plain"
                )
            else:
                st.warning("Tidak ada IP dengan score 0 ditemukan (atau gagal mengambil data).")
