import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

db.collection('persons').add({'name':'John', 'age':40})

#ADD DOCUMENTS (WITH AUTO IDs)
data1 = {'name': 'paolo', 'age':30, 'employed':True}
db.collection('people').add(data1)
db.collection('people').add({'name': 'marko', 'age':20, 'employed':False})


#SET DOCUMENTS WITH KNOWN IDs
data = {'name': 'paolo', 'age':30, 'employed':True}
db.collection('people').document('paolone').set(data) #document reference: paolone


#SET DOCUMENTS WITH AUTO IDS
db.collection('people').document().set(data)

#MERGING (AGGIUNGERE CAMPI AI DOCUMENTI)
db.collection('people').document('paolone').set({'indirizzo':'Milano'}, merge = True) #senza merge=true tutti i campi sarebbero stati sovrascritti e sarebbe rimasto solo address

db.collection('people').document('paolone').collection('movies').add({'name': 'avengers', 'date': '12/09/99'})
db.collection('people').document('paolone').collection('movies').document('HP').set({'name': 'harry potter', 'date': '12/09/10'})


#READ DATA
#PRENDERE UN DOCUMENTO CON ID NOTO

result = db.collection('people').document('paolone').get()

if result.exists:
    print(result.to_dict()) #to dict serve a convertire l'informazione in maniera leggibile (stile json)

#prendere tutti i documenti di una collection
docs = db.collection('people').get()

for doc in docs:
    print(doc.to_dict())

#query
docs = db.collection('people').where("age", ">", "40").get() #3 stringhe: parametro, operatore di confronto, valore
paoloni = db.collection('people').where("name", "==", "paolone").get()
persone_su_youtube_o_instagram = db.collection('people').where("socials", "array-contains-any", ["youtube", "instagram"]).get()
milano_londra = db.collection('people').where("address", "in", ["milano", "londra"]).get()

for doc in docs:
    print(doc.to_dict())



#UPDATE DATA ID NOTO
db.collection('people').document('p1').update({"age":50})
db.collection('people').document('p1').update({"age":firestore.Increment(10)}) #età+10
db.collection('people').document('p2').update({"address":"Paris"})
#se il campo esiste verrà aggiornato altrimenti verrà aggiunto al documento

db.collection('people').document('p1').update({"socials":firestore.ArrayRemove(['linkedin'])})
db.collection('people').document('p1').update({"socials":firestore.ArrayUnion(['linkedin'])})

#UPDATE DATA ID NON NOTO
#metodo 1 (dispendioso in quanto bisogna scorrere ogni volta tutti i documenti)
docs = db.collection('persons').get()
for doc in docs:
    if doc.to_dict()['age']>=40:
        key = doc.id
        db.collection('people').document(key).update({"agegroup":"middle-aged"})


#metodo 2 (più efficiente)
docs= db.collection('people').where("age",">=", 40).get() 
for doc in docs:
    key = doc.id
    db.collection('people').document(key).update({"agegroup":"middle-aged"})



#DELETE DATA - ID NOTO
db.collection('people').document('p1').delete()

#DELETE DATA - ID NOTO - field
db.collection('people').document('p2').update({"socials":firestore.DELETE_FIELD})

#DELETE DATA - ID NON NOTO 
docs = db.collection('people').where("age", ">=", "40").get()
for doc in docs:
    key = doc.id
    db.collection('people').document(key).delete()

docs = db.collection('people').where("age", ">=", "40").get()
for doc in docs:
    key = doc.id
    db.collection('people').document(key).update({"age":firestore.DELETE_FIELD})

docs = db.collection('people').get()
for doc in docs:
    key = doc.id
    db.collection('people').document(key).delete()

