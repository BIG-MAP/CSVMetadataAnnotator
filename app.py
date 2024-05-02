import pandas as pd
import csv
import streamlit as st
import json
import os
import urllib


def analyze_csv_bytesio(csv_bytesio):
    # Detect the dialect of the CSV file
    dialect = csv.Sniffer().sniff(csv_bytesio.getvalue().decode('utf-8'))
    csv_bytesio.seek(0)  # Reset the file pointer

    # Use pandas to read the CSV from BytesIO object with detected dialect
    df = pd.read_csv(csv_bytesio, dialect=dialect)

    # Get column names and number of rows
    column_names = df.columns.tolist()
    row_count = len(df)

    return {
        "column_names": column_names,
        "row_count": row_count,
        "dialect": {
            "delimiter": dialect.delimiter,
            "quotechar": dialect.quotechar,
            "escapechar": dialect.escapechar,
            "doublequote": dialect.doublequote,
            "lineterminator": dialect.lineterminator,
            "quoting": dialect.quoting,
            "skipinitialspace": dialect.skipinitialspace
        }
    }

@st.cache_data
def load_schema(filepath:str = "template.jsonld")->dict:

    with open(filepath, "r") as f:
        return json.load(f)

@st.cache_data
def get_ontology_concepts()-> list:
    
    with open("./data/context.json") as f:
        data = json.load(f)
    return [key for key in data["@context"].keys() if isinstance(key, str) and len(key) > 0 and key[0].isupper()]
    

############## APP ################################


json_container = st.sidebar.expander("JSON-LD")

st.title("CSV annotator")
st.markdown("""App to create a linked data description of a csv file. Check the [Github repo](https://github.com/BIG-MAP/CSVMetadataAnnotator) 
            for more information.   
            **Steps**:  
            1. Upload a csv file.  
            2. Tag each column to a concept, prefix and unit in BattINFO.  
            3. Explore in the sidebar the JSON-LD description.  
            4. Download the JSON-LD file.""")

schema:dict = load_schema()
concepts:list = get_ontology_concepts()


try:
    uploaded_file = st.file_uploader("Upload your csv file")
except Exception as error:
    st.error(f"""It is not possible to load the csv file. Here is the error log: \n
             {error} \n
            Consult the README.md for more information on how to format the csv file.""")
    uploaded_file = None


if uploaded_file:
    file_description = analyze_csv_bytesio(uploaded_file) 
    schema["tableSchema"]["dialect"].update(file_description["dialect"])
    st.markdown("## Annotate")
    file_url = st.text_input("Location URL: where is your file?", help="An URL pointing to the location of your file. Example https://my_repo.com/myfile.csv")

    for col_name in file_description["column_names"]:
        

        stcol1, stcol2, stcol3, stcol4 = st.columns([1, 2, 1, 1])
        stcol1.markdown("**" + col_name + "**")
        quantity = stcol2.selectbox("Quantity", options=concepts, key=f"Q_{col_name}")
        unit_prefix = stcol3.selectbox("Unit Prefix", options=["None"]+concepts, key=f"P_{col_name}")
        unit = stcol4.selectbox("Unit", options=["None"]+concepts, key=f"U_{col_name}")
        st.divider()

        schema["tableSchema"]["columns"].append(
            {"titles":col_name,
             "propertyUrl": "battinfo:"+quantity,
             "hasMetricPrefix":"battinfo:"+unit_prefix if unit_prefix else "None",
             "hasMeasurementUnit":"battinfo:"+unit}
        )

    schema["url"] = file_url
    json_container.json(schema)
    st.sidebar.download_button("Download linked data file",
                               data=json.dumps(schema, indent=4), 
                               file_name=os.path.splitext(uploaded_file.name)[0]+"_metadata.jsonld")