# import os, requests
# import main

# def paginaCambiata(url, storageId):
#     newSoup = main.get_soup(url)
#     oldSoup = main.storage.child(storageId).download(main.storagePath, storageId)
#     print(newSoup)

# def checkPagine():
#     siti = main.db.collection('Sito').get()
#     utenti = main.db.collection('Utente-Sito').get()
#     sitiCambiati = []
#     utentiDaAvvisare = []
#     for sito in siti:
#         key = sito.key
#         urlSito = main.db.collection('Sito').document(key).get('url')
#         storageid = main.db.collection('Sito').document(key).get('storageid')
        
#         if paginaCambiata(urlSito, storageid):
#             sitiCambiati.append(urlSito)

#     for utente in utenti:
#         key = utente.key
#         urlSalvato = main.db.collection('Utente-Sito').document(key).get('sito')
#         user = main.db.collection('Utente-Sito').document(key).get('utente')
#         nomeSito = main.db.collection('Utente-Sito').document(key).get('nome')
        
#         if urlSalvato in sitiCambiati:
#             avvisaUtente(user, urlSalvato, nomeSito)

# def checkProdotti():
#     pass

# def avvisaUtente(utente, url, nomeSito):
#     pass

