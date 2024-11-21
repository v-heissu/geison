import streamlit as st
import json
import pandas as pd
from io import BytesIO

def flatten_json(nested_json):
    """
    Appiattisce un JSON annidata in una struttura piatta.
    Per esempio, address.postalCode diventa semplicemente postalCode
    """
    flattened = []
    
    for item in nested_json['items']:
        flat_item = {}
        # Aggiungi l'ID
        flat_item['_id'] = item['_id']
        
        # Aggiungi i campi dell'indirizzo
        if 'address' in item:
            for key, value in item['address'].items():
                flat_item[key] = value
                
        # Aggiungi il placeId da geo
        if 'geo' in item and 'placeId' in item['geo']:
            flat_item['placeId'] = item['geo']['placeId']
            
        # Aggiungi altri campi a livello root
        for key, value in item.items():
            if key not in ['_id', 'address', 'geo']:
                flat_item[key] = value
                
        flattened.append(flat_item)
    
    return flattened

def convert_json_to_df(json_str):
    try:
        # Converti la stringa JSON in un dizionario Python
        data = json.loads(json_str)
        
        # Appiattisci la struttura JSON
        flattened_data = flatten_json(data)
        
        # Converti in DataFrame
        df = pd.DataFrame(flattened_data)
        
        # Riorganizza le colonne in un ordine più logico
        desired_order = [
            '_id', 'postalCode', 'addressLocality', 'streetAddress',
            'addressRegion', 'addressCountry', 'province', 'placeId',
            'name', 'text_en', 'updatedAt'
        ]
        
        # Filtra solo le colonne che esistono nel DataFrame
        columns = [col for col in desired_order if col in df.columns]
        # Aggiungi eventuali colonne rimanenti alla fine
        remaining_columns = [col for col in df.columns if col not in desired_order]
        columns.extend(remaining_columns)
        
        return df[columns]
    
    except Exception as e:
        st.error(f"Errore nella conversione del JSON: {str(e)}")
        return None

def main():
    st.title("Convertitore JSON in Tabella")
    
    # Area di testo per incollare il JSON
    json_input = st.text_area("Incolla qui il tuo JSON:", height=200)
    
    if st.button("Converti"):
        if json_input:
            df = convert_json_to_df(json_input)
            
            if df is not None:
                # Mostra la tabella
                st.write("Anteprima della tabella:")
                st.dataframe(df)
                
                # Download CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Scarica CSV",
                    data=csv,
                    file_name="dati.csv",
                    mime="text/csv"
                )
                
                # Download Excel
                try:
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
