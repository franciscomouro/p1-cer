from pymongo import MongoClient
import time
from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime


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


while (True):
    guardar_valores()
    time.sleep(120)