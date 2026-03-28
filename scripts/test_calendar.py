"""
Test Calendar Sync - Artificiall Ops Manager
============================================
Testa a criação de um evento no Calendário do Outlook via Graph API.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from integrations.teams_api import TeamsAPIIntegration
from config.settings import Settings

def test_calendar():
    print("=== Testando Sincronização de Calendário Outlook ===")
    
    teams = TeamsAPIIntegration(
        tenant_id=Settings.MICROSOFT_TENANT_ID,
        client_id=Settings.MICROSOFT_CLIENT_ID,
        client_secret=Settings.MICROSOFT_CLIENT_SECRET,
        organizer_user_id=Settings.MICROSOFT_ORGANIZER_ID
    )
    
    subject = "Teste de Integração Bot Artificiall"
    start_time = datetime.utcnow() + timedelta(hours=1) # Daqui a 1 hora
    
    print(f"📅 Criando evento: {subject}")
    print(f"⏰ Início (UTC): {start_time}")
    
    try:
        event = teams.create_calendar_event(
            subject=subject,
            start_time=start_time,
            duration=30,
            attendees=["test-ops@artificiall.ai"], # E-mail de teste
            content="Este é um teste automático da integração de calendário."
        )
        
        print("\n✅ Sucesso!")
        print(f"🆔 ID do Evento: {event['id']}")
        print(f"📌 Join URL (Teams): {event['join_url']}")
        print(f"🔗 Link Outlook: {event['web_link']}")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    test_calendar()
