import streamlit as st
import json
import pandas as pd
from io import BytesIO
import re
from typing import List, Dict, Union, Tuple

def aggressive_pattern_extraction(text: str) -> List[Dict]:
    """
    Estrae aggressivamente pattern che sembrano oggetti JSON
    """
    # Rimuovi caratteri problematici iniziali/finali
    text = text.strip().lstrip('\ufeff').strip('[]')
    
    # Pattern più comune nei tuoi dati
    base_pattern = r'{[^}]+}'
    
    # Trova tutti i potenziali oggetti JSON
    potential_objects = re.finditer(base_pattern, text)
    objects = []
    
    for match in potential_objects:
        obj_text = match.group(0)
        
        # Estrai coppie chiave-valore
        pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', obj_text)
        if pairs:
            obj = {}
            for key, value in pairs:
                obj[key] = value
            if obj:  # Se abbiamo trovato almeno una coppia valida
                objects.append(obj)
    
    # Se non troviamo oggetti, proviamo un approccio più aggressivo
    if not objects:
        # Cerca qualsiasi coppia chiave:valore
        pairs = re.findall(r'["\']?([a-zA-Z@][a-zA-Z0-9_@]*)["\']?\s*:\s*["\']([^"\',}]+)["\']', text)
        if pairs:
            obj = {}
            for key, value in pairs:
                obj[key] = value
            objects.append(obj)
    
    return objects

def extract_nested_json(text: str) -> List[Dict]:
    """
    Estrae JSON annidati dal testo
    """
    # Prima cerca oggetti JSON ben formati
    json_pattern = r'({[^{}]*({[^{}]*})*[^{}]*})'
    matches = re.finditer(json_pattern, text)
    objects = []
    
    for match in matches:
        try:
            obj = json.loads(match.group(0))
            if isinstance(obj, dict):
                objects.append(obj)
        except:
            # Se il parsing JSON fallisce, prova l'estrazione aggressiva
            extracted = aggressive_pattern_extraction(match.group(0))
            objects.extend(extracted)
    
    # Se non troviamo nulla, prova l'estrazione aggressiva sull'intero testo
    if not objects:
        objects = aggressive_pattern_extraction(text)
    
    return objects

def main():
    st.title("Convertitore JSON Ultra Smart")
    
    with st.expander("ℹ️ Come funziona"):
        st.markdown("""
        Convertitore avanzato che:
        1. Cerca pattern JSON nel testo
        2. Estrae aggressivamente coppie chiave-valore
        3. Supporta strutture annidate
        4. Gestisce formattazione non standard
        """)
    
    # Area input
    json_input = st.text_area("Incolla qui il tuo testo:", height=200)
    
    if st.button("Converti"):
        if json_input:
            try:
                # Estrai i dati
                extracted_data = extract_nested_json(json_input)
                
                if not extracted_data:
                    st.error("Nessuna struttura dati valida trovata nel testo")
                    st.code(json_input[:1000])
                    return
                
                # Debug view
                with st.expander("🔍 Struttura Estratta"):
                    st.json(extracted_data)
                
                # Crea DataFrame
                df = pd.DataFrame(extracted_data)
                
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
                
                # Mostra statistiche
                with st.expander("📊 Statistiche"):
                    st.write(f"Oggetti trovati: {len(extracted_data)}")
                    if not df.empty:
                        st.write(f"Colonne trovate: {list(df.columns)}")
                        st.write("Esempi di valori:")
                        for col in df.columns:
                            st.write(f"- {col}: {df[col].iloc[0] if len(df) > 0 else 'N/A'}")
                
            except Exception as e:
                st.error(f"Errore nell'elaborazione: {str(e)}")
                st.write("Testo problematico:")
                st.code(json_input[:1000])
                
                # Mostra il parsing passo-passo
                with st.expander("🔍 Debug Dettagliato"):
                    st.write("Pattern trovati:")
                    # Mostra i pattern trovati nel testo
                    for pattern in re.finditer(r'{[^}]+}', json_input):
                        st.code(pattern.group(0))

if __name__ == "__main__":
    main()
