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
from functions import *

@bot.message_handler(commands=['start'])#Registra l'utente nel database
def start(message):
    global USER, EMAIL
    USER = message.chat.id
    EMAIL = ""
    db.collection('Utente').add({'nome': USER, 'email' : EMAIL})
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


    


@bot.message_handler(commands=['registraemail'])
def registraEmail(message):
    global USER
    USER = message.chat.id
    Utente = db.collection('Utente').where("nome", "==", USER).get()[0]
    email = Utente.get("email")
    if email == "":
        msg = bot.reply_to(message,"Bene, mandami qui di seguito l'email che vuoi registrare sul tuo account:")

    else:
        button = InlineKeyboardButton(text = "Annulla", callback_data = "annulla")
        keyboard=[[button]]
        markup = InlineKeyboardMarkup(keyboard)
        global EMAIL
        global ANNULLA
        ANNULLA = False
        EMAIL = Utente.get('email')
        stringa = f"Hai già un'email registrata con l'indirizzo '{EMAIL}', vorresti sovrascrivere l'indirizzo con uno nuovo? Se si inviami il nuovo indirizzo, altrimenti premi il tasto 'Annulla' "
        msg = bot.send_message(USER, stringa, reply_markup=markup)
        

    bot.register_next_step_handler(msg, mailStep2)


@bot.callback_query_handler(func=lambda call: call.data.find("annulla") != -1)
def annullaRegistrazione(call):
    global ANNULLA 
    ANNULLA = True
    print("annulla")
    bot.send_message(USER, f"Il tuo indirizzo email è rimasto invariato ({EMAIL})")

def mailStep2(message):
    if not ANNULLA:
        print(ANNULLA)
        Utente = db.collection('Utente').where("nome", "==", USER).get()
        if message.entities[0].type == "email":
            db.collection('Utente').document(Utente[0].id).update({"email":message.text})
            bot.send_message(message.chat.id, f"Il tuo indirizzo email '{message.text}' è stato registrato 👍")


        else:
            bot.reply_to(message, f"Ops, l'indirizzo email inserito non è valido 😕")



            
 


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





if __name__ == "__main__":
    bot.infinity_polling()   
    #checkLoop()



