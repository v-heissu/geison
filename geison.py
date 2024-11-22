import streamlit as st
import json
import pandas as pd
from io import BytesIO
import re

def ensure_json_format(text: str) -> str:
    """
    Assicura che il testo sia in formato JSON valido
    """
    # Rimuove BOM e whitespace
    text = text.strip().lstrip('\ufeff')
    
    # Rimuove caratteri non JSON all'inizio
    text = re.sub(r'^[^{\[]+', '', text)
    
    # Rimuove caratteri non JSON alla fine
    text = re.sub(r'[^}\]]+$', '', text)
    
    # Fix citazioni proprietà
    def fix_property_quotes(match):
        return f'"{match.group(1)}":'
    
    # Trova proprietà non quotate o con quote singole e le corregge
    text = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', fix_property_quotes, text)
    text = re.sub(r"'([^']+)'\s*:", fix_property_quotes, text)
    
    # Sostituisce citazioni multiple con singole
    text = re.sub(r'"{2,}', '"', text)
    text = re.sub(r"'{2,}", "'", text)
    
    # Converte citazioni singole in doppie per i valori
    text = re.sub(r":\s*'([^']*)'", r': "\1"', text)
    
    # Corregge valori speciali
    text = re.sub(r':\s*null\b', ': null', text, flags=re.IGNORECASE)
    text = re.sub(r':\s*true\b', ': true', text, flags=re.IGNORECASE)
    text = re.sub(r':\s*false\b', ': false', text, flags=re.IGNORECASE)
    
    return text

def smart_json_loads(text: str) -> dict:
    """
    Tenta di caricare il JSON in modo intelligente, provando diverse correzioni
    """
    text = ensure_json_format(text)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Se fallisce, prova a correggere ulteriormente
        st.error(f"Errore nel parsing iniziale: {str(e)}")
        st.write("Tentativo di correzione automatica...")
        
        # Rimuove virgole trailing
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Aggiunge virgolette mancanti intorno ai valori
        text = re.sub(r':\s*([a-zA-Z][a-zA-Z0-9_]*)\s*([,}])', r': "\1"\2', text)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Impossibile correggere il JSON: {str(e)}\n\nJSON pulito:\n{text}")

def flatten_json(obj, parent_key='', sep='_'):
    """
    Appiattisce un oggetto JSON in un dizionario singolo livello
    """
    items = {}
    
    def _flatten(obj, parent_key='', sep='_'):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, (dict, list)):
                    _flatten(v, new_key, sep=sep)
                else:
                    items[new_key] = v
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                if isinstance(v, (dict, list)):
                    _flatten(v, new_key, sep=sep)
                else:
                    items[new_key] = v
        else:
            items[parent_key] = obj
    
    _flatten(obj, parent_key, sep)
    return items

def main():
    st.title("Convertitore JSON Super")
    
    with st.expander("ℹ️ Informazioni"):
        st.markdown("""
        Questa versione gestisce automaticamente:
        - Proprietà senza virgolette
        - Mix di citazioni singole e doppie
        - JSON malformattato
        - Valori non standard
        """)
    
    json_input = st.text_area("Incolla qui il tuo JSON:", height=200)
    
    if st.button("Converti"):
        if json_input:
            try:
                # Step 1: Pulisci e normalizza
                cleaned_json = ensure_json_format(json_input)
                
                # Debug view
                with st.expander("🔍 JSON Normalizzato"):
                    st.code(cleaned_json)
                
                # Step 2: Parse
                data = smart_json_loads(cleaned_json)
                
                # Step 3: Flatten e converti
                if isinstance(data, list):
                    flat_data = [flatten_json(item) for item in data]
                else:
                    flat_data = [flatten_json(data)]
                
                df = pd.DataFrame(flat_data)
                
                # Step 4: Output
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
                with st.expander("📊 Dettagli"):
                    st.write("Struttura dei dati:")
                    for col in df.columns:
                        st.write(f"- {col}: {df[col].dtype}")
                
            except Exception as e:
                st.error(f"Errore: {str(e)}")
                st.code(cleaned_json[:1000] if 'cleaned_json' in locals() else json_input[:1000])

if __name__ == "__main__":
    main()
