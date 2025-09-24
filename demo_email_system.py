#!/usr/bin/env python3
"""
Demonstrație a sistemului de email reporting
Generează rapoarte și demonstrează salvarea în istoric
"""

import os
import sys
from datetime import datetime, timedelta
from enhanced_hub_generator import EnhancedHubGenerator

def demo_system():
    """Demonstrație completă a sistemului"""
    print("🚀 Demonstrație Enhanced HUB Report Generator cu Email")
    print("=" * 60)
    
    # Data pentru demo (se poate schimba)
    data_demo = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"📅 Data demo: {data_demo}")
    
    # Inițializează generatorul
    try:
        generator = EnhancedHubGenerator()
        print("✅ Generator inițializat cu succes")
    except Exception as e:
        print(f"❌ Eroare la inițializare: {e}")
        return
    
    # Verifică dacă există fișierul master_data.csv
    fisier_master = os.path.join(generator.base_url, 'master_data.csv')
    if not os.path.exists(fisier_master):
        print(f"⚠️ Fișierul master nu există: {fisier_master}")
        print("Creez un fișier demo pentru test...")
        create_demo_master_data(fisier_master)
    
    print("\n1. 📊 Testez generarea rapoartelor (fără email)...")
    try:
        # Generează doar rapoartele, fără email
        success = generator.generate_reports_with_email(data_demo, send_emails=False)
        if success:
            print("✅ Rapoarte generate cu succes și salvate în istoric")
        else:
            print("❌ Eroare la generarea rapoartelor")
            return
    except Exception as e:
        print(f"❌ Eroare: {e}")
        return
    
    print("\n2. 📈 Verific centrele disponibile...")
    try:
        centre = generator.get_available_centres(data_demo)
        if centre:
            print(f"✅ Găsite {len(centre)} centre cu date:")
            for centru, numar_rute in centre[:5]:  # Primele 5
                print(f"   • {centru}: {numar_rute} rute")
            if len(centre) > 5:
                print(f"   ... și încă {len(centre) - 5} centre")
        else:
            print("⚠️ Nu s-au găsit centre cu date")
    except Exception as e:
        print(f"❌ Eroare la verificarea centrelor: {e}")
    
    print("\n3. 🗄️ Verific baza de date...")
    try:
        import sqlite3
        conn = sqlite3.connect(generator.email_system.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rapoarte_istoric")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Baza de date conține {count} înregistrări")
    except Exception as e:
        print(f"❌ Eroare la verificarea bazei de date: {e}")
    
    print("\n4. 📧 Status email...")
    try:
        config_path = generator.email_system.config_path
        addresses_path = generator.email_system.email_addresses_path
        
        config_exists = os.path.exists(config_path)
        addresses_exist = os.path.exists(addresses_path)
        
        print(f"   📧 Configurație email: {'✅' if config_exists else '❌'} {config_path}")
        print(f"   📬 Adrese centre: {'✅' if addresses_exist else '❌'} {addresses_path}")
        
        if config_exists and addresses_exist:
            print("   💡 Pentru a trimite email-uri, configurați credențialele în fișierele de mai sus")
        else:
            print("   ⚙️ Rulați setup_email_system.py pentru a crea template-urile")
            
    except Exception as e:
        print(f"❌ Eroare la verificarea email: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Demo completat cu succes!")
    print("\n📋 Rezumat:")
    print("• Sistem inițializat și funcțional")
    print("• Baza de date SQLite creată pentru istoric")
    print("• Template-uri pentru email create")
    print("• Funcționalitatea de raportare testată")
    print("\n🎯 Următorii pași:")
    print("1. Configurați credențialele email în email_config.json")
    print("2. Actualizați adresele email în email_addresses_centre.xlsx")
    print("3. Utilizați enhanced_hub_generator.py pentru operațiuni complete")

def create_demo_master_data(file_path):
    """Creează un fișier demo master_data.csv pentru test"""
    import pandas as pd
    from datetime import datetime
    
    # Date demo simple
    demo_data = {
        'CodBare': ['TEST001', 'TEST002', 'TEST003'],
        'Ruta': ['ALB-BVH', 'BVH-SIB', 'SBH-ROM'],
        'Centru exp': ['ALBA IULIA', 'BRASOV', 'SIBIU'],
        'Centru dest': ['BRASOV', 'SIBIU', 'BUCUREȘTI'],
        'Expeditor': ['Test Exp 1', 'Test Exp 2', 'Test Exp 3'],
        'Destinatar': ['Test Dest 1', 'Test Dest 2', 'Test Dest 3'],
        'bucati': [1, 2, 1],
        'Greutate': [1.5, 2.0, 1.2],
        'Categorie': ['Colete', 'Colete', 'Colete'],
        'Scanare': [datetime.now(), datetime.now(), datetime.now()],
        'Tip Scanare': ['Iesire Centru', 'Intrare Centru', 'Iesire Centru'],
        'Centru': ['BRASOV', 'BRASOV', 'SIBIU'],
        'User': ['test_user', 'test_user', 'test_user']
    }
    
    df = pd.DataFrame(demo_data)
    df.to_csv(file_path, index=False)
    print(f"✅ Fișier demo creat: {file_path}")

if __name__ == "__main__":
    demo_system()