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
from .utils import AveragePrices
import unicodedata

logging.basicConfig(filename='errorLogs.txt',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

def categorize_pdf(doc):
        type = 0
        page = doc[0]
        if page.get_text():
            if ("AVERE" in page.get_text()[:50]):
                type = 1
            else:
                type = 2
                            
        return type

class DocumentUploadToDatabase():

    url_object = URL.create(
        "mysql",
        username="stefan",
        password="Gigelfrone112!!", 
        host="localhost",
        database="declaratiiavere",
    )

    engine = create_engine(url_object)


    #populare header_list

    path = os.path.dirname(os.path.realpath(__file__)) + "\static\\avere\model_avere.pdf"
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


    path = os.path.dirname(os.path.realpath(__file__)) + "\static\\avere\model_interese.pdf"
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

    
 
    


    @staticmethod
    def get_cell_color(page, rect):
        pix = page.get_pixmap()
        avg_color = pix.color_topusage(rect)
        #print(f"avg_color: {avg_color[1].hex()}")
        return avg_color[1].hex()


    @staticmethod
    def table_merging(doc, tip):
        tables_df = []
        prev_header_incomplete = False
        for page in doc:
            tables = page.find_tables(strategy="lines_strict")
            for table in tables:
                header_bbox = table.header.bbox
                header_color = DocumentUploadToDatabase.get_cell_color(page, header_bbox)
                if table.header.names not in DocumentUploadToDatabase.header_list[tip-1]:
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
                            
                    elif "" in table.header.names and table.header.names[0] not in DocumentUploadToDatabase.last_table_special_fields[tip-1]:
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

    @staticmethod
    def extract_fields(string):
        fields = re.findall(r'(\w+):\s([\w\.\*\-]+)', string)
        field_dict = {key: value for key, value in fields}
        return field_dict

    @staticmethod
    def remove_diacritics(input_str):
        # Normalize the input string to NFD (Normalization Form D)
        normalized_str = unicodedata.normalize('NFD', input_str)
        
        # Filter out the combining characters (diacritics)
        filtered_str = ''.join(
            char for char in normalized_str if not unicodedata.combining(char)
        )
        
        return filtered_str

    @staticmethod
    def prelucrare_suprafata(str): 
        m1 = re.search(r'(\d+)\s+(\w+)', str)
        m2 = re.search(r'(\d+)', str)

        if m1:
            if m1.group(2).lower() in ["m2", "mp", "metri patrati", "metri pătrați"]:
                return int(float(m1.group(1)))
            elif m1.group(2).lower() == 'ar':
                return int(float(m1.group(1)) * 100)
            elif m1.group(2).lower() == 'ha':
                return int(float(m1.group(1)) * 10000)
            elif m1.group(2).lower() in ['km2', 'kmp']:
                return int(float(m1.group(1)) * 1000000)
            else:
                raise Exception("Tip de suprafata necunoscut")

    @staticmethod
    def get_price_per_m2_aux(judet):
        judet = DocumentUploadToDatabase.remove_diacritics(judet)
        if judet.lower() not in AveragePrices.indice_teren.keys():
            return 1
        else:
            return AveragePrices.indice_teren[judet.lower()]

    @staticmethod
    def prelucrare_mijl_transport(marca):
        if marca.lower() in AveragePrices.car_brands.keys():
            return AveragePrices.car_brands[marca.lower()]
        else:
            return 30000

    @staticmethod
    def insert_teren_cladire(table, tip, doc_id, an):
        first_item = table.iloc[0, 0]
        has_letters = re.search(r'[A-Za-z]', first_item)
        if has_letters is None:
            return 0 
        table = table.replace(["\n"], [" "], regex=True)
        locatii = table.iloc[:, 0].tolist()
        
        locatii = list(map(DocumentUploadToDatabase.extract_fields, locatii))
        locatii = {key: [d[key] for d in locatii] for key in locatii[0]}
        
        table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
        table.insert(1, "tip", [tip for i in range (len(table.index))], True)
        table.insert(2, "tara", locatii["Tara"], True)
        table.insert(3, "judet", locatii["Judet"], True)
        table.insert(4, "localitate", locatii["Localitate"], True)
        table = table.drop(table.columns[5], axis=1)

        suprafete = list(map(DocumentUploadToDatabase.prelucrare_suprafata, table.iloc[:, 7].tolist()))
        table.insert(7, "suprafata", suprafete, True)
        table = table.drop(table.columns[8], axis=1)

        if tip == 0:
            list_prices_m2_aux = list(map(DocumentUploadToDatabase.get_price_per_m2_aux, locatii["Judet"]))
            print(list_prices_m2_aux)
            print(suprafete)
            print(len(table.index))
            final_prices = []
            for i in range(len(table.index)):
                if("intravilan" in table.iloc[i, 5].lower()):
                    final_prices.append(int(33 * list_prices_m2_aux[i] * suprafete[i]))
                else:
                    final_prices.append(int(list_prices_m2_aux[i] * suprafete[i]))
            table['val_estimata'] = final_prices

            table.rename(columns={'Categoria*': 'categorie', 'Anul\ndobândirii': 'an_dobandire',
                            'Cota-\nparte': 'cota_parte', 'Modul de\ndobândire': 'mod_dobandire',
                            'Titularul1)': 'proprietar'}, inplace=True)
        else:
            final_prices = []
            for cladire in suprafete:
                if an < 2012:
                    final_prices.append(cladire * AveragePrices.indice_imobiliar['2012'])
                elif an > 2024:
                    final_prices.append(cladire * AveragePrices.indice_imobiliar['2024'])
                else:
                    final_prices.append(cladire * AveragePrices.indice_imobiliar[str(an)])
            table['val_estimata'] = final_prices

            table.rename(columns={'Categoria*': 'categorie', 'Anul\ndobândirii': 'an_dobandire',
                            'Cota-\nparte': 'cota_parte', 'Modul de\ndobândire': 'mod_dobandire',
                            'Titularul2)': 'proprietar'}, inplace=True)

        table.to_sql('teren_cladire', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        return sum(final_prices)

    @staticmethod
    def insert_mijloc_transport(table, doc_id):
        first_item = table.iloc[0, 0]
        has_letters = re.search(r'[A-Za-z]', first_item)
        if has_letters is None:
            return 0
        table = table.replace("\n", " ", regex=True)
        table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)

        final_prices = list(map(DocumentUploadToDatabase.prelucrare_mijl_transport, table.iloc[:, 2]))
        table['val_estimata'] = final_prices

        table.rename(columns={'Natura': 'natura', 'Marca': 'marca',
                            'Nr. de bucăţi': 'nr_bucati', 
                            'Anul de fabricaţie': 'an_fabricatie', 
                            'Modul de\ndobândire': 'mod_dobandire'}, inplace=True)
        
        table.to_sql('mijloc_transport', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        return sum(final_prices)

    @staticmethod 
    def insert_bun_cultural(table, doc_id):
        first_item = table.iloc[0, 0]
        has_letters = re.search(r'[A-Za-z]', first_item)
        if has_letters is None:
            return 0
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

        table.to_sql('bun_cultural', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        
        final_prices = 0
        for i in range(len(lista_valoare_nr)):
            if 'ron' in lista_valoare_valuta[i].lower():
                final_prices += int (lista_valoare_nr[i]/5)
            else:
                final_prices += lista_valoare_nr[i]
        
        return final_prices

    @staticmethod
    def insert_bun_instrainat(table, doc_id):
        first_item = table.iloc[0, 0]
        has_letters = re.search(r'[A-Za-z]', first_item)
        if has_letters is None:
            return 0
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
        table.to_sql('bun_instrainat', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        #return table

    @staticmethod
    def insert_activa_financiara_indirecta(table, doc_id):
        first_item = table.iloc[0, 0]
        has_letters = re.search(r'[A-Za-z]', first_item)
        if has_letters is None:
            return 0
        table = table.replace(["\n", None], [" ", "-"], regex=True)
        table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)


        table.rename(columns={'Instituţia care\nadministrează\nşi adresa acesteia': 'institutie', "Tipul*": 'tip', 
                    'Valuta': 'valuta', 'Deschis în\nanul': 'an', 'Sold/valoare la zi': 'sold'}, inplace=True)
        table.to_sql('activa_financiara_indirecta', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)

        final_prices = 0
        sold = list(map(lambda x : int(float(x)), table['sold']))
        valuta = table['valuta']
        
        for i in range(len(valuta)):
            if 'ron' in valuta[i].lower():
                final_prices += int (sold[i]/5)
            else:
                final_prices += sold[i]
        
        return final_prices
        
    @staticmethod
    def insert_activa_financiara_directa(table, doc_id):
        first_item = table.iloc[0, 0]
        has_letters = re.search(r'[A-Za-z]', first_item)
        if has_letters is None:
            return 0
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
        table.to_sql('activa_financiara_directa', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        
        final_prices = 0
        for i in range(len(lista_valoare_nr)):
            if 'ron' in lista_valoare_valuta[i].lower():
                final_prices += int (lista_valoare_nr[i]/5)
            else:
                final_prices += lista_valoare_nr[i]
        
        return final_prices

    @staticmethod
    def insert_alta_activa_financiara(table, doc_id):
        first_item = table.iloc[0, 0]
        has_letters = re.search(r'[A-Za-z]', first_item)
        if has_letters is None:
            return 0
        table = table.replace(["\n", None], [" ", "-"], regex=True)
        table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
        
        table.rename(columns={'Descriere': 'descriere', "Valoare": 'valoare', 'Valuta': 'valuta'}, inplace=True)
        table.to_sql('alta_activa_financiara', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        
        final_prices = 0
        sold = list(map(lambda x : int(float(x)), table['valoare']))
        valuta = table['valuta']
        
        for i in range(len(valuta)):
            if 'ron' in valuta[i].lower():
                final_prices += int (sold[i]/5)
            else:
                final_prices += sold[i]
        
        return final_prices

    @staticmethod
    def insert_datorie(table, doc_id):
        first_item = table.iloc[0, 0]
        has_letters = re.search(r'[A-Za-z]', first_item)
        if has_letters is None:
            return 0
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
        table.to_sql('datorie', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        
        final_prices = 0

        for i in range(len(lista_valoare_nr)):
            if 'ron' in lista_valoare_valuta[i].lower():
                final_prices += int (lista_valoare_nr[i]/5)
            else:
                final_prices += lista_valoare_nr[i]
        
        return final_prices

    @staticmethod
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
        new_table_df.to_sql('ajutor', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        return new_table_df
                
    @staticmethod            
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
        new_table_df.to_sql('venit', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        return new_table_df

    @staticmethod    
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
        table.to_sql('membru_non_stat', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        
        return table

    @staticmethod
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
        table.to_sql('membru_stat', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        return table
        
    @staticmethod
    def insert_membru_sindicat(table, doc_id):
        first_item = table.iloc[0, 0]
        has_letters = re.search(r'[A-Za-z]', first_item)
        if has_letters is None:
            return
        table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)

        table.rename(columns={'3. Calitatea de membru în cadrul asociaţiilor profesionale şi/sau sindicale': 'functie'}, inplace=True)
        table.to_sql('membru_sindicat', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        return table

    @staticmethod
    def insert_membru_partid(table, doc_id):
        first_item = table.iloc[0, 0]
        has_letters = re.search(r'[A-Za-z]', first_item)
        if has_letters is None:
            return
        table.insert(0, "doc_id", [doc_id for i in range (len(table.index))], True)
        
        table.rename(columns={'4. Calitatea de membru în organele de conducere, administrare şi control, retribuite sau\nneretribuite, deţinute în cadrul partidelor politice, funcţia deţinută şi denumirea partidului\npolitic': 'functie'}, inplace=True)
        table.to_sql('membru_partid', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        return table

    @staticmethod    
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
        new_table_df.to_sql('contract', con=DocumentUploadToDatabase.engine, if_exists='append', index=False)
        return new_table_df

    ######PENTRU TESTARE######
    # path = "avere_ciolacu.pdf"
    # doc = fitz.open(path)

    # tabele = table_merging(doc, 1)
    # table = tabele[4]
    # display(table)
    # table = insert_bun_instrainat(table, 1)

    # display(table)
    # #with engine.connect() as connection:

    # #rez = insert_mijloc_transport(table, 1)
    # #print(rez)
    # #connection.commit()
    # doc.close()
    ######PENTRU TESTARE######

    @staticmethod
    def get_current_ids(connection):
        titular_id = connection.execute(text(f"""select * from titular order by titular_id desc;""")).first()
        if titular_id is None:
            titular_id = 1
        else:
            titular_id = titular_id.titular_id + 1

        doc_id = connection.execute(text(f"""select * from document order by doc_id desc;""")).first()
        if doc_id is None:
            doc_id = 1
        else:
            doc_id = doc_id.doc_id + 1

        return titular_id, doc_id

    @staticmethod
    def database_insertion(path, connection, current_titular_id, current_doc_id):
        doc = fitz.open(path)
        try:
            doc_type = categorize_pdf(doc)
            if doc_type != 0:
                tables_df = DocumentUploadToDatabase.table_merging(doc, doc_type)
            if doc_type == 1:
                if len(tables_df) != 12:
                    raise Exception("Eroare la alipirea tabelelor de avere")              
            if doc_type == 2:
                if len(tables_df) != 6:
                    raise Exception("Eroare la alipirea tabelelor de avere") 
                    
        except Exception as e:
            print(path)
            logging.error(traceback.format_exc() + f"FILEPATH: {path}")
            return (3, f"EROARE, fisier {path}")

        try: 

            if (doc_type == 1):
                page = doc[0]
                nume, init_tata, prenume, functie, institutie = re.findall(r'(?:Subsemnatul|Subsemnata)\s([a-zA-ZĂăÎîșȘțȚâÂ\-]+)\s([a-zA-ZĂăÎîșȘțȚâÂ\.\-]+)\s([a-zA-ZĂăÎîșȘțȚâÂ\- ]+),\savând\sfunc[ţț]ia\sde\s([\d\.a-zA-ZĂăÎîșȘțȚâÂ\- \n]+)\sla\s([\da-zA-ZĂăÎîșȘțȚâÂ\- \n]+), CNP', page.get_text()[:300])[0]
                nume = nume.replace('\n', ' ')
                init_tata = init_tata.replace('\n', ' ')
                prenume = prenume.replace('\n', ' ')
                functie = functie.replace('\n', ' ')
                institutie = institutie.replace('\n', ' ')

                raw_date = tables_df[11].iloc[0, 0]
                format_date = f'{raw_date[6:]}-{raw_date[3:5]}-{raw_date[:2]}'
                an = int(raw_date[6:])
                
                existing_titular = connection.execute(text(f"""select * from titular where nume = '{nume}' and init_tata = '{init_tata}'
                                                and prenume = '{prenume}';"""))
                if existing_titular.rowcount > 0:
                    existing_titular = existing_titular.first()
                    current_titular_id = existing_titular.titular_id
                    an_ultima_declaratie = existing_titular.an_ultima_declaratie
                else:
                    connection.execute(text(f"INSERT INTO TITULAR VALUES('{current_titular_id}', '{nume}', '{init_tata}', '{prenume}', '{functie}', '{institutie}', -1, 1901);"))
                    an_ultima_declaratie = 1901
                

                existing_document = connection.execute(text(f"""select * from document where titular_id = '{current_titular_id}' and data = '{format_date}' and tip = '{doc_type}';"""))

                if existing_document.rowcount > 0:
                    return (doc_type, f"AVERE, DUPLICAT, {nume} {init_tata} {prenume}")
                else:
                    connection.execute(text(f"INSERT INTO DOCUMENT VALUES('{current_doc_id}', '{current_titular_id}', '{format_date}', '{doc_type}', 0);"))

                
                connection.commit() 

                total_doc = 0
                total_doc += DocumentUploadToDatabase.insert_teren_cladire(tables_df[0], 0, current_doc_id, an)
                total_doc += DocumentUploadToDatabase.insert_teren_cladire(tables_df[1], 1, current_doc_id, an)
                total_doc += DocumentUploadToDatabase.insert_mijloc_transport(tables_df[2], current_doc_id)
                total_doc += DocumentUploadToDatabase.insert_bun_cultural(tables_df[3], current_doc_id)
                DocumentUploadToDatabase.insert_bun_instrainat(tables_df[4], current_doc_id)
                total_doc += DocumentUploadToDatabase.insert_activa_financiara_indirecta(tables_df[5], current_doc_id)
                total_doc += DocumentUploadToDatabase.insert_activa_financiara_directa(tables_df[6], current_doc_id)
                total_doc += DocumentUploadToDatabase.insert_alta_activa_financiara(tables_df[7], current_doc_id)
                total_doc -= DocumentUploadToDatabase.insert_datorie(tables_df[8], current_doc_id)
                DocumentUploadToDatabase.insert_ajutor(tables_df[9], current_doc_id)
                DocumentUploadToDatabase.insert_venit(tables_df[10], current_doc_id)

                connection.execute(text(f"UPDATE DOCUMENT SET avere_doc = '{total_doc}' where doc_id = '{current_doc_id}';"))
                if (an > an_ultima_declaratie):
                    connection.execute(text(f"UPDATE TITULAR SET avere_personala = '{total_doc}', an_ultima_declaratie = '{an}' where titular_id = '{current_titular_id}';"))
                connection.commit() 

            elif (doc_type == 2):
                
                page = doc[0]
                nume, init_tata, prenume, functie, institutie = re.findall(r'(?:Subsemnatul|Subsemnata)\s([a-zA-ZĂăÎîșȘțȚâÂ\-]+)\s([a-zA-ZĂăÎîșȘțȚâÂ\.\-]+)\s([a-zA-ZĂăÎîșȘțȚâÂ\- ]+),\savând\sfunc[ţț]ia\sde\s([\d\.a-zA-ZĂăÎîșȘțȚâÂ\- \n]+)\sla\s([\da-zA-ZĂăÎîșȘțȚâÂ\- \n]+), CNP', page.get_text()[:300])[0]
                
                nume = nume.replace('\n', ' ')
                init_tata = init_tata.replace('\n', ' ')
                prenume = prenume.replace('\n', ' ')
                functie = functie.replace('\n', ' ')
                institutie = institutie.replace('\n', ' ')
                
                raw_date = tables_df[5].iloc[0, 0]
                format_date = f'{raw_date[6:]}-{raw_date[3:5]}-{raw_date[:2]}'

                existing_titular = connection.execute(text(f"""select * from titular where nume = '{nume}' and init_tata = '{init_tata}'
                                                and prenume = '{prenume}';"""))
                if existing_titular.rowcount > 0:
                    current_titular_id = existing_titular.first().titular_id
                else:
                    connection.execute(text(f"INSERT INTO TITULAR VALUES('{current_titular_id}', '{nume}', '{init_tata}', '{prenume}', '{functie}', '{institutie}', -1, 1901);"))
                
                existing_document = connection.execute(text(f"""select * from document where titular_id = '{current_titular_id}' and data = '{format_date}' and tip = '{doc_type}';"""))

                if existing_document.rowcount > 0:
                    return (doc_type, f"INTERESE, DUPLICAT, {nume} {init_tata} {prenume}")
                else:
                    connection.execute(text(f"INSERT INTO DOCUMENT VALUES('{current_doc_id}', '{current_titular_id}', '{format_date}', '{doc_type}', 0);"))

                connection.commit() 
                
                DocumentUploadToDatabase.insert_membru_non_stat(tables_df[0].replace("\n", " ", regex=True), current_doc_id)
                DocumentUploadToDatabase.insert_membru_stat(tables_df[1].replace("\n", " ", regex=True), current_doc_id)
                DocumentUploadToDatabase.insert_membru_sindicat(tables_df[2].replace("\n", " ", regex=True), current_doc_id)
                DocumentUploadToDatabase.insert_membru_partid(tables_df[3].replace("\n", " ", regex=True), current_doc_id)
                DocumentUploadToDatabase.insert_contract(tables_df[4].replace("\n", " ", regex=True), current_doc_id)

            doc.close()

            if (doc_type == 0):
                return (0, "")
            elif doc_type == 1:
                return (1, f"AVERE, SUCCES, {nume} {init_tata} {prenume}")
            elif doc_type == 2:
                return (2, f"INTERESE, SUCCES, {nume} {init_tata} {prenume}")

        except Exception as e:
            print(path)
            logging.error(traceback.format_exc() + f"FILEPATH: {path}")
            return (3, f"EROARE, fisier {path}")
    ######PENTRU TESTARE######
    # with engine.connect() as connection:
    #     database_insertion('interese_ciolacu.pdf', connection)
    ######PENTRU TESTARE######
