from time import sleep
from threading import Thread
from unicodedata import numeric
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
from firebase_admin import storage
import yagmail
import smtplib
from email.mime.text import MIMEText


NOTIFICA_EMAIL = False

SENDING_EMAIL_USERNAME = creds.SENDING_EMAIL_USERNAME
SENDING_EMAIL_PASSWORD = creds.SENDING_EMAIL_PASSWORD 

TIMEOUT = 300 

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



HEADERS = ({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
            'Content-Type': 'application/json',
            })

def get_soup(url):
    response = requests.get(url, headers=HEADERS)

   
    if response.ok:
        soup = BeautifulSoup(response.content, 'html.parser')
        soup.prettify()
        return soup

    else:
        print(response.status_code)


def urlCheck(message):
    # pattern1 = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.\w+\/?"
    # pattern2 = r"[-a-zA-Z0-9]{1,256}\.[a-zA-Z0-9()]{1,6}"
    # if re.match(pattern1, message.text) or re.match(pattern2, message.text):
    try:
        if message.entities[0].type == "url":
            return True
        
    except:
        return False


def nomeEsistente(nome, utente):
    nomi = db.collection('Utente-Sito').where("utente", "==", utente).where("nome", "==", nome).get()
    if len(nomi)>0:
        return True
    return False

def truncate_url(url):
    pattern = r"https?:\/\/(www\.)?([-a-zA-Z0-9@:%._\+~#=]{1,256}\.\w+)\/?"
    t = re.search(pattern, url).group(2)
    return t


def uploadHtml(url, nomeCustom):  
    if urlCheck(url):
        # try:
        urlSito = url.text
        utente = url.chat.id
        html = str(get_soup(urlSito)) 
        #troncato = truncate_url(urlSito)
        
        
        s = db.collection('Sito').where("url", "==", urlSito).get()
        if len(s) == 0: #Se il sito non era già presente
            nomeFile = uuid.uuid4().hex
            fh = open(nomeFile, "w", encoding="utf-8")
            fh.write(html)
            fh.close()
            storage.child(storagePath + nomeFile).put(nomeFile)
            db.collection('Sito').add({'url': urlSito, 'storageid': nomeFile})



            try: 
                os.unlink(nomeFile)
            except Exception as e:
                print(e)

        us = db.collection('Utente-Sito').where("utente", "==", utente).where("sito", "==", urlSito).get()
        if len(us)==0: # Se il sito non era già stato registrato dall'utente
            db.collection('Utente-Sito').add({'utente':utente, 'sito':urlSito, 'nome': nomeCustom.text})
            return True
        return False

        # except Exception as e:
        #     bot.reply_to(message, str(e)) 


def prezzoAbbassato(prodotto, obiettivo):
    nuovoPrezzo = getProductprice(prodotto)
    if nuovoPrezzo < obiettivo:
        return nuovoPrezzo
    return -1

def paginaCambiata(url, storageId):
    newSoup = str(get_soup(url))
    storage.child(storagePath + storageId).download("", storageId)
    fh=open(storageId, 'r', encoding="utf-8")
    oldSoup = fh.read()
    fh.close()
    

    if newSoup == oldSoup:
        print("Uguali")
        try: 
            os.unlink(storageId)

        except Exception as e:
            print(e)

        return False

    else: 
        fh = open("Vecchiosito", "w", encoding='utf-8')
        fh.write(oldSoup)
        fh.close()
        fh2 = open("Nuovosito", "w", encoding='utf-8')
        fh2.write(newSoup)
        fh2.close()
        handler = open(storageId, 'w', encoding='utf-8')
        handler.write(newSoup)
        handler.close()
        storage.child(storagePath + storageId).put(storageId)        


    try: 
        os.unlink(storageId)

    except Exception as e:
        print(e)

    return True

def avvisaUtenteSito(utente, url, nomeSito):
    bot.send_message(utente, f"Il sito memorizzato come '{nomeSito}' ha subito dei cambiamenti: \n" + url)
    dbUser = db.collection('Utente').where('nome', '==', utente).get()[0]
    mailAddress = dbUser.get('email')
    oggetto = "Cambiamento pagine"
    contenuto = f"Il sito memorizzato come '{nomeSito}' ha subito dei cambiamenti: \n" + url

    if NOTIFICA_EMAIL:
        inviaEmail(mailAddress,oggetto, contenuto)

def avvisaUtenteProdotto(user, prodotto, nomeProd, nuovoPrezzo):
    bot.send_message(user, f"Il prezzo del prodotto memorizzato come '{nomeProd}' si è abbassato a {nuovoPrezzo}€: \n" + prodotto)
    dbUser = db.collection('Utente').where('nome', '==', user).get()[0]
    mailAddress = dbUser.get('email')
    oggetto = "Abbassamento prezzo"
    contenuto = f"Il prezzo del prodotto memorizzato come '{nomeProd}' si è abbassato a {nuovoPrezzo}€: \n" + prodotto

    if NOTIFICA_EMAIL:
        inviaEmail(mailAddress,oggetto, contenuto)


def checkAutomaticoSito():
    utenteSito = db.collection('Utente-Sito').get()
    sitiCambiati = []
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
            avvisaUtenteSito(user, urlSalvato, nomeSito)

def checkAutomaticoProdotto():
    utenteProdotto = db.collection('Utente-Prodotto').where('utente', "!=", "").get()
    prodottiAbbassati = {}
    for prodotto in utenteProdotto:
        urlProdotto = prodotto.get('prodotto')
        obiettivo = prodotto.get('obiettivo')
        nuovoPrezzo = prezzoAbbassato(urlProdotto, obiettivo)
        if nuovoPrezzo != -1:
            prodottiAbbassati[urlProdotto] = nuovoPrezzo

    for utente in utenteProdotto:
        prodotto = utente.get('prodotto')
        user = utente.get('utente')
        nomeProd = utente.get('nome')


        if prodotto in prodottiAbbassati:
            nuovoPrezzo = prodottiAbbassati[prodotto]
            avvisaUtenteProdotto(user, prodotto, nomeProd, nuovoPrezzo)

def inviaEmail(destinatario, oggetto, contenuto):
    yagmail.SMTP(SENDING_EMAIL_USERNAME, SENDING_EMAIL_PASSWORD).send(destinatario, oggetto, contenuto)

def priceConverter(strPrice):
    pricePattern="(\d+((\.|\,)\d+)?)"
    try:
        numeric_price = re.search(pricePattern, strPrice).group(1).replace(".", "")
        numeric_price = numeric_price.replace(",", ".")
    except:
        numeric_price = re.search(pricePattern, strPrice).group(1)
    numeric_price = float(numeric_price)
    
    return numeric_price

def getProductprice(urlProd):
    soup = get_soup(urlProd)
    price = "prezzo non trovato"

    patternAmazon = "amazon\.\w+\/.+"
    patternSubito = "subito\.it\/\w+"
    patternEbay = "ebay\.\w+\/\w+"
    patternZalando = "zalando\.it/\w+"
    patternVinted = "vinted\.it/\w+"

    if re.search(patternAmazon, str(urlProd)):
        price = soup.find('span', class_="a-offscreen").get_text()


    elif re.search(patternEbay, str(urlProd)): 
        price = soup.find('span', id = 'prcIsum').get_text()

    
    elif re.search(patternSubito, str(urlProd)):
        price = soup.find('p', class_="index-module_price__N7M2x AdInfo_ad-info__price__tGg9h index-module_large__SUacX").get_text()

    elif re.search(patternZalando, str(urlProd)):
        price = soup.find('p', class_="RYghuO uqkIZw ka2E9k uMhVZi FxZV-M pVrzNP").get_text()

    # elif re.search(patternVinted, str(urlProd)):
    #     print("vinted")
    #     price = soup.find('h1', class_="Text_text__QBn4- Text_heading__gV4um Text_left__3s3CR").get_text()

    

    else:
        raise Exception("Prezzo non trovato")
    
    numeric_price = priceConverter(price)    

    return numeric_price

class checkThread(Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            print("running")
            checkAutomaticoSito()
            checkAutomaticoProdotto()
            sleep(TIMEOUT)