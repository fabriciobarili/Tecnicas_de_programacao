import pytesseract
from ImageReader import *
import csv
import pandas as pd
import re
from geopy.geocoders import Nominatim

unique_id = uuid.uuid4().hex

image_path = 'Images/UBER_V2_3.jpg'
output_dir = 'Images/sliced'

original, processed = process_image(image_path)
cv2.imwrite(f'Images/img_processed/{unique_id}.jpg', processed)

data = pytesseract.image_to_string(processed, 'por')
#print(data)

XML = pytesseract.image_to_data(processed, 'por')

dataset_xml = set_xml_values_on_dataset(XML)
#print(dataset_xml)

# Convert dataset_xml to a pandas DataFrame
df = pd.DataFrame(dataset_xml)

# Optionally, save the DataFrame to a CSV file
logging.info("Sanitizing the dataset.")
sanitized_dataset = dataset_xml[
    (df['conf'].astype(float) >= 70) &  # Keep rows with confidence >= 65
    (df['top'].astype(int) >= 700) &  # The price starts at 700
    (df['text'].str.strip() != '') &    # Remove rows with empty 'text'
    (df['word_num'].astype(int) >= 1)   # Remove rows with Word_Num < 0
]

# Create a new dataset joining strings by block_num + par_num
joined_dataset = sanitized_dataset.groupby(['block_num', 'par_num']).agg(
    max_height=('height', 'sum'),
    lowest_top=('top', 'min'),
    joined_text=('text', lambda x: ' '.join(x))
).reset_index()
#print(joined_dataset)

#print(sanitized_dataset)

sanitized_dataset.to_csv('sanitized_dataset.csv', index=False, encoding='utf-8-sig')
df.to_csv('df.csv', index=False, encoding='utf-8-sig')

logging.info("Grouping the dataset by block_num and par_num.")
grouped_dataset = sanitized_dataset.groupby(['block_num', 'par_num']).agg(
    max_height=('height', 'sum'),
    lowest_top=('top', 'min'),
    combined_text=('text', lambda x: ' '.join(x))  # Concatenate text for each group
).reset_index()

logging.info("Saving wrapped blocks.")





def extract_ride_info(text):
    # Price: R$ followed by float with comma
    price_pattern = r'R\$ ?(\d{1,3}(?:\.\d{3})*,\d{2})'
    # Score: float with comma, not preceded by R$
    score_pattern = r'\b\d{1,2},\d{2}\b'
    # Time: number before 'minuto' or 'minutos'
    time_pattern = r'(\d{1,3}) ?minutos?'
    # Distance: float with dot before 'km' inside parentheses or not
    distance_pattern = r'(\d{1,3}(?:[.,]\d{1,2})?) ?km'
    # Dropoff address: after km and before a line break or colon
    dropoff_pattern = r'km\)\s*([^\n:]+)'
    # Pickup address: next line after dropoff (if multiline string)
    pickup_pattern = r'km\)[^\n]*\n([^\n]+)'

    result = {}

    # Price
    price_match = re.search(price_pattern, text)
    result['price'] = price_match.group(1).replace('.', '').replace(',', '.') if price_match else None

    # Score (find all, skip if preceded by R$)
    score_match = None
    for m in re.finditer(score_pattern, text):
        start = m.start()
        preceding = text[max(0, start-3):start]
        if not re.search(r'R\$\s*$', preceding):
            score_match = m
            break
    result['score'] = score_match.group(0).replace(',', '.') if score_match else None

    # Time
    time_match = re.search(time_pattern, text)
    result['minutes'] = int(time_match.group(1)) if time_match else None

    # Distance
    distance_match = re.search(distance_pattern, text)
    if distance_match:
        result['distance'] = float(distance_match.group(1).replace(',', '.'))
    else:
        result['distance'] = None

    # Dropoff address
    dropoff_match = re.search(dropoff_pattern, text, re.IGNORECASE)
    result['dropoff_address'] = dropoff_match.group(1).strip() if dropoff_match else None

    # Pickup address
    pickup_match = re.search(pickup_pattern, text, re.IGNORECASE)
    result['pickup_address'] = pickup_match.group(1).strip() if pickup_match else None

    return result


for idx, row in grouped_dataset.iterrows():
    block_num = row['block_num']
    par_num = row['par_num']
    max_height = row['max_height']
    lowest_top = row['lowest_top']
    combined_text = row['combined_text']
    print(f"Text: {combined_text}")
    info = extract_ride_info(combined_text)
    #print(info)
    # Create a new image for the wrapped block
    #wrapped_block_img = processed[lowest_top:lowest_top + max_height, :]

    # Save the wrapped block image
    #cv2.imwrite(f'Images/wrapped_blocks/{unique_id}_{block_num}_{par_num}.jpg', wrapped_block_img)
#fragment_img = save_wrapped_blocks(grouped_dataset, processed, output_dir, unique_id)

def extract_ride_info(dataset, text_column='combined_text'):
    """
    Processes a dataset, extracting all pattern names and values from each text entry.
    Returns a list of dicts with 'text', 'pattern', and 'value' for each match.
    Only exports patterns with a non-None value.
    """
    results = []
    price_pattern = r'R\$ ?(\d{1,3}(?:\.\d{3})*,\d{2})'
    score_pattern = r'\b\d{1,2},\d{2}\b'
    time_pattern = r'(\d{1,3}) ?minutos?'
    distance_pattern = r'(\d{1,3}(?:[.,]\d{1,2})?) ?km'
    address_pattern = (
        r'((?:Rua|Avenida|Av\.?|Travessa|Praça|Rodovia|Estrada|Alameda|Largo|Vila|R\.|Tv\.|Pç\.)'
        r'[\w\s\.,\-º°]*'           # Street name (can be empty)
        r'(?:\d{1,5})?'             # Optional number
        r'(?:[\w\s\.,\-º°]+)?'      # Optional complement/neighborhood
        r'(?:-\s*[\w\s]+)?'         # Optional dash and neighborhood/city
        r'(?:,\s*[\w\s]+)?'         # Optional comma and city
        r'(?:-\s*[A-Z]{2})?'        # Optional dash and state
        r'(?:;\s*\d{5}-\d{3})?'     # Optional CEP
        r')'
    )

    for _, row in dataset.iterrows():
        text = row[text_column]

        # Price
        for price_match in re.finditer(price_pattern, text):
            value = price_match.group(1).replace('.', '').replace(',', '.')
            if value:
                results.append({'text': text, 'pattern': 'price', 'value': value})

        # Score (skip if preceded by R$)
        for m in re.finditer(score_pattern, text):
            start = m.start()
            preceding = text[max(0, start-3):start]
            if not re.search(r'R\$\s*$', preceding):
                value = m.group(0).replace(',', '.')
                if value:
                    results.append({'text': text, 'pattern': 'score', 'value': value})

        # Time (minutes)
        for time_match in re.finditer(time_pattern, text):
            value = time_match.group(1)
            if value:
                results.append({'text': text, 'pattern': 'minutes', 'value': int(value)})

        # Distance (km)
        for distance_match in re.finditer(distance_pattern, text):
            value = distance_match.group(1)
            if value:
                results.append({'text': text, 'pattern': 'distance', 'value': float(value.replace(',', '.'))})

        # Address (improved regex)
        for address_match in re.finditer(address_pattern, text, re.IGNORECASE):
            value = address_match.group(1).strip()
            if value:
                results.append({'text': text, 'pattern': 'address', 'value': value})

    return results

# Example usage:
extracted = extract_ride_info(grouped_dataset)
for item in extracted:
    print(item['pattern'], item['value'])


