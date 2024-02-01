import streamlit as st
import easyocr
import re
import numpy as np
import pandas as pd
from PIL import Image
import psycopg2

st.title("BizCardX: Extracting Business Card Data with OCR")

uploaded_files = st.file_uploader("Choose a business card")

# Initialize address variable
address = ""

# Establish the database connection and create cursor
conn = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="ma143mahi@",
    database="mahender",
    port=5432
)
cursor = conn.cursor()

# Assuming 'pics' table already exists
# cursor.execute("create table pics (image bytea)")
# cursor.execute("create table card4 (Name varchar(50), Designation varchar(50), Email_address varchar(50), pincode varchar(50), Mobile_Number varchar(50), Website_url varchar(50), company_name varchar(50), Area varchar(50), City_and_State varchar(50))")

if uploaded_files is not None:
    image = Image.open(uploaded_files)
    reader = easyocr.Reader(['en'])
    result = reader.readtext(np.array(image), detail=0)

    st.image(uploaded_files, caption='Business Card')

    data_dict = {}  # creating a dictionary to store the extracted data
    mobile_number = []
    website = []
    a = []
    company_name = []

    # identifying name and designation from the extracted data
    data_dict["Name"] = result[0]
    data_dict["Designation"] = result[1]
    for i in data_dict.values():
        result.remove(i)
    for i in result:
        if re.match("^[+][(]{0,1}[0-9]{1,4}[)]{0,1}[-\s./0-9]$", i) and len(i) >= 10:
            mobile_number.append(i)
        elif re.match(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", i):
            data_dict["Email_address"] = i
        elif re.match(r"[a-zA-Z].+[a-zA-Z0-9](?:[.]+[a-z]{2,3})", i) or i[0:3] == "www" or i[0:3] == "WWW":
            website.append(i)
        elif re.match(r"[0-9]{6}", i):
            data_dict["Pincode"] = i
        elif re.match(r"[a-zA-Z]+\s[0-9]{6}", i):
            a = i.split(" ")
            data_dict["pincode"] = a[1]
            address2 = a[0]
            address = address + address2
        elif re.match(r"[0-9]{3}\s[a-zA-Z]{3}\s[a-zA-Z]+[\s]?[\,]?[\,]?[\s]?[a-zA-Z]+[\,]?[\;]?[a-zA-Z]+[\,]?[\;]?", i):
            address = i
        elif re.match(r"[a-zA-Z]+", i):
            company_name.append(i)

    # storing combined data which is extracted into the dictionary
    data_dict["Mobile_Number"] = ",".join(mobile_number)
    data_dict["Website_url"] = ".".join(website)
    data_dict["company_name"] = " ".join(company_name)

    # extracting area, city, and state from the string address
    def resulted_address(text):
        text = text.split(",")
        for i in text:
            if i == '':
                text.remove(i)
        data_dict["Area"] = text[0]
        text.remove(text[0])
        data_dict["City_and_State"] = ",".join(text)

    resulted_address(address)

    # streamlit application
 

   

# streamlit application
    df = pd.DataFrame(data=data_dict.items(), columns=["details", "data"])
    st.dataframe(df)

    if st.button('save_data'):  # saving the data into the database
    # Create the 'pics' and 'card4' tables if they do not exist
        cursor.execute("create table if not exists pics (image bytea)")
        cursor.execute("create table if not exists card4 (Name varchar(50), Designation varchar(50), Email_address varchar(50), pincode varchar(50), Mobile_Number varchar(50), Website_url varchar(50), company_name varchar(50), Area varchar(50), City_and_State varchar(50))")

    # Convert image data to bytea format
        image_data_bytea = psycopg2.Binary(image.tobytes())

    # Insert data into the 'pics' table
        cursor.execute("insert into pics (image) values (%s)", (image_data_bytea,))
    
    # Insert data into the 'card4' table
        list2 = [i for i in data_dict.values()]
        query = "insert into card4 values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        val = (list2[0], list2[1], list2[2], list2[3], list2[4], list2[5], list2[6], list2[7], list2[8])
        cursor.execute(query, val)
        conn.commit()

    if st.button('delete_data'):  # button to delete data from the database
        cursor.execute("truncate card4")
        cursor.execute("truncate pics")

# Close cursor and connection
    cursor.close()
    conn.close()
