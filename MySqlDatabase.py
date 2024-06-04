#!/usr/bin/env python
# coding: utf-8

# In[1]:


import mysql.connector
import keyring


# In[41]:


db = mysql.connector.connect(
    host="localhost",
    user="stefan",
    passwd="Gigelfrone112!!",
    auth_plugin = 'mysql_native_password',
    database = "declaratiiavere",
)

mycursor = db.cursor()


# In[ ]:


mycursor.execute("SHOW tables;")


# In[ ]:


for result in mycursor:
    print(result)


# In[49]:


mycursor.execute("DROP TABLE TEREN_CLADIRE;")
mycursor.execute("DROP TABLE MIJLOC_TRANSPORT;")
mycursor.execute("DROP TABLE BUN_CULTURAL;")
mycursor.execute("DROP TABLE BUN_INSTRAINAT;")
mycursor.execute("DROP TABLE ACTIVA_FINANCIARA_INDIRECTA;")
mycursor.execute("DROP TABLE ACTIVA_FINANCIARA_DIRECTA;")
mycursor.execute("DROP TABLE ALTA_ACTIVA_FINANCIARA")
mycursor.execute("DROP TABLE AJUTOR;")
mycursor.execute("DROP TABLE MEMBRU_STAT;")
mycursor.execute("DROP TABLE MEMBRU_NON_STAT;")
mycursor.execute("DROP TABLE MEMBRU_PARTID;")
mycursor.execute("DROP TABLE MEMBRU_SINDICAT;")
mycursor.execute("DROP TABLE VENIT;")
mycursor.execute("DROP TABLE CONTRACT;")
mycursor.execute("DROP TABLE DATORIE;")
mycursor.execute("DROP TABLE DOCUMENT;")
mycursor.execute("DROP TABLE TITULAR;")






# In[50]:


mycursor.execute("""CREATE TABLE TITULAR(
                titular_id INT PRIMARY KEY,
                nume VARCHAR(50),
                init_tata VARCHAR(8),
                prenume VARCHAR(50),
                functie VARCHAR(80),
                institutie VARCHAR(80)
                );""")

mycursor.execute("""CREATE TABLE DOCUMENT(
                doc_id INT PRIMARY KEY,
                titular_id INT,
                data DATE,
                tip INT,
                FOREIGN KEY (titular_id) REFERENCES TITULAR(titular_id)
                );""")

mycursor.execute("""CREATE TABLE TEREN_CLADIRE(
                teren_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                tip INT,
                tara VARCHAR(40),
                judet VARCHAR(40),
                localitate VARCHAR(40),
                categorie VARCHAR(40),
                an_dobandire YEAR,
                suprafata INT,
                cota_parte VARCHAR(40),
                mod_dobandire VARCHAR(70),
                proprietar VARCHAR (150),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE MIJLOC_TRANSPORT(
                mijloc_transport_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                natura VARCHAR(50),
                marca VARCHAR(50),
                nr_bucati INT,
                an_fabricatie YEAR,
                mod_dobandire VARCHAR(70),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE BUN_CULTURAL(
                bun_cultural_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                descriere_sumara VARCHAR(90),
                an_dobandire YEAR,
                valoare_nr INT,
                valoare_valuta VARCHAR(15),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE BUN_INSTRAINAT(
                bun_instrainat_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                natura VARCHAR(50),
                data DATE,
                persoana_catre VARCHAR(70),
                forma VARCHAR(40),
                valoare_nr INT,
                valoare_valuta VARCHAR(10),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE ACTIVA_FINANCIARA_DIRECTA(
                fin_direct_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                emitent VARCHAR(70),
                tip VARCHAR(130),
                nr_sau_cota INT,
                valoare_nr INT,
                valoare_valuta VARCHAR(10),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE ACTIVA_FINANCIARA_INDIRECTA(
                fin_indirect_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                institutie VARCHAR(100),
                tip VARCHAR(130),
                valuta VARCHAR(10),
                an YEAR,
                sold INT,
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE ALTA_ACTIVA_FINANCIARA(
                fin_alte_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                descriere VARCHAR(80),
                valoare INT,
                valuta VARCHAR(10),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")


mycursor.execute("""CREATE TABLE DATORIE(
                datorie_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                creditor VARCHAR(70),
                an_creata YEAR,
                an_scadenta YEAR,
                valoare_nr INT,
                valoare_valuta VARCHAR(10),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE AJUTOR(
                ajutor_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                realizator_tip INT,
                realizator_nume VARCHAR(2570),
                sursa VARCHAR(120),
                serviciu_obiect VARCHAR(60),
                venit_nr INT,
                venit_valuta VARCHAR(10),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE VENIT(
                venit_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                venit_tip VARCHAR(100),
                realizator_tip INT,
                realizator_nume VARCHAR(80),
                sursa VARCHAR(100),
                serviciu_obiect VARCHAR(70),
                venit_nr INT,
                venit_valuta VARCHAR(10),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")


mycursor.execute("""CREATE TABLE MEMBRU_NON_STAT(
                membru_non_stat_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                unitate VARCHAR(120),
                calitate VARCHAR(40),
                nr_parti_sociale INT,
                valoare_nr INT,
                valoare_valuta VARCHAR(10),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE MEMBRU_STAT(
                membru_stat_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                unitate VARCHAR(120),
                calitate VARCHAR(40),
                valoare_nr INT,
                valoare_valuta VARCHAR(10),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE MEMBRU_SINDICAT(
                membru_sindicat_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                functie VARCHAR(100),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE MEMBRU_PARTID(
                membru_partid_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                functie VARCHAR(100),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")

mycursor.execute("""CREATE TABLE CONTRACT(
                contract_id INT PRIMARY KEY AUTO_INCREMENT,
                doc_id INT,
                tip_beneficiar INT,
                nume_beneficiar VARCHAR(60),
                institutie_contractanta VARCHAR(100),
                procedura VARCHAR(50),
                tip_contract VARCHAR(40),
                data_incheiere YEAR,
                durata VARCHAR(30),
                valoare_nr INT,
                valoare_valuta VARCHAR(10),
                FOREIGN KEY (doc_id) REFERENCES DOCUMENT(doc_id)
                );""")


# In[3]:


mycursor = db.cursor()


# In[24]:


mycursor.execute("""SELECT * from TITULAR;""")
for result in mycursor:
    print(result)


# In[25]:


mycursor.execute("""SELECT * from DOCUMENT;""")
for result in mycursor:
    print(result)


# In[26]:


mycursor.execute("""SELECT * from TEREN_CLADIRE;""")
for result in mycursor:
    print(result)


# In[27]:


mycursor.execute("""SELECT * from MIJLOC_TRANSPORT;""")
for result in mycursor:
    print(result)


# In[28]:


mycursor.execute("""SELECT * from BUN_CULTURAL;""")
for result in mycursor:
    print(result)


# In[29]:


mycursor.execute("""SELECT * from BUN_INSTRAINAT;""")
for result in mycursor:
    print(result)


# In[30]:


mycursor.execute("""SELECT * from ACTIVA_FINANCIARA_INDIRECTA;""")
for result in mycursor:
    print(result)


# In[31]:


mycursor.execute("""SELECT * from ACTIVA_FINANCIARA_DIRECTA;""")
for result in mycursor:
    print(result)


# In[32]:


mycursor.execute("""SELECT * from ALTA_ACTIVA_FINANCIARA;""")
for result in mycursor:
    print(result)


# In[33]:


mycursor.execute("""SELECT * from DATORIE;""")
for result in mycursor:
    print(result)


# In[34]:


mycursor.execute("""SELECT * from AJUTOR;""")
for result in mycursor:
    print(result)


# In[35]:


mycursor.execute("""SELECT * from VENIT;""")
for result in mycursor:
    print(result)


# In[42]:


mycursor.execute("""SELECT * from MEMBRU_STAT;""")
for result in mycursor:
    print(result)


# In[43]:


mycursor.execute("""SELECT * from MEMBRU_NON_STAT;""")
for result in mycursor:
    print(result)


# In[44]:


mycursor.execute("""SELECT * from MEMBRU_PARTID;""")
for result in mycursor:
    print(result)


# In[45]:


mycursor.execute("""SELECT * from MEMBRU_SINDICAT;""")
for result in mycursor:
    print(result)


# In[46]:


mycursor.execute("""SELECT * from CONTRACT;""")
for result in mycursor:
    print(result)


# In[ ]:




