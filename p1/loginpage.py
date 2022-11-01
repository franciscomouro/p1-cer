from pymongo import MongoClient
from datetime import datetime
import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, request, url_for, session
import threading
import time
import json
import urllib.request
import uuid
import hashlib

app = Flask(__name__)  
app.secret_key = "ayush"
valor_final = 0
def obtener_valor():
    url = 'https://es.investing.com/currencies/eur-usd' #dir web que queremos
    page = requests.get(url) #descargamos página
    soup = BeautifulSoup(page.content, 'html.parser')  #así nos lo interpreta como html; "le da formato".

#parte del archivo html que queremos aislar
    linea_html = str(soup.find_all('span', class_='text-2xl'))

#obtención de todos los número de dicha línea de html
    extraer_nums = [int(extraer_nums) for extraer_nums in re.findall(r'-?\d+\.?\d*', linea_html)]

#operaciones para sacar el valor exacto
    aux = len(str(extraer_nums[2]))
    valor_final=extraer_nums[1]+extraer_nums[2]/(10**aux)
    return valor_final




def aumentar_nmedias():
    client = MongoClient('localhost')
    db = client['Mongaso']
    col = db['registrados']
    x = col.find({'email' : session['email']})
    for y in x:
        y = str(y)
        pos = y.find("'nmedias_sol': '") + 16
        cadena_nueva = y[pos:]
        pos=cadena_nueva.find("'}")
        cadena_nueva = cadena_nueva[:pos]
        #print(cadena_nueva)
        cadena_nueva = int(cadena_nueva)
        cadena_nueva = cadena_nueva + 1
        cadena_nueva = str(cadena_nueva)
        myquery = {'email' : session['email']}
        newvalues = {"$set" : { 'nmedias_sol' : cadena_nueva}}
        col.update_one(myquery, newvalues)


def aumentar_nmedias_ol():
    client = MongoClient('localhost')
    db = client['Mongaso']
    col = db['registrados']
    x = col.find({'email' : session['email']})
    for y in x:
        y = str(y)
        pos = y.find("'nmedias_sol_ol': '") + 19
        cadena_nueva = y[pos:]
        pos=cadena_nueva.find("', '")
        cadena_nueva = cadena_nueva[:pos]
        #print(cadena_nueva)
        cadena_nueva = int(cadena_nueva)
        cadena_nueva = cadena_nueva + 1
        cadena_nueva = str(cadena_nueva)
        myquery = {'email' : session['email']}
        newvalues = {"$set" : { 'nmedias_sol_ol' : cadena_nueva}}
        col.update_one(myquery, newvalues)

def guardar_valores():
    client = MongoClient('localhost')
    db = client['Mongaso']
    col2 = db['prueba2']
    valor = obtener_valor()
    fecha = str(datetime.now())
    col2.insert_one({
        "valor": str(valor),
        'fecha': fecha

            })

def guardar_valores_ol():
    valor_final = obtener_valor()
    urllib.request.urlopen("https://api.thingspeak.com/update?api_key=8J32SG2ZY7TCDX1V&field1=" + str(valor_final))    


    
def timer():
    while True:
        time.sleep(118)
        guardar_valores()
        time.sleep(1)
        guardar_valores_ol()
        time.sleep(1)
        


def obtener_media_ol():
    http_r = urllib.request.urlopen("https://api.thingspeak.com/channels/1912687/feeds.json?results=2") #javi es la respuesta a la petición http (respuesta = archivo json)
    cuerpo = http_r.read().decode('utf8') #obtener el cuerpo de la respuesta http
    cuerpo_json = json.loads(cuerpo)
    cuerpo_json["feeds"]
    n_entradas = cuerpo_json["channel"]["last_entry_id"] #obtener numero de entradas

    http_r = urllib.request.urlopen("https://api.thingspeak.com/channels/1912687/feeds.json?results="+str(cuerpo_json["channel"]["last_entry_id"])) #javi es la respuesta a la petición http (respuesta = archivo json)
    cuerpo = http_r.read().decode('utf8') #obtener el cuerpo de la respuesta http
    cuerpo_json = json.loads(cuerpo)
    cuerpo_json_feeds = cuerpo_json["feeds"]
    sumatorio = 0
    for elementos in cuerpo_json_feeds:
        valor = elementos["field1"].replace("'", "")
        sumatorio = sumatorio + float(valor)
        #sumatorio = sumatorio + int(valor)
        print(valor)
    solucion = round(sumatorio/n_entradas, 4)
    return solucion
 
def obtener_ultimos_valores(umbral):
    http_r = urllib.request.urlopen("https://api.thingspeak.com/channels/1912687/feeds.json?results=2") #javi es la respuesta a la petición http (respuesta = archivo json)
    cuerpo = http_r.read().decode('utf8') #obtener el cuerpo de la respuesta http
    cuerpo_json = json.loads(cuerpo)
    cuerpo_json["feeds"]
    n_entradas = cuerpo_json["channel"]["last_entry_id"] #obtener numero de entradas

    http_r = urllib.request.urlopen("https://api.thingspeak.com/channels/1912687/feeds.json?results="+str(cuerpo_json["channel"]["last_entry_id"])) #javi es la respuesta a la petición http (respuesta = archivo json)
    cuerpo = http_r.read().decode('utf8') #obtener el cuerpo de la respuesta http
    cuerpo_json = json.loads(cuerpo)
    cuerpo_json_feeds = cuerpo_json["feeds"]
    
    contador = n_entradas-1
    valores_devueltos = []
    fechas_devueltas = []
    numero_valores = 0
    

    while (contador >= 0):
        valor = cuerpo_json_feeds[contador]["field1"].replace("'", "")
        valor = float(valor)
        if (valor > umbral):
            fecha = cuerpo_json_feeds[contador]["created_at"]
            valores_devueltos.append(valor)
            fechas_devueltas.append(fecha)
            numero_valores = numero_valores + 1
        if (numero_valores == 5):
            break
        contador = contador - 1

    return valores_devueltos, numero_valores, fechas_devueltas

def comprobar_email(): #0 si no está, 1 si está
    client = MongoClient('localhost')
    db = client['Mongaso']
    col = db['registrados']
    for entrada in col.find({}):
        entrada = str(entrada)
        pos = entrada.find("'email': '") + 10
        cadena_nueva = entrada[pos:]
        pos=cadena_nueva.find("', 'p")
        cadena_nueva = cadena_nueva[:pos]
        if (cadena_nueva == request.form['email']):
            return 1, str(entrada)
    return 0, "0"

def obtener_contrasena(cadena):
    pos = cadena.find("'password': '") + 13
    cadena_nueva = cadena[pos:]
    pos=cadena_nueva.find("', 'usuario'")
    cadena_nueva = cadena_nueva[:pos]
    #print (cadena_nueva)
    return cadena_nueva


def obtener_usuario():
    if 'username' in session:
        return session['username']
    else:
        client = MongoClient('localhost')
        db = client['Mongaso']
        col = db['registrados']
        for entrada in col.find({}):
            entrada = str(entrada)
            pos = entrada.find("'email': '") + 10
            cadena_nueva = entrada[pos:]
            pos=cadena_nueva.find("', 'p")
            cadena_nueva = cadena_nueva[:pos]
            if (cadena_nueva == session['email']):
                cad_usuario = entrada
                pos = cad_usuario.find("'usuario': '") + 12
                cadena_usuario_nueva = cad_usuario[pos:]
                pos=cadena_usuario_nueva.find("', 'nmedias_sol_ol'")
                cadena_usuario_nueva = cadena_usuario_nueva[:pos]
                #print (cadena_usuario_nueva, "uwu")
                session['username']= cadena_usuario_nueva
                return cadena_usuario_nueva

def obtener_nmedias():
    client = MongoClient('localhost')
    db = client['Mongaso']
    col = db['registrados']
    for entrada in col.find({}):
        entrada = str(entrada)
        pos = entrada.find("'email': '") + 10
        cadena_nueva = entrada[pos:]
        pos=cadena_nueva.find("', 'p")
        cadena_nueva = cadena_nueva[:pos]
        if (cadena_nueva == session['email']):
            cad_usuario = entrada
            pos = cad_usuario.find("'nmedias_sol': '") + 16
            cadena_usuario_nueva = cad_usuario[pos:]
            pos=cadena_usuario_nueva.find("'}")
            cadena_usuario_nueva = cadena_usuario_nueva[:pos]
            #print (cadena_usuario_nueva, "uwu")
            return cadena_usuario_nueva


def obtener_nmedias_ol():
    client = MongoClient('localhost')
    db = client['Mongaso']
    col = db['registrados']
    for entrada in col.find({}):
        entrada = str(entrada)
        pos = entrada.find("'email': '") + 10
        cadena_nueva = entrada[pos:]
        pos=cadena_nueva.find("', 'p")
        cadena_nueva = cadena_nueva[:pos]
        if (cadena_nueva == session['email']):
            cad_usuario = entrada
            pos = cad_usuario.find("'nmedias_sol_ol': ") + 19
            cadena_usuario_nueva = cad_usuario[pos:]
            #print (cadena_usuario_nueva)
            pos=cadena_usuario_nueva.find("', 'nmedi")
            cadena_usuario_nueva = cadena_usuario_nueva[:pos]
            #print (cadena_usuario_nueva, "uwu online")
            return cadena_usuario_nueva

def obtener_media_local():

    client = MongoClient('localhost')
    db = client['Mongaso']
    col2 = db['prueba2']
    acumulacion = 0
    for entrada in col2.find({}):
        entrada = str(entrada)
        pos = entrada.find("'valor': '") + 10
        cadena_nueva = entrada[pos:]
        pos=cadena_nueva.find("', 'fecha'")
        cadena_nueva = cadena_nueva[:pos]
        #print(cadena_nueva)
        cadena_nueva = float(cadena_nueva)
        acumulacion = acumulacion + cadena_nueva
    res = round(acumulacion/(col2.count_documents({})), 4)
    return res

@app.route('/')  
def home():  

    if 'email' in session: 
        return render_template("logeado.html",nombre = obtener_usuario(), valor = str(obtener_valor()), nmedias = obtener_nmedias(), nmedias_ol = obtener_nmedias_ol())
    else:
        return render_template("homepage2.html", valor = str(obtener_valor()))  
    

@app.route('/registro')
def registro():
    return render_template("registropage.html")
@app.route('/intermedio', methods = ["POST"])
def intermedio():
    correo = request.form['email']
    if (comprobar_email()[0] == 0):
        session['email']=request.form['email']
        session['username'] = request.form['usuario']
        contr_sin_cifrar = request.form['pass']
        sal = uuid.uuid4().hex
        contrasena_codif = hashlib.sha256(sal.encode() + contr_sin_cifrar.encode()).hexdigest() + ':' + sal #sal sin cifrar aparte
        client = MongoClient('localhost')
        db = client['Mongaso']
        col = db['registrados']
        col.insert_one({
            "email": session['email'],
            'password': contrasena_codif,
            'usuario': request.form['usuario'],
            'nmedias_sol_ol': "0",
            'nmedias_sol': "0"

                })

        return render_template("success_l.html")

    return render_template("error.html") 
@app.route('/medialocal', methods = ["POST"])
def medialocal():
    #print (request.args.get, "swanseneger")
    media_local = str(obtener_media_local())
    aumentar_nmedias()
    return render_template("medialocal.html", media_local=media_local)

@app.route('/mediaonline', methods = ["POST"])
def mediaonline():
    #print("me ha dado lepra")
    media_online = str(obtener_media_ol())
    aumentar_nmedias_ol()
    return render_template("mediaonline.html", media_online=media_online)

@app.route('/umbralhistorico', methods = ["POST"])
def umbral_historico():
    if request.method == "POST":
        try:
            umbral = float(request.form['umbral'])
            valores_obtenidos, numero_valores, fechas_devueltas = obtener_ultimos_valores(umbral)   
            return render_template('success_umbral.html', numero_valores=numero_valores, valores_obtenidos=valores_obtenidos, fechas_devueltas=fechas_devueltas) 
        except:
            return render_template('error_umbral.html')
        

@app.route('/login')  
def login():  
    return render_template("loginpage3.html")  
@app.route('/success',methods = ["POST"])   
def success(): 
    if request.method == "POST":
        comprobacion = comprobar_email()
        if (comprobacion[0] == 1):
            contrasena_rec, sal_rec = obtener_contrasena(comprobacion[1]).split(':')
            contrasena_comp = hashlib.sha256(sal_rec.encode() + request.form['pass'].encode()).hexdigest()
            #print(contrasena)
            #print(comprobacion[1])
            if (contrasena_comp == contrasena_rec):
                session['email'] = request.form['email']
                return render_template('success3.html')
            return render_template('loginmal.html')

@app.route('/graficas', methods = ["POST"])
def graficas():
    if request.method == "POST":
        return render_template('graficas.html')

@app.route('/logout')  
def logout(): 
  if 'email' in session:  
    session.pop('email',None)
    session.pop('username', None)
    return render_template('logoutpage2.html');  
  else:  
    return '<p>user already logged out</p>'   
@app.route('/profile')  
def profile():  
   if 'email' in session:  
      email = session['email']  
      return              render_template('profile.html',name=email)   
   else:  
    return '<p>Please login first</p>'  
if __name__ == "__main__":
    
    t = threading.Thread(target = timer)
    t.start()

    #app.run()
    app.run(host='0.0.0.0', port=5000, debug=True)
     
