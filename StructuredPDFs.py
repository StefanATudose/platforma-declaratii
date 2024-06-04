#!/usr/bin/env python
# coding: utf-8

# In[1]:


from sqlalchemy import URL
from sqlalchemy import create_engine
import fitz
import io
from PIL import Image
import pandas as pd
import re
from IPython.display import display
import os
import traceback
import logging
import mysql.connector
from sqlalchemy import text


# In[2]:


url_object = URL.create(
    "mysql",
    username="stefan",
    password="Gigelfrone112!!", 
    host="localhost",
    database="declaratiiavere",
)

engine = create_engine(url_object)

with engine.connect() as connection:
    result = connection.execute(text("show tables;"))
    for row in result:
        print(row)


# In[3]:


def categorize_pdf(doc):
    type = 0
    page = doc[0]
    if page.get_text():
        if ("AVERE" in page.get_text()[:50]):
            type = 1
        else:
            type = 2
                
              
    return type


# In[4]:


#populare header_list

path = "model_avere.pdf"
doc = fitz.open(path)

header_list = []


header_list_avere = []
if categorize_pdf(doc) == 1:
    for page in doc:
        tabele = page.find_tables(strategy="lines_strict")
        for tabel in tabele:
            header_list_avere.append(tabel.header.names)

header_list.append(header_list_avere)
doc.close()


header_list_avere.pop(12)
header_list_avere.pop(1)


path = "model_interese.pdf"
doc = fitz.open(path)

header_list_interese = []
if categorize_pdf(doc) == 2:
    for page in doc:
        tabele = page.find_tables(strategy="lines_strict")
        for tabel in tabele:
            header_list_interese.append(tabel.header.names)
            
header_list.append(header_list_interese)

doc.close()


header_list_interese.pop(5)

last_table_special_fields = [["1.1. Titular", "1.2. Soţ/soţie", "1.2. Copii", "1.3. Copii", "2.1. Titular", "2.2. Soţ/soţie",
                            "3.1. Titular", "3.2. Soţ/soţie", "4.1. Titular", "4.2. Soţ/soţie", "5.1. Titular",
                            "5.2. Soţ/soţie", "6.1. Titular", "6.2. Soţ/soţie", "7.1. Titular", "7.2. Soţ/soţie",
                            "7.3. Copii", "8.1. Titular", "8.2. Soţ/soţie", "8.3. Copii"], ["Titular", "Soţ/soţie",
                            "Rude de gradul I1) ale titularului", """Societăţi comerciale/ Persoană fizică autorizată/ Asociaţii familiale/ Cabinete individuale, cabinete
asociate, societăţi civile profesionale sau societăţi civile profesionale cu răspundere limitată care
desfăşoară profesia de avocat/ Organizaţii neguvernamentale/ Fundaţii/ Asociaţii2)"""]]


# In[5]:


def get_cell_color(page, rect):
    pix = page.get_pixmap()
    avg_color = pix.color_topusage(rect)
    #print(f"avg_color: {avg_color[1].hex()}")
    return avg_color[1].hex()


# In[6]:


def table_merging(doc, tip):
    tables_df = []
    prev_header_incomplete = False
    for page in doc:
        tables = page.find_tables(strategy="lines_strict")
        for table in tables:
            header_bbox = table.header.bbox
            header_color = get_cell_color(page, header_bbox)
            if table.header.names not in header_list[tip-1]:
                if header_color == "bfbfbf":
                    #display(table.to_pandas())
                    
                    if prev_header_incomplete:
                        prev_header_incomplete = False
                        col_number = 0
                        for col_name in table.header.names:
                            if col_name != "":
                                tables_df[-1].rename(columns = {tables_df[-1].columns[col_number]: tables_df[-1].columns[col_number] + "\n" + col_name}, inplace = True)
                                #tables_df[-1].columns[col_number] = tables_df[-1].columns[col_number] + "\n" + col_name
                            col_number = col_number + 1
                        table_new = table.to_pandas()
                        table_new.columns = tables_df[-1].columns
                        tables_df[-1] = pd.concat([tables_df[-1], table_new], ignore_index=True)
                        #display(tables_df[-1])
                    else:
                        prev_header_incomplete = True
                        tables_df.append(table.to_pandas())
                        #display(tables_df[-1])
                        
                elif "" in table.header.names and table.header.names[0] not in last_table_special_fields[tip-1]:
                    #display(table.to_pandas())
                    col_number = 0
                    for col_name in table.header.names:
                        if col_name != "":
                            tables_df[-1].iloc[-1, col_number] = tables_df[-1].iloc[-1, col_number] + "\n" + col_name
                        col_number = col_number + 1
                    #print("ajuns")
                    table_new = table.to_pandas()
                    table_new.columns = tables_df[-1].columns
                    tables_df[-1] = pd.concat([tables_df[-1], table_new], ignore_index=True)
                    #display(tables_df[-1])

                
                else:
                    table_new = table.to_pandas()
                    table_new_header_df = pd.DataFrame(table_new.columns).T
                    table_new_header_df.columns = tables_df[-1].columns
                    tables_df[-1] = pd.concat([tables_df[-1], table_new_header_df], axis=0, ignore_index=True)
                    table_new.columns = tables_df[-1].columns
                    tables_df[-1] = pd.concat([tables_df[-1], table_new], ignore_index=True)
                    #display(tables_df[-1])

                
                
            else:
                tables_df.append(table.to_pandas())
                #display(tables_df[-1])
    return tables_df


# In[7]:


def extract_fields(string):
    fields = re.findall(r'(\w+):\s(\w+)', string)
    field_dict = {key: value for key, value in fields}
    return field_dict


# In[8]:


def insert_teren_cladire(table, tip, doc_id):
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table = table.replace(["\n", " m2"], [" ", ""], regex=True)
    locatii = table.iloc[:, 0].tolist()
    
    locatii = list(map(extract_fields, locatii))
    locatii = {key: [d[key] for d in locatii] for key in locatii[0]}
    
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
    table.insert(1, "tip", [tip for i in range (len(table.index))], True)
    table.insert(2, "tara", locatii["Tara"], True)
    table.insert(3, "judet", locatii["Judet"], True)
    table.insert(4, "localitate", locatii["Localitate"], True)
    table = table.drop(table.columns[5], axis=1)

    if tip == 0:
        table.rename(columns={'Categoria*': 'categorie', 'Anul\ndobândirii': 'an_dobandire',
                         'Suprafaţa': 'suprafata', 'Cota-\nparte': 'cota_parte', 'Modul de\ndobândire': 'mod_dobandire',
                         'Titularul1)': 'proprietar'}, inplace=True)
    else:
        table.rename(columns={'Categoria*': 'categorie', 'Anul\ndobândirii': 'an_dobandire',
                         'Suprafaţa': 'suprafata', 'Cota-\nparte': 'cota_parte', 'Modul de\ndobândire': 'mod_dobandire',
                         'Titularul2)': 'proprietar'}, inplace=True)
    #table.drop(index=[1, 2, 3, 4])
    #return table
    table.to_sql('teren_cladire', con=engine, if_exists='append', index=False)
    

    
def insert_mijloc_transport(table, doc_id):
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table = table.replace("\n", " ", regex=True)
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)

    table.rename(columns={'Natura': 'natura', 'Marca': 'marca',
                         'Nr. de bucăţi': 'nr_bucati', 
                          'Anul de fabricaţie': 'an_fabricatie', 
                          'Modul de\ndobândire': 'mod_dobandire'}, inplace=True)
    
    table.to_sql('mijloc_transport', con=engine, if_exists='append', index=False)
    #return table
    
def insert_bun_cultural(table, doc_id):
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table = table.replace(["\n", None], [" ", "-"], regex=True)
    
    lista_valoare = list(table.iloc[:, -1])
    lista_valoare = [re.findall(r'([\d\-]+)\s([a-zA-Z]+)', string) for string in lista_valoare]
    lista_valoare_nr = [int(item[0]) if item[0].isdigit() else 0 for sublist in lista_valoare for item in sublist if sublist]
    lista_valoare_valuta = [item[1] for sublist in lista_valoare for item in sublist if sublist]
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
    table.insert(3, "valoare_nr", lista_valoare_nr, True)
    table.insert(4, "valoare_valuta", lista_valoare_valuta, True)
    table = table.drop(table.columns[5], axis=1)
    
    table.rename(columns={'Descriere sumară': 'descriere_sumara', 'Anul dobândiri': 'an_dobandire'}, inplace=True)

    table.to_sql('bun_cultural', con=engine, if_exists='append', index=False)
    
    #return table

def insert_bun_instrainat(table, doc_id):
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table = table.replace(["\n", None], [" ", "-"], regex=True)
    lista_valoare = list(table.iloc[:, -1])
    lista_valoare = [re.findall(r'([\d\-]+)\s([a-zA-Z]+)', string) for string in lista_valoare]
    lista_valoare_nr = [int(item[0]) if item[0].isdigit() else 0 if item[0].isdigit() else 0 for sublist in lista_valoare for item in sublist if sublist]
    lista_valoare_valuta = [item[1] for sublist in lista_valoare for item in sublist if sublist]
    
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
    table.insert(5, "valoare_nr", lista_valoare_nr, True)
    table.insert(6, "valoare_valuta", lista_valoare_valuta, True)
    table = table.drop(table.columns[7], axis=1)

    table.rename(columns={'Natura bunului\nînstrăinat': 'natura', "Data\nînstrăinării": 'data', 
                 'Persoana catre\ncare s-a\nînstrăinat': 'persoana_catre', 'Forma înstrăinării': 'forma'}, inplace=True)
    table.to_sql('bun_instrainat', con=engine, if_exists='append', index=False)
    #return table

def insert_activa_financiara_indirecta(table, doc_id):
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table = table.replace(["\n", None], [" ", "-"], regex=True)
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
    # table.loc[0, "Sold/valoare la zi"] = 5
    # table.loc[0, "Deschis în\nanul"] = 2005

    table.rename(columns={'Instituţia care\nadministrează\nşi adresa acesteia': 'institutie', "Tipul*": 'tip', 
                 'Valuta': 'valuta', 'Deschis în\nanul': 'an', 'Sold/valoare la zi': 'sold'}, inplace=True)
    table.to_sql('activa_financiara_indirecta', con=engine, if_exists='append', index=False)

    return table
    
def insert_activa_financiara_directa(table, doc_id):
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table = table.replace(["\n", None], [" ", "-"], regex=True)
    lista_valoare = list(table.iloc[:, -1])
    lista_valoare = [re.findall(r'([\d\-]+)\s([a-zA-Z]+)', string) for string in lista_valoare]
    lista_valoare_nr = [int(item[0]) if item[0].isdigit() else 0 for sublist in lista_valoare for item in sublist if sublist]
    lista_valoare_valuta = [item[1] for sublist in lista_valoare for item in sublist if sublist]
    
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
    table.insert(4, "valoare_nr", lista_valoare_nr, True)
    table.insert(5, "valoare_valuta", lista_valoare_valuta, True)
    table = table.drop(table.columns[6], axis=1)
    
    table.rename(columns={'Emitent\ntitlu/societatea în care\npersoana este\nacţionar sau\nasociat/beneficiar de\nîmprumut': 'emitent', 
                          "Tipul*": 'tip', 'Număr de titluri/\ncota de participare': 'nr_sau_cota'}, inplace=True)
    table.to_sql('activa_financiara_directa', con=engine, if_exists='append', index=False)
    
    #return table

def insert_alta_activa_financiara(table, doc_id):
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table = table.replace(["\n", None], [" ", "-"], regex=True)
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
    
    table.rename(columns={'Descriere': 'descriere', "Valoare": 'valoare', 'Valuta': 'valuta'}, inplace=True)
    table.to_sql('alta_activa_financiara', con=engine, if_exists='append', index=False)
    return table

def insert_datorie(table, doc_id):
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table = table.replace(["\n", None], [" ", "-"], regex=True)
    lista_valoare = list(table.iloc[:, -1])
    lista_valoare = [re.findall(r'([\d\-]+)\s([a-zA-Z]+)', string) for string in lista_valoare]
    lista_valoare_nr = [int(item[0]) if item[0].isdigit() else 0 for sublist in lista_valoare for item in sublist if sublist]
    lista_valoare_valuta = [item[1] for sublist in lista_valoare for item in sublist if sublist]
    
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
    table.insert(4, "valoare_nr", lista_valoare_nr, True)
    table.insert(5, "valoare_valuta", lista_valoare_valuta, True)
    table = table.drop(table.columns[6], axis=1)
    
    table.rename(columns={'Creditor': 'creditor', "Contractat în anul": 'an_creata', 'Scadent în anul': 'an_scadenta'}, inplace=True)
    table.to_sql('datorie', con=engine, if_exists='append', index=False)
    return table

def insert_ajutor(table, doc_id):
    table = table.replace(["\n", None], [" ", "-"], regex=True)
    realizator_tip = -1
    realizator_tip_list = []
    realizator_nume_list = []
    sursa_list = []
    serviciu_obiect_list = []
    venit_nr_list = []
    venit_valuta_list = []
 
    for row_num in range(len(table.index)):
        first_elem_in_row = table.iloc[row_num, 0]
        if ("Titular" in first_elem_in_row):
            realizator_tip = 0
        elif ("Soț" in first_elem_in_row or "Soţ" in first_elem_in_row):
            realizator_tip = 1
        elif ("Copii" in first_elem_in_row):
            realizator_tip = 2
        elif first_elem_in_row != "-" and len(first_elem_in_row) > 4:
            realizator_tip_list.append(realizator_tip)
            realizator_nume_list.append(table.iloc[row_num, 0])
            sursa_list.append(table.iloc[row_num, 1])
            serviciu_obiect_list.append(table.iloc[row_num, 2])
            venit = re.findall(r'(\d+)\s([a-zA-Z]+)', table.iloc[row_num, 3])
            if venit:
                venit_nr, venit_valuta = venit[0]
            else:
                venit_nr, venit_valuta = (0, 'NONE')
            venit_nr_list.append(venit_nr)
            venit_valuta_list.append(venit_valuta)
    doc_list = [doc_id for i in range(len(realizator_nume_list))]
    new_table_df = pd.DataFrame.from_dict({"doc_id": doc_list, "realizator_tip": realizator_tip_list,
                                         "realizator_nume": realizator_nume_list, "sursa": sursa_list, 
                                        "serviciu_obiect": serviciu_obiect_list, "venit_nr": venit_nr_list,
                                        "venit_valuta": venit_valuta_list})
    new_table_df.to_sql('ajutor', con=engine, if_exists='append', index=False)
    return new_table_df
            
            
def insert_venit(table, doc_id):
    table = table.replace(["\n", None], [" ", "-"], regex=True)
    realizator_tip = -1
    venit_tip = -1
    venit_tip_list = []
    realizator_tip_list = []
    realizator_nume_list = []
    sursa_list = []
    serviciu_obiect_list = []
    venit_nr_list = []
    venit_valuta_list = []
    for row_num in range(len(table.index)):
        first_elem_in_row = table.iloc[row_num, 0]
        if re.match(r'(\d).\s', first_elem_in_row):
            venit_tip = first_elem_in_row
        elif ("Titular" in first_elem_in_row):
            realizator_tip = 0
        elif ("Soț" in first_elem_in_row or "Soţ" in first_elem_in_row):
            realizator_tip = 1
        elif ("Copii" in first_elem_in_row):
            realizator_tip = 2
        elif first_elem_in_row != "-" and len(first_elem_in_row) > 4:
            venit_tip_list.append(venit_tip)
            realizator_tip_list.append(realizator_tip)
            realizator_nume_list.append(table.iloc[row_num, 0])
            sursa_list.append(table.iloc[row_num, 1])
            serviciu_obiect_list.append(table.iloc[row_num, 2])
            venit = re.findall(r'(\d+)\s([a-zA-Z]+)', table.iloc[row_num, 3])
            if venit:
                venit_nr, venit_valuta = venit[0]
            else:
                venit_nr, venit_valuta = (0, 'NONE')
            venit_nr_list.append(venit_nr)
            venit_valuta_list.append(venit_valuta)
    doc_list = [doc_id for i in range(len(realizator_nume_list))]
    new_table_df = pd.DataFrame.from_dict({"doc_id": doc_list, "venit_tip": venit_tip_list ,"realizator_tip": realizator_tip_list,
                                         "realizator_nume": realizator_nume_list, "sursa": sursa_list, 
                                        "serviciu_obiect": serviciu_obiect_list, "venit_nr": venit_nr_list,
                                        "venit_valuta": venit_valuta_list})
    new_table_df.to_sql('venit', con=engine, if_exists='append', index=False)
    return new_table_df
    
def insert_membru_non_stat(table, doc_id):
    table = table.drop(0)
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table = table.replace(["\n", None], [" ", "-"], regex=True)
    lista_valoare = list(table.iloc[:, -1])
    lista_valoare = [re.findall(r'([\d\-]+)\s([a-zA-Z]+)', string) for string in lista_valoare]

    lista_valoare_nr = [int(item[0]) if item[0].isnumeric() else 0 for sublist in lista_valoare for item in sublist if sublist]
    lista_valoare_valuta = [item[1] for sublist in lista_valoare for item in sublist if sublist]
    lista_parti_sociale = list(table.iloc[:, 2])
    lista_parti_sociale = [re.search(r'[\d]+', string) for string in lista_parti_sociale]
    
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
    table.insert(3, "nr_parti_sociale", lista_valoare_nr, True)
    table = table.drop(table.columns[4], axis=1)
    table.insert(4, "valoare_nr", lista_valoare_nr, True)
    table.insert(5, "valoare_valuta", lista_valoare_valuta, True)
    table = table.drop(table.columns[6], axis=1)
 	
    table.rename(columns={'1. Asociat sau acţionar la societăţi comerciale, companii/societăţi naţionale, instituţii de credit,\ngrupuri de interes economic, precum şi membru în asociaţii, fundaţii sau alte organizaţii\nneguvernamentale:': 'unitate',
                            "Col1": 'calitate'}, inplace=True)
    table.to_sql('membru_non_stat', con=engine, if_exists='append', index=False)
    
    return table

def insert_membru_stat(table, doc_id):
    table = table.drop(0)
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table = table.replace(["\n", None], [" ", "-"], regex=True)
    lista_valoare = list(table.iloc[:, -1])
    lista_valoare = [re.findall(r'([\d\-]+)\s([a-zA-Z]+)', string) for string in lista_valoare]
    lista_valoare_nr = [int(item[0]) if item[0].isdigit() else 0 for sublist in lista_valoare for item in sublist if sublist]
    lista_valoare_valuta = [item[1] for sublist in lista_valoare for item in sublist if sublist]
    
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
    table.insert(3, "valoare_nr", lista_valoare_nr, True)
    table.insert(4, "valoare_valuta", lista_valoare_valuta, True)
    table = table.drop(table.columns[5], axis=1)
    


    table.rename(columns={'2. Calitatea de membru în organele de conducere, administrare şi control ale societăţilor\ncomerciale, ale companiilor/societăţilor naţionale, ale instituţiilor de credit, ale grupurilor de\ninteres economic, ale asociaţiilor sau fundaţiilor ori ale altor organizaţii neguvernamentale:': 'unitate',
                        "Col1": 'calitate'}, inplace=True)
    table.to_sql('membru_stat', con=engine, if_exists='append', index=False)
    return table
    

def insert_membru_sindicat(table, doc_id):
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)

    table.rename(columns={'3. Calitatea de membru în cadrul asociaţiilor profesionale şi/sau sindicale': 'functie'}, inplace=True)
    table.to_sql('membru_sindicat', con=engine, if_exists='append', index=False)
    return table

def insert_membru_partid(table, doc_id):
    first_item = table.iloc[0, 0]
    has_letters = re.search(r'[A-Za-z]', first_item)
    if has_letters is None:
        return
    table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
    
    table.rename(columns={'4. Calitatea de membru în organele de conducere, administrare şi control, retribuite sau\nneretribuite, deţinute în cadrul partidelor politice, funcţia deţinută şi denumirea partidului\npolitic': 'functie'}, inplace=True)
    table.to_sql('membru_partid', con=engine, if_exists='append', index=False)
    return table
    
def insert_contract(table, doc_id):
    table = table.drop(0)
    table = table.replace(["\n", None], [" ", "-"], regex=True)
    tip_beneficiar = -1
    tip_beneficiar_list = []
    beneficiar_nume_list = []
    institutie_list = []
    procedura_list = []
    tip_contract_list = []
    data_incheiere_list = []
    durata_list = []
    valoare_nr_list = []
    valoare_valuta_list = []
    for row_num in range(len(table.index)):
        first_elem_in_row = table.iloc[row_num, 0]
        if ("Titular" in first_elem_in_row):
            tip_beneficiar = 0
        elif ("Soț" in first_elem_in_row or "Soţ" in first_elem_in_row):
            tip_beneficiar = 1
        elif ("Rude de gradul I" in first_elem_in_row):
            tip_beneficiar = 2
        elif ("Societăţi comerciale" in first_elem_in_row):
            tip_beneficiar = 3
        elif first_elem_in_row != "-" and len(first_elem_in_row) > 4:
            tip_beneficiar_list.append(tip_beneficiar)
            beneficiar_nume_list.append(table.iloc[row_num, 0])
            institutie_list.append(table.iloc[row_num, 1])
            procedura_list.append(table.iloc[row_num, 2])
            tip_contract_list.append(table.iloc[row_num, 3])
            data_incheiere_list.append(table.iloc[row_num, 4])
            durata_list.append(table.iloc[row_num, 5])
            valoare = re.findall(r'(\d+)\s([a-zA-Z]+)', table.iloc[row_num, 6])
            if valoare:
                valoare_nr, valoare_valuta = valoare[0]
            else:
                valoare_nr, valoare_valuta = (0, 'NONE')
            valoare_nr_list.append(valoare_nr)
            valoare_valuta_list.append(valoare_valuta)
    doc_list = [doc_id for i in range(len(tip_beneficiar_list))]
    
    new_table_df = pd.DataFrame.from_dict({"doc_id": doc_list, "tip_beneficiar": tip_beneficiar_list ,"nume_beneficiar": beneficiar_nume_list,
                                         "institutie_contractanta": institutie_list, "procedura": procedura_list, 
                                        "tip_contract": tip_contract_list, "data_incheiere" : data_incheiere_list,
                                           "durata": durata_list,
                                           "valoare_nr": valoare_nr_list,
                                        "valoare_valuta": valoare_valuta_list})
    new_table_df.to_sql('contract', con=engine, if_exists='append', index=False)
    return new_table_df



# In[9]:


path = "avere_ciolacu.pdf"
doc = fitz.open(path)

tabele = table_merging(doc, 1)
table = tabele[4]
display(table)
table = insert_bun_instrainat(table, 1)

display(table)
#with engine.connect() as connection:

#rez = insert_mijloc_transport(table, 1)
#print(rez)
#connection.commit()
doc.close()


# In[19]:


total_doc_id = 10
total_titular_id = 10


# In[20]:


def database_insertion(path, connection):
    doc = fitz.open(path)
    global total_doc_id, total_titular_id
    try:
        doc_type = categorize_pdf(doc)
        if doc_type != 0:
            tables_df = table_merging(doc, doc_type)
        if doc_type == 1:
            if len(tables_df) != 12:
                raise Exception("Asset table not merged correctly")              
        if doc_type == 2:
            if len(tables_df) != 6:
                raise Exception("Interests table not merged correctly") 
                
    except Exception as e:
        print(path)
        logging.error(traceback.format_exc())
        return
    if (doc_type == 1):
        page = doc[0]
        nume, init_tata, prenume, functie, institutie = re.findall(r'(?:Subsemnatul|Subsemnata) ([a-zA-ZĂăÎîșȘțȚâÂ\-]+) ([a-zA-ZĂăÎîșȘțȚâÂ\.\-]+) ([a-zA-ZĂăÎîșȘțȚâÂ\- ]+), având func[ţț]ia de ([a-zA-ZĂăÎîșȘțȚâÂ\- \n]+) la ([a-zA-ZĂăÎîșȘțȚâÂ\- \n]+), CNP', page.get_text()[:300])[0]
        nume = nume.replace('\n', ' ')
        init_tata = init_tata.replace('\n', ' ')
        prenume = prenume.replace('\n', ' ')
        functie = functie.replace('\n', ' ')
        institutie = institutie.replace('\n', ' ')
        raw_date = tables_df[11].iloc[0, 0]
        format_date = f'{raw_date[6:]}-{raw_date[3:5]}-{raw_date[:2]}'
        
        current_doc_id = total_doc_id
        total_doc_id += 1
        
        existing_titular = connection.execute(text(f"""select * from titular where nume = '{nume}' and init_tata = '{init_tata}'
                                        and prenume = '{prenume}' and functie = '{functie}' and institutie = '{institutie}';"""))
        if existing_titular.rowcount > 0:
            current_titular_id = existing_titular.first().titular_id
        else:
            current_titular_id = total_titular_id
            connection.execute(text(f"INSERT INTO TITULAR VALUES('{current_titular_id}', '{nume}', '{init_tata}', '{prenume}', '{functie}', '{institutie}');"))
            total_titular_id += 1
        
        connection.execute(text(f"INSERT INTO DOCUMENT VALUES('{current_doc_id}', '{current_titular_id}', '{format_date}', '{doc_type}');"))
        connection.commit() 
        insert_teren_cladire(tables_df[0], 0, current_doc_id)
        insert_teren_cladire(tables_df[1], 1, current_doc_id)
        insert_mijloc_transport(tables_df[2], current_doc_id)
        insert_bun_cultural(tables_df[3], current_doc_id)
        insert_bun_instrainat(tables_df[4], current_doc_id)
        insert_activa_financiara_indirecta(tables_df[5], current_doc_id)
        insert_activa_financiara_directa(tables_df[6], current_doc_id)
        insert_alta_activa_financiara(tables_df[7], current_doc_id)
        insert_datorie(tables_df[8], current_doc_id)
        insert_ajutor(tables_df[9], current_doc_id)
        insert_venit(tables_df[10], current_doc_id)

    elif (doc_type == 2):
        
        page = doc[0]
        nume, init_tata, prenume, functie, institutie = re.findall(r'(?:Subsemnatul|Subsemnata) ([a-zA-ZĂăÎîșȘțȚâÂ\-]+) ([a-zA-ZĂăÎîșȘțȚâÂ\.\-]+) ([a-zA-ZĂăÎîșȘțȚâÂ\- ]+), având func[ţț]ia de ([a-zA-ZĂăÎîșȘțȚâÂ\- \n]+) la ([a-zA-ZĂăÎîșȘțȚâÂ\- \n]+), CNP', page.get_text()[:300])[0]
        
        raw_date = tables_df[5].iloc[0, 0]
        format_date = f'{raw_date[6:]}-{raw_date[3:5]}-{raw_date[:2]}'
        
        current_doc_id = total_doc_id
        total_doc_id += 1

        existing_titular = connection.execute(text(f"""select * from titular where nume = '{nume}' and init_tata = '{init_tata}'
                                        and prenume = '{prenume}' and functie = '{functie}' and institutie = '{institutie}';"""))
        if existing_titular.rowcount > 0:
            current_titular_id = existing_titular.first().titular_id
        else:
            current_titular_id = total_titular_id
            connection.execute(text(f"INSERT INTO TITULAR VALUES('{current_titular_id}', '{nume}', '{init_tata}', '{prenume}', '{functie}', '{institutie}');"))
            total_titular_id += 1
        
        connection.execute(text(f"INSERT INTO DOCUMENT VALUES('{current_doc_id}', '{current_titular_id}', '{format_date}', '{doc_type}');"))
        connection.commit() 
        insert_membru_non_stat(tables_df[0].replace("\n", " ", regex=True), current_doc_id)
        insert_membru_stat(tables_df[1].replace("\n", " ", regex=True), current_doc_id)
        insert_membru_sindicat(tables_df[2].replace("\n", " ", regex=True), current_doc_id)
        insert_membru_partid(tables_df[3].replace("\n", " ", regex=True), current_doc_id)
        insert_contract(tables_df[4].replace("\n", " ", regex=True), current_doc_id)

    doc.close()


# In[21]:


with engine.connect() as connection:
    database_insertion('interese_ciolacu.pdf', connection)


# In[ ]:


pdfs = []

for filename in os.listdir("pdf/"):
    pdfs.append(f"pdf/{filename}")

structured = 0
correct = 0
total = 0

for path in pdfs:
    doc = fitz.open(path)
    total = total + 1
    try:
        category = categorize_pdf(doc)
        if category != 0:
            structured = structured + 1
            tables_df = table_merging(doc, category)
        if category == 1:
            if len(tables_df) == 12:
                correct = correct + 1
            else:
                print("1: " + path)
        if category == 2:
            if len(tables_df) == 6:
                correct = correct + 1
            else:
                print("2: " + path)

    except Exception as e:
        print(path)
        logging.error(traceback.format_exc())
        continue
    doc.close()
    print(f"{correct}/{structured}/{total}")


           


# In[23]:


path = "model_avere.pdf"
doc = fitz.open(path)

# tabele = table_merging(doc, 1)
# table = tabele[0]

# display(table)

# table = insert_teren_cladire(table, 0, 5)

# display(table)

page = doc[0]
print(page.get_text()[:300])

rez = re.findall(r'(?:Subsemnatul|Subsemnata) ([a-zA-ZĂăÎîșȘțȚâÂ\-]+) ([a-zA-ZĂăÎîșȘțȚâÂ\.\-]+) ([a-zA-ZĂăÎîșȘțȚâÂ\- ]+), având func[ţț]ia de ([a-zA-ZĂăÎîșȘțȚâÂ\- \n]+) la ([a-zA-ZĂăÎîșȘțȚâÂ\- \n]+), CNP', page.get_text()[:300])

print(rez)


doc.close()


# In[11]:


path = "model_interese.pdf"
doc = fitz.open(path)

tabele = table_merging(doc, 2)
table = tabele[5]

display(table)

raw_date = table.iloc[0, 0]

format_date = f'{raw_date[6:]}-{raw_date[3:5]}-{raw_date[:2]}'

print(format_date)
doc_id = 7



doc.close()


# In[33]:


def func(a):
    a = a + 1
    print(a)

a = 1
func(a)
print(a)


# In[ ]:


## TODO: change headers for each insert function
## FINISH insert assembler


# In[ ]:




