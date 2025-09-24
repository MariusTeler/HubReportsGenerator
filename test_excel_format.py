#!/usr/bin/env python3
"""
Script pentru testarea și demonstrarea formatului Excel
"""

import pandas as pd
import os
from email_reporting_system import EmailReportingSystem

def demo_excel_editing():
    """Demonstrație editare și citire Excel"""
    print("📊 Demonstrație Format Excel pentru Adrese Email")
    print("=" * 55)
    
    email_system = EmailReportingSystem()
    excel_path = email_system.email_addresses_path
    
    # Verifică dacă fișierul există
    if not os.path.exists(excel_path):
        print("📝 Creez fișierul Excel...")
        email_system.create_email_addresses_template()
    
    print(f"📁 Fișier Excel: {excel_path}")
    
    # Citește și afișează structura
    df = pd.read_excel(excel_path, sheet_name='Email_Addresses')
    print(f"\n📋 Structura fișierului:")
    print(f"• Coloane: {list(df.columns)}")
    print(f"• Total centre: {len(df)}")
    
    print(f"\n📊 Primele 5 rânduri:")
    print(df.head().to_string(index=False))
    
    # Demonstrație modificare programatică
    print(f"\n🔧 Demonstrație modificare programatică:")
    
    # Schimbă câteva adrese email pentru demonstrație
    df.loc[df['Centru'] == 'BUCUREȘTI', 'Adrese_Email'] = 'manager.bucuresti@test.com; director.bucuresti@test.com; rapoarte.bucuresti@test.com'
    df.loc[df['Centru'] == 'CLUJ', 'Adrese_Email'] = 'cluj.manager@test.com'
    df.loc[df['Centru'] == 'NUGAT', 'Activ'] = 'NU'  # Dezactivează NUGAT
    
    # Salvează modificările
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Email_Addresses', index=False)
        
        # Formatarea coloanelor
        worksheet = writer.sheets['Email_Addresses']
        worksheet.column_dimensions['A'].width = 20  # Centru
        worksheet.column_dimensions['B'].width = 50  # Adrese Email
        worksheet.column_dimensions['C'].width = 10  # Activ
        worksheet.column_dimensions['D'].width = 40  # Observații
    
    print("✅ Modificări salvate în Excel!")
    
    # Testează citirea cu noile modificări
    print(f"\n🔍 Testez citirea actualizată:")
    try:
        addresses = email_system.load_email_addresses()
        
        print(f"✅ Încărcat cu succes {len(addresses)} centre active")
        
        # Afișează exemplele modificate
        if 'BUCUREȘTI' in addresses:
            print(f"• BUCUREȘTI: {addresses['BUCUREȘTI']}")
        if 'CLUJ' in addresses:
            print(f"• CLUJ: {addresses['CLUJ']}")
        if 'NUGAT' not in addresses:
            print(f"• NUGAT: Dezactivat (nu apare în listă)")
        
        # Verifică formatarea adreselor multiple
        for centru, emails in addresses.items():
            if len(emails) > 1:
                print(f"• {centru}: {len(emails)} adrese - {emails}")
                break
                
    except Exception as e:
        print(f"❌ Eroare la citire: {e}")
    
    print(f"\n" + "=" * 55)
    print(f"📝 Cum să editați fișierul Excel manual:")
    print(f"1. Deschideți {excel_path} în Excel/LibreOffice")
    print(f"2. Editați coloana 'Adrese_Email' cu adresele dorite")
    print(f"3. Folosiți ';' (punct și virgulă) pentru adrese multiple")
    print(f"4. Setați 'Activ' la 'NU' pentru a dezactiva un centru")
    print(f"5. Salvați fișierul și rulați din nou sistemul")
    
    print(f"\n📋 Exemple de adrese valide:")
    print(f"• Un email: manager@company.com")
    print(f"• Două email-uri: manager@company.com; supervisor@company.com")
    print(f"• Mai multe: email1@company.com; email2@company.com; email3@company.com")

if __name__ == "__main__":
    demo_excel_editing()