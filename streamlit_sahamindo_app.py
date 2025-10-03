import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_idx_ringkasan():
    url = "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-saham"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return pd.DataFrame()
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    rows = []
    for tr in table.find_all("tr")[1:]:
        cols = tr.find_all("td")
        if not cols:
            continue
        row = [td.get_text(strip=True) for td in cols]
        rows.append(row)
    df = pd.DataFrame(rows, columns=headers)
    return df

def main():
    st.title("Ringkasan Saham IDX")
    df = fetch_idx_ringkasan()
    if df.empty:
        st.error("Gagal mengambil data dari IDX")
    else:
        st.dataframe(df)

if __name__ == "__main__":
    main()
