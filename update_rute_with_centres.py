#!/usr/bin/env python3
"""
Script pentru actualizarea fișierelor de rute cu coloana Centru
Maparea se face pe baza codurilor din numele rutelor
"""

import pandas as pd
import os

def get_centre_mapping():
    """Returnează dicționarul de mapare între coduri și centre"""
    return {
        # Coduri comune pentru centre
        'ALB': 'ALBA IULIA',
        'ARD': 'ARAD', 
        'BAC': 'BACĂU',
        'BMR': 'BISTRIȚA',
        'BRG': 'BĂRĂGAN',
        'BRL': 'BRĂILA',
        'BRV': 'BRĂILA',  # Brăila varianta
        'BST': 'BESTFACTOR',
        'BUZ': 'BUZĂU',
        'CLJ': 'CLUJ',
        'CLM': 'CĂLĂRAȘI',
        'CMP': 'CÂMPINA',
        'CRS': 'CRAIOVA',
        'CRV': 'CRAIOVA',  # Craiova varianta
        'CTA': 'CONSTANȚA',
        'DTS': 'DROBETA',
        'DVA': 'DEVA',
        'FCS': 'FOCȘANI',
        'FGR': 'FĂGĂRAȘ',
        'FLT': 'FLOREȘTÎ',
        'GLT': 'GALAȚI',
        'IAS': 'IAȘI',
        'LGJ': 'LUGOJ',
        'MCC': 'MEDIAȘ',
        'MED': 'MEDIAȘ',  # Mediaș varianta
        'ONS': 'ONEȘTÎ',
        'ORD': 'ORADEA',
        'OTP': 'OTOPENI',
        'PIT': 'PITEȘTI',
        'PLO': 'PLOIEȘTI',
        'PPT': 'POPEȘTI',
        'RGN': 'REȘIȚA',
        'ROM': 'BUCUREȘTI',
        'RST': 'REȘIȚA',  # Reșița varianta
        'RVL': 'RÂMNICU VÂLCEA',
        'SFG': 'SFÂNTU GHEORGHE',
        'SIB': 'SIBIU',
        'SLB': 'SĂLAJ',
        'SLT': 'SLATINA',
        'SMR': 'SATU MARE',
        'T': 'TIMIȘOARA',
        'TGJ': 'TARGU JIU',
        'TGM': 'TÂRGU MUREȘ',
        'TGS': 'TÂRGOVIȘTE',
        'TGV': 'TÂRGOVIȘTE',  # Târgoviște varianta
        'TIM': 'TIMIȘOARA',
        'TLC': 'TULCEA',
        'TNV': 'TURNUL NOVAC',
        'URZ': 'URZICENI',
        'ZAL': 'ZALĂU',
        'NUGAT': 'NUGAT'
    }

def extract_centre_from_route_name(route_name, centre_mapping):
    """Extrage centrul din numele rutei pe baza mapping-ului"""
    route_name = route_name.strip()
    
    # Elimină prefixele comune
    if route_name.startswith('PL '):
        route_name = route_name[3:]
    elif route_name.startswith('RMB '):
        route_name = route_name[4:]
    
    # Împarte pe '-' și ia prima parte
    parts = route_name.split('-')
    if len(parts) >= 2:
        first_code = parts[0].strip()
        second_code = parts[1].split()[0].strip()  # În caz că are număr sau alte caractere
        
        # Pentru rutele care vin spre hub (ex: ALB-BVH), centrul este primul cod
        if second_code in ['BVH', 'SBH']:
            return centre_mapping.get(first_code, first_code)
        # Pentru rutele care pleacă din hub (ex: BVH-ALB), centrul este al doilea cod
        elif first_code in ['BVH', 'SBH']:
            return centre_mapping.get(second_code, second_code)
    
    # Cazuri speciale sau fallback
    return 'NECUNOSCUT'

def update_rute_file_with_centres(file_path, centre_mapping):
    """Actualizează fișierul de rute cu coloana Centru"""
    print(f"Actualizez fișierul: {file_path}")
    
    # Citește fișierul existent
    df = pd.read_csv(file_path)
    
    # Verifică dacă coloana Centru există deja
    if 'Centru' in df.columns:
        print(f"Coloana 'Centru' există deja în {file_path}")
        return
    
    # Adaugă coloana Centru
    df['Centru'] = df['Denumire'].apply(lambda x: extract_centre_from_route_name(x, centre_mapping))
    
    # Salvează fișierul actualizat
    df.to_csv(file_path, index=False)
    print(f"Coloana 'Centru' a fost adăugată cu succes în {file_path}")
    
    # Afișează câteva exemple pentru verificare
    print("Primele 10 rute cu centrele asociate:")
    print(df[['Denumire', 'Centru']].head(10).to_string(index=False))
    print()

def main():
    """Funcția principală"""
    base_path = '/Users/telermarius/Library/CloudStorage/Dropbox/DSC/Rapoarte/HUB Brasov/Utile'
    
    # Fișierele de rute de actualizat
    rute_files = [
        os.path.join(base_path, 'ruteBrasov.csv'),
        os.path.join(base_path, 'ruteSIBIU.csv')
    ]
    
    centre_mapping = get_centre_mapping()
    
    print("Actualizez fișierele de rute cu coloana 'Centru'...")
    print("=" * 60)
    
    for file_path in rute_files:
        if os.path.exists(file_path):
            update_rute_file_with_centres(file_path, centre_mapping)
        else:
            print(f"ATENȚIE: Fișierul {file_path} nu există!")
    
    print("=" * 60)
    print("Actualizarea fișierelor de rute s-a încheiat!")

if __name__ == "__main__":
    main()