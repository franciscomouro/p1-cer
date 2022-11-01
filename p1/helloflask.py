from flask import Flask
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re

app = Flask(__name__)



@app.route("/")
def hello():
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

    return str(valor_final)


if __name__ == "__main__":
    #app.run()
    app.run(host='0.0.0.0', port=5000, debug=True)
