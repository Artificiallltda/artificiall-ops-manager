"""
Fix Table Names - Artificiall Ops Manager
=========================================
Este script renomeia as tabelas padrão do Excel (Table1, Table2, etc)
para os nomes que o bot espera: TblFuncionarios, TblPonto, TblDecisoes.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

import requests
from config.settings import Settings


def get_token():
    url = f"https://login.microsoftonline.com/{Settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
    resp = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": Settings.MICROSOFT_CLIENT_ID,
        "client_secret": Settings.MICROSOFT_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def graph(token, method, endpoint, data=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.request(
        method, f"https://graph.microsoft.com/v1.0{endpoint}",
        headers=headers, json=data, timeout=30
    )
    if resp.status_code not in [200, 201, 204]:
        print(f"  ⚠️  {resp.status_code}: {resp.text[:300]}")
    return resp.json() if resp.content else {}


def main():
    print("=== Fix Table Names — Artificiall Ops Manager ===\n")

    token = get_token()
    user_id = Settings.MICROSOFT_ORGANIZER_ID
    drive_id = Settings.EXCEL_DRIVE_ITEM_ID
    BASE = f"/users/{user_id}/drive/items/{drive_id}/workbook"

    print(f"🔍 Buscando tabelas em {drive_id}...")
    tables = graph(token, "GET", f"{BASE}/tables").get("value", [])

    if not tables:
        print("❌ Nenhuma tabela encontrada no arquivo!")
        return

    # Mapeamento por ordem de criação (ou ordem alfabética de Table1, 2, 3)
    # 1. TblFuncionarios
    # 2. TblPonto
    # 3. TblDecisoes
    # Vamos assumir que foram criadas nessa ordem.
    
    target_names = ["TblFuncionarios", "TblPonto", "TblDecisoes"]
    
    # Ordena as tabelas por nome (Table1, Table2...) para garantir consistência
    sorted_tables = sorted(tables, key=lambda t: t.get("name", ""))

    for i, table in enumerate(sorted_tables):
        if i >= len(target_names):
            break
            
        old_name = table["name"]
        new_name = target_names[i]
        table_id = table["id"]
        
        print(f"🔄 Renomeando {old_name} (ID: {table_id}) para {new_name}...")
        
        res = graph(token, "PATCH", f"{BASE}/tables/{table_id}", {"name": new_name})
        if "name" in res and res["name"] == new_name:
            print(f"  ✅ Sucesso!")
        else:
            print(f"  ❌ Falha ao renomear {old_name}")

    print("\n✅ Verificação final:")
    final_tables = graph(token, "GET", f"{BASE}/tables").get("value", [])
    for t in final_tables:
        print(f"  • {t['name']}")

    print("\n🚀 Agora o bot no Railway deverá reconhecer as tabelas!")


if __name__ == "__main__":
    main()
