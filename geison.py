import streamlit as st
import json
import pandas as pd
from io import BytesIO
import re

def extract_objects_from_text(text: str) -> str:
    """
    Estrae e formatta correttamente oggetti JSON da testo malformattato
    """
    # Rimuove spazi e caratteri iniziali/finali
    text = text.strip().lstrip('\ufeff')
    
    # Se il testo inizia con '[', cerca di sistemare l'array
    if text.startswith('['):
        try:
            # Trova tutti gli oggetti che iniziano con {@type
            objects = re.finditer(r'{"@type":[^}]+}', text)
            valid_objects = []
            
            for obj in objects:
                try:
                    # Pulisci l'oggetto
                    clean_obj = obj.group()
                    # Verifica che sia un JSON valido
                    json.loads(clean_obj)
                    valid_objects.append(clean_obj)
                except:
                    continue
            
            if valid_objects:
                return f"[{','.join(valid_objects)}]"
        except:
            pass
    
    # Trova tutti i pattern che sembrano oggetti JSON
    object_pattern = r'{[^}]+}'
    potential_objects = re.finditer(object_pattern, text)
    
    valid_objects = []
    for obj in potential_objects:
        try:
            # Pulisci l'oggetto
            clean_obj = obj.group()
            # Sistema le citazioni
            clean_obj = re.sub(r'([{,]\s*)([a-zA-Z@_][a-zA-Z0-9@_]*)\s*:', r'\1"\2":', clean_obj)
            # Sostituisci citazioni singole con doppie
            clean_obj = clean_obj.replace("'", '"')
            # Verifica che sia un JSON valido
            json.loads(clean_obj)
            valid_objects.append(clean_obj)
        except:
            continue
    
    if valid_objects:
        return f"[{','.join(valid_objects)}]"
    
    raise ValueError("Nessun oggetto JSON valido trovato nel testo")

def clean_json_text(text: str) -> str:
    """
    Pulisce e normalizza il testo JSON
    """
    # Sistema le citazioni delle proprietà
    text = re.sub(r'([{,]\s*)([a-zA-Z@_][a-zA-Z0-9@_]*)\s*:', r'\1"\2":', text)
    
    # Sistema le citazioni dei valori
    text = re.sub(r':\s*"([^"]*)"', r':"\1"', text)
    text = re.sub(r':\s*\'([^\']*)\'', r':"\1"', text)
    
    # Sistema i valori speciali
    text = re.sub(r':\s*(null|true|false)\b', lambda m: f':{m.group(1).lower()}', text, flags=re.IGNORECASE)
    
    # Rimuove spazi extra
    text = re.sub(r'\s+', ' ', text)
    
    return text

def parse_json_safely(text: str) -> dict:
    """
    Tenta di parsare il JSON in modo sicuro con multipli tentativi
    """
    try:
        # Prima prova: parse diretto
        return json.loads(text)
    except:
        try:
            # Seconda prova: pulizia e parse
            cleaned = clean_json_text(text)
            return json.loads(cleaned)
        except:
            # Terza prova: estrazione oggetti
            extracted = extract_objects_from_text(text)
            return json.loads(extracted)

def main():
    st.title("Convertitore JSON Pro Max")
    
    with st.expander("ℹ️ Informazioni"):
        st.markdown("""
        Versione avanzata che gestisce:
        - JSON malformattato
        - Array incompleti
        - Oggetti consecutivi
        - Citazioni miste
        - Strutture complesse
        """)
    
    json_input = st.text_area("Incolla qui il tuo JSON:", height=200)
    
    if st.button("Converti"):
        if json_input:
            try:
                # Step 1: Parse sicuro
                data = parse_json_safely(json_input)
                
                # Step 2: Converti in DataFrame
                if isinstance(data, list):
                    df = pd.json_normalize(data)
                else:
                    df = pd.json_normalize([data])
                
                # Mostra anteprima
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
                
                # Debug info
                with st.expander("🔍 Debug Info"):
                    st.write("JSON Structure:")
                    st.json(data)
                    
                    st.write("Column Types:")
                    st.write(df.dtypes.to_dict())
                
            except Exception as e:
                st.error(f"Errore nel processing: {str(e)}")
                st.write("Debug del testo di input:")
                st.code(json_input[:1000])

if __name__ == "__main__":
    main()
