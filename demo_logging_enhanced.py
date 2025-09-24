#!/usr/bin/env python3
"""
Demonstrație log-uri îmbunătățite pentru sistemul de email
"""

from enhanced_hub_generator import EnhancedHubGenerator
import os

def demo_enhanced_logging():
    """Demonstrează log-urile îmbunătățite"""
    print("📝 Demonstrație Log-uri Îmbunătățite pentru Email")
    print("=" * 55)
    
    generator = EnhancedHubGenerator()
    
    # Verifică câteva centre disponibile
    centres = generator.get_available_centres('2025-08-28')
    
    if not centres:
        print("❌ Nu sunt centre disponibile pentru demo")
        return
    
    print(f"📊 Centre disponibile pentru demo: {len(centres)}")
    
    # Demonstrează log-urile pentru primele 3 centre
    demo_centres = centres[:3]
    
    for i, (centru, numar_rute) in enumerate(demo_centres, 1):
        print(f"\n{i}. 📧 Demo email pentru {centru} ({numar_rute} rute):")
        print("-" * 50)
        
        try:
            # Arată adresele configurate
            email_addresses = generator.email_system.load_email_addresses()
            if centru in email_addresses:
                addresses = email_addresses[centru]
                print(f"   📬 Adrese configurate: {', '.join(addresses)}")
            else:
                print(f"   ⚠️ Nu sunt adrese configurate pentru {centru}")
                continue
            
            # Simulează trimiterea (fără trimitere reală pentru demo)
            print(f"   🔄 Se pregătește email-ul...")
            
            # Doar log-urile, fără trimitere efectivă
            raport_data = generator.email_system.get_centre_report_last_30_days(centru, '2025-08-28')
            html_content = generator.email_system.generate_email_report_html(centru, raport_data)
            
            print(f"   📄 HTML generat: {len(html_content):,} caractere")
            print(f"   📊 Date raport: {len(raport_data)} rute în ultimele 30 zile")
            
            # Pentru primul centru, trimite email real pentru demonstrație
            if i == 1:
                print(f"   📤 Trimit email real pentru demonstrație...")
                success = generator.send_test_email(centru, '2025-08-28')
                if success:
                    print(f"   ✅ Email trimis cu succes!")
                else:
                    print(f"   ❌ Eroare la trimiterea email-ului")
            else:
                print(f"   🔍 (Simulare - email nu a fost trimis)")
            
        except Exception as e:
            print(f"   ❌ Eroare: {e}")
    
    # Arată locația log-ului
    log_path = generator.email_system.utile_path + "/email_reporting.log"
    print(f"\n📋 Log-uri salvate în: {log_path}")
    
    if os.path.exists(log_path):
        print(f"📏 Mărime fișier log: {os.path.getsize(log_path):,} bytes")
        
        print(f"\n📖 Ultimele 5 linii din log:")
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-5:]:
                    print(f"   {line.strip()}")
        except Exception as e:
            print(f"   ❌ Nu pot citi log-ul: {e}")
    
    print(f"\n" + "=" * 55)
    print(f"✅ Demo log-uri completat!")
    print(f"\n📝 Informații înregistrate în log-uri:")
    print(f"• 📧 Adresele email către care se trimit mesajele")
    print(f"• 🔗 Serverul SMTP și portul folosit")
    print(f"• 👤 Utilizatorul pentru autentificare")
    print(f"• 📄 Subiectul și mărimea email-ului")
    print(f"• ✅ Confirmarea trimiterii cu succes")
    print(f"• ⚠️ Erorile detaliate în caz de probleme")

if __name__ == "__main__":
    demo_enhanced_logging()