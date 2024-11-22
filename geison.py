import streamlit as st
import json
import pandas as pd
from io import BytesIO
import re
from typing import List, Dict, Union, Tuple

def analyze_text_structure(text: str) -> Tuple[str, List[Dict]]:
    """
    Analizza la struttura del testo e identifica potenziali oggetti JSON
    """
    # Pulisci il testo base
    text = text.strip().lstrip('\ufeff')
    
    # Pattern comuni in testo che dovrebbe essere JSON
    common_patterns = {
        'object_start': r'{[^}]*"@type"[^}]+}',
        'key_value': r'"?([a-zA-Z@][a-zA-Z0-9_@]*)"?\s*:\s*([^,}\]]+)',
        'quoted_string': r'"([^"\\]*(\\.[^"\\]*)*)"',
        'single_quoted': r"'([^'\\]*(\\.[^'\\]*)*)'",
    }
    
    def extract_structured_data(text: str) -> List[Dict]:
        """Estrae dati strutturati dal testo"""
        objects = []
        current_object = {}
        
        # Cerca coppie chiave-valore
        matches = re.finditer(common_patterns['key_value'], text)
        for match in matches:
            key, value = match.groups()
            # Pulisci la chiave
            key = key.strip('"\'')
            # Pulisci il valore
            value = value.strip()
            if value.startswith('"') or value.startswith("'"):
                value = value[1:-1] if value.endswith(value[0]) else value
            # Aggiungi al dizionario
            current_object[key] = value
            
            # Se troviamo un tipo, potrebbe essere un nuovo oggetto
            if key == "@type" and current_object:
                objects.append(current_object.copy())
                current_object = {}
        
        if current_object:
            objects.append(current_object)
        
        return objects

    def clean_extracted_objects(objects: List[Dict]) -> List[Dict]:
        """Pulisce e normalizza gli oggetti estratti"""
        cleaned = []
        for obj in objects:
            clean_obj = {}
            for k, v in obj.items():
                # Pulisci la chiave
                clean_key = k.strip('"\'@')
                # Pulisci il valore
                if isinstance(v, str):
                    v = v.strip('"\'')
                    # Prova a convertire in tipi appropriati
                    if v.lower() == 'null':
                        v = None
                    elif v.lower() == 'true':
                        v = True
                    elif v.lower() == 'false':
                        v = False
                    elif v.replace('.','').isdigit():
                        try:
                            v = float(v) if '.' in v else int(v)
                        except:
                            pass
                clean_obj[clean_key] = v
            cleaned.append(clean_obj)
        return cleaned

    # Estrai dati strutturati
    extracted_objects = extract_structured_data(text)
    cleaned_objects = clean_extracted_objects(extracted_objects)
    
    # Crea JSON valido
    json_str = json.dumps(cleaned_objects)
    
    return json_str, cleaned_objects

def main():
    st.title("Convertitore JSON Smart")
    
    with st.expander("ℹ️ Come funziona"):
        st.markdown("""
        Questo convertitore:
        1. Analizza la struttura del testo input
        2. Identifica oggetti e valori
        3. Ricostruisce il JSON
        4. Converte in tabella
        
        Funziona anche con JSON malformattato o testo semi-strutturato.
        """)
    
    # Area input
    json_input = st.text_area("Incolla qui il tuo testo:", height=200)
    
    if st.button("Converti"):
        if json_input:
            try:
                # Analizza e estrai i dati
                json_str, extracted_data = analyze_text_structure(json_input)
                
                # Debug view
                with st.expander("🔍 Dati Estratti"):
                    st.code(json_str)
                
                # Crea DataFrame
                df = pd.DataFrame(extracted_data)
                
                # Mostra risultati
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
                    st.write(f"Oggetti trovati: {len(extracted_data)}")
                    st.write(f"Colonne identificate: {list(df.columns)}")
                    st.write("Tipi di dati:")
                    for col in df.columns:
                        st.write(f"- {col}: {df[col].dtype}")
                
            except Exception as e:
                st.error(f"Errore nell'elaborazione: {str(e)}")
                st.write("Testo problematico:")
                st.code(json_input[:1000])

if __name__ == "__main__":
    main()
