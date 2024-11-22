import streamlit as st
import json
import pandas as pd
from io import BytesIO
from typing import Union, List, Dict
import re

def flatten_dict(d: Union[Dict, List], parent_key: str = '', sep: str = '_') -> Dict:
    """
    Appiattisce un dizionario o una lista annidata in un dizionario piatto.
    Gestisce liste, dizionari annidati e valori semplici.
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
    Converte intelligentemente i dati in un DataFrame, 
    cercando di mantenere la struttura più logica possibile.
    """
    # Se è una lista di dizionari, prova prima la conversione diretta
    if isinstance(data, list) and all(isinstance(x, dict) for x in data):
        try:
            return pd.DataFrame(data)
        except:
            pass
    
    # Se è un dizionario con una chiave che contiene una lista di dizionari
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list) and all(isinstance(x, dict) for x in value):
                try:
                    return pd.DataFrame(value)
                except:
                    continue
    
    # Se i metodi precedenti falliscono, appiattisci completamente
    flattened = flatten_dict(data)
    return pd.DataFrame([flattened])

def clean_json(json_str: str) -> str:
    """Pulisce il JSON da potenziali problemi comuni"""
    # Rimuove BOM se presente
    json_str = json_str.strip().lstrip('\ufeff')
    
    # Gestisce le citazioni singole
    json_str = re.sub(r"(?<!\\)'", '"', json_str)
    
    # Gestisce i caratteri di escape
    json_str = json_str.replace('\n', ' ').replace('\r', ' ')
    
    return json_str

def main():
    st.title("Convertitore JSON Universale")
    
    with st.expander("ℹ️ Informazioni sul convertitore"):
        st.markdown("""
        Questo convertitore può gestire:
        - JSON semplici e complessi
        - Liste di oggetti
        - Oggetti annidati
        - Strutture miste
        
        Prova ad estrarre automaticamente la struttura tabellare più logica dai dati.
        """)
    
    # Area di testo per incollare il JSON
    json_input = st.text_area("Incolla qui il tuo JSON:", height=200)
    
    cols = st.columns(2)
    convert_button = cols[0].button("Converti")
    
    if convert_button and json_input:
        try:
            # Pulisci e analizza il JSON
            cleaned_json = clean_json(json_input)
            data = json.loads(cleaned_json)
            
            # Converti in DataFrame
            df = smart_flatten(data)
            
            # Mostra anteprima
            st.write("Anteprima della tabella:")
            st.dataframe(df)
            
            # Bottoni per il download
            col1, col2 = st.columns(2)
            
            # Download CSV
            csv = df.to_csv(index=False)
            col1.download_button(
                label="📄 Scarica CSV",
                data=csv,
                file_name="dati_convertiti.csv",
                mime="text/csv"
            )
            
            # Download Excel
            try:
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                col2.download_button(
                    label="📊 Scarica Excel",
                    data=buffer.getvalue(),
                    file_name="dati_convertiti.xlsx",
                    mime="application/vnd.ms-excel"
                )
            except Exception as e:
                st.warning("Export Excel non disponibile. Usa il formato CSV.")
            
            # Mostra statistiche
            with st.expander("📊 Statistiche dei dati"):
                st.write(f"Numero di righe: {len(df)}")
                st.write(f"Numero di colonne: {len(df.columns)}")
                st.write("Colonne trovate:", list(df.columns))
        
        except json.JSONDecodeError as e:
            st.error(f"Errore nella decodifica del JSON: {str(e)}")
            st.info("Suggerimento: Verifica che il JSON sia valido e ben formattato")
        except Exception as e:
            st.error(f"Errore durante la conversione: {str(e)}")
            st.info("Prova a verificare la struttura del tuo JSON")

if __name__ == "__main__":
    main()
