import  requests
import uuid
from threading import Barrier
import creds
import webbrowser
import telebot
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import os
import re
import urllib
from bs4 import BeautifulSoup
import pyrebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
#import scraper

debug = False

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

API_KEY = creds.API_KEY


firebase = pyrebase.initialize_app(creds.firebaseConfig)
auth = firebase.auth()
storage = firebase.storage()
storagePath = "Soups/"

#UPLOAD
#storage.child(cloudfilename).put(filename)
#DOWNLOAD
#storage.child(cloudfilename).download(path, filename)

#LETTURA SENZA DOWNLOAD
#storage.child(cloudfilename).get_url(None)
#f = urllib.request.urlopen(url).read
bot = telebot.TeleBot(API_KEY)   
USER = None


HEADERS = ({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
            'Content-Type': 'application/json',
            })



def get_soup(url):
    response = requests.get(url, headers=HEADERS)

   
    if response.ok:
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup

    else:
        print(response.status_code)

def static_soup(soup: BeautifulSoup) -> BeautifulSoup:
    for s in soup.select('script'):
        s.extract()
    
    for s in soup.select('meta'):
        s.extract()

    return soup

def urlCheck(message):
    # pattern1 = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.\w+\/?"
    # pattern2 = r"[-a-zA-Z0-9]{1,256}\.[a-zA-Z0-9()]{1,6}"
    # if re.match(pattern1, message.text) or re.match(pattern2, message.text):
    if message.entities[0].type == "url":
        return True
        
    return False


def nomeEsistente(nome, utente):
    nomi = db.collection('Utente-Sito').where("utente", "==", utente).where("nome", "==", nome).get()
    if len(nomi)>0:
        return True
    return False

def truncate_url(url):
    pattern = r"https?:\/\/(www\.)?([-a-zA-Z0-9@:%._\+~#=]{1,256}\.\w+)\/?"
    t = re.search(pattern, url).group(2)
    if debug:
        print("URL TRONCATO : " + t)
    return t


def uploadHtml(url, nomeCustom):  
    if urlCheck(url):
        # try:
        urlSito = url.text
        utente = url.chat.id
        html = str(get_soup(urlSito).prettify())
        #troncato = truncate_url(urlSito)
        
        
        s = db.collection('Sito').where("url", "==", urlSito).get()
        if len(s) == 0: #Se il sito non era già presente
            nomeFile = uuid.uuid4().hex
            fh = open(nomeFile, "w", encoding="utf-8")
            fh.write(str(html))
            storage.child(storagePath + nomeFile).put(nomeFile)
            db.collection('Sito').add({'url': urlSito, 'storageid': nomeFile})



            try: 
                os.unlink(nomeFile)
                print("rimosso")
            except Exception as e:
                print(e)

        us = db.collection('Utente-Sito').where("utente", "==", utente).where("sito", "==", urlSito).get()
        if len(us)==0: # Se il sito non era già stato registrato dall'utente
            db.collection('Utente-Sito').add({'utente':utente, 'sito':urlSito, 'nome': nomeCustom.text})
            return True
        return False

        # except Exception as e:
        #     bot.reply_to(message, str(e)) 

@bot.message_handler(commands=['start'])#Registra l'utente nel database
def start(message):
    USER = message.chat.id
    db.collection('Utente').add({'nome': USER})
    bot.send_message(message.chat.id, "Benvenuto, io sono Geronimo utilizza i comandi per poter tracciare siti web e prodotti: ")


    
# @bot.message_handler(func=urlCheck) #CONTROLLA CHE SIA UN URL E CHE SIA VALIDO
# def mioSend(message):
#     URL = message.text
#     soup = get_soup(URL)
#     price = "prezzo non trovato"

#     patternAmazon = "amazon\.\w+\/.+"
#     patternSubito = "subito.it\/\w+"
#     patternEbay = "ebay\.\w+\/\w+"

#     if re.search(patternAmazon, str(message)):
#         if debug:
#             bot.send_message(message.chat.id, "amazon")

#         price = soup.find('span', class_="a-offscreen").get_text()
#         bot.send_message(message.chat.id, "prezzo: " + price)


#     elif re.search(patternEbay, str(message)): 
#         if debug:
#             bot.send_message(message.chat.id, "ebay")

#         price = soup.find('span', id = 'prcIsum').get_text()
#         bot.send_message(message.chat.id, "prezzo: " + price)

    
#     elif re.search(patternSubito, str(message)):
#         if debug:
#             bot.send_message(message.chat.id, "subito")

#         price = soup.find('p', class_="index-module_price__N7M2x AdInfo_ad-info__price__tGg9h index-module_large__SUacX").get_text()
#         bot.send_message(message.chat.id, "prezzo: " + price)


    
#     pricePattern="\d+((\.|\,)\d+)?"
#     # numeric_price = re.match(pricePattern, price)
#     # numeric_price = int(numeric_price)
#     # if numeric_price > 0:
#     #     print(numeric_price)




#COMANDO /webList
@bot.message_handler(commands=['listasiti'])
def list(message):
    dict = {}
    docs = db.collection("Utente-Sito").where("utente", "==", message.chat.id).get()
    keyboard = []

    for doc in docs:
        if doc.get('sito') not in dict: #unique
            dict[doc.get('sito')] = doc.get('nome')

  
    for k in dict.keys():
        tempButton = InlineKeyboardButton(text = dict[k], url = k)
        keyboard.append([tempButton])

    markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(message.chat.id, "Ecco la lista dei siti salvati:" ,reply_markup=markup)



   



#COMANDO /addURL
@bot.message_handler(commands=['aggiungisito'])
def add(message):
    msg = bot.send_message(message.chat.id, "Bene, mandami qui di seguito l'URL del sito che vuoi monitorare: ")
    bot.register_next_step_handler(msg, addStep2)

 
def addStep2(message):
    
    if not urlCheck(message):
        bot.reply_to(message, "Questo url non è valido ☹")

    else:
        urlDaSalvare = message
        msg = bot.reply_to(message, "Con che nome vorresti memorizzare questo link?") #todo: force reply?
        bot.register_next_step_handler(msg, addStep3, urlDaSalvare)
 


        
def addStep3(message, urlDaSalvare):

    # if nomeEsistente(message.text, message.chat.id):
    #     msg =  bot.reply_to(message,"Hai già utilizzato il nome inserito, inseriscine uno nuovo:")
    #     bot.register_next_step_handler(msg, addStep3, urlDaSalvare)

    if uploadHtml(urlDaSalvare, message):
        bot.reply_to(message, "Url aggiunto con successo 👍")
    else:
        bot.send_message(message.chat.id, "L'url inserito era già stato aggiunto 😁")

    #except Exception as e:
        # bot.send_message(message.chat.id, "Ops, qualcosa è andato storto ☹")
        # print(e)

    

#COMANDO /removeURL
@bot.message_handler(commands=['rimuovisito'])
def remove(message):
    msg = bot.send_message(message.chat.id, "Bene, inviami il nome da te scelto o l'url del sito che vuoi ELIMINARE dalla lista:")
    bot.register_next_step_handler(msg,removeStep2)

def removeStep2(message):
    perUrl = db.collection('Utente-Sito').where("sito", "==", message.text).get()
    perNome = db.collection('Utente-Sito').where("nome", "==", message.text).get()
    docs = [*perUrl, *perNome]
    for doc in docs:
        key = doc.id
        db.collection('Utente-Sito').document(key).delete()
        bot.send_message(message.chat.id, f"Il sito memorizzato come '{doc.get('nome')}' è stato eliminato \n" + doc.get('sito'))
        #break

#COMANDO /addProduct
@bot.message_handler(commands=['aggiungiprodotto'])
def addProduct(message):
    pass

#COMANDO /removeProduct
@bot.message_handler(commands=['rimuoviprodotto'])
def removeProduct(message):
    pass

#COMANDO /productsList
@bot.message_handler(commands=['listaprodotti'])
def productsList(message):
    pass


# markup = types.ReplyKeyboardMarkup(row_width=2)
# itembtn1 = types.KeyboardButton('a')
# itembtn2 = types.KeyboardButton('b')
# itembtn3 = types.KeyboardButton('c')
# itembtn4 = types.KeyboardButton('d')
# markup.add(itembtn1, itembtn2, itembtn3, itembtn4)

def paginaCambiata(url, storageId):
    newSoup = str(get_soup(url).prettify()) 
    storage.child(storagePath + storageId).download("", storageId)
    fh=open(storageId, 'r', encoding="utf-8")
    oldSoup = fh.read()
    fh.close()
    

    if newSoup == oldSoup:
        print("Sito Uguale")
        return False

    # else:
    #     #storage.child(storagePath + storageId).put(storageId)


    # try: 
    #     os.unlink(storageId)

    # except Exception as e:
    #     print(e)

    print("SitoCambiato")
    return True
    


@bot.message_handler(commands=['check'])
def checkPagine(message):
    utenteSito = db.collection('Utente-Sito').get()
    sitiCambiati = []
    utentiDaAvvisare = []
    for sito in utenteSito:
        urlSito = sito.get('sito')
        s = db.collection('Sito').where('url',"==",urlSito).get()
        storageid = s[0].get('storageid')
        
        if paginaCambiata(urlSito, storageid):
            sitiCambiati.append(urlSito)

    for utente in utenteSito:
        urlSalvato = utente.get('sito')
        user = utente.get('utente')
        nomeSito = utente.get('nome')
        
        if urlSalvato in sitiCambiati:
            avvisaUtente(user, urlSalvato, nomeSito)


def avvisaUtente(utente, url, nomeSito):
    bot.send_message(utente, f"Il sito memorizzato come '{nomeSito}' ha subito dei cambiamenti: \n" + url)

bot.infinity_polling()

# if __name__ == "__main__":


#     # scraper.checkPagine()
#     # scraper.checkProdotti()
#     scraper.paginaCambiata("https://firebasestorage.googleapis.com/v0/b/geronimo-499a0.appspot.com/o/Soups%2F002f90e61b6446149d0bc5f639450084?alt=media&token=9c112c82-75c1-4cc4-9a4d-40a745719150","002f90e61b6446149d0bc5f639450084")

#     bot.infinity_polling()   



