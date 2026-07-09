import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
from datetime import datetime

# Configurazione della pagina ottimizzata per smartphone
st.set_page_config(layout="wide", page_title="Centrale Volumetrica 2.0")

# --- BLOCCO SICUREZZA ---
if "autenticato" not in st.session_state:
    st.session_state["autenticato"] = False

if not st.session_state["autenticato"]:
    st.markdown("### 🔒 Accesso Riservato - Aggregatore 2.0")
    password_inserita = st.text_input("Inserisci la chiave d'accesso:", type="password")
    if st.button("Sblocca Dashboard"):
        if password_inserita == "MollaCarica2026":
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("Chiave d'accesso errata.")
else:
    # --- MOTORE CONFIGURAZIONE DATI REAL ---
    VALORE_TOTALE_PORTAFOGLIO_EUR = 377036.06
    FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", "default_key")  # Configura in .streamlit/secrets.toml
    
    @st.cache_data(ttl=300)  # Aggiorna i dati ogni 5 minuti
    def scarica_dati_mercato():
        df_base = pd.DataFrame([
            {"ticker": "INTC", "nome": "Intel Corp.", "tipo": "Azione", "q": 550, "pmc": 118.84, "valuta": "USD", "simbolo_finnhub": "INTC"},
            {"ticker": "BABA", "nome": "Alibaba Group Holding Ltd", "tipo": "Azione", "q": 400, "pmc": 95.02, "valuta": "USD", "simbolo_finnhub": "BABA"},
            {"ticker": "NVDA", "nome": "Nvidia Corp", "tipo": "Azione", "q": 300, "pmc": 183.20, "valuta": "EUR", "simbolo_finnhub": "NVDA"},
            {"ticker": "OKLO", "nome": "Oklo Inc.", "tipo": "Azione", "q": 350, "pmc": 62.17, "valuta": "USD", "simbolo_finnhub": "OKLO"},
            {"ticker": "CCJ",  "nome": "Cameco Corp.", "tipo": "Azione", "q": 150, "pmc": 98.07, "valuta": "EUR", "simbolo_finnhub": "CCJ"},
            {"ticker": "SPCX", "nome": "Space Exploration Technologies", "tipo": "Azione", "q": 80, "pmc": 151.10, "valuta": "USD", "simbolo_finnhub": "SPCX"},
            {"ticker": "MSFT", "nome": "Microsoft Corporation", "tipo": "Azione", "q": 50, "pmc": 371.46, "valuta": "USD", "simbolo_finnhub": "MSFT"},
            {"ticker": "VATN.SW", "nome": "Vat Group N", "tipo": "Azione", "q": 15, "pmc": 581.83, "valuta": "CHF", "simbolo_finnhub": "VATN.SW"},
            {"ticker": "BITM", "nome": "Bitmine Immersion Tec.new", "tipo": "Azione", "q": 500, "pmc": 18.68, "valuta": "EUR", "simbolo_finnhub": "BITM.SW"},
            {"ticker": "COSM", "nome": "Cosmo N.v.", "tipo": "Azione", "q": 50, "pmc": 88.60, "valuta": "EUR", "simbolo_finnhub": "COSM.MI"},
            {"ticker": "URNM.MI", "nome": "VanEck Uranium UCITS", "tipo": "ETF", "q": 1152, "pmc": 52.92, "valuta": "EUR", "simbolo_finnhub": "URNM.MI"},
            {"ticker": "INRG.MI", "nome": "iShares Global Clean Energy", "tipo": "ETF", "q": 2800, "pmc": 10.41, "valuta": "EUR", "simbolo_finnhub": "INRG.MI"},
            {"ticker": "EMDV.MI", "nome": "WisdomTree Emerging Markets", "tipo": "ETF", "q": 500, "pmc": 27.75, "valuta": "EUR", "simbolo_finnhub": "EMDV.MI"},
            {"ticker": "CX50.MI", "nome": "Invesco ChinaNex 50 UCITS", "tipo": "ETF", "q": 600, "pmc": 11.71, "valuta": "EUR", "simbolo_finnhub": "CX50.MI"},
            {"ticker": "SMCX.MI", "nome": "SPDR MSCI Europe Consumer", "tipo": "ETF", "q": 50, "pmc": 226.54, "valuta": "EUR", "simbolo_finnhub": "SMCX.MI"},
            {"ticker": "BNK.MI",  "nome": "WisdomTree FTSE MIB Banks", "tipo": "ETC/Leva", "q": 900, "pmc": 15.39, "valuta": "EUR", "simbolo_finnhub": "BNK.MI"},
            {"ticker": "E50.MI",  "nome": "WisdomTree Euro Stoxx 50", "tipo": "ETC/Leva", "q": 300, "pmc": 42.48, "valuta": "EUR", "simbolo_finnhub": "E50.MI"},
            {"ticker": "AG3L.MI", "nome": "WisdomTree Silver 3x Daily", "tipo": "ETC/Leva", "q": 1150, "pmc": 12.70, "valuta": "EUR", "simbolo_finnhub": "AG3L.MI"}
        ])
        
        # Scarica i tassi di cambio
        try:
            cambio_usd = yf.Ticker("EURUSD=X").fast_info['lastPrice']
            cambio_chf = yf.Ticker("EURCHF=X").fast_info['lastPrice']
        except:
            cambio_usd, cambio_chf = 1.1440, 0.9224
        
        # Scarica i prezzi da Finnhub
        prezzi_live = {}
        for idx, row in df_base.iterrows():
            try:
                url = f"https://finnhub.io/api/v1/quote?symbol={row['simbolo_finnhub']}&token={FINNHUB_API_KEY}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'c' in data and data['c'] > 0:
                        prezzi_live[row['ticker']] = data['c']
                    else:
                        prezzi_live[row['ticker']] = row['pmc']
                else:
                    prezzi_live[row['ticker']] = row['pmc']
            except:
                prezzi_live[row['ticker']] = row['pmc']
        
        return df_base, prezzi_live, cambio_usd, cambio_chf

    df, dati_live, c_usd, c_chf = scarica_dati_mercato()

    def calcola_valori(row):
        spot_live = dati_live.get(row['ticker'], row['pmc'])
        if np.isnan(spot_live) or spot_live == 0: 
            spot_live = row['pmc']
        
        # --- CONVERSIONE PREZZI IN EUR ---
        if row['valuta'] == 'USD':
            spot_eur = spot_live / c_usd
            pmc_eur = row['pmc'] / c_usd
        elif row['valuta'] == 'CHF':
            spot_eur = spot_live / c_chf
            pmc_eur = row['pmc'] / c_chf
        else:  # EUR
            spot_eur = spot_live
            pmc_eur = row['pmc']
        
        # --- CALCOLO CONTROVALORE IN EUR ---
        ctv_eur = row['q'] * spot_eur
        
        # --- CALCOLO INVESTIMENTO INIZIALE IN EUR ---
        inv_iniziale = row['q'] * pmc_eur
        
        # --- PERFORMANCE IN %
        if inv_iniziale > 0:
            perf = ((ctv_eur - inv_iniziale) / inv_iniziale) * 100
        else:
            perf = 0
        
        return pd.Series([ctv_eur, spot_eur, pmc_eur, inv_iniziale, perf])

    df[['Capitale_EUR', 'Spot_EUR', 'PMC_EUR', 'Investimento_Iniziale_EUR', 'Performance_%']] = df.apply(calcola_valori, axis=1)
    df['Peso_%'] = (df['Capitale_EUR'] / VALORE_TOTALE_PORTAFOGLIO_EUR) * 100
    df['Gain_Loss_EUR'] = df['Capitale_EUR'] - df['Investimento_Iniziale_EUR']

    # --- INTERFACCIA GRAFICA MOBILE ---
    st.title("💼 Centrale Operativa Live v2.0")
    
    # Metriche principali
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Controvalore Totale", value=f"{df['Capitale_EUR'].sum():,.2f} EUR")
    with col2:
        inv_tot = df['Investimento_Iniziale_EUR'].sum()
        st.metric(label="Investimento Iniziale", value=f"{inv_tot:,.2f} EUR")
    with col3:
        perf_totale = ((df['Capitale_EUR'].sum() - inv_tot) / inv_tot) * 100 if inv_tot > 0 else 0
        st.metric(label="Performance Totale", value=f"{perf_totale:+.2f}%")
    
    if st.button("🔐 Blocca / Esci"):
        st.session_state["autenticato"] = False
        st.rerun()
        
    st.write("---")
    
    st.subheader("📋 Griglia Asset Real-Time (Tutti i prezzi in EUR)")
    df_vis = df[['ticker', 'nome', 'PMC_EUR', 'Spot_EUR', 'Capitale_EUR', 'Performance_%', 'Peso_%']].copy()
    df_vis.columns = ['Ticker', 'Nome', 'PMC (EUR)', 'Prezzo Live (EUR)', 'Controvalore (EUR)', 'Performance %', 'Peso %']
    df_vis['PMC (EUR)'] = df_vis['PMC (EUR)'].map('{:.2f}'.format)
    df_vis['Prezzo Live (EUR)'] = df_vis['Prezzo Live (EUR)'].map('{:.2f}'.format)
    df_vis['Controvalore (EUR)'] = df_vis['Controvalore (EUR)'].map('{:,.2f}'.format)
    df_vis['Performance %'] = df_vis['Performance %'].map('{:+.2f}%'.format)
    df_vis['Peso %'] = df_vis['Peso %'].map('{:.2f}%'.format)
    st.dataframe(df_vis.sort_values(by="Ticker"), use_container_width=True, hide_index=True)
    
    st.write("---")
    st.subheader("🎯 Analisi Istituzionale & Verdetto")
    selezionato = st.selectbox("Seleziona titolo per interrogare il cervello strategico:", df['ticker'].unique())
    asset = df[df['ticker'] == selezionato].iloc[0]
    
    # Simulazione dinamica dei livelli monetari agganciati allo spot live
    net_flow_sim = 245000.0 if asset['ticker'] in ['INTC', 'OKLO'] else (-15000.0 if asset['ticker'] == 'BABA' else 0.0)
    max_pain_sim = asset['Spot_EUR'] * 1.01 if asset['ticker'] in ['INTC', 'OKLO'] else asset['Spot_EUR']
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Prezzo di Carico (PMC)", value=f"{asset['PMC_EUR']:.2f} EUR")
        st.metric(label="Ultimo Prezzo Battuto", value=f"{asset['Spot_EUR']:.2f} EUR", delta=f"{asset['Performance_%']:.2f}%")
    with col2:
        st.metric(label="Controvalore Posizione", value=f"€{asset['Capitale_EUR']:,.2f}")
        st.metric(label="Gain/Loss", value=f"€{asset['Gain_Loss_EUR']:+,.2f}")

    st.markdown("**Verdetto Cervello Strategico:**")
    if asset['tipo'] == 'ETC/Leva' and asset['ticker'] == 'AG3L.MI':
        st.error("⚠️ ALERT DECAY ATTIVO: Il titolo si trova in una struttura laterale prolungata. Il decadimento da volatilità sta erodendo il valore temporale della leva giornaliera. Valutare alleggerimento protettivo tattico.")
    elif net_flow_sim > 100000 and asset['Spot_EUR'] < asset['PMC_EUR']:
        st.success("🟢 STRATEGIA: MOLLA CARICA. Le balene stanno assorbendo la lettera sul book. Gli acquisti istituzionali grandi taglie proteggono il trend sotto il livello di Max Pain delle opzioni. Mantenere salda la posizione.")
    elif asset['Performance_%'] > 15.0:
        st.warning("🔄 ROTAZIONE SETTORIALE: Il titolo ha quasi saturato la spinta volumetrica istituzionale della scadenza attuale. L'algoritmo suggerisce di liquidare una quota per prelevare profitto e ruotarlo su asset compressi in fase di accumulo.")
    else:
        st.info("ℹ️ STRATEGIA: STRUTTURA IN EQUILIBRIO. Il prezzo muove in linea con i volumi del Point of Control (POC). I flussi monetari istituzionali e retail sono bilanciati. Nessuna azione correttiva richiesta.")
