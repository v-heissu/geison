import streamlit as st
import json
import pandas as pd
from io import BytesIO
import re

def fix_quotes(text: str) -> str:
    """
    Corregge i problemi di citazione nel JSON
    """
    # Rimuove BOM e whitespace
    text = text.strip().lstrip('\ufeff')
    
    # Fix per citazioni multiple
    text = re.sub(r'"{2,}', '"', text)  # Sostituisce citazioni multiple con singole
    text = re.sub(r"'{2,}", "'", text)  # Sostituisce apostrofi multipli con singoli
    
    # Gestisce il caso di citazioni alternate
    text = re.sub(r'"([^"]*)"([^"]*)"', r'"\1\\"\2"', text)
    
    # Rimuove caratteri non-JSON all'inizio
    text = re.sub(r'^[^{\[]+', '', text)
    
    # Rimuove caratteri non-JSON alla fine
    text = re.sub(r'[^}\]]+$', '', text)
    
    return text

def normalize_json(text: str) -> str:
    """
    Normalizza il JSON rimuovendo problemi comuni
    """
    # Rimuove caratteri di controllo
    text = ''.join(ch for ch in text if ch >= ' ')
    
    # Corregge le citazioni
    text = fix_quotes(text)
    
    # Corregge i valori null/None
    text = re.sub(r':\s*null\b', ': null', text, flags=re.IGNORECASE)
    text = re.sub(r':\s*none\b', ': null', text, flags=re.IGNORECASE)
    
    # Corregge i booleani
    text = re.sub(r':\s*true\b', ': true', text, flags=re.IGNORECASE)
    text = re.sub(r':\s*false\b', ': false', text, flags=re.IGNORECASE)
    
    return text

def flatten_json(obj, parent_key='', sep='_'):
    """
    Appiattisce un oggetto JSON in un dizionario singolo livello
    """
    items = {}
    
    def add_item(key, value):
        """Aggiunge un item al dizionario risultante"""
        if isinstance(value, (dict, list)):
            items.update(flatten_json(value, key, sep))
        else:
            items[key] = value
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            add_item(new_key, value)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            add_item(new_key, value)
    else:
        items[parent_key] = obj
        
    return items

def main():
    st.title("Convertitore JSON Ultra")
    
    with st.expander("ℹ️ Informazioni"):
        st.markdown("""
        Questo convertitore gestisce:
        - Problemi di citazione
        - JSON malformattato
        - Strutture annidate
        - Caratteri speciali
        """)
    
    # Area di testo per il JSON
    json_input = st.text_area("Incolla qui il tuo JSON:", height=200)
    
    if st.button("Converti"):
        if json_input:
            try:
                # Normalizza e pulisci il JSON
                cleaned_json = normalize_json(json_input)
                
                # Debug view del JSON pulito
                with st.expander("🔍 JSON Pulito"):
                    st.code(cleaned_json)
                
                # Parse del JSON
                try:
                    data = json.loads(cleaned_json)
                except Exception as e:
                    st.error(f"Errore nel parsing JSON pulito: {str(e)}")
                    st.stop()
                
                # Converti in DataFrame
                if isinstance(data, list):
                    flat_data = [flatten_json(item) for item in data]
                else:
                    flat_data = [flatten_json(data)]
                
                df = pd.DataFrame(flat_data)
                
                # Mostra preview
                st.write("Anteprima della tabella:")
                st.dataframe(df)
                
                # Download buttons
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
                with st.expander("📊 Statistiche"):
                    st.write(f"Righe: {len(df)}")
                    st.write(f"Colonne: {len(df.columns)}")
                    st.write("Tipi di dati:", df.dtypes.to_dict())
                
            except Exception as e:
                st.error(f"Errore: {str(e)}")
                st.code(json_input[:500])

if __name__ == "__main__":
    main()
