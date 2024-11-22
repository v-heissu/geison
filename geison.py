import streamlit as st
import json
import pandas as pd
from io import BytesIO
import re
from typing import List, Dict, Union

def clean_json_input(json_str: str) -> str:
    """Pulisce l'input JSON mantenendo tutti i record"""
    json_str = json_str.strip().lstrip('\ufeff')
    
    try:
        json.loads(json_str)
        return json_str
    except:
        try:
            start_idx = json_str.find('{')
            if start_idx == -1:
                return json_str
            
            count = 0
            in_string = False
            escape = False
            last_closing = -1
            
            for i, char in enumerate(json_str[start_idx:]):
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
                    if char == '{':
                        count += 1
                    elif char == '}':
                        count -= 1
                        if count == 0:
                            last_closing = i
            
            if last_closing != -1:
                complete_json = json_str[start_idx:start_idx + last_closing + 1]
                json.loads(complete_json)
                return complete_json
            
        except Exception as e:
            st.error(f"Errore nella pulizia del JSON: {str(e)}")
        
        return json_str

def flatten_json_object(obj: dict, parent_key: str = '', sep: str = '_') -> dict:
    """Appiattisce un oggetto JSON mantenendo una struttura pulita"""
    items = {}
    
    def _clean_key(k: str) -> str:
        k = k.strip('_')
        k = re.sub(r'[@\s]+', '_', k)
        return k.lower()
    
    for k, v in obj.items():
        clean_k = _clean_key(k)
        new_key = f"{parent_key}{sep}{clean_k}" if parent_key else clean_k
        
        if isinstance(v, dict):
            if k in ['address', 'geo']:
                for sub_k, sub_v in v.items():
                    sub_clean_k = _clean_key(sub_k)
                    items[sub_clean_k] = sub_v
            else:
                items.update(flatten_json_object(v, new_key, sep=sep))
        elif isinstance(v, list):
            if v and all(isinstance(x, (str, int, float)) for x in v):
                items[new_key] = ', '.join(str(x) for x in v)
            else:
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        if k == "liveBlogUpdate":
                            flat_item = flatten_json_object(item)
                            for sub_k, sub_v in flat_item.items():
                                items[_clean_key(sub_k)] = sub_v
                        else:
                            items.update(flatten_json_object(item, f"{new_key}{sep}{i}", sep=sep))
        else:
            items[new_key] = v
            
    return items

def process_json_data(json_str: str) -> pd.DataFrame:
    """Processa il JSON e lo converte in DataFrame"""
    cleaned_json = clean_json_input(json_str)
    
    try:
        data = json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        st.error(f"Errore nel parsing JSON: {str(e)}")
        st.code(cleaned_json[:1000])
        raise
    
    if isinstance(data, dict):
        if "items" in data:
            items = data["items"]
        elif "liveBlogUpdate" in data:
            items = data["liveBlogUpdate"]
        else:
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("Formato JSON non supportato")
    
    flattened_data = [flatten_json_object(item) for item in items]
    df = pd.DataFrame(flattened_data)
    
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(lambda x: x.replace('&apos;', "'").replace('&quot;', '"') if isinstance(x, str) else x)
    
    priority_columns = ['name', 'postalcode', 'addresslocality', 'streetaddress', 
                       'addressregion', 'addresscountry', 'province', 'headline', 
                       'articlebody', 'datepublished']
    
    current_cols = list(df.columns)
    ordered_cols = [col for col in priority_columns if col in current_cols]
    ordered_cols.extend([col for col in current_cols if col not in ordered_cols])
    
    return df[ordered_cols]

def main():
    st.title("Convertitore JSON Universal Plus")
    
    with st.expander("ℹ️ Informazioni"):
        st.markdown("""
        Versione aggiornata che gestisce:
        - JSON da file o testo
        - Strutture nidificate
        - LiveBlog updates
        - Dati malformattati
        """)
    
    # File upload
    uploaded_file = st.file_uploader("Carica un file JSON", type=['json'])
    
    # Text input
    json_input = st.text_area("...oppure incolla qui il tuo JSON:", height=200)
    
    if st.button("Converti"):
        try:
            # Process either uploaded file or text input
            if uploaded_file is not None:
                json_str = uploaded_file.getvalue().decode('utf-8')
            elif json_input:
                json_str = json_input
            else:
                st.warning("Inserisci un JSON o carica un file")
                return
                
            df = process_json_data(json_str)
            
            # Show preview
            st.write("Anteprima della tabella:")
            st.dataframe(df)
            
            col1, col2 = st.columns(2)
            
            # CSV download
            csv = df.to_csv(index=False)
            col1.download_button(
                "📄 Scarica CSV",
                data=csv,
                file_name="dati.csv",
                mime="text/csv"
            )
            
            # Excel download
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
            
            # Stats
            with st.expander("📊 Dettagli"):
                st.write(f"Righe trovate: {len(df)}")
                st.write(f"Colonne: {', '.join(df.columns)}")
        
        except Exception as e:
            st.error(f"Errore nell'elaborazione: {str(e)}")
            if 'json_str' in locals():
                st.code(json_str[:1000])

if __name__ == "__main__":
    main()
