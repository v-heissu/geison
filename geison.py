import streamlit as st
import json
import pandas as pd
from io import BytesIO
import re

def fix_consecutive_objects(text: str) -> str:
    """
    Corregge oggetti JSON consecutivi convertendoli in un array
    """
    # Rimuove whitespace e caratteri non necessari
    text = text.strip().lstrip('\ufeff')
    
    # Rimuove caratteri non JSON all'inizio
    text = re.sub(r'^[^{\[]+', '', text)
    
    # Cerca di identificare oggetti JSON consecutivi
    objects = []
    brace_count = 0
    current_obj = []
    in_string = False
    escape = False
    
    for char in text:
        if escape:
            escape = False
            current_obj.append(char)
            continue
            
        if char == '\\':
            escape = True
            current_obj.append(char)
            continue
            
        if char == '"' and not escape:
            in_string = not in_string
            current_obj.append(char)
            continue
            
        if not in_string:
            if char == '{':
                brace_count += 1
                if brace_count == 1 and current_obj:  # Nuovo oggetto inizia
                    objects.append(''.join(current_obj))
                    current_obj = []
                current_obj.append(char)
            elif char == '}':
                brace_count -= 1
                current_obj.append(char)
                if brace_count == 0:  # Oggetto completo
                    objects.append(''.join(current_obj))
                    current_obj = []
            else:
                current_obj.append(char)
        else:
            current_obj.append(char)
    
    if current_obj:
        objects.append(''.join(current_obj))
    
    # Rimuove oggetti vuoti e spazi
    objects = [obj.strip() for obj in objects if obj.strip()]
    
    # Converte in array JSON se ci sono più oggetti
    if len(objects) > 1:
        return f"[{','.join(objects)}]"
    elif objects:
        return objects[0]
    return text

def ensure_json_format(text: str) -> str:
    """
    Assicura che il testo sia in formato JSON valido
    """
    # Prima sistema gli oggetti consecutivi
    text = fix_consecutive_objects(text)
    
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

def main():
    st.title("Convertitore JSON Super Plus")
    
    with st.expander("ℹ️ Informazioni"):
        st.markdown("""
        Questa versione gestisce:
        - Oggetti JSON consecutivi
        - Proprietà non correttamente quotate
        - Mix di stili di citazione
        - JSON malformattato
        """)
    
    json_input = st.text_area("Incolla qui il tuo JSON:", height=200)
    
    if st.button("Converti"):
        if json_input:
            try:
                # Step 1: Sistema gli oggetti consecutivi e normalizza
                cleaned_json = ensure_json_format(json_input)
                
                # Debug view
                with st.expander("🔍 JSON Normalizzato"):
                    st.code(cleaned_json)
                
                # Step 2: Parse
                data = json.loads(cleaned_json)
                
                # Step 3: Converti in DataFrame
                if isinstance(data, list):
                    df = pd.json_normalize(data)
                else:
                    df = pd.json_normalize([data])
                
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
                
            except Exception as e:
                st.error(f"Errore: {str(e)}")
                st.code(cleaned_json[:1000] if 'cleaned_json' in locals() else json_input[:1000])

if __name__ == "__main__":
    main()
