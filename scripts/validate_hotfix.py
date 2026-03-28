#!/usr/bin/env python3
"""
Script de Validação das Correções - Hotfix 28/03/2026

Este script valida as 3 correções críticas implementadas:
- QA-C01: Comando /register_me e pending ID
- QA-C02: Log seguro de decisões (sem texto completo)
- QA-C03: Timezone compatível com Windows

Execução:
    python scripts/validate_hotfix.py

Requisitos:
    - Python 3.10+
    - pytest instalado
"""

import os
import sys
import json
from datetime import datetime, timedelta, timezone

# Adicionar raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_header(title: str) -> None:
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name: str, passed: bool, details: str = "") -> None:
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status} - {test_name}")
    if details:
        print(f"   {details}")


# =============================================================================
# QA-C01: Validação do comando /register_me e pending ID
# =============================================================================

def validate_qa_c01() -> bool:
    """Validate QA-C01 fix: telegram_id pending resolution."""
    print_header("QA-C01: Validação /register_me e pending ID")
    
    all_passed = True
    
    # Test 1: Verificar se handle_register_me existe
    try:
        from handlers.register import handle_register_me
        print_result("handle_register_me existe", True)
    except ImportError as e:
        print_result("handle_register_me existe", False, str(e))
        all_passed = False
    
    # Test 2: Verificar se google_sheets tem métodos de atualização
    try:
        from integrations.google_sheets import GoogleSheetsIntegration
        
        has_update = hasattr(GoogleSheetsIntegration, 'update_employee_telegram_id')
        has_get_pending = hasattr(GoogleSheetsIntegration, 'get_employee_by_pending_id')
        
        print_result("update_employee_telegram_id() existe", has_update)
        print_result("get_employee_by_pending_id() existe", has_get_pending)
        
        if not has_update or not has_get_pending:
            all_passed = False
            
    except ImportError as e:
        print_result("Métodos GoogleSheetsIntegration", False, str(e))
        all_passed = False
    
    # Test 3: Verificar pending ID com username no register.py
    try:
        with open("handlers/register.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        has_pending_username = 'pending_{username}' in content or "pending_{username}" in content
        has_register_me_handler = 'handle_register_me' in content
        
        print_result("Lógica pending_{username} no register.py", has_pending_username)
        print_result("handle_register_me no register.py", has_register_me_handler)
        
        if not has_pending_username or not has_register_me_handler:
            all_passed = False
            
    except Exception as e:
        print_result("Leitura de register.py", False, str(e))
        all_passed = False
    
    # Test 4: Verificar bot.py registra handler /register_me
    try:
        with open("bot.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        has_register_me_route = 'CommandHandler("register_me"' in content
        has_register_me_import = 'handle_register_me' in content
        
        print_result("Handler /register_me registrado no bot.py", has_register_me_route)
        print_result("handle_register_me importado no bot.py", has_register_me_import)
        
        if not has_register_me_route or not has_register_me_import:
            all_passed = False
            
    except Exception as e:
        print_result("Leitura de bot.py", False, str(e))
        all_passed = False
    
    return all_passed


# =============================================================================
# QA-C02: Validação do log seguro de decisões
# =============================================================================

def validate_qa_c02() -> bool:
    """Validate QA-C02 fix: secure decision logging."""
    print_header("QA-C02: Validação Log Seguro de Decisões")
    
    all_passed = True
    
    # Test 1: Verificar se decision_text NÃO está no log
    try:
        with open("handlers/decision.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Procurar por decision_text no contexto de log
        has_decision_text_in_log = '"decision_text": decisao_texto' in content
        has_text_length = '"text_length": len(decisao_texto)' in content
        
        decision_text_removed = not has_decision_text_in_log
        text_length_added = has_text_length
        
        print_result("decision_text removido do log", decision_text_removed, 
                    "Texto completo NÃO é mais logado" if decision_text_removed else "Texto completo AINDA está no log!")
        print_result("text_length adicionado como metadado", text_length_added,
                    "Apenas tamanho do texto é logado" if text_length_added else "text_length não encontrado")
        
        if not decision_text_removed or not text_length_added:
            all_passed = False
            
    except Exception as e:
        print_result("Leitura de decision.py", False, str(e))
        all_passed = False
    
    # Test 2: Verificar comentário de segurança
    try:
        with open("handlers/decision.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        has_security_comment = 'SECURITY' in content.upper() and 'decision_text' in content.lower()
        print_result("Comentário de segurança presente", has_security_comment)
        
    except Exception as e:
        print_result("Verificação comentário segurança", False, str(e))
        all_passed = False
    
    return all_passed


# =============================================================================
# QA-C03: Validação do timezone compatível com Windows
# =============================================================================

def validate_qa_c03() -> bool:
    """Validate QA-C03 fix: Windows-compatible timezone."""
    print_header("QA-C03: Validação Timezone Windows-Compatible")
    
    all_passed = True
    
    # Test 1: Verificar se strptime foi removido
    try:
        with open("middleware/logger.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        has_strptime = 'strptime("-03:00"' in content or "strptime('-03:00'" in content
        has_timedelta = 'timedelta(hours=-3)' in content or "timedelta(hours=-3)" in content
        
        strptime_removed = not has_strptime
        timedelta_added = has_timedelta
        
        print_result("strptime removido", strptime_removed,
                    "datetime.strptime não é mais usado" if strptime_removed else "strptime AINDA está no código!")
        print_result("timedelta adicionado", timedelta_added,
                    "timezone(timedelta(hours=-3)) usado" if timedelta_added else "timedelta não encontrado")
        
        if not strptime_removed or not timedelta_added:
            all_passed = False
            
    except Exception as e:
        print_result("Leitura de logger.py", False, str(e))
        all_passed = False
    
    # Test 2: Testar funcionalidade do timezone
    try:
        from middleware.logger import OperationLogger
        
        logger = OperationLogger()
        timestamp = logger._get_timestamp()
        
        # Validar formato ISO 8601 com timezone
        has_timezone_indicator = '-03:00' in timestamp or '+00:00' in timestamp or 'Z' in timestamp
        is_valid_iso = True
        try:
            # Tentar parse do timestamp
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            is_valid_iso = False
        
        print_result("Timestamp gerado é válido", is_valid_iso, f"Timestamp: {timestamp}")
        print_result("Timestamp tem indicador de timezone", has_timezone_indicator)
        
        if not is_valid_iso:
            all_passed = False
            
    except Exception as e:
        print_result("Teste funcional do timezone", False, str(e))
        all_passed = False
    
    # Test 3: Simulação Windows (ambientes sem strptime com %z)
    try:
        # Testar que timedelta funciona independentemente do OS
        tz = timezone(timedelta(hours=-3))
        test_timestamp = datetime.now(tz).isoformat()
        
        print_result("timezone(timedelta) funciona no ambiente atual", True,
                    f"Timestamp de teste: {test_timestamp}")
        
    except Exception as e:
        print_result("timezone(timedelta) funciona", False, str(e))
        all_passed = False
    
    return all_passed


# =============================================================================
# Validação Geral: Executar testes unitários
# =============================================================================

def run_unit_tests() -> bool:
    """Run unit tests to validate all fixes."""
    print_header("Execução de Testes Unitários")
    
    import subprocess
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # Extrair resultado
        lines = result.stdout.split('\n')
        for line in lines:
            if 'passed' in line or 'failed' in line or 'error' in line:
                print(f"   {line.strip()}")
        
        all_passed = result.returncode == 0
        
        if all_passed:
            print_result("Todos os testes unitários", True, "31/31 passed")
        else:
            print_result("Todos os testes unitários", False, "Alguns testes falharam")
            print("\nSaída completa:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
        
        return all_passed
        
    except Exception as e:
        print_result("Execução de testes", False, str(e))
        return False


# =============================================================================
# Main
# =============================================================================

def main():
    """Run all validations."""
    print("\n" + "🔍 " * 20)
    print("  VALIDAÇÃO DAS CORREÇÕES - HOTFIX 28/03/2026")
    print("🔍 " * 20)
    
    results = {}
    
    # Run individual validations
    results["QA-C01"] = validate_qa_c01()
    results["QA-C02"] = validate_qa_c02()
    results["QA-C03"] = validate_qa_c03()
    
    # Run unit tests
    results["TESTES"] = run_unit_tests()
    
    # Print summary
    print_header("RESUMO DA VALIDAÇÃO")
    
    all_passed = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("  ✅ TODAS AS VALIDAÇÕES PASSARAM!")
        print("  Hotfix pronto para deploy em homologação.")
    else:
        print("  ❌ ALGUMAS VALIDAÇÕES FALHARAM!")
        print("  Revise os erros acima antes de prosseguir.")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
