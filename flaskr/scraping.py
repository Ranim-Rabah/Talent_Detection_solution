from math import e
from flask import Flask, request, render_template, jsonify, request,Blueprint
import utils
from utils import *
from _thread import start_new_thread
from dateparser.search import search_dates
import translators as ts
import spacy
from spacy.matcher import PhraseMatcher
# load default skills data base
from skillNer.general_params import SKILL_DB
# import skill extractor
from skillNer.skill_extractor_class import SkillExtractor
from pymongo import MongoClient
from datetime import datetime

import numpy as np
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords 
from string import punctuation
from nltk.stem import WordNetLemmatizer
import pandas as pd
import nltk

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from string import punctuation
from scipy.sparse import csr_matrix, hstack

import pymongo

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

scraping = Blueprint('scraping', __name__)


progress_scrapping = 0 
progress_data_cleaning = 0
progress_processing = 0
name_db = ""

def progression(df2, df_fdp, key_word):
    
    global progress_processing
    
    shape=df2.shape
    shape_df_fdp=df_fdp.shape
    df3 = df2.copy()
    tokenized_scraping=[]
    progress_processing = 0.75
    for i in range(shape[0]):
        text_to_tokenize = str(df2.at[i, "Expérience_ang"])
        text_to_tokenize+=str(df2.at[i, "Durée d'expérience"])
        word_sent = word_tokenize(text_to_tokenize.lower().replace("   ", " "))
        _stopwords = set(stopwords.words('english') + list(punctuation)+list("·")+list('–')+list('--')+list('●')+list('•')+list('’'))
        word_sent=[word for word in word_sent if word not in _stopwords]
        lemmatizer = WordNetLemmatizer()
        word_sent= [lemmatizer.lemmatize(word) for word in word_sent]
        tokenized_scraping.append(word_sent)
        progress_processing = round(5 / shape[0] + progress_processing, 2)
    
    df3['NLP'] = tokenized_scraping
    progress_processing = 14.85
    chaines =[]
    for i in range(shape[0]):
        separateur = " "
        chaine_extractor = separateur.join(tokenized_scraping[i])
        chaines.append(chaine_extractor)
        progress_processing = round(5 / shape[0] + progress_processing, 2)
    
    df3['NLP Chaine'] = chaines
    progress_processing = 28.92
    # pdf extractor dataset

    tokenized_extractor=[]
    row_tokens = []  # Create a list to store tokens for each row
    for j in range(7, shape_df_fdp[1]):
        text_to_tokenize = str(df_fdp.iloc[0, j])
        word_sent = word_tokenize(text_to_tokenize.lower().replace("   ", " "))
        _stopwords = set(stopwords.words('english') + list(punctuation) + list("·") + list('–') + list('--') + list('●') + list('•') + list('’')+ list('➢'))
        word_sent = [word for word in word_sent if word not in _stopwords]
        lemmatizer = WordNetLemmatizer()
        word_sent = [lemmatizer.lemmatize(word) for word in word_sent]
        row_tokens.extend(word_sent)  # Extend the list for each row
        progress_processing = round(20 / (shape_df_fdp[1] - 7) + progress_processing, 2)
    tokenized_extractor.append(row_tokens)

    df_fdp['NLP'] = tokenized_extractor
    separateur = " "

    chaine_extractor = separateur.join(tokenized_extractor[0])
    df_fdp['NLP Chaine'] = chaine_extractor
    progress_processing = 44

    # TF-IDF

    vectorizer = TfidfVectorizer()
    progress_processing = 44.71

    # scraping dataset

    X = vectorizer.fit_transform(chaines)
    list_extractor=[chaine_extractor]
    Y = vectorizer.fit_transform(list_extractor)
    progress_processing = 44.27

    # cosine similarity

    # Pad the document vector with zeros to match the dimensions of tfidf_extractor
    if X.shape[1] < Y.shape[1]:
        num_zeros_to_add = Y.shape[1]-X.shape[1]
        zero_padding = csr_matrix((X.shape[0], num_zeros_to_add))
        X = hstack([X, zero_padding])
    elif X.shape[1] > Y.shape[1]:
        num_zeros_to_add = X.shape[1]-Y.shape[1]
        zero_padding = csr_matrix((Y.shape[0], num_zeros_to_add))
        Y = hstack([Y, zero_padding])
    progress_processing = 44.63
    
    similarity = cosine_similarity(X, Y)
    progress_processing = 99.74

    print(similarity)
    top_indices = np.argsort(similarity, axis=0)[::-1][:5]

    df_final = df2.copy()
    df_final = df_final.iloc[top_indices.flatten()]

    #df_final.to_excel('C:/Users/user/Desktop/final_scored.xlsx', index=False)
    
    # Etablir la connexion a MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['userdbtest']  # Remplacez par le nom de votre base de donnees
    global name_db
    name_db = "Talents : , " + key_word + " , " + str(datetime.today())[:-7]
    collection = db[name_db]   # Remplacez par le nom de votre collection
    # Convertissez le DataFrame en liste de dictionnaires
    records = df_final.to_dict(orient='records')
    # Inserez les enregistrements dans la collection
    collection.insert_many(records)
    client.close()


    progress_processing = 100

def clean(df, df_fdp, key_word):
    
    global progress_data_cleaning

    shape=df.shape
    print(df)
    shape_df_fdp=df_fdp.shape
    
    # Nettoyage :
    NbLignes, NbCollones = df.shape
    for i in range(NbLignes) : 
        for j in range(NbCollones) :
            df.iloc[i,j] = nettoyage(df.iloc[i,j]) 

    df2 = df.copy()
    progress_data_cleaning = 1
    
    for i in range(shape[0]):
        text_to_translate = str(df.iloc[i, 0])
        sentences = text_to_translate.split('   ')
        pourcentage1 = 30 / shape[0]
        translated_text = ''
        for sentence in sentences:
            cleaned_sentence = sentence.strip()
            if cleaned_sentence:
                try:
                    translated_sentence = ts.translate_text(cleaned_sentence, translator='google', to_lang='en')
                    translated_text += translated_sentence + '   '
                    time.sleep(0.3)
                    print(i)
                    print(sentence)
                    print("boucleeee1")
                except Exception as e:
                    print(f"An error occurred while translating: {e}")
                    print("cell", i, j)
                    translated_text += cleaned_sentence + '   '
        progress_data_cleaning = round(pourcentage1 + progress_data_cleaning ,2)
        # Update the DataFrame cell using `at` accessor
        df2.at[i, 'Expérience_ang'] = translated_text
        
    print("ba3ed awel 1 boucle : "+str(progress_data_cleaning))
    progress_data_cleaning = 31
    print("ba3ed awel 1 boucle : "+str(progress_data_cleaning))
    for i in range(shape_df_fdp[1]):
        text_to_translate = str(df_fdp.iloc[0, i])
        sentences = text_to_translate.split('   ')
        translated_text = ''
        pourcentage2 = 30 / (shape_df_fdp[1]+len(sentences))
        for sentence in sentences:
            cleaned_sentence = sentence.strip()
            if cleaned_sentence:
                try:
                    translated_sentence = ts.translate_text(cleaned_sentence, translator='google', to_lang='en')
                    translated_text += translated_sentence + '   '
                    time.sleep(0.3)
                    print(i)
                    print(j)
                    print("boucleeee2")
                except Exception as e:
                    print(f"An error occurred while translating: {e}")
                    print("cell", i, j)
                    translated_text += cleaned_sentence + '   '
            progress_data_cleaning = round(pourcentage2 + progress_data_cleaning ,2)
        # Update the DataFrame cell using `at` accessor
        df_fdp.at[0, "A" + str(i)] = translated_text
    print("ba3ed awel 1 boucle : "+str(progress_data_cleaning))
    progress_data_cleaning = 61
    print("ba3ed awel 1 boucle : "+str(progress_data_cleaning))
    shape_df_fdp=df_fdp.shape
    current_job=[]
    current_position=[]
    date=[]
    site=[]
    cities=['tunisia','tunisie','ariana','béja','beja','ben arous' , 'bizerte','gabès','gabes','gafsa','jendouba','kairouan','kasserine','kébili','kebili','kef','mahdia','manouba','médenine','medenine','monastie','nabeul','sfax','sidi bouzid','zaghouan','tunis','tozeur','tataouine','sousse','siliana']
    pattern = r'(\d+)\s*years\s*(.*?)'
    #pattern2 = r'(\d+)\s*months\s*(.*?)'#pattern ken hat details 2 experiences f nafs el haja
    #pattern3 = r'^Compétences :'
    for i in range(len(df)):
        value = df2.loc[i, 'Expérience']
        data = value.split("   ")
    
        current_job.append(data[0])
    
        matches = re.findall(pattern, data[1])
        #matches2 = re.findall(pattern2, data[1])
        if not matches:
            current_position.append(data[1])
            if search_dates(data[2]):
                date.append(data[2])
                if verification(data[3])==1:
                    site.append(data[3])
                else:
                    site.append(" ")
            else:
                date.append(" ")
                if verification(data[2])==1:
                    site.append(data[2])
                else:
                    site.append(" ")
        else: 
            current_position.append(data[2])
            if search_dates(data[3]):
                date.append(data[3])
                if verification(data[4])==1:
                    site.append(data[4])
                else:
                    site.append(" ") 
            else:
                date.append(" ")
                if verification(data[3])==1:
                    site.append(data[3])
                else:
                    site.append(" ")
    print("66 66")
    progress_data_cleaning = 66

    # init params of skill extractor
    nlp = spacy.load("en_core_web_lg")
    skills=[]
    # init skill extractor
    skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)
    progress_data_cleaning = 67
    for i in range(shape[0]):
        data=[]
        for j in range(shape[1]):
            text = str(df.iloc[i, j])
            if text != "":
                annotations = skill_extractor.annotate(text)
                full_matches = [match['doc_node_value'] for match in annotations['results']['full_matches']]
                ngram_scored = [match['doc_node_value'] for match in annotations['results']['ngram_scored']]
                all_doc_node_values = full_matches + ngram_scored
                data=data+all_doc_node_values
                data=remove_duplicates(data)
        progress_data_cleaning = round(12/shape[0]  + progress_data_cleaning  ,2)
        skills.append(data)
    #print(skills)
    print("honi yelzem 79")
    skills_fdp=[]
    for i in range(shape_df_fdp[0]):
        data_fdp=[]
        for j in range(7,shape_df_fdp[1]):
            text = str(df_fdp.iloc[i, j])
            if text != "":
                annotations = skill_extractor.annotate(text)
                full_matches = [match['doc_node_value'] for match in annotations['results']['full_matches']]
                ngram_scored = [match['doc_node_value'] for match in annotations['results']['ngram_scored']]
                all_doc_node_values = full_matches + ngram_scored
                data_fdp=data_fdp+all_doc_node_values
        progress_data_cleaning = round(12/shape_df_fdp[0] + progress_data_cleaning ,2)
        skills_fdp.append(data_fdp)
    print("honi yelzem 91")
    print(skills_fdp)

    L_descriptionsExperience = list()
    for i in range(shape[0]) : 
    
        # Pour avoir des listes
        L_descriptionsExperience.append(extraire_descriptionsExpérience(df.loc[i,'Expérience']))
       
    duration=[]
    progress_data_cleaning = 95
    for i in range(shape[0]):
        timee = extract_durations(df.iloc[i, 0])
        ttime=0
        for j in range(len(timee)):
            echelle =  (timee[j][1])
            if echelle == "mois":
                ttime+=int(timee[j][0])
            else: 
                ttime+=int(timee[j][0])*12
    
            ans=str(ttime//12)
            mois=str(ttime%12)
            if ans=="1":
                if mois=="0":
                    durée = ans+" an"
                else:
                    durée = ans+" an "+mois+" mois"
            else:
                if mois=="0":
                    durée = ans+" ans"
                else:
                    durée = ans+" ans "+mois+" mois"
        
        
        duration.append(durée)
        #print(duration[i])
    progress_data_cleaning = 98
    df2['Current job'] = current_job
    df2['Current position'] = current_position
    df2['Date'] = date
    df2['Site'] = site
    df2['Skills'] = skills
    df2["Durée d'expérience"] = duration
    df2["Description expérience"] = L_descriptionsExperience
    df2['Nb Certificat'] = nb_certif(df)

    df_fdp['Skills'] = skills_fdp
    
    #df2.to_excel("C:/Users/user/Desktop/output_testfinalr.xlsx")
    
    # Etablir la connexion a MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['userdbtest']  # Remplacez par le nom de votre base de donnees
    collection1 = db["Data cleaned : " + key_word + " " + str(datetime.today())[:-7]]   # Remplacez par le nom de votre collection
    collection2 = db["pdf extractor cleaned : " + key_word + " " + str(datetime.today())[:-7]]   # Remplacez par le nom de votre collection
    # Convertissez le DataFrame en liste de dictionnaires
    records1 = df2.to_dict(orient='records')
    records2 =  df_fdp.to_dict(orient='records')
    # Inserez les enregistrements dans la collection
    collection1.insert_many(records1)
    collection2.insert_many(records2)
    client.close()
    
    progress_data_cleaning = 100
    
    return df2, df_fdp
    
def Work(df_fdp, key_word = "java", user_name = "nouriahi02@gmail.com", pass_word = "sltbienbonjour"):

    global progress_scrapping
    
    # -- Connection -- # 

    driver = webdriver.Chrome()
    #driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get("https://linkedin.com/uas/login")
    time.sleep(randint(5,10)+round(random(),3))

    username = driver.find_element(By.ID, "username")
    password = driver.find_element(By.ID, "password")

    username.clear()
    password.clear()

    username.send_keys(user_name) 
    time.sleep(0.805)
    password.send_keys(pass_word)
    #driver.find_element(By.NAME, 'submit').click()
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    #len_articles = driver.find_element(By.XPATH, '//p[@class="c-block-listing__results"]/strong[1]').text
    time.sleep(10 + randint(2,3) + round(random(),3))

    #driver.find_element(By.XPATH, "//button[@class='search-global-typeahead__collapsed-search-button']").click()
    
    # -- Recherche -- #
    time.sleep(0.445)
    recherche = driver.find_element(By.XPATH, "//input[@class='search-global-typeahead__input']")
    time.sleep(1.152)
    recherche.clear()
    time.sleep(0.379)
    recherche.send_keys(key_word)
    #driver.find_element(By.XPATH, "//button[@class='search-global-typeahead__collapsed-search-button']").click()

    recherche.send_keys(Keys.ENTER)

    time.sleep(5.698)
    
    #driver.find_element(By.XPATH, "//div[@id='search-reusables__filters-bar']/ul/li[1]/button").click()
    personnes = driver.find_elements(By.XPATH, "//div[@id='search-reusables__filters-bar']/ul/li")
    while len(personnes) == 0 :
        personnes = driver.find_elements(By.XPATH, "//a[@class='app-aware-link  scale-down ']")
    for i in range(len(personnes)):
        ppersonnes = driver.find_elements(By.XPATH, "//div[@id='search-reusables__filters-bar']/ul/li")
        per = ppersonnes[i].get_attribute("textContent")
        per=clean_string1(per)
        if per=='Personnes':
            x=ppersonnes[i]

    x.click()
    time.sleep(3.049)
    progress_scrapping += 2 
    
    # -- Scrapping -- #
    page = 1
    nbr_pages = 99
    nom_list=[]
    element=[]
    titre=[]
    localisation=[]
    url=[]
    ghlat = 0
    page = 1
    nbr_pages = 20
    try : 
        while(1): 
            page_prec = page
            people = driver.find_elements(By.XPATH, "//a[@class='app-aware-link  scale-down ']")
            while len(people) < 3:
                people = driver.find_elements(By.XPATH, "//a[@class='app-aware-link  scale-down ']")
            nbp = len(people)
            i = 0
            while i < 1:
                try:
                    for p in people:
                        pple = driver.find_elements(By.XPATH, "//a[@class='app-aware-link  scale-down ']")
                        print(len(people))
                        while len(pple) < 3:
                            pple = driver.find_elements(By.XPATH, "//a[@class='app-aware-link  scale-down ']")

                        pple[i].click()
                        try :
                            time.sleep(randint(5, 7) + round(random(), 3))
                            print("2")
                            if title_function(driver) == 0:
                                x = driver.find_element(By.XPATH, "//span[@class='artdeco-button__text']")
                                action = ActionChains(driver)
                                action.move_to_element(x).click().perform()
                            else:
                                title = title_function(driver)
                                elements = elements_function(driver)

                                for f in range(len(elements)):
                                    text = clean_string1(elements[f])
                                    elements[f] = text
                                    f = f + 1

                                while len(elements) > len(title):
                                    elements.pop(-1)

                                nom = driver.find_element(By.XPATH, "//h1[@class='text-heading-xlarge inline t-24 v-align-middle break-words']")
                                nomm = nom.get_attribute("textContent")
                                title.append("Nom")
                                nom_list.append(nomm)
                                elements.append(nomm)
                                
                                x = driver.find_element(By.XPATH, "//span[@class='text-body-small inline t-black--light break-words']")
                                loc = x.get_attribute("textContent")
                                title.append("Localisation")
                                localisation.append(loc)
                                elements.append(loc)
                                
                                current_url = driver.current_url
                                url.append(current_url)
            
                                clik = driver.find_elements(By.XPATH, "//span[@class='pvs-navigation__text']")
                                clik = extra_click(clik)
                                h = 0
                                time.sleep(randint(3, 4) + round(random(), 3))

                                for cl in clik:
                                    cclik = driver.find_elements(By.XPATH, "//span[@class='pvs-navigation__text']")
                                    cclik = extra_click(cclik)
                                    cclik[h].click()
                                    time.sleep(randint(5, 6) + round(random(), 3))
                                    print("5")
                                    t = driver.find_element(By.XPATH, "//div[@class='flex-grow-1 display-flex justify-space-between']")
                                    tt = t.get_attribute("textContent")
                                    tt = clean_string1(tt)
                                    print("6")
                                    text = driver.find_element(By.XPATH, "//div[@class='pvs-list__container']")
                                    tx = text.get_attribute("textContent")

                                    try:
                                        index_value = title.index(tt)
                                        elements[index_value] = tx
                                    except ValueError:
                                        print("No match found in title list for:", tt)

                                    for s in range(len(elements)):
                                        text = clean_string1(elements[s])
                                        elements[s] = text
                                        s = s + 1

                                    h = h + 1
                                    driver.back()
                                    time.sleep(randint(3, 6) + round(random(), 3))

                                element.append(elements)
                                titre.append(title)
                                driver.back()
                                time.sleep(randint(3, 5) + round(random(), 3))



                        except : 
                            driver.back()
                        i = i + 1
                        progress_scrapping = round(progress_scrapping + 98/nbp)  # --!-- progress_scrapping --!-- #
                        time.sleep(randint(2, 3) + round(random(), 3))
                except:
                    i = i + 1
                    ghlat += 1
                    progress_scrapping = round(progress_scrapping + 98/nbp)  # --!-- progress_scrapping --!-- #
                    print("probleme n°" + str(ghlat))
                    time.sleep(randint(2, 3) + round(random(), 3))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            data = driver.find_elements(By.XPATH, "//span[@class='artdeco-button__text']")
            for e in data :
                el = e.get_attribute("textContent")
                if "Suivant" in el :
                    e.click()
                    page += 1
            time.sleep(randint(4,8)+round(random(),3))
            if page > nbr_pages or page == page_prec:
                break     
    except :
        print("sortie du boucle")
    driver.quit()
    # -- Preparation de DataFrame -- #
    for i in range(len(titre)):
        print(i)
        print(titre[i])
        if titre[i][0] != 'Expérience':
            titre[i].insert(0, 'Expérience')
            element[i].insert(0, " ")
        if titre[i][1] != 'Formation':
            titre[i].insert(1, 'Formation')
            element[i].insert(1, " ")
        if titre[i][2] != 'Licences et certifications':
            titre[i].insert(2, 'Licences et certifications')
            element[i].insert(2, " ")
        if titre[i][3] != 'Projets':
            titre[i].insert(3, 'Projets')
            element[i].insert(3, " ")
        if titre[i][4] != 'Bénévolat':
            titre[i].insert(4, 'Bénévolat')
            element[i].insert(4, " ")
        if titre[i][5] != 'Compétences':
            titre[i].insert(5, 'Compétences')
            element[i].insert(5, " ")
        if titre[i][6] != 'Résultats d’examens':
            titre[i].insert(6, 'Résultats d’examens')
            element[i].insert(6, " ")
        if titre[i][7] != 'Langues':
            titre[i].insert(7, 'Langues')
            element[i].insert(7, " ")
        if titre[i][8] != 'Nom':
            titre[i].insert(8, 'Nom')
            element[i].insert(8, " ")
        print(len(titre[i]))
        print(titre[i])
        if (len(titre[i]) < 10) or (titre[i][9] != 'Localisation'):
            titre[i].insert(9, 'Localisation')
            element[i].insert(9, " ")
         

    titles = ['Expérience', 'Formation', 'Licences et certifications', 'Projets', 'Bénévolat', 'Compétences',
              'Résultats d’examens', 'Langues', 'Nom', 'Localisation']

    df = create_dataframe(titles, element)
    df['Current url'] = url

    # Etablir la connexion a MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['userdbtest']  # Remplacez par le nom de votre base de donnees
    collection = db["Data scraping : " + key_word + " " + str(datetime.today())[:-7]]   # Remplacez par le nom de votre collection
    # Convertissez le DataFrame en liste de dictionnaires
    records = df.to_dict(orient='records')
    # Inserez les enregistrements dans la collection
    collection.insert_many(records)
    client.close()

    """ !!! --- !!! """
    df2, df_fdp = clean(df, df_fdp, key_word)
    
    progression(df2, df_fdp, key_word)
    """ !!! --- !!! """



@scraping.route('/scraping', methods = ['GET', 'POST'])
def home():
    print("hello")
    return render_template("Dash/scraping/df.html")



@scraping.route('/traitement', methods=['POST'])
def traitement():
    print("mo3chiw")
    uploaded_file = request.files['pdfFile']
    key_word = request.form.get('key_word') 
    user_name = request.form.get('user_name') 
    pass_word = request.form.get('pass_word') 
    if uploaded_file.filename != '' :
        # Sauvegarder le fichier sur le serveur 
        #uploaded_file.save('C:/Users/user/Desktop/fichier.pdf')
        df_fdp = pdf_extractor(uploaded_file,key_word)
        start_new_thread(Work,(df_fdp, key_word, user_name, pass_word))
        #start_new_thread(clean,(key_word, user_name, pass_word))
        return render_template('Dash/scraping/rogress.html')
    return render_template('Dash/scraping/df.html')

@scraping.route('/update_progress', methods=['POST'])
def update_progress():
    print("ba3aw")  
    print(progress_data_cleaning)
    scraping.progress_scrapping = progress_scrapping
    scraping.progress_data_cleaning = progress_data_cleaning
    scraping.progress_processing = progress_processing

    response = {
        'progress_scrapping': progress_scrapping,
        'progress_data_cleaning': progress_data_cleaning,
        'progress_processing': progress_processing
    }
    return jsonify(response)


@scraping.route('/traiter_resultat', methods= ['POST'])
def traiter_resultat():
    media_items = list() 
    
    # Etablir la connexion a MongoDB
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['userdbtest']  # Remplacez 'ma_base_de_donnees' par le nom de votre base de données
    global name_db
    collection = db[name_db]   # Remplacez 'ma_collection' par le nom de votre collection

    # Récupérez les données à partir de la collection
    data = collection.find()

    # Convertissez les données en DataFrame
    df = pd.DataFrame(data)

    # Fermez la connexion
    client.close()

    for i in range(min(7,df.shape[0])) :   
        media_items.append({
        #'image' : "static/img/product-"+str(i)+".jpg",
        'Nom': df.at[i,"Nom"],
        'Link': df.at[i,"Current url"],
        'Formation': df.at[i,"Formation"],
        'Expérience': df.at[i,"Expérience"],
        'Compétences': df.at[i,"Compétences"],
        })
    return media_items

@scraping.route('/afficher_resultat', methods= ['GET','POST'])
def afficher_resultat():
    media_items = traiter_resultat()
    return render_template('Dash/scraping/resultat.html', media_items = media_items)

