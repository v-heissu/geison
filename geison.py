import streamlit as st
import json
import pandas as pd
from io import BytesIO
import re
from typing import List, Dict, Union

def flatten_json_object(obj: dict, parent_key: str = '', sep: str = '_') -> dict:
    """
    Appiattisce un oggetto JSON mantenendo una struttura pulita dei nomi delle colonne
    """
    items = {}
    
    def _clean_key(k: str) -> str:
        """Pulisce e normalizza i nomi delle chiavi"""
        k = k.strip('_')
        k = re.sub(r'[@\s]+', '_', k)
        return k.lower()
    
    for k, v in obj.items():
        clean_k = _clean_key(k)
        new_key = f"{parent_key}{sep}{clean_k}" if parent_key else clean_k
        
        if isinstance(v, dict):
            # Per address e altri oggetti annidati conosciuti, mantieni la struttura piatta
            if k in ['address', 'geo']:
                for sub_k, sub_v in v.items():
                    sub_clean_k = _clean_key(sub_k)
                    items[sub_clean_k] = sub_v
            else:
                items.update(flatten_json_object(v, new_key, sep=sep))
        elif isinstance(v, list):
            # Per liste, converti in stringa se sono dati semplici
            if v and all(isinstance(x, (str, int, float)) for x in v):
                items[new_key] = ', '.join(str(x) for x in v)
            else:
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.update(flatten_json_object(item, f"{new_key}{sep}{i}", sep=sep))
        else:
            items[new_key] = v
            
    return items

def process_json_data(json_str: str) -> pd.DataFrame:
    """
    Processa il JSON e lo converte in DataFrame
    """
    data = json.loads(json_str)
    
    # Gestisci diversi formati di input
    if isinstance(data, dict):
        if "items" in data:  # Formato con items e pagination
            items = data["items"]
        elif "liveBlogUpdate" in data:  # Formato liveblog
            items = data["liveBlogUpdate"]
        else:
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("Formato JSON non supportato")
    
    # Appiattisci ogni oggetto
    flattened_data = [flatten_json_object(item) for item in items]
    
    # Crea DataFrame
    df = pd.DataFrame(flattened_data)
    
    # Pulisci i dati
    for col in df.columns:
        if df[col].dtype == object:
            # Decodifica HTML entities
            df[col] = df[col].apply(lambda x: x.replace('&apos;', "'").replace('&quot;', '"') if isinstance(x, str) else x)
    
    # Riordina le colonne in modo logico
    priority_columns = ['name', 'postalcode', 'addresslocality', 'streetaddress', 
                       'addressregion', 'addresscountry', 'province', 'headline', 
                       'articlebody', 'datepublished']
    
    # Ottieni tutte le colonne presenti
    current_cols = list(df.columns)
    # Ordina prima le colonne prioritarie (se presenti)
    ordered_cols = [col for col in priority_columns if col in current_cols]
    # Aggiungi le colonne rimanenti
    ordered_cols.extend([col for col in current_cols if col not in ordered_cols])
    
    return df[ordered_cols]

def main():
    st.title("Convertitore JSON Universal Plus")
    
    with st.expander("ℹ️ Informazioni"):
        st.markdown("""
        Questo convertitore gestisce automaticamente:
        - JSON con strutture annidate (address, geo, etc.)
        - LiveBlog updates
        - Array di oggetti
        - Decodifica HTML entities
        """)
    
    json_input = st.text_area("Incolla qui il tuo JSON:", height=200)
    
    if st.button("Converti"):
        if json_input:
            try:
                # Processa il JSON
                df = process_json_data(json_input)
                
                # Mostra preview
                st.write("Anteprima della tabella:")
                st.dataframe(df)
                
                # Download options
                col1, col2 = st.columns(2)
                
                # CSV
                csv = df.to_csv(index=False)
                col1.download_button(
                    "📄 Scarica CSV",
                    data=csv,
                    file_name="dati.csv",
                    mime="text/csv"
                )
                
                # Excel
                try:
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    col2.download_button(
                        "📊 Scarica Excel",
                        data=buffer.getvalue(),
                        file_name="dati.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                except Exception:
                    st.warning("Export Excel non disponibile. Usa il CSV.")
                
                # Statistiche
                with st.expander("📊 Dettagli"):
                    st.write(f"Righe trovate: {len(df)}")
                    st.write(f"Colonne: {', '.join(df.columns)}")
                
            except Exception as e:
                st.error(f"Errore nell'elaborazione: {str(e)}")
                st.code(json_input[:1000])

if __name__ == "__main__":
    main()
