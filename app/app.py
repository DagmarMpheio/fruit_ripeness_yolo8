import os
import argparse
from PIL import Image

import torch
import cv2
import numpy as np
import tensorflow as tf
from keras.utils import load_img, img_to_array
from keras.models import load_model


import flask
from flask import Flask, render_template, request, send_file, redirect, url_for, Response, flash
from werkzeug.utils import secure_filename
from flask import send_from_directory
import shutil
import time
import sqlite3

from ultralytics import YOLO


app = Flask(__name__)

# Definir a chave secreta no seu aplicativo Flask
app.secret_key = b'8\xbfYs/\x90\xa7\xceO\x0f]\xfc\xb1\xb6\xe7\x9dm\x1d-\x96\xa3l\x1en'

BASE_PATH = os.getcwd()
UPLOAD_PATH = os.path.join(BASE_PATH, 'static/uploads/')
DATABASE_PATH = os.path.join(BASE_PATH, 'static/database/')
DATABASE = os.path.join(DATABASE_PATH, 'motoqueiro.db')


@app.route('/')
def home():
    return render_template("index.html")
    
# metodo de classificacao do modelo
imgpath = None  # Definir uma variável global para armazenar o nome do arquivo

@app.route("/deteccao", methods=["GET", "POST"])
def deteccao():
    global imgpath  # Indicar que a variável imgpath será usada globalmente
    
    if request.method == "POST":
        if 'file' in request.files:
            f = request.files['file']
            # print(f)
            basepath = os.path.dirname(__file__)
            filepath = os.path.join(basepath,'uploads', f.filename)
            # print("upload folder is ", filepath)
            f.save(filepath)
            
            imgpath = f.filename # Atribuir o nome do arquivo à variável global imgpath
            print("Imagem Detectada: ", imgpath) # Imprimir o valor da variável imgpath

            file_extension = f.filename.rsplit('.',1)[1].lower()
            #print("extensao: ",file_extension)

            # se na requisicao tiver um ficheiro e está de acordo com as extensões permitidas, faça
            if file_extension == 'jpg':
                img = cv2.imread(filepath)
                # print("img: ",img)

                #Trabalhar com o YOLO na Detenção de imagens
                model = YOLO('best.pt')
                model.predict(filepath, save= True)
                #print("yolo: ",model)
                
                return display(f.filename)
            
            elif file_extension == 'mp4':
                video_path = filepath
                cap = cv2.VideoCapture(video_path)

                # Pegar as dimenções do video
                frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                # Definir o codec e criar o objecto VideoWrite
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter('output.mp4', fourcc,30.0,(frame_width, frame_height))

                # Inicializar o modelo YOLO v8 aqui
                model = YOLO('best.pt')

                while cap.isOpened():
                    ret, frame=cap.read()
                    if not ret: 
                        break

                    # Fazer a detenção do YOLO vc8 nos frames aqui
                    results = model(frame, save=True)
                    print(results)
                    cv2.waitKey(1)

                    res_plotted = results[0].plot()
                    cv2.imshow("result", res_plotted)

                    # Escrever o video da saida
                    out.write(res_plotted)

                    if cv2.waitKey(1)==ord('q'):
                        break
            
                return video_feed()
            
        return render_template("deteccao_imagem.html", upload=True)
    return render_template("deteccao_imagem.html", upload=False)
            
    # se o usuario nao preencher o formulario, mantem na mesma pagina
    #else:
        #return render_template('index.html')
    
  
    #folder_path = 'runs/detect'
    #subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    #latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
    #image_path = folder_path+'/'+latest_subfolder+'/'+f.filename
    #return render_template('index.html', image_path=image_path)
    
@app.route('/show_image/<filename>')
def show_image(filename):
    uploads_folder = os.path.join(app.root_path, 'uploads')
    latest_file_not_detected = os.path.join(uploads_folder, filename)
    return send_file(latest_file_not_detected, mimetype='image/jpeg')

@app.route('/image/<path:filename>')
def display(filename):
    folder_path = 'runs/detect'
    subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path,x)))
    directory = folder_path+'/'+latest_subfolder
    #print("Mostrando sub directorios: ", directory)
    files = os.listdir(directory)
    latest_file = files[0]

    #print("ultima imagem: ",latest_file)

    filename = os.path.join(folder_path, latest_subfolder, latest_file)
    #print("file: ",filename)
    
    basepath = os.path.dirname(__file__)
    #latest_file_not_detected = os.path.join(basepath,'uploads', latest_file)
   
    #uploads_folder = os.path.join(app.root_path, 'uploads')
    #latest_file_not_detected = os.path.join(uploads_folder, filename=latest_file)
    file_extension = filename.rsplit('.',1)[1].lower()
    uploads_folder = os.path.join(app.root_path, 'uploads')
    latest_file_not_detected = os.path.join(uploads_folder, filename)
    environ = request.environ
    if file_extension == 'jpg':
        # Copiar o arquivo para o diretório de destino
        shutil.copy(filename, 'static/detencoes')
        
        #return send_from_directory(directory, filename) # Mostrar o resultado detectados no boldenbox
        #return render_template('display_image.html', filename=latest_file, directory=directory)
        # Renderize a mesma página com a imagem enviada
        #return render_template('index.html', latest_file=latest_file)
        # Redirecione para a página que exibirá a imagem enviada
        return render_template('deteccao_imagem.html', latest_file=latest_file, 
                               latest_file_not_detected=latest_file_not_detected)
    
    else:
        return " Invalid file format"

def fetch_data_from_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT sum(n_com_capacete), sum(n_sem_capacete) FROM relatorio')
    data = cursor.fetchone()
    conn.close()
    return data

def fetch_all_data_from_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM relatorio')
    data = cursor.fetchall()
    conn.close()
    return data

@app.route('/relatorio')
def relatorio():
    dados_tabela = fetch_all_data_from_db()
    totals = fetch_data_from_db()
    lista = [totals[0], totals[1]]
    dados = [0 if i is None else i for i in lista]
    totalSoma = sum(dados)
    if(totalSoma == 0):
        return render_template("relatorio.html", message='Sem resultados para o relatorio')
    else:
        values = [totals[0], totals[1]]
        totalCapacete = (totals[0] / sum(values)) * 100
        totalSemCapacete = (totals[1] / sum(values)) * 100
        valueTotal = [totalCapacete, totalSemCapacete]
        #print(len(values))
        data = {
            "labels": ['Motoqueiros com capacetes', 'Motoqueiros sem capacete'],
            "datasets": [
                {
                    "label": "Relatório dos Motoqueiros detectados",
                    "borderWidth": 1,
                    "fillColor": "rgba(220,220,220,0.5)",
                    "backgroundColor": ['green', 'blue', 'yellow', 'purple'],
                    "data": valueTotal
                }
            ]
        }
        return render_template("relatorio.html", data=data, dados_tabela=dados_tabela)

with sqlite3.connect(DATABASE) as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relatorio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            imagem TEXT NOT NULL,
            n_com_capacete INTEGER,
            n_sem_capacete INTEGER,
            criado_em DATE DEFAULT CURRENT_TIMESTAMP
        )
    ''')


@app.route('/guardar', methods=['POST', 'GET'])
def guardar():
    if request.method == 'POST':
        # Check if the POST request has the file part
        # if 'image' not in request.files:
        #     return redirect(request.url)

        # image = request.files['image']
        # if image.filename == '':
        #     return redirect(request.url)

        # imagem = image.filename
        imagem = request.form.get('image', '')
        n_com_capacete = request.form.get('n_com_capacete', '')
        n_sem_capacete = request.form.get('n_sem_capacete', '')

        # Save the image to the upload folder
        # image.save(os.path.join(UPLOAD_PATH, imagem))

        # Insert the metadata into the SQLite database
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO relatorio (imagem, n_com_capacete, n_sem_capacete) VALUES (?, ?, ?)', (imagem, n_com_capacete, n_sem_capacete))
            conn.commit()

        return redirect(url_for('relatorio'))
    return render_template("deteccao_imagem.html", upload=False)


# funcao para excluir o historico
@app.route('/delete-history/<int:id>', methods=['POST'])
def delete_history(id):
    if request.method=='POST':
        # excluir historico
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                DELETE FROM relatorio WHERE id={id}
            """)
            conn.commit()
            flash('Histórico excluído com sucesso!', 'success')
        return redirect(url_for('relatorio'))

def get_frame():
    folder_path = os.getcwd()
    mp4_files = 'output.mp4'
    video = cv2.VideoCapture(mp4_files) # caminho de detenção de video
    while True:
        success, image = video.read()
        if not success:
            break
        ret, jpeg = cv2.imencode('.jpg', image)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
        time.sleep(0.1) # Controlar o video pro um(1)ms no ecrá

# Função para detectar objectos em video numa página HTML
@app.route("/video_feed")
def video_feed():
    print ("function called")
    return Response(get_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SISDET")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()
    app.run(host="0.0.0.0", port=args.port)  # debug=True causes Restarting with stat
