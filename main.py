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

@bot.message_handler(commands=['greet'])
def greet(message):
    bot.reply_to(message, "ciao")

@bot.message_handler(commands=['hey'])
def greet(message):
    bot.send_message(message.chat.id, "hey")
    
def urlCheck(message):
    pattern1 = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.\w+\/?"
    pattern2 = r"[-a-zA-Z0-9]{1,256}\.[a-zA-Z0-9()]{1,6}"
    if re.match(pattern1, str(message.text)) or re.match(pattern2, str(message.text)):
        bot.send_message(message.chat.id, "link")
        return True

    return False

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
@bot.message_handler(commands=['aggiungiURL'])
def add(message):
    pass

#COMANDO /removeURL
@bot.message_handler(commands=['rimuoviURL'])
def remove(message):
    pass

#COMANDO /addProduct
@bot.message_handler(commands=['aggiungiProdotto'])
def addProduct(message):
    pass

#COMANDO /removeProduct
@bot.message_handler(commands=['rimuoviProdotto'])
def removeProduct(message):
    pass

#COMANDO /productsList
@bot.message_handler(commands=['listaProdotti'])
def productsList(message):
    pass


markup = types.ReplyKeyboardMarkup(row_width=2)
itembtn1 = types.KeyboardButton('a')
itembtn2 = types.KeyboardButton('b')
itembtn3 = types.KeyboardButton('c')
itembtn4 = types.KeyboardButton('d')
markup.add(itembtn1, itembtn2, itembtn3, itembtn4)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Scegli un'opzione:", reply_markup=markup)






bot.polling()   



