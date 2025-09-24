#!/usr/bin/env python3
"""
Script pentru migrarea fișierelor de configurare în folderul Utile
"""

import os
import shutil

def migrate_config_files():
    """Migrează fișierele de configurare în folderul Utile"""
    print("🚚 Migrare fișiere de configurare în folderul Utile")
    print("=" * 55)
    
    base_path = '/Users/telermarius/Library/CloudStorage/Dropbox/DSC/Rapoarte/HUB Brasov/'
    utile_path = os.path.join(base_path, 'Utile')
    
    # Asigură că folderul Utile există
    os.makedirs(utile_path, exist_ok=True)
    print(f"📁 Folder Utile: {utile_path}")
    
    # Lista fișierelor de migrat
    files_to_migrate = [
        'email_config.json',
        'email_addresses_centre.xlsx',
        'rapoarte_istoric.db',
        'email_reporting.log'
    ]
    
    migrated_count = 0
    
    for filename in files_to_migrate:
        source_path = os.path.join(base_path, filename)
        dest_path = os.path.join(utile_path, filename)
        
        if os.path.exists(source_path):
            try:
                if os.path.exists(dest_path):
                    print(f"⚠️ {filename}: Există deja în Utile - se păstrează cel existent")
                else:
                    shutil.move(source_path, dest_path)
                    print(f"✅ {filename}: Migrat cu succes")
                    migrated_count += 1
            except Exception as e:
                print(f"❌ {filename}: Eroare la migrare - {str(e)}")
        else:
            print(f"📄 {filename}: Nu există în locația sursă")
    
    print(f"\n" + "=" * 55)
    print(f"📊 Rezultat migrare:")
    print(f"• Fișiere migrate: {migrated_count}")
    print(f"• Locație nouă: {utile_path}")
    
    # Verifică structura finală
    print(f"\n📋 Conținut folder Utile:")
    if os.path.exists(utile_path):
        utile_files = os.listdir(utile_path)
        config_files = [f for f in utile_files if f.endswith(('.json', '.xlsx', '.db', '.log'))]
        
        for filename in sorted(config_files):
            file_path = os.path.join(utile_path, filename)
            file_size = os.path.getsize(file_path)
            print(f"• {filename} ({file_size:,} bytes)")
        
        if not config_files:
            print("• (fără fișiere de configurare)")
    
    print(f"\n✅ Migrare completată!")
    print(f"💡 Sistemul va folosi automat noua locație din folderul Utile")

if __name__ == "__main__":
    migrate_config_files()