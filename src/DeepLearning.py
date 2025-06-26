import pandas as pd
from geopy.geocoders import Nominatim
import re


# Função para extrair features de endereço
def process_address(address):
    # Extrair CEP (se existir)
    cep = re.search(r'\d{5}-?\d{3}', address)
    #print(cep)
    cep = cep.group(0) if cep else None

    #print(address)

    # Extrair número (se existir)
    numero = re.search(r'(?<!\d)\d{1,5}(?!\d)', address)
    numero = numero.group(0) if numero else -1

    # Contar componentes do endereço
    parts = [p.strip() for p in re.split(r'[,-]', address) if p.strip()]
    num_components = len(parts)

    return {
        'tem_cep': 1 if cep else 0,
        'tem_numero': 1 if numero != -1 else 0,
        'num_componentes': num_components,
        'comprimento_endereco': len(address)
    }