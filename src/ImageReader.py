import os
import cv2
import pytesseract
import numpy as np
from PIL import Image, ImageEnhance
import uuid
from typing import List, Dict, Tuple
import re
import logging
import sys
from datetime import datetime
import pandas as pd

# Usando o Pytesseract para OCR
# Definindo o caminho do executável do Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configuração do arquivo de log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('image_processing.log')
    ]
)

# Função para processar a imagem e aplicar melhorias para OCR
def process_image(image_path, output_dir='Images/processed'):
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        img = Image.open(image_path)

        # Aumentando a nitidez da imagem
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(3)

        # Convertendo a imagem para RGB
        cv_img = np.array(img)
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)

        # Convertendo para escala de cinza
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # Aplicando threshold adaptativo para melhorar o contraste
        processed = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            21,
            10
        )

        # Salvando a imagem processada
        processed_image_name = os.path.join(output_dir, "processed_image.jpg")
        cv2.imwrite(processed_image_name, processed)

        return cv_img, processed

    except Exception as e:
        print(f"Erro no processamento da imagem: {e}")
        return None, None

# Converte dados XML do OCR em um DataFrame do pandas
def set_xml_values_on_dataset(xml_data, pandas_config=None):
    """
    Converte dados XML em um DataFrame do pandas.
    """
    rows = []
    for line in xml_data.splitlines()[1:]:  # Ignora o cabeçalho
        values = line.split('\t')
        if len(values) >= 12:  # Garante que há colunas suficientes
            rows.append({
                "level": values[0],
                "page_num": values[1],
                "block_num": values[2],
                "par_num": values[3],
                "line_num": values[4],
                "word_num": values[5],
                "left": values[6],
                "top": values[7],
                "width": values[8],
                "height": int(values[9]),
                "conf": values[10],
                "text": values[11]
            })

    # Aplica configuração do pandas se fornecida
    if pandas_config:
        return pd.DataFrame(rows, **pandas_config)
    return pd.DataFrame(rows)

# Salva blocos de texto agrupados como imagens separadas
def save_wrapped_blocks(grouped_dataset, processed_image, output_dir, unique_id):
    results = []
    #print(grouped_dataset)
    for _, row in grouped_dataset.iterrows():
        y_start = int(row['lowest_top'])
        y_end = y_start + int(row['max_height'])
        wrapped_image = processed_image[y_start:y_end, :]  # Pega toda a largura, da menor até a maior altura

        # Salva a imagem do bloco
        img_name = f"{unique_id}_wrapped_block_{row['block_num']}_par_{row['par_num']}.jpg"
        output_path = os.path.join(output_dir, img_name)
        cv2.imwrite(output_path, wrapped_image)
        results.append({
            'block_num': row['block_num'],
            'par_num': row['par_num'],
            'img_name': img_name
        })
    return results

# Extrai informações da corrida usando expressões regulares
def extract_ride_info_using_Regex(dataset, text_column='combined_text'):
    """
    Processa o dataset, extraindo padrões de preço, nota, tempo, distância e endereço.
    Retorna uma lista de dicionários com 'text', 'pattern' e 'value' para cada ocorrência.
    """
    results = []
    price_pattern = r'R\$ ?(\d{1,3}(?:\.\d{3})*,\d{2})'
    score_pattern = r'\b\d{1,2},\d{2}\b'
    time_pattern = r'(\d{1,3}) ?minutos?'
    distance_pattern = r'(\d{1,3}(?:[.,]\d{1,2})?) ?km'
    address_pattern = (
        r'((?:Rua|Avenida|Av\.?|Travessa|Praça|Rodovia|Estrada|Alameda|Largo|Vila|R\.|Tv\.|Pç\.)'
        r'[\w\s\.,\-º°]*'
        r'(?:\d{1,5})?'
        r'(?:[\w\s\.,\-º°]+)?'
        r'(?:-\s*[\w\s]+)?'
        r'(?:,\s*[\w\s]+)?'
        r'(?:-\s*[A-Z]{2})?'
        r'(?:;\s*\d{5}-\d{3})?'
        r')'
    )

    for _, row in dataset.iterrows():
        text = row[text_column]

        # Preço
        for price_match in re.finditer(price_pattern, text):
            value = price_match.group(1).replace('.', '').replace(',', '.')
            if value:
                results.append({'text': text, 'pattern': 'price', 'value': value})

        # Nota (ignora se vier após R$)
        for m in re.finditer(score_pattern, text):
            start = m.start()
            preceding = text[max(0, start-3):start]
            if not re.search(r'R\$\s*$', preceding):
                value = m.group(0).replace(',', '.')
                if value:
                    results.append({'text': text, 'pattern': 'score', 'value': value})

        # Tempo em minutos
        for time_match in re.finditer(time_pattern, text):
            value = time_match.group(1)
            if value:
                results.append({'text': text, 'pattern': 'minutes', 'value': int(value)})

        # Distância em km
        for distance_match in re.finditer(distance_pattern, text):
            value = distance_match.group(1)
            if value:
                results.append({'text': text, 'pattern': 'distance', 'value': float(value.replace(',', '.'))})

        # Endereço (regex aprimorado)
        for address_match in re.finditer(address_pattern, text, re.IGNORECASE):
            value = address_match.group(1).strip()
            if value:
                results.append({'text': text, 'pattern': 'address', 'value': value})

    return results

# Função principal que executa todo o fluxo de leitura e extração
def Reader(image_path, output_dir='Images/sliced'):
    image_basename = os.path.splitext(os.path.basename(image_path))[0]

    logging.info(f"Processando imagem: {image_path}")
    original, processed = process_image(image_path)

    logging.info("Extraindo texto da imagem processada.")
    data = pytesseract.image_to_string(processed, 'por')

    logging.info("Extraindo dados detalhados do OCR.")
    XML = pytesseract.image_to_data(processed, 'por')
    dataset_xml = set_xml_values_on_dataset(XML)

    logging.info("Sanitizando o dataset.")
    sanitized_dataset = dataset_xml[
        (dataset_xml['conf'].astype(float) >= 50) &
        (dataset_xml['top'].astype(int) >= 500) &
        (dataset_xml['text'].str.strip() != '') &
        (dataset_xml['word_num'].astype(int) >= 0)
    ]

    logging.info("Agrupando o dataset por block_num e par_num.")
    grouped_dataset = sanitized_dataset.groupby(['block_num', 'par_num']).agg(
        max_height=('height', 'sum'),
        lowest_top=('top', 'min'),
        combined_text=('text', lambda x: ' '.join(x))
    ).reset_index()

    logging.info("Salvando blocos agrupados como imagens.")
    unique_id = uuid.uuid4().hex
    fragment_img = save_wrapped_blocks(grouped_dataset, processed, output_dir, unique_id)

    logging.info("Salvando imagens originais e processadas.")
    cv2.imwrite(f'Images/img_original/{unique_id}.jpg', original)
    cv2.imwrite(f'Images/img_processed/{unique_id}.jpg', processed)

    # Cria novo dataset juntando textos por block_num + par_num
    joined_dataset = sanitized_dataset.groupby(['block_num', 'par_num']).agg(
        max_height=('height', 'sum'),
        lowest_top=('top', 'min'),
        joined_text=('text', lambda x: ' '.join(x))
    ).reset_index()

    logging.info("Salvando blocos agrupados novamente.")
    unique_id = uuid.uuid4().hex
    fragment_img = save_wrapped_blocks(joined_dataset, processed, output_dir, unique_id)
    fragment_dataset = pd.DataFrame(fragment_img)
    fragment_dataset.to_csv(f'csv/{unique_id}_fragment_dataset.csv', index=False, encoding='utf-8-sig')

    # Faz o merge do joined_dataset com fragment_dataset usando block_num e par_num
    merged_dataset = pd.merge(
        fragment_dataset,
        joined_dataset[['block_num', 'par_num', 'joined_text']],
        left_on=['block_num', 'par_num'],
        right_on=['block_num', 'par_num'],
        how='left'
    )
    #print(merged_dataset)

    # Salva o dataset mesclado em CSV
    extracted = extract_ride_info_using_Regex(grouped_dataset)
    

    # Cria um DataFrame com as informações extraídas
    extracted_df = pd.DataFrame([{'pattern': item['pattern'], 'value': item['value']} for item in extracted])
    extracted_df['img_basename'] = unique_id
    extracted_df.to_csv(f'csv/{unique_id}_extracted_info.csv', index=False, encoding='utf-8-sig')

    merged_dataset.to_csv(f'csv/{unique_id}_merged_dataset.csv', index=False, encoding='utf-8-sig')
    
    #return unique_id, merged_dataset , extracted_df
    # Retorna também os nomes das imagens originais e processadas
    original_img_name = f'Images/img_original/{unique_id}.jpg'
    processed_img_name = f'Images/img_processed/{unique_id}.jpg'
    return unique_id, merged_dataset, extracted_df, original_img_name, processed_img_name

# Retorna o valor de um padrão específico no DataFrame
# Se houver várias ocorrências, retorna a ocorrência especificada (1 para a primeira, 2 para a segunda, etc.)
def get_pattern_value(df, pattern, occurrence=1):
    matches = df[df['pattern'] == pattern]
    if len(matches) >= occurrence:
        return matches.iloc[occurrence - 1]['value']
    return None

def to_scalar(val):
    if isinstance(val, pd.Series):
        return val.item()
    return val