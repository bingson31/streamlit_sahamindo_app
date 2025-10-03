import streamlit as st
import pandas as pd
import numpy as np
import datetime
import re
import google.generativeai as genai  # SDK Gemini

# — Modul data saham —
def get_stock_history(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fungsi simulasi: ambil data historis saham (OHLC) untuk simbol dan rentang tanggal.
    Ganti dengan API nyata (misalnya GoAPI atau scrapper IDX) untuk produksi.
    """
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

# — Modul interaksi Gemini —
def setup_gemini(api_key: str):
    genai.configure(api_key=api_key)

def ask_gemini(prompt: str, messages: list = None) -> str:
    if messages is None:
        messages = []

    try:
        model = genai.GenerativeModel("gemini-pro")
        chat = model.start_chat(history=[{"role": "user", "parts": m} for m in messages])
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"❌ Terjadi kesalahan saat menghubungi Gemini: {e}"

# — Aplikasi Streamlit —
def main():
    st.set_page_config(page_title="Chatbot Saham IDX", layout="wide")
    st.title("💬 Chatbot Pemantau Saham Indonesia")
    st.write("Tanyakan harga saham dengan format: **Harga BBCA pada 2025-09-01**")

    # Input API key
    gemini_key = st.text_input("🔑 Masukkan Gemini API Key", type="password")
    if not gemini_key:
        st.warning("Silakan masukkan Gemini API Key terlebih dahulu.")
        return

    setup_gemini(gemini_key)

    # Simpan riwayat chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Tampilkan riwayat chat
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input pengguna
    prompt = st.chat_input("Tulis pertanyaan kamu di sini...")

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Parsing saham + tanggal
        match = re.search(r"Harga\s+([A-Za-z0-9]+)\s+pada\s+(\d{4}-\d{2}-\d{2})", prompt, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper()
            tanggal = match.group(2)

            # Ambil data saham
            df = get_stock_history(symbol, tanggal, tanggal)
            if df.empty:
                reply = f"❌ Data untuk saham **{symbol}** pada tanggal **{tanggal}** tidak ditemukan."
            else:
                row = df.iloc[0]
                reply = (
                    f"📈 Harga saham **{symbol}** pada **{tanggal}**:\n"
                    f"- Open: Rp{row['open']:.2f}\n"
                    f"- High: Rp{row['high']:.2f}\n"
                    f"- Low: Rp{row['low']:.2f}\n"
                    f"- Close: Rp{row['close']:.2f}\n"
                    f"- Volume: {row['volume']:,}\n"
                )

                # Kirim ke Gemini untuk penjelasan
                gemini_prompt = f"Berikan analisis singkat dan sederhana terhadap data saham berikut:\n{reply}"
                analisis = ask_gemini(gemini_prompt, messages=[prompt])
                reply += "\n---\n" + analisis

        else:
            # Pertanyaan umum → kirim ke Gemini langsung
            reply = ask_gemini(prompt, messages=[msg["content"] for msg in st.session_state.chat_history])

        # Tampilkan jawaban
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

if __name__ == "__main__":
    main()
