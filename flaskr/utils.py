from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
import re
from selenium.webdriver.common.action_chains import ActionChains
from random import random, randint
import pdfplumber 
import translators as ts
from pymongo import MongoClient
from datetime import datetime


def clean_string1(input_string):
    # Remove line breaks and leading/trailing spaces
    cleaned_string = input_string.replace('\n', '').strip()
    # Remove repeated words
    cleaned_string = re.sub(r'\b(\w+)\b\s+\1', r'\1', cleaned_string)
    return cleaned_string

def remove_second_half(input_string):
    #if input_string=='Licences et certificationsLicences et certifications':
     #   removed_string ='Licences et certifications'
    #else:
    half_length = len(input_string) // 2
    removed_string = input_string[:half_length]
    return removed_string

def clean_string2(input_string):
    # Remove line breaks and leading/trailing spaces
    cleaned_string = input_string.replace('\n', '').strip()
    # Remove repeated words using regular expression
    cleaned_string = re.sub(r'\b(\w+)\b(?=.*\b\1\b)', '', cleaned_string)
    # Remove exactly the second half of the string
    cleaned_string = remove_second_half(cleaned_string)
    #if cleaned_string=='Licences et certificationsL':
     #   cleaned_string ='Licences et certifications'
    return cleaned_string

def title_function(driver):
    Title = list()
    title=[]
    title_elements = driver.find_elements(By.TAG_NAME, "h2")
    titles=['Expérience', 'Formation', 'Licences et certifications','Projets', 'Bénévolat', 'Compétences','Résultats ’examens', 'Langues']

    if title_elements[1].get_attribute("textContent")=='Vous n’avez pas accès à ce profil':
        return 0
    else:
        for t in title_elements:    
            ti = t.get_attribute("textContent")
            ti=clean_string2(ti)
            if ti=='Licences  certificationsL':
                ti='Licences et certifications'
            title.append(ti)

        for t in title :
            if t in titles :
                Title.append(t)
        #print(len(Title))
        return Title
    
def elements_function(driver):
    elements=[]
    
    data_elements = driver.find_elements(By.XPATH, "(//section/div[@class='pvs-list__outer-container'])")

    for e in data_elements:    
        el = e.get_attribute("textContent")
        elements.append(el)
        #print(el)
    
    elements.pop(-1)
    elements.pop(-1)

    print("----------------------")
    print(len(elements))
    print("----------------------")

    return elements

def extra_click(cclik):
    click_list=[]
    for e in cclik:    
        el = e.get_attribute("textContent")
        el=clean_string1(el)
        click_list.append(el)
    elements_to_remove = ['Afficher toutes les entreprises','Afficher le projet', 'Afficher toutes les newsletters',
                          'Afficher toutes les Top Voices', 'Afficher tous les groupes', 'Afficher toutes les écoles',
                          'Afficher l’identifiant', 'Afficher la publication', 'Tout afficher', 'Voir tous les détails (4)', 'Voir tous les détails (6)',
                          'Voir tous les détails (5)','Afficher les vérifications', 'Afficher tous les posts' ]

    for i in range(len(click_list)-1, -1, -1):
        if click_list[i] in elements_to_remove:
            click_list.pop(i)
            cclik.pop(i)
   
    print(click_list)
    return cclik

def clean_data(cell_data):
    if cell_data is not None:
        return cell_data.replace(',', '')
    else:
        return ''

def create_dataframe(titles,element,separator=','):
    max_length = max(len(row) for row in element)
    data_dict = {titles[i]: [separator.join(row[i]) if i < len(row) else None for row in element] for i in range(len(titles))}
    # Fill the DataFrame with lists of elements and convert to a DataFrame
    df = pd.DataFrame({key: pd.Series(value) for key, value in data_dict.items()})
    df = df.applymap(clean_data)
    return df

def pdf_extractor(feed,key_word):
    text = ""
    with pdfplumber.open(feed) as pdf:
        pages = pdf.pages
        for page in pages:
            text+=page.extract_text(x_tolerance=2)
            
    pattern = r'-\s*m\s*o\s*c\s*e\s*rfo\s*S\s*1 ©\s*\d+'
    pdf_text = re.sub(pattern, '', text)
    
    lines = pdf_text.splitlines()
    Titre = lines[0]
    
    titles = ['Mission', 'Activités', 'Compétences et qualités requises', 'Compétences techniques :', 'Outils :', 'Qualités requises :']
    # Créez une liste pour stocker le texte entre chaque titre
    elements = []
    # Parcourez les titres
    for i in range(len(titles)-1):
        start_index = pdf_text.find(titles[i])
        end_index = pdf_text.find(titles[i+1])
        if start_index != -1 and end_index != -1:
            elements.append(pdf_text[start_index+len(titles[i]):end_index])
        elif start_index != -1 and end_index == -1:
            elements.append(pdf_text[start_index+len(titles[i]):])
        else:
            elements.append("")
    # Ajoutez le texte après le dernier titre
    last_title = titles[-1]
    last_title_index = pdf_text.find(last_title)
    if last_title_index != -1:
        elements.append(pdf_text[last_title_index+len(last_title):])
    else:
        elements.append("")

    titles.insert(0,'Titre')
    elements.insert(0,Titre)
    
    for i in range(len(titles)):
        elements[i]=elements[i].replace("\n", " ")
               
    data = {title: [element] for title, element in zip(titles, elements)}
    df = pd.DataFrame(data)
    #df.to_excel("C:/Users/r.rabah/Desktop/front_project - integration/data/pdf_extractor.xlsx", index=False)
     # Etablir la connexion a MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['userdbtest']  # Remplacez par le nom de votre base de donnees
    collection2 = db["pdf extractor : " + key_word + " " + str(datetime.today())[:-7]]   # Remplacez par le nom de votre collection
    # Convertissez le DataFrame en liste de dictionnaires
    records2 =  df.to_dict(orient='records')
    # Inserez les enregistrements dans la collection
    collection2.insert_many(records2)
    client.close()
    return df

def nettoyage(ch) : # ATTENTION : on suppose que les doublons des chaines ne sont pas efface
    CH = ""
    sh=""
    nbr_esp = 1
    nbr_esp_max = 3 # le nombre des espace que vous voulez le laisser, dans ce cas : "             " ==> "   "
    coef_nbr_esp_max = 2**nbr_esp_max
    ch = str(ch).replace("m’a permis de trouver cet emploiLinkedIn m’a permis de trouver cet emploi","")
    for cara in ch :
        if cara == " " :
            if nbr_esp < coef_nbr_esp_max :
                nbr_esp = nbr_esp<<1
                sh += cara
        else :
            nbr_esp  = 1
            sh += cara
    
    chs = sh.split('   ')
    for cc in chs :
        mid = len(cc)>>1 # division sur deux pour avoir le milieu de la chaine.
        ind = 0
        verif = 1
        while(ind<mid):
            if cc[mid + ind] != cc[ind]:
                verif = 0
                break
            ind += 1
        if verif :
            CH += cc[:mid] + "   "
        else : 
            CH += cc + "   "
    if len(CH)>3 and (CH[-1]==' ' and (CH[-2]==' ' and CH[-3]==' ')) :
        CH = CH[:-3]
    return CH       

def verification(data): 
    cities=['tunisia','tunisie','ariana','béja','beja','ben arous' , 'bizerte','gabès','gabes','gafsa','jendouba','kairouan','kasserine','kébili','kebili','kef','mahdia','manouba','médenine','medenine','monastie','nabeul','sfax','sidi bouzid','zaghouan','tunis','tozeur','tataouine','sousse','siliana']
    for city in cities:
        if data.lower().find(city)!=-1:
            return 1
    return 0       

def remove_duplicates(input_list):
    return list(set(input_list))

def is_city(ch):  
    cities  =['tunisie','lac 1','lac 2','kélibia','ariana','béja','beja','ben arous' , 'bizerte','gabès','gabes','gafsa','jendouba','kairouan','kasserine','kébili','kebili','kef','mahdia','manouba','médenine','medenine','monastie','nabeul','sfax','sidi bouzid','zaghouan','tunis','tozeur','tataouine','sousse','siliana']
    for city in cities:
        if ch.lower().find(city) != -1:
            return 1
    return 0

def is_date(ch):
    duree = ['mois','an','ans']
    mois = ['aujourd’hui',
            'janv.','févr.','mars.','avr.','mai.','juin.','juil.','août.','sept.','oct.','nov.','déc.',
            'janv','févr','mars','avr','mai','juin','juil','août','sept','oct','nov','déc']
    d = 0
    m = 0
    for w in ch.split():
        if d == 0 :
            if w in mois :
                d = 1
        if m == 0 :
            if w in duree :
                m = 1
        if d and m :
            return 1
    return 0

def extraire_descriptionsExpérience(ch) : 
    CH = ""

    chs = ch.split('   ')
    
    for i in range(len(chs)-1) :
        if is_city(chs[i]) :
            cc = chs[i+1]
            if len(cc)>30 and (1-is_date(cc)) and cc.count("Temps plein") == 0 and cc[:13]!="Compétences :" and cc[:31]!="m’a permis de trouver cet emploi":  
                CH += cc+".   "
                
    if len(CH)>3 and (CH[-1]==' ' and (CH[-2]==' ' and CH[-3]==' ')) :
        CH = CH[:-3]
    return CH          

def extract_durations(text):
    pattern = r'\b(\d+)\s+(mois|an(?:s)?)\b'
    durations = re.findall(pattern, text, re.IGNORECASE)
    return durations

def nb_certif(df):
    for i in range(df.shape[0]):
        text = df.iloc[i, 2]
        occurrences = text.count("Émise le") + text.count("Date de délivrance :")    
    return occurrences
