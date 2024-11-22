import streamlit as st
import json
import pandas as pd
from io import BytesIO
from typing import Union, List, Dict
import re

def extract_valid_json(text: str) -> str:
    """
    Estrae il primo JSON valido dal testo, ignorando caratteri non validi
    """
    # Cerca l'inizio di un oggetto o array JSON
    start_patterns = ['{', '[']
    end_patterns = ['}', ']']
    
    # Trova la prima occorrenza di un pattern di inizio valido
    starts = [(text.find(p), p) for p in start_patterns if text.find(p) != -1]
    if not starts:
        raise ValueError("Nessun JSON valido trovato nel testo")
    
    start_pos, start_char = min(starts, key=lambda x: x[0])
    
    # Determina il carattere di chiusura corrispondente
    end_char = end_patterns[start_patterns.index(start_char)]
    
    # Inizializza il contatore per le parentesi
    count = 0
    in_string = False
    escape = False
    
    # Cerca la fine corrispondente
    for i in range(start_pos, len(text)):
        char = text[i]
        
        if escape:
            escape = False
            continue
            
        if char == '\\':
            escape = True
            continue
            
        if char == '"' and not escape:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == start_char:
                count += 1
            elif char == end_char:
                count -= 1
                if count == 0:
                    # Abbiamo trovato la fine del JSON
                    return text[start_pos:i+1]
    
    raise ValueError("JSON non valido o incompleto")

def clean_json_text(text: str) -> str:
    """
    Pulisce il testo del JSON da caratteri problematici
    """
    # Rimuove BOM e whitespace
    text = text.strip().lstrip('\ufeff')
    
    # Rimuove commenti se presenti
    text = re.sub(r'//.*?\n|/\*.*?\*/', '', text, flags=re.S)
    
    # Prova a estrarre il JSON valido
    try:
        return extract_valid_json(text)
    except ValueError as e:
        st.error(f"Errore durante la pulizia del JSON: {str(e)}")
        return text

def flatten_complete(obj: Union[Dict, List, str], parent_key: str = '', sep: str = '_') -> Dict:
    """
    Appiattisce completamente qualsiasi struttura JSON
    """
    items = {}
    
    def try_parse_json(value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return value
        return value
    
    if isinstance(obj, dict):
        for k, v in obj.items():
            v = try_parse_json(v)
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, (dict, list)):
                items.update(flatten_complete(v, new_key, sep=sep))
            else:
                items[new_key] = v
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            v = try_parse_json(v)
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            
            if isinstance(v, (dict, list)):
                items.update(flatten_complete(v, new_key, sep=sep))
            else:
                items[new_key] = v
    else:
        obj = try_parse_json(obj)
        if isinstance(obj, (dict, list)):
            items.update(flatten_complete(obj, parent_key, sep=sep))
        else:
            items[parent_key] = obj
    
    return items

def main():
    st.title("Convertitore JSON Universal Plus")
    
    with st.expander("ℹ️ Come usare"):
        st.markdown("""
        1. Incolla il tuo JSON (anche se contiene errori)
        2. Il sistema:
           - Rimuoverà automaticamente caratteri non validi
           - Estrarrà il primo JSON valido trovato
           - Convertirà tutto in formato tabellare
        3. Scarica i risultati in CSV o Excel
        """)
    
    # Area di testo per il JSON
    json_input = st.text_area("Incolla qui il tuo JSON:", height=200)
    
    if st.button("Converti"):
        if json_input:
            try:
                # Pulizia e estrazione del JSON valido
                cleaned_json = clean_json_text(json_input)
                
                # Parse del JSON pulito
                data = json.loads(cleaned_json)
                
                # Appiattimento e conversione in DataFrame
                if isinstance(data, list):
                    flat_data = [flatten_complete(item) for item in data]
                else:
                    flat_data = [flatten_complete(data)]
                    
                df = pd.DataFrame(flat_data)
                
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
                
                # Mostra JSON pulito in caso di debug
                with st.expander("🔍 Debug"):
                    st.code(cleaned_json)
                
            except json.JSONDecodeError as e:
                st.error(f"Errore nel parsing JSON: {str(e)}")
                st.code(cleaned_json[:500] + "..." if len(cleaned_json) > 500 else cleaned_json)
            except Exception as e:
                st.error(f"Errore: {str(e)}")

if __name__ == "__main__":
    main()
