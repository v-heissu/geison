import streamlit as st
import json
import pandas as pd
from io import BytesIO

def convert_json_to_df(json_str):
    try:
        # Converti la stringa JSON in un dizionario Python
        data = json.loads(json_str)
        
        # Se il JSON è una lista di dizionari, convertilo direttamente
        if isinstance(data, list):
            df = pd.DataFrame(data)
        # Se è un dizionario singolo, mettilo in una lista
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise ValueError("Il formato JSON non è supportato")
            
        return df
    except Exception as e:
        st.error(f"Errore nella conversione del JSON: {str(e)}")
        return None

def main():
    st.title("Convertitore JSON in Excel/CSV")
    
    # Area di testo per incollare il JSON
    json_input = st.text_area("Incolla qui il tuo JSON:", height=200)
    
    if st.button("Converti"):
        if json_input:
            df = convert_json_to_df(json_input)
            
            if df is not None:
                # Mostra la tabella
                st.write("Anteprima della tabella:")
                st.dataframe(df)
                
                # Download CSV (sempre disponibile)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Scarica CSV",
                    data=csv,
                    file_name="dati.csv",
                    mime="text/csv"
                )
                
                # Download Excel (con gestione errori)
                try:
                    import openpyxl
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    st.download_button(
                        label="Scarica Excel",
                        data=buffer.getvalue(),
                        file_name="dati.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                except ImportError:
                    st.warning("La funzionalità Excel non è disponibile. Per favore usa il formato CSV.")
        else:
            st.warning("Per favore, inserisci un JSON valido")

if __name__ == "__main__":
    main()
