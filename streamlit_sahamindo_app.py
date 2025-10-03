import streamlit as st
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import google.generativeai as genai


# ========== 1. SETUP DATA SAHAM (simulasi) ==========
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


# ========== 2. SETUP GEMINI ==========
def setup_gemini(api_key: str):
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"❌ Gagal mengatur Gemini: {e}")
        return False


def ask_gemini(prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error dari Gemini: {e}"


# ========== 3. PLOT GRAFIK SAHAM ==========
def plot_price_chart(df: pd.DataFrame, symbol: str):
    fig, ax = plt.subplots()
    ax.plot(df["date"], df["close"], marker="o", linestyle="-", label="Close Price")
    ax.set_title(f"Grafik Harga Saham {symbol}")
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Harga Penutupan")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)


# ========== 4. APP STREAMLIT ==========
def main():
    st.set_page_config(page_title="📊 Chatbot Saham Indonesia", layout="wide")
    st.title("📈 Chatbot Saham Indonesia")
    st.markdown("Tanyakan **apa saja** seputar saham. Contoh: `Harga BBCA pada 2025-10-01`, `Apa itu saham?`, `Strategi cuan jangka panjang?`")

    gemini_key = st.text_input("🔐 Masukkan API Key Gemini kamu", type="password")
    if not gemini_key:
        st.info("Masukkan API Key Gemini untuk mulai.")
        return

    if not setup_gemini(gemini_key):
        return

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Tampilkan riwayat obrolan
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input pertanyaan dari user
    prompt = st.chat_input("Tanyakan sesuatu...")

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        match = re.search(r"Harga\s+([A-Za-z0-9]+)\s+pada\s+(\d{4}-\d{2}-\d{2})", prompt, re.IGNORECASE)

        if match:
            # Jika pertanyaan adalah harga saham
            symbol = match.group(1).upper()
            tanggal = match.group(2)

            start_date = pd.to_datetime(tanggal) - pd.Timedelta(days=7)
            end_date = pd.to_datetime(tanggal) + pd.Timedelta(days=7)
            df = get_stock_history(symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

            if df.empty:
                reply = f"❌ Data saham `{symbol}` pada tanggal `{tanggal}` tidak tersedia."
            else:
                row = df[df["date"] == pd.to_datetime(tanggal)]
                if row.empty:
                    reply = f"❌ Tidak ada data persis pada tanggal **{tanggal}** untuk saham {symbol}."
                else:
                    row = row.iloc[0]
                    harga = (
                        f"📊 Harga saham **{symbol}** pada **{tanggal}**:\n"
                        f"- Open: Rp{row['open']:.2f}\n"
                        f"- High: Rp{row['high']:.2f}\n"
                        f"- Low: Rp{row['low']:.2f}\n"
                        f"- Close: Rp{row['close']:.2f}\n"
                        f"- Volume: {row['volume']:,}"
                    )
                    gemini_prompt = f"Analisislah data saham berikut sebagai analis keuangan:\n{harga}"
                    analisis = ask_gemini(gemini_prompt)
                    reply = harga + "\n\n---\n" + analisis

                    with st.expander("📉 Lihat Grafik Harga Saham"):
                        plot_price_chart(df, symbol)
        else:
            # Pertanyaan bebas -> langsung ke Gemini
            reply = ask_gemini(prompt)

        # Tampilkan jawaban
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)


if __name__ == "__main__":
    main()
