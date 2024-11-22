import streamlit as st
import json
import pandas as pd
from io import BytesIO
from typing import Union, List, Dict
import re

def flatten_complete(obj: Union[Dict, List, str], parent_key: str = '', sep: str = '_') -> Dict:
    """
    Appiattisce completamente qualsiasi struttura JSON, inclusi i JSON nidificati nelle stringhe
    """
    items = {}
    
    def try_parse_json(value):
        """Prova a parsare una stringa come JSON"""
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

def clean_column_name(name: str) -> str:
    """Pulisce e semplifica i nomi delle colonne"""
    # Rimuove caratteri speciali e spazi
    name = re.sub(r'[^\w\s-]', '', str(name))
    # Sostituisce spazi con underscore
    name = re.sub(r'[-\s]+', '_', name)
    # Rimuove underscore multipli
    name = re.sub(r'_+', '_', name)
    return name.lower().strip('_')

def create_dataframe(data: Union[Dict, List]) -> pd.DataFrame:
    """
    Crea un DataFrame appiattito da qualsiasi struttura JSON
    """
    if isinstance(data, list):
        # Se è una lista di oggetti, appiattisci ogni elemento
        flat_data = [flatten_complete(item) for item in data]
    else:
        # Se è un oggetto singolo, appiattiscilo
        flat_data = [flatten_complete(data)]
    
    # Crea il DataFrame
    df = pd.DataFrame(flat_data)
    
    # Pulisci i nomi delle colonne
    df.columns = [clean_column_name(col) for col in df.columns]
    
    return df

def main():
    st.title("Convertitore JSON Avanzato")
    
    with st.expander("ℹ️ Informazioni"):
        st.markdown("""
        Questo convertitore:
        - Appiattisce completamente qualsiasi struttura JSON
        - Gestisce JSON nidificati in stringhe
        - Pulisce e semplifica i nomi delle colonne
        - Esporta in CSV o Excel
        """)
    
    json_input = st.text_area("Incolla qui il tuo JSON:", height=200)
    
    if st.button("Converti"):
        if json_input:
            try:
                # Parse del JSON
                data = json.loads(json_input)
                
                # Creazione DataFrame completamente appiattito
                df = create_dataframe(data)
                
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
                    file_name="dati_appiattiti.csv",
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
                        file_name="dati_appiattiti.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                except ImportError:
                    st.warning("Export Excel non disponibile. Usa il CSV.")
                
                # Statistiche
                with st.expander("📊 Dettagli"):
                    st.write("Struttura dei dati:")
                    for col in df.columns:
                        st.write(f"- {col}: {df[col].dtype}")
                    
            except json.JSONDecodeError as e:
                st.error(f"Errore nel parsing JSON: {str(e)}")
                st.info("Verifica che il JSON sia valido")
            except Exception as e:
                st.error(f"Errore: {str(e)}")

if __name__ == "__main__":
    main()
