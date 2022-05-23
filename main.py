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
    USER = message.chat.id
    EMAIL = ""
    db.collection('Utente').add({'nome': USER, 'email' : EMAIL})
    bot.send_message(message.chat.id, "Benvenuto, io sono Geronimo, utilizza i comandi per poter tracciare siti web e prodotti: ")


    





#COMANDO /webList
@bot.message_handler(commands=['listasiti'])
def list(message):
    dict = {}
    docs = db.collection("Utente-Sito").where("utente", "==", message.chat.id).get()
    keyboard = [] 

    for doc in docs:
        if doc.get('sito') not in dict: #unique
            dict[doc.get('sito')] = doc.get('nome')

    if len(dict) > 0:
        for k in dict.keys():
            tempButton = InlineKeyboardButton(text = dict[k], url = k)
            keyboard.append([tempButton])

        markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(message.chat.id, "Ecco la lista dei siti salvati:" ,reply_markup=markup)

    else:
        bot.send_message(message.chat.id, "Al momento non hai salvato nessuna pagina web da monitorare, per aggiungere una pagina utilizza il comando /aggiungisito:" )
      

   



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

    if(type(message.text) is str):

        if uploadHtml(urlDaSalvare, message):
            bot.reply_to(message, "Url aggiunto con successo 👍")
        else:
            bot.send_message(message.chat.id, "L'url inserito era già stato aggiunto 😁")

    else:
        bot.send_message(message.chat.id, "Il nome specificato non è valido 😕")





    

#COMANDO /removeURL
@bot.message_handler(commands=['rimuovisito'])
def remove(message):
    if len(db.collection("Utente-Sito").where("utente", "==", message.chat.id).get()) == 0:
        bot.send_message(message.chat.id, "Al momento non hai salvato nessuna pagina web da monitorare, per aggiungere una pagina utilizza il comando /aggiungisito:")

    else:
        msg = bot.send_message(message.chat.id, "Bene, inviami il nome da te scelto o l'url del sito che vuoi ELIMINARE dalla lista:")
        bot.register_next_step_handler(msg,removeStep2)

def removeStep2(message): #TODO da rivedere e fare senza foreach
    try:
        perUrl = db.collection('Utente-Sito').where("sito", "==", message.text).get()
        perNome = db.collection('Utente-Sito').where("nome", "==", message.text).get()
        docs = [*perUrl, *perNome]
        if len(docs) > 0:
            for doc in docs:
                key = doc.id
                db.collection('Utente-Sito').document(key).delete()
                bot.send_message(message.chat.id, f"Il sito memorizzato come '{doc.get('nome')}' è stato eliminato \n" + doc.get('sito'))
                break

        else:    
            bot.send_message(message.chat.id, "Il sito da te specificato non risulta presente nella lista 😕")

    except:
        bot.send_message(message.chat.id, "Il sito da te specificato non risulta presente nella lista 😕")
        print("non rimosso")

@bot.message_handler(commands=['aggiungiprodotto'])
def add(message):
    
    msg = bot.send_message(message.chat.id, "Bene, mandami qui di seguito l'URL del prodotto che vuoi monitorare: ")
    bot.register_next_step_handler(msg, prodStep2)

def prodStep2(message):
    bot.send_message(message.chat.id, str(getProductprice(message.text)) + "€")

#COMANDO /removeProduct
@bot.message_handler(commands=['rimuoviprodotto'])
def removeProduct(message):
    pass

#COMANDO /productsList
@bot.message_handler(commands=['listaprodotti'])
def productsList(message):
    pass


    


@bot.message_handler(commands=['registraemail'])
def registraEmail(message):
    USER = message.chat.id
    Utente = db.collection('Utente').where("nome", "==", USER).get()[0]
    email = Utente.get("email")
    if email == "":
        msg = bot.reply_to(message,"Bene, mandami qui di seguito l'email che vuoi registrare sul tuo account:")
        bot.register_next_step_handler(msg, mailStep3)

    else:
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('Modifica ⚙️')
        itembtn2 = types.KeyboardButton('Annulla ↩️')
        markup.add(itembtn1, itembtn2)
        stringa = f"Hai già un'email registrata con l'indirizzo '{email}', vorresti modificare il tuo indirizzo? Se si seleziona 'Modifica', altrimenti seleziona 'Annulla' "
        msg = bot.send_message(USER, stringa, reply_markup=markup)
        bot.register_next_step_handler(msg, mailStep2)
        

def mailStep2(message):
    USER = message.chat.id
    Utente = db.collection('Utente').where("nome", "==", USER).get()[0]
    email = Utente.get("email")
    markup = types.ReplyKeyboardRemove()

    if message.text == "Annulla ↩️":
        bot.send_message(USER, f"Il tuo indirizzo email è rimasto invariato ({email}) 👌", reply_markup=markup)

    elif message.text == "Modifica ⚙️":
        msg = bot.send_message(USER, "Mandami qui di seguito il tuo nuovo indirizzo email:", reply_markup=markup)
        bot.register_next_step_handler(msg, mailStep3)

    else:
        bot.send_message(USER, "Ops, il messaggio da te inviato non è valido 😕", reply_markup=markup)

    

def mailStep3(message):
    USER = message.chat.id
    Utente = db.collection('Utente').where("nome", "==", USER).get()[0]
    markup = types.ReplyKeyboardRemove()
    try:
        if message.entities[0].type == "email":
            db.collection('Utente').document(Utente.id).update({"email":message.text})
            bot.send_message(message.chat.id, f"Il tuo indirizzo email '{message.text}' è stato registrato 👍", reply_markup=markup)

        else:
            bot.reply_to(message, f"Ops, l'indirizzo email inserito non è valido 😕", reply_markup=markup)

    except Exception as e:
        print(e)
        bot.reply_to(message, f"Ops, l'indirizzo email inserito non è valido 😕", reply_markup=markup)
    



            
@bot.message_handler(commands=['eliminaemail'])
def eliminaEmail(message):
    utente = message.chat.id

    email = db.collection('Utente').where("nome", "==", utente).get()[0].get("email")

    if email != "":
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('Elimina ❌')
        itembtn2 = types.KeyboardButton('Annulla ↩️')
        markup.add(itembtn1, itembtn2)
        msg = bot.send_message(utente, "Sei sicuro di voler eliminare il tuo indirizzo email? Così facendo non riceverai più notifiche tramite email, se decidi di proseguire ricordati che puoi registrare una nuova email quando vuoi tramite il comando /registraemail", reply_markup=markup)
        bot.register_next_step_handler(msg,eliminaEmailStep2)

    else:
        bot.send_message(utente, "Non hai nessuna email registrata, se vuoi ricevere notifiche sul tuo indirizzo di posta, utilizza il comando /registraemail 🙂")

def eliminaEmailStep2(message):
    utente = message.chat.id
    email = db.collection('Utente').where("nome", "==", utente).get()[0].get("email")
    markup = types.ReplyKeyboardRemove()
    if message.text == "Elimina ❌":
        key = db.collection('Utente').where('nome', '==', utente).get()[0].id
        db.collection('Utente').document(key).update({'email':''})
        bot.send_message(utente, "Indirizzo email eliminato con successo 👍", reply_markup=markup)

    elif message.text == "Annulla ↩️":
        bot.send_message(utente, f"Il tuo indirizzo email è rimasto invariato ({email}) 👌", reply_markup=markup)

    else:
        bot.send_message(utente, f"Comando non valido, il tuo indirizzo email è rimasto invariato ({email})", reply_markup=markup)




@bot.message_handler(commands=['check'])
def checkPagine(message):
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
            avvisaUtente(user, urlSalvato, nomeSito)



if __name__ == "__main__":
    ct = checkThread()
    #ct.start()
    bot.infinity_polling() 



