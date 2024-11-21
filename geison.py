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
                
                # Bottoni per il download
                col1, col2 = st.columns(2)
                
                # Download Excel
                with col1:
                    excel_buffer = BytesIO()
                    df.to_excel(excel_buffer, index=False)
                    excel_data = excel_buffer.getvalue()
                    
                    st.download_button(
                        label="Scarica Excel",
                        data=excel_data,
                        file_name="dati.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                
                # Download CSV
                with col2:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Scarica CSV",
                        data=csv,
                        file_name="dati.csv",
                        mime="text/csv"
                    )
        else:
            st.warning("Per favore, inserisci un JSON valido")

if __name__ == "__main__":
    main()
