import streamlit as st
import pandas as pd
import numpy as np
import datetime
import re
import google.generativeai as genai  # pip install google-generativeai


# -------- DATA SIMULASI (bisa diganti real API nanti) --------
def get_stock_history(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    df = pd.DataFrame({
        "date": dates,
        "open": 100 + np.random.randn(len(dates)).cumsum(),
        "high": 100 + np.random.randn(len(dates)).cumsum(),
        "low": 100 + np.random.randn(len(dates)).cumsum(),
        "close": 100 + np.random.randn(len(dates)).cumsum(),
        "volume": (np.random.rand(len(dates)) * 1e6).astype(int),
    })
    return df


# -------- KONFIGURASI GEMINI --------
def setup_gemini(api_key: str):
    genai.configure(api_key=api_key)


def ask_gemini(prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error saat menghubungi Gemini: {e}"


# -------- APLIKASI STREAMLIT --------
def main():
    st.set_page_config(page_title="Chatbot Saham IDX", layout="wide")
    st.title("📈 Chatbot Pemantau Saham Indonesia")
    st.markdown("Tanyakan harga saham seperti: **Harga BBCA pada 2025-09-01**")

    # Input API Key
    gemini_key = st.text_input("🔑 Masukkan Gemini API Key", type="password")
    if not gemini_key:
        st.warning("Masukkan Gemini API key terlebih dahulu.")
        return
    setup_gemini(gemini_key)

    # Simpan riwayat chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Tampilkan chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input pengguna
    prompt = st.chat_input("Tulis pertanyaan kamu di sini...")

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Cari pola pertanyaan saham
        match = re.search(r"Harga\s+([A-Za-z0-9]+)\s+pada\s+(\d{4}-\d{2}-\d{2})", prompt, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper()
            tanggal = match.group(2)

            df = get_stock_history(symbol, tanggal, tanggal)
            if df.empty:
                reply = f"❌ Data untuk saham **{symbol}** pada tanggal **{tanggal}** tidak ditemukan."
            else:
                row = df.iloc[0]
                harga = (
                    f"📊 Harga saham **{symbol}** pada **{tanggal}**:\n"
                    f"- Open: Rp{row['open']:.2f}\n"
                    f"- High: Rp{row['high']:.2f}\n"
                    f"- Low: Rp{row['low']:.2f}\n"
                    f"- Close: Rp{row['close']:.2f}\n"
                    f"- Volume: {row['volume']:,}\n"
                )

                # Interpretasi dengan Gemini
                gemini_prompt = f"Berikan analisis sederhana terhadap data saham berikut:\n\n{harga}"
                analisis = ask_gemini(gemini_prompt)
                reply = harga + "\n---\n" + analisis
        else:
            # Pertanyaan umum dikirim ke Gemini
            reply = ask_gemini(prompt)

        # Tampilkan jawaban asisten
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)


if __name__ == "__main__":
    main()
