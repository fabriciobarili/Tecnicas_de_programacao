# filepath: /UberReader/UberReader/src/main.py
#Coleta de informações de aplicativos
import datetime
import cv2
import pytesseract
from DeepLearning import *
from ImageReader import *
from DBConnection import *
import pandas as pd
from Classes import *
import uuid
import logging
from Classes import *
from DBConnection import *

# Configure logging
logging.basicConfig(
    filename='uber_reader.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    try:
        logging.info("Inicializadndo UberReader script.")
        output_dir = 'Images/sliced'
        
        for i in range(1, 6):
            

            image_path = f'Images/UBER_V2_{i}.jpg'
            unique_id,r,s,processed, original = Reader(image_path, output_dir)
            
            #pegando, a partir das strings processadas, os valores de cada campo
            #quando o padrão aparece mais de uma vez, vejo qual ordem desejo pegar
            distance_pickup_km = get_pattern_value(s, 'distance', 1)
            distance_travel_km = get_pattern_value(s, 'distance', 2)
            pickup_address = get_pattern_value(s, 'address', 1)
            drop_address = get_pattern_value(s, 'address', 2)
            distance_travel_time = get_pattern_value(s, 'minutes', 1)
            distance_pickup_time = get_pattern_value(s, 'minutes', 2)
            ride_value = get_pattern_value(s, 'price', 1)
            preco_extra = get_pattern_value(s, 'price', 2)
            passenger_score = get_pattern_value(s, 'score', 1)

            ride = UberOfferedRide.create(original, processed, unique_id, ride_value, passenger_score, distance_pickup_km, distance_pickup_time, distance_travel_km, distance_travel_time, pickup_address, drop_address)
            con = get_connection()
            if con:
                insert_uber_offered_ride(con, ride)
                logging.info(f"Informações da corrida inseridas no banco de dados com sucesso. ID único: {unique_id}")
                logging.info(f"Processamento da imagem {i} concluído. ID único: {unique_id}")
                con.close()
            else:
                logging.error("Falha ao conectar ao banco de dados.")

            # Criando e inserindo as imagens fatiadas no banco de dados
            sliced_images = []

            # Criando um DataFrame pandas com as imagens fatiadas
            df_sliced = pd.DataFrame(r)
            print("Iniciando o processamento das imagens fatiadas.")
            img = SlicedImage.create(unique_id, df_sliced['img_name'][0], df_sliced['block_num'][0], df_sliced['par_num'][0], df_sliced['joined_text'][0])           
            logging.info(f"Imagem fatiada criada: {img.img_name} com ID único: {unique_id}")
            for idx, row in df_sliced.iterrows():
                con = get_connection()
                img = SlicedImage.create(unique_id, row['img_name'], row['block_num'], row['par_num'], row['joined_text'])
                if con:
                    insert_sliced_image(con, img)
                    logging.info(f"Imagem fatiada {img.img_name} inserida no banco de dados com sucesso. ID único: {unique_id}")
                    #sliced_images.append(img)
                    con.close()
                else:
                    logging.error("Falha ao conectar ao banco de dados.")
                logging.info(f"Processamento da imagem {i} concluído. ID único: {unique_id}")
        
        logging.info("Script completado com sucesso.")

    except Exception as e:
        logging.error(f"Ocorreu um erro: {e}")
