import streamlit as st
import json
import pandas as pd
from io import BytesIO
from typing import Union, List, Dict
import re

def deep_clean_json(json_str: str) -> str:
    """
    Pulizia approfondita del JSON per gestire casi problematici
    """
    # Rimuove BOM e whitespace
    json_str = json_str.strip().lstrip('\ufeff')
    
    # Cerca di trovare il primo oggetto JSON valido
    try:
        # Cerca l'inizio dell'oggetto o array JSON
        start_curly = json_str.find('{')
        start_square = json_str.find('[')
        
        # Prendi il primo carattere valido di inizio JSON
        if start_curly == -1 and start_square == -1:
            raise ValueError("Nessun JSON valido trovato")
        
        start = min(x for x in [start_curly, start_square] if x != -1)
        json_str = json_str[start:]
        
        # Conta le parentesi per trovare la fine del JSON
        stack = []
        in_string = False
        escape = False
        end_pos = -1
        
        for i, char in enumerate(json_str):
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
                if char in '{[':
                    stack.append(char)
                elif char in '}]':
                    if not stack:
                        break
                    opening = stack.pop()
                    if (opening == '{' and char != '}') or (opening == '[' and char != ']'):
                        break
                    if not stack:  # Abbiamo trovato la fine del JSON
                        end_pos = i + 1
                        break
        
        if end_pos != -1:
            json_str = json_str[:end_pos]
        
        # Verifica che sia un JSON valido
        json.loads(json_str)
        
        return json_str
    
    except Exception as e:
        st.error(f"Errore durante la pulizia del JSON: {str(e)}")
        return json_str

def flatten_dict(d: Union[Dict, List], parent_key: str = '', sep: str = '_') -> Dict:
    """
    Appiattisce un dizionario o una lista annidata in un dizionario piatto.
    """
    items = []
    
    if isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, (dict, list)):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
                
    elif isinstance(d, list):
        for i, v in enumerate(d):
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            
            if isinstance(v, (dict, list)):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
    else:
        items.append((parent_key, d))
        
    return dict(items)

def smart_flatten(data: Union[Dict, List]) -> pd.DataFrame:
    """
    Converte intelligentemente i dati in un DataFrame
    """
    # Se è una lista di dizionari, prova la conversione diretta
    if isinstance(data, list) and all(isinstance(x, dict) for x in data):
        try:
            return pd.DataFrame(data)
        except:
            pass
    
    # Se è un dizionario con una lista di dizionari
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list) and all(isinstance(x, dict) for x in value):
                try:
                    return pd.DataFrame(value)
                except:
                    continue
    
    # Appiattimento completo come fallback
    flattened = flatten_dict(data)
    return pd.DataFrame([flattened])

def main():
    st.title("Convertitore JSON Universale")
    
    with st.expander("ℹ️ Guida all'uso"):
        st.markdown("""
        1. **Incolla il tuo JSON** nel campo di testo
        2. Il convertitore:
           - Pulirà automaticamente il JSON
           - Troverà la struttura più adatta
           - Creerà una tabella dei dati
        3. **Scarica** i risultati in CSV o Excel
        """)
    
    # Area di testo per il JSON
    json_input = st.text_area("Incolla qui il tuo JSON:", height=200)
    
    if st.button("Converti"):
        if json_input:
            try:
                # Pulizia approfondita del JSON
                cleaned_json = deep_clean_json(json_input)
                
                # Parse del JSON pulito
                data = json.loads(cleaned_json)
                
                # Conversione in DataFrame
                df = smart_flatten(data)
                
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
                except ImportError:
                    st.warning("Export Excel non disponibile. Usa il CSV.")
                
                # Statistiche
                with st.expander("📊 Statistiche"):
                    st.write(f"Righe: {len(df)}")
                    st.write(f"Colonne: {len(df.columns)}")
                    
            except json.JSONDecodeError as e:
                st.error(f"Errore JSON: {str(e)}")
                st.code(cleaned_json[:500] + "..." if len(cleaned_json) > 500 else cleaned_json)
            except Exception as e:
                st.error(f"Errore: {str(e)}")

if __name__ == "__main__":
    main()
