"""
Create Tables — Artificiall Ops Manager
========================================
Cria as 3 abas e tabelas estruturadas no arquivo ArtificiallOps.xlsx no OneDrive.

Execute após setup_excel.py:
  python scripts/create_tables.py
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
        method,
        f"https://graph.microsoft.com/v1.0{endpoint}",
        headers=headers,
        json=data,
        timeout=30,
    )
    if resp.status_code not in [200, 201, 204]:
        print(f"  ⚠️  {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()
    return resp.json() if resp.content else {}


BASE = f"/users/{Settings.MICROSOFT_ORGANIZER_ID}/drive/items/{Settings.EXCEL_DRIVE_ITEM_ID}/workbook"

SHEETS = [
    {
        "name": "Funcionários",
        "table": "TblFuncionarios",
        "headers": ["telegram_id", "nome", "numero", "data_cadastro", "cargo", "ativo", "role", "email", "username"],
        "range": "A1:I2",
        "sample": ["", "", "", "", "", "", "", "", ""],
    },
    {
        "name": "Ponto",
        "table": "TblPonto",
        "headers": ["id", "telegram_id", "nome", "tipo", "timestamp", "data", "timezone"],
        "range": "A1:G2",
        "sample": ["", "", "", "", "", "", ""],
    },
    {
        "name": "Decisões",
        "table": "TblDecisoes",
        "headers": ["id", "data", "decisao", "registrado_por", "ceo_telegram_id", "categoria"],
        "range": "A1:F2",
        "sample": ["", "", "", "", "", ""],
    },
]


def main():
    print("=== Create Tables — Artificiall Ops Manager ===\n")

    token = get_token()
    print(f"✅ Token obtido\n")

    # Abre uma sessão de persistência no workbook
    print("📂 Abrindo sessão no workbook...")
    session = graph(token, "POST", f"{BASE}/createSession", {"persistChanges": True})
    session_id = session.get("id", "")
    print(f"✅ Sessão: {session_id[:30]}...\n")

    # Garante que a Sheet1 padrão será renomeada para a primeira aba
    existing_sheets = graph(token, "GET", f"{BASE}/worksheets").get("value", [])
    existing_names = [s["name"] for s in existing_sheets]

    for sheet_config in SHEETS:
        sheet_name = sheet_config["name"]
        table_name = sheet_config["table"]
        headers = sheet_config["headers"]
        rng = sheet_config["range"]
        sample = sheet_config["sample"]

        print(f"📋 Configurando aba: {sheet_name}")

        # Cria a aba se não existir
        if sheet_name not in existing_names:
            if existing_names and existing_names[0] not in [s["name"] for s in SHEETS]:
                # Renomeia a Sheet padrão
                graph(token, "PATCH", f"{BASE}/worksheets/{existing_names[0]}",
                      {"name": sheet_name})
                existing_names[0] = sheet_name
                print(f"  ✅ Aba renomeada para '{sheet_name}'")
            else:
                graph(token, "POST", f"{BASE}/worksheets/add", {"name": sheet_name})
                print(f"  ✅ Aba '{sheet_name}' criada")
        else:
            print(f"  ℹ️  Aba '{sheet_name}' já existe")

        # Escreve cabeçalho + linha vazia para poder criar a tabela
        try:
            graph(token, "PATCH", f"{BASE}/worksheets/{sheet_name}/range(address='{rng}')",
                  {"values": [headers, sample]})
            print(f"  ✅ Cabeçalhos escritos: {headers}")
        except Exception as e:
            print(f"  ⚠️  Erro ao escrever cabeçalhos: {e}")

        # Cria a tabela
        try:
            graph(token, "POST", f"{BASE}/worksheets/{sheet_name}/tables/add",
                  {"address": rng, "hasHeaders": True})

            # Renomeia a tabela para o nome correto
            tables = graph(token, "GET", f"{BASE}/worksheets/{sheet_name}/tables").get("value", [])
            if tables:
                table_id = tables[-1]["id"]
                graph(token, "PATCH", f"{BASE}/worksheets/{sheet_name}/tables/{table_id}",
                      {"name": table_name})
            print(f"  ✅ Tabela '{table_name}' criada")
        except Exception as e:
            print(f"  ⚠️  Tabela pode já existir ou houve erro: {e}")

    # Fecha a sessão
    try:
        graph(token, "DELETE", f"{BASE}/closeSession")
    except Exception:
        pass

    print("\n" + "="*55)
    print("🎉 SETUP COMPLETO! O Excel Online está pronto.")
    print("="*55)
    print("\n📌 Próximo passo: suba o bot no Railway com o .env configurado.")


if __name__ == "__main__":
    main()
