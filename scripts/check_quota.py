import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_access_token(tenant_id, client_id, client_secret):
    """Get Microsoft Graph access token."""
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def check_drive_status():
    """Check the status of the configured OneDrive/SharePoint drive."""
    tenant_id = os.getenv("MICROSOFT_TENANT_ID")
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    user_id = os.getenv("MICROSOFT_ORGANIZER_ID")
    drive_item_id = os.getenv("EXCEL_DRIVE_ITEM_ID")

    print(f"\n{'='*60}")
    print("🔍 DIAGNÓSTICO ARTIFICIALL OPS MANAGER")
    print(f"{'='*60}\n")
    
    try:
        token = get_access_token(tenant_id, client_id, client_secret)
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Drive Info & Quota
        print(f"📊 [PASSO 1] Verificando cota para usuário: {user_id}")
        drive_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive"
        resp = requests.get(drive_url, headers=headers)
        resp.raise_for_status()
        drive_data = resp.json()
        
        quota = drive_data.get("quota", {})
        total = quota.get("total", 0) / (1024**3)
        used = quota.get("used", 0) / (1024**3)
        remaining = quota.get("remaining", 0) / (1024**3)
        state = quota.get("state", "unknown")
        
        print(f"   - Estado: {state.upper()}")
        print(f"   - Espaço: {used:.2f} GB / {total:.2f} GB ({remaining:.2f} GB livres)")
        
        # 2. File Status
        print(f"📄 [PASSO 2] Verificando arquivo Excel (ID: {drive_item_id[:10]}...)")
        item_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/items/{drive_item_id}"
        resp = requests.get(item_url, headers=headers)
        resp.raise_for_status()
        item_data = resp.json()
        print(f"   - Nome: {item_data.get('name')}")
        print(f"   - URL Web: {item_data.get('webUrl')[:100]}...")

        # 3. Workbook Sessions (Lock Check)
        print("🔒 [PASSO 3] Testando escrita no Workbook (Criação de Sessão)...")
        session_url = f"{item_url}/workbook/createSession"
        resp = requests.post(session_url, headers=headers, json={"persistChanges": True})
        
        if resp.status_code == 201:
            session_id = resp.json().get("id")
            close_url = f"{item_url}/workbook/closeSession"
            close_headers = headers.copy()
            close_headers["workbook-session-id"] = session_id
            requests.post(close_url, headers=close_headers)
        else:
            print(f"   ❌ BLOQUEADO ({resp.status_code})")
            error_msg = resp.json().get("error", {}).get("message", "")
            error_code = resp.json().get("error", {}).get("code", "")
            print(f"   ⚠️ MOTIVO: {error_code} - {error_msg}")

        # 4. Global Write Test
        print("📝 [PASSO 4] Testando criação de novo arquivo na raiz...")
        test_file_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/test_bot_{os.getpid()}.txt:/content"
        resp = requests.put(test_file_url, headers=headers, data="Teste Artificiall Ops")
        
        if resp.status_code in [200, 201]:
            print("   ✅ SUCESSO: O bot CONSEGUE criar novos arquivos no seu OneDrive.")
            test_id = resp.json().get("id")
            requests.delete(f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/items/{test_id}", headers=headers)
        else:
            print(f"   ❌ BLOQUEADO ({resp.status_code})")
            error_msg = resp.json().get("error", {}).get("message", "")
            print(f"   ⚠️ MOTIVO: {error_msg}")

    except Exception as e:
        print(f"\n💥 ERRO NO DIAGNÓSTICO: {e}")

    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    check_drive_status()
