import  requests
import creds
import webbrowser
import telebot
from telebot import types
import os
import re
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

API_KEY = creds.API_KEY

bot = telebot.TeleBot(API_KEY)   



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
        
def urlCheck(message):
    pattern1 = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.\w+\/?"
    pattern2 = r"[-a-zA-Z0-9]{1,256}\.[a-zA-Z0-9()]{1,6}"
    if re.match(pattern1, message.text) or re.match(pattern2, message.text):
        bot.send_message(message.chat.id, "link")
        return True

    return False





@bot.message_handler(commands=['start'])#Registra l'utente nel database
def start(message):
    user = message.chat.id
    db.collection('Utente').add({'nome': user})
    bot.send_message(message.chat.id, "Benvenuto, io sono Geronimo utilizza i comandi per poter tracciare siti web e prodotti: ")


    
@bot.message_handler(func=urlCheck) #CONTROLLA CHE SIA UN URL E CHE SIA VALIDO
def mioSend(message):
    URL = message.text
    soup = get_soup(URL)
    price = "prezzo non trovato"

    patternAmazon = "amazon\.\w+\/.+"
    patternSubito = "subito.it\/\w+"
    patternEbay = "ebay\.\w+\/\w+"

    if re.search(patternAmazon, str(message)):
        bot.send_message(message.chat.id, "amazon")
        price = soup.find('span', class_="a-offscreen").get_text()

    elif re.search(patternEbay, str(message)): 
        print("ebay")
        bot.send_message(message.chat.id, "ebay")
        price = soup.find('span', id = 'prcIsum').get_text()
    
    elif re.search(patternSubito, str(message)):
        bot.send_message(message.chat.id, "subito")
        price = soup.find('p', class_="index-module_price__N7M2x AdInfo_ad-info__price__tGg9h index-module_large__SUacX").get_text()

    
    pricePattern="\d+((\.|\,)\d+)?"
    # numeric_price = re.match(pricePattern, price)
    # numeric_price = int(numeric_price)
    # if numeric_price > 0:
    #     print(numeric_price)

    bot.send_message(message.chat.id, "prezzo: " + price)

#COMANDO /webList
@bot.message_handler(commands=['listaSiti'])
def list(message):
    pass

#COMANDO /addURL
@bot.message_handler(commands=['aggiungisito'])
def add(message):
    msg = bot.send_message(message.chat.id, "Bene, mandami qui di seguito l'URL del sito che vuoi monitorare: ")
    bot.register_next_step_handler(msg, addStep2)

def addStep2(message):
    if urlCheck(message):
        try:
            urlSito = message.text
            html = get_soup(urlSito)
            db.collection('Sito').add({'url': urlSito, 'html': html})
            db.collection('Utente-Sito').add({'sito':urlSito, 'utente':message.chat.id})
            bot.send_message(message.chat.id, "Url aggiunto con successo")

        except Exception as e:
            bot.reply_to(message, str(e))
        
        
    

#COMANDO /removeURL
@bot.message_handler(commands=['rimuovisito'])
def remove(message):
    pass

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


markup = types.ReplyKeyboardMarkup(row_width=2)
itembtn1 = types.KeyboardButton('a')
itembtn2 = types.KeyboardButton('b')
itembtn3 = types.KeyboardButton('c')
itembtn4 = types.KeyboardButton('d')
markup.add(itembtn1, itembtn2, itembtn3, itembtn4)








bot.infinity_polling()   



