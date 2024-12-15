import os
import argparse
import cv2

from flask import Flask, render_template, request, send_file, redirect, url_for, Response, flash, abort
import shutil
import time
import sqlite3

import mimetypes

from ultralytics import YOLO


app = Flask(__name__)

# Definir a chave secreta no seu aplicativo Flask
app.secret_key = b'8\xbfYs/\x90\xa7\xceO\x0f]\xfc\xb1\xb6\xe7\x9dm\x1d-\x96\xa3l\x1en'
app.config['MAX_CONTENT_LENGHT'] = 16 * 1024 * 1024

BASE_PATH = os.getcwd()
UPLOAD_PATH = os.path.join(BASE_PATH, 'static/uploads/')
DATABASE_PATH = os.path.join(BASE_PATH, 'static/database/')
DATABASE = os.path.join(DATABASE_PATH, 'fruits.db')


@app.route('/')
def home():
    return render_template("index.html")


# metodo de classificacao do modelo
imgpath = None  # Definir uma variável global para armazenar o nome do arquivo


@app.route("/deteccao", methods=["GET", "POST"])
def deteccao():
    global imgpath  # Indicar que a variável imgpath será usada globalmente

    video_output_path = None  # Caminho do vídeo processado
    video_output_name = None  # Nome do vídeo processado
    original_video_output = None  # Nome do vídeo processado
    original_video_output_name = None  # Nome do vídeo processado

    if request.method == "POST":
        if 'file' in request.files:
            f = request.files['file']
            modelo_nome = request.form.get('modelo_nome')
            print("\nmodelo_nome: ", modelo_nome)
            basepath = os.path.dirname(__file__)
            file_extension = f.filename.rsplit('.', 1)[1].lower()
            print("extensao: ", file_extension)
            imgpath = f.filename  # Atribuir o nome do arquivo à variável global imgpath
            original_video_output_name = imgpath
            # Imprimir o valor da variável imgpath
            print("Imagem / Video Detectado: ", imgpath)
            print("Imagem / Video Original: ", original_video_output_name)

            file_extension = f.filename.rsplit('.', 1)[1].lower()
            # print("extensao: ",file_extension)

            # se na requisicao tiver um ficheiro e está de acordo com as extensões permitidas, faça
            if file_extension in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
                # Converter o arquivo para .jpg, se necessário
                if file_extension == 'jpeg' or file_extension == 'webp':
                    new_filename = f.filename.rsplit(
                        '.', 1)[0] + '.jpg'  # Alterar extensão para .jpg
                else:
                    new_filename = f.filename

                filepath = os.path.join(
                    basepath, 'static/uploads-imagens', new_filename)
                print("Upload folder is ", filepath)
                f.save(filepath)

                # Abrir a imagem e salvar novamente como .jpg, se necessário
                if file_extension in {'jpeg', 'png', 'gif', 'webp'}:
                    print(f"Convertendo {f.filename} para {new_filename}")
                    img = cv2.imread(filepath)
                    # Sobrescrevendo com o formato .jpg
                    cv2.imwrite(filepath, img)

                # Verificar a resolução da imagem
                img = cv2.imread(filepath)
                height, width = img.shape[:2]
                if height > 640 or width > 640:
                    print(
                        f"Redimensionando imagem de {width}x{height} para 640x640")
                    img = cv2.resize(
                        img, (640, 640), interpolation=cv2.INTER_AREA)
                    # Sobrescrever o arquivo redimensionado
                    cv2.imwrite(filepath, img)

                # YOLO na detecção de imagens com base no modelo escolhido
                if modelo_nome == 'Medium':
                    model = YOLO('M_best.pt')
                elif modelo_nome == 'Nano':
                    model = YOLO('N_best.pt')
                else:
                    model = YOLO('S_best.pt')

                # Inferência com a versão final do arquivo convertido e redimensionado
                model.predict(filepath, save=True)
                return display(new_filename)

            elif file_extension == 'mp4' or file_extension == 'mkv' or file_extension == 'avi' or file_extension == 'flv':
                filepath = os.path.join(
                    basepath, 'static/uploads-videos', f.filename)
                print("upload folder is ", filepath)
                f.save(filepath)

                video_path = filepath
                cap = cv2.VideoCapture(video_path)

                # Pegar as dimenções do video
                frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                # Definir o codec e criar o objecto VideoWrite
                # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                # Usando o codec X264 para MKV
                fourcc = cv2.VideoWriter_fourcc(*'X264')
                out = cv2.VideoWriter(
                    'static/deteccoes-videos/'+f.filename, fourcc, 30.0, (frame_width, frame_height))

                # YOLO na Detenção de imagens como base no modelo escolhido
                if modelo_nome == 'Medium':
                    model = YOLO('M_best.pt')
                elif modelo_nome == 'Nano':
                    model = YOLO('N_best.pt')
                else:
                    model = YOLO('S_best.pt')

                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # Fazer a detenção do YOLO vc8 nos frames aqui
                    results = model(frame, save=True)
                    print("results: ", results)
                    cv2.waitKey(1)

                    res_plotted = results[0].plot()
                    # cv2.imshow("result", res_plotted)

                    # Escrever o video da saida
                    out.write(res_plotted)

                    video_output_name = f.filename
                    video_output_path = 'static/deteccoes-videos/' + video_output_name
                    original_video_output = 'static/uploads-videos/' + original_video_output_name

                    if cv2.waitKey(1) == ord('q'):
                        break
                # return display(f.filename)

                # return video_feed()
                return display_video(video_output_path, original_video_output, original_video_output_name)

        # return render_template("deteccao_imagem.html", upload=True)
        return redirect(url_for('deteccao', _anchor='deteccao'))
    return render_template("deteccao_imagem.html", upload=False)

    # se o usuario nao preencher o formulario, mantem na mesma pagina
    # else:
    # return render_template('index.html')

    # folder_path = 'runs/detect'
    # subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    # latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
    # image_path = folder_path+'/'+latest_subfolder+'/'+f.filename
    # return render_template('index.html', image_path=image_path)


@app.route('/show_image/<filename>')
def show_image(filename):
    uploads_folder = os.path.join(app.root_path, "static", "uploads-imagens")
    image_path = os.path.join(uploads_folder, filename)

    # Verificar se o arquivo existe
    if not os.path.isfile(image_path):
        print(f"Arquivo não encontrado: {image_path}")
        return abort(404, description="Imagem não encontrada")

    # Detectar o MIME type com base na extensão do arquivo
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        print(f"MIME type não detectado para o arquivo: {image_path}")
        mime_type = 'application/octet-stream'  # Fallback para tipo genérico

    print(f"Servindo arquivo: {image_path}, MIME type: {mime_type}")
    return send_file(image_path, mimetype=mime_type)


@app.route('/show_video/<filename>')
def show_video(filename):
    uploads_folder = os.path.join(app.root_path+"/static", 'uploads-videos')
    video_path = os.path.join(uploads_folder, filename)
    print("video_path: ", video_path)
    # mimetype='video/x-msvideo'
    return send_file(video_path, mimetype='video/x-msvideo')


@app.route("/display_video/<video_path>")
def display_video(video_path, original_video_path, original_video_output_name):
    # video_path = f'static/deteccoes-videos/{video_path}'
    return render_template('video_display.html', video_path=video_path, original_video_path=original_video_path, original_video_output_name=original_video_output_name)


@app.route('/image/<path:filename>')
def display(filename):
    folder_path = 'runs/detect'
    subfolders = [f for f in os.listdir(
        folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(
        os.path.join(folder_path, x)))
    directory = folder_path+'/'+latest_subfolder
    # print("Mostrando sub directorios: ", directory)
    files = os.listdir(directory)
    latest_file = files[0]

    # print("ultima imagem: ",latest_file)

    filename = os.path.join(folder_path, latest_subfolder, latest_file)
    # print("file: ",filename)

    basepath = os.path.dirname(__file__)
    # latest_file_not_detected = os.path.join(basepath,'uploads', latest_file)

    # uploads_folder = os.path.join(app.root_path, 'uploads')
    # latest_file_not_detected = os.path.join(uploads_folder, filename=latest_file)
    file_extension = filename.rsplit('.', 1)[1].lower()
    print("Extensao do ficheiro: ", file_extension)

    if file_extension == 'jpg' or file_extension == 'png':
        uploads_folder = os.path.join(app.root_path, 'static/uploads-imagens')
        latest_file_not_detected = os.path.join(uploads_folder, filename)
    else:
        uploads_folder = os.path.join(app.root_path, 'static/uploads-videos')
        latest_file_not_detected = os.path.join(uploads_folder, filename)
    environ = request.environ

    if file_extension == 'jpg' or file_extension == 'jpeg' or file_extension == 'png' or file_extension == 'webp':
        # Copiar o arquivo para o diretório de destino
        shutil.copy(filename, 'static/deteccoes-imagens')

        # return send_from_directory(directory, filename) # Mostrar o resultado detectados no boldenbox
        # return render_template('display_image.html', filename=latest_file, directory=directory)
        # Renderize a mesma página com a imagem enviada
        # return render_template('index.html', latest_file=latest_file)
        # Redirecione para a página que exibirá a imagem enviada
        return render_template('deteccao_imagem.html', latest_file=latest_file,
                               latest_file_not_detected=latest_file_not_detected, file_extension=file_extension)

    if file_extension == 'mp4' or file_extension == 'mkv' or file_extension == 'avi':
        # Copiar o arquivo para o diretório de destino
        shutil.copy(filename, 'static/deteccoes-videos')

        return render_template('deteccao_imagem.html', latest_file=latest_file,
                               latest_file_not_detected=latest_file_not_detected, file_extension=file_extension)

    else:
        return "Formato do ficheiro inválido"


def fetch_data_from_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT sum(fruta_verde), sum(fruta_semi_madura), sum(fruta_madura), sum(fruta_super_madura), sum(fruta_podre) FROM relatorio')
    data = cursor.fetchone()
    conn.close()
    return data


def fetch_all_data_from_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM relatorio ORDER BY criado_em DESC')
    data = cursor.fetchall()
    conn.close()
    return data


@app.route('/relatorio')
def relatorio():
    dados_tabela = fetch_all_data_from_db()
    totals = fetch_data_from_db()
    lista = [totals[0], totals[1], totals[2], totals[3], totals[4]]
    dados = [0 if i is None else i for i in lista]
    totalSoma = sum(dados)
    if (totalSoma == 0):
        return render_template("relatorio.html", message='Sem resultados para o relatorio')
    else:
        values = [totals[0], totals[1], totals[2], totals[3], totals[4]]
        totalFrutaVerde = (totals[0] / sum(values)) * 100
        totalFrutaSemiMadura = (totals[1] / sum(values)) * 100
        totalFrutaMadura = (totals[2] / sum(values)) * 100
        totalFrutaSuperMadura = (totals[3] / sum(values)) * 100
        totalFrutaPodre = (totals[4] / sum(values)) * 100
        valueTotal = [totalFrutaVerde, totalFrutaSemiMadura,
                      totalFrutaMadura, totalFrutaSuperMadura, totalFrutaPodre]
        print("valueTotal: ", sum(values))
        # print(len(values))
        data = {

            "labels": ['Fruta Verde {}%'.format(round(totalFrutaVerde, 2)), 'Fruta Semi Madura {} %'.format(round(totalFrutaSemiMadura, 2)), 'Fruta Madura {} %'.format(round(totalFrutaMadura, 2)), 'Fruta Super Madura {} %'.format(round(totalFrutaSuperMadura, 2)), 'Fruta Podre {} %'.format(round(totalFrutaPodre, 2))],
            "datasets": [

                {
                    "label": "Relatório do Estado de Maturação das Frutas",
                    "borderWidth": 1,
                    "fillColor": "rgba(220,220,220,0.5)",
                    "backgroundColor": ['#16a34a', '#dc2626', 'yellow', 'purple'],
                    "data": valueTotal
                },
            ]
        }
        return render_template("relatorio.html", data=data, dados_tabela=dados_tabela, totalFrutaVerde=totals[0], totalFrutaSemiMadura=totals[1], totalFrutaMadura=totals[2], totalFrutaSuperMadura=totals[3], totalFrutaPodre=totals[4], total=sum(values))


with sqlite3.connect(DATABASE) as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relatorio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            imagem TEXT NOT NULL,
            fruta_verde INTEGER,
            fruta_semi_madura INTEGER,
            fruta_madura INTEGER,
            fruta_super_madura INTEGER,
            fruta_podre INTEGER,
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
        imagem = request.form.get('imagem')
        fruta_verde = request.form.get('fruta_verde', '')
        fruta_semi_madura = request.form.get('fruta_semi_madura', '')
        fruta_madura = request.form.get('fruta_madura', '')
        fruta_super_madura = request.form.get('fruta_super_madura', '')
        fruta_podre = request.form.get('fruta_podre', '')

        # Save the image to the upload folder
        # image.save(os.path.join(UPLOAD_PATH, imagem))

        # Insert the metadata into the SQLite database
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO relatorio (imagem, fruta_verde, fruta_semi_madura, fruta_madura, fruta_super_madura, fruta_podre) VALUES (?, ?, ?, ?, ?, ?)', (imagem, fruta_verde, fruta_semi_madura, fruta_madura, fruta_super_madura, fruta_podre))
            conn.commit()

        return redirect(url_for('relatorio'))
    return render_template("deteccao_imagem.html", upload=False)


# funcao para excluir o historico
@app.route('/delete-history/<int:id>', methods=['POST'])
def delete_history(id):
    if request.method == 'POST':
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
    video = cv2.VideoCapture(mp4_files)  # caminho de detenção de video
    while True:
        success, image = video.read()
        if not success:
            break
        ret, jpeg = cv2.imencode('.jpg', image)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
        time.sleep(0.1)  # Controlar o video pro um(1)ms no ecrá

# Função para detectar objectos em video numa página HTML


@app.route("/video_feed")
def video_feed():
    print("function called")
    return Response(get_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/latest_video_feed")
def latest_video_feed():
    videos_folder = os.path.join(app.static_folder, "deteccoes-videos")
    files = os.listdir(videos_folder)
    if not files:
        return "Nenhum vídeo encontrado"

    latest_file = max(files, key=lambda x: os.path.getmtime(
        os.path.join(videos_folder, x)))
    latest_file_path = os.path.join(videos_folder, latest_file)

    return send_file(latest_file_path, mimetype='video/mp4')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SISDET")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()
    # debug=True causes Restarting with stat
    app.run(host="0.0.0.0", port=args.port)
