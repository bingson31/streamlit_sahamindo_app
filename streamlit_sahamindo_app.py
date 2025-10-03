import streamlit as st
import pandas as pd
import datetime
from google import genai  # dari SDK Gemini (google-genai) :contentReference[oaicite:3]{index=3}

# — Modul data saham — 
def get_stock_history(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Ambil data historis saham (OHLC) untuk simbol dan rentang tanggal.
    Kamu harus ganti implementasi ini agar memanggil API nyata atau scrapper.
    Format DataFrame minimal: date, open, high, low, close, volume
    """
    # ==== contoh dummy: data acak / simulasi ====
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    df = pd.DataFrame({
        "date": dates,
        "open": 100 + pd.np.random.randn(len(dates)).cumsum(),
        "high": 100 + pd.np.random.randn(len(dates)).cumsum(),
        "low": 100 + pd.np.random.randn(len(dates)).cumsum(),
        "close": 100 + pd.np.random.randn(len(dates)).cumsum(),
        "volume": (pd.np.random.rand(len(dates)) * 1e6).astype(int),
    })
    return df

# — Modul interaksi dengan Gemini API — 
def setup_gemini(api_key: str):
    genai.configure(api_key=api_key)

def ask_gemini(prompt: str, messages: list = None) -> str:
    """
    Kirim prompt + history ke Gemini dan kembalikan jawaban teks.
    """
    if messages is None:
        messages = []
    # Membentuk daftar prompt gabungan
    full_prompt = "\n".join(messages + [prompt])
    resp = genai.Client().models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt
    )
    return resp.text

# — Streamlit app utama — 
def main():
    st.set_page_config(page_title="Chatbot Saham IDX", layout="wide")
    st.title("Chatbot Pemantau Saham Indonesia")
    st.write("Tanyakan harga saham (kode) pada tanggal tertentu. Misalnya: “Harga BBCA pada 2025-09-01”")

    # Ambil API key dari secrets atau input manual
    gemini_key = st.text_input("Masukkan Gemini API Key", type="password")
    if not gemini_key:
        st.warning("Masukkan Gemini API key terlebih dahulu")
        return
    setup_gemini(gemini_key)

    # Inisialisasi session state untuk chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []  # list of dicts: {"role": "user/assistant", "content": str}

    # Tampilkan riwayat chat
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Tulis pertanyaan tentang saham Indonesia …")
    if prompt:
        # Simpan pertanyaan user
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Logic sederhana: jika prompt mengandung pattern `Harga <symbol> pada <date>`
        # parse prompt
        symbol = None
        tanggal = None
        import re
        m = re.search(r"Harga\s+([A-Za-z0-9]+)\s+pada\s+(\d{4}-\d{2}-\d{2})", prompt, re.IGNORECASE)
        if m:
            symbol = m.group(1).upper()
            tanggal = m.group(2)
        else:
            # fallback: panggil Gemini langsung
            reply = ask_gemini(prompt, messages=[m["content"] for m in st.session_state.chat_history])
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
            return

        # Jika symbol & tanggal didapat, ambil data saham
        df = get_stock_history(symbol, tanggal, tanggal)
        if df.empty:
            reply = f"Maaf, saya tidak menemukan data untuk saham `{symbol}` pada tanggal `{tanggal}`."
        else:
            row = df.iloc[0]
            # Buat ringkasan teks
            reply = (
                f"Harga saham **{symbol}** pada **{tanggal}**:\n"
                f"- Open: {row['open']:.2f}\n"
                f"- High: {row['high']:.2f}\n"
                f"- Low: {row['low']:.2f}\n"
                f"- Close: {row['close']:.2f}\n"
                f"- Volume: {row['volume']}\n"
            )
        # Gunakan Gemini untuk memperkaya jawaban (opsional)
        # Misalnya prompt internal: "Anda adalah analis, interpretasikan data berikut: {reply}"
        gemini_prompt = f"Interpretasikan data saham berikut sebagai analis: \n{reply}"
        enriched = ask_gemini(gemini_prompt, messages=[m["content"] for m in st.session_state.chat_history])
        full_reply = reply + "\n\n" + enriched

        # Tampilkan jawaban
        st.session_state.chat_history.append({"role": "assistant", "content": full_reply})
        with st.chat_message("assistant"):
            st.markdown(full_reply)

if __name__ == "__main__":
    main()
