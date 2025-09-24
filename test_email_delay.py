#!/usr/bin/env python3
"""
Test script pentru demonstrarea delay-ului între email-uri
"""

from enhanced_hub_generator import EnhancedHubGenerator
import sqlite3
import time

def demo_email_delay():
    """Demonstrează delay-ul între trimiterea email-urilor"""
    print("🧪 Demo: Delay între trimiterea email-urilor")
    print("=" * 50)
    
    generator = EnhancedHubGenerator()
    
    # Găsește primele 3 centre cu date pentru test
    centre_disponibile = generator.get_available_centres('2025-08-28')
    
    if len(centre_disponibile) < 2:
        print("❌ Nu există suficiente centre pentru demonstrație")
        return
    
    # Limitează la primele 3 centre pentru demo
    centre_test = centre_disponibile[:3]
    
    print(f"📊 Centre pentru demo ({len(centre_test)} centre):")
    for i, (centru, rute) in enumerate(centre_test, 1):
        print(f"  {i}. {centru} ({rute} rute)")
    
    delay_seconds = 2
    estimated_time = (len(centre_test) - 1) * delay_seconds + len(centre_test) * 1  # ~1s per email
    
    print(f"\n⏱️ Configurație delay:")
    print(f"  • Delay între email-uri: {delay_seconds} secunde")
    print(f"  • Timp estimat total: ~{estimated_time} secunde")
    print(f"  • Nu se adaugă delay după ultimul email")
    
    print(f"\n📧 Pentru testul complet cu {len(centre_test)} centre:")
    print("1. Rulați: python enhanced_hub_generator.py")  
    print("2. Selectați opțiunea 3: 'Trimite doar email-uri'")
    print("3. Introduceți data: 2025-08-28")
    print("4. Urmăriți log-urile pentru a vedea delay-ul")
    
    print(f"\n📋 În log-uri veți vedea:")
    print("  • 'Pregătesc email pentru centrul [NUME]'")
    print("  • 'Email trimis cu succes pentru centrul [NUME]'") 
    print(f"  • 'Pauză de {delay_seconds} secunde înainte de următorul email...'")
    print("  • Fără delay după ultimul email")
    
    print(f"\n🎯 Beneficii delay:")
    print("  • Previne blocarea serverului SMTP")
    print("  • Reduce riscul de rate limiting")
    print("  • Permite procesarea email-urilor în mod controlat")
    print(f"  • Cu {len(centre_disponibile)} centre total: ~{(len(centre_disponibile)-1) * 2 / 60:.1f} minute delay")

if __name__ == "__main__":
    demo_email_delay()