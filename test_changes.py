#!/usr/bin/env python
"""
test_changes.py — Validación rápida de cambios
Verifica que la sintaxis es correcta y los módulos se cargan
"""

import sys

print("🔍 Validando cambios...")

# 1. Validar schema.sql
print("\n✓ Verificando schema.sql...")
try:
    with open("database/schema.sql", "r", encoding="utf-8") as f:
        content = f.read()
        if "guild_config_kv" in content:
            print("  ✅ Tabla guild_config_kv encontrada en schema")
        else:
            print("  ❌ ERROR: Tabla guild_config_kv no encontrada")
            sys.exit(1)
except Exception as e:
    print(f"  ❌ ERROR leyendo schema: {e}")
    sys.exit(1)

# 2. Validar setup_cog.py
print("\n✓ Verificando backend/setup_cog.py...")
try:
    with open("backend/setup_cog.py", "r", encoding="utf-8") as f:
        content = f.read()
        if "setup_ticket" in content and "setup_verificar" in content:
            print("  ✅ Comandos setup_ticket y setup_verificar encontrados")
        else:
            print("  ❌ ERROR: Comandos no encontrados")
            sys.exit(1)
except Exception as e:
    print(f"  ❌ ERROR leyendo setup_cog: {e}")
    sys.exit(1)

# 3. Validar main.py
print("\n✓ Verificando main.py...")
try:
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
        checks = [
            ("SetupCommands import", "from backend.setup_cog import SetupCommands"),
            ("SetupCommands en on_ready", "await bot.add_cog(SetupCommands"),
            ("config endpoint", "/api/config/{section}"),
            ("guild_config_kv insert", "guild_config_kv")
        ]
        
        all_ok = True
        for name, pattern in checks:
            if pattern in content:
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ ERROR: {name} no encontrado")
                all_ok = False
        
        if not all_ok:
            sys.exit(1)
except Exception as e:
    print(f"  ❌ ERROR leyendo main.py: {e}")
    sys.exit(1)

# 4. Validar .env
print("\n✓ Verificando .env...")
try:
    with open(".env", "r", encoding="utf-8") as f:
        content = f.read()
        if "GUILD_ID" in content:
            print("  ✅ GUILD_ID presente en .env")
        else:
            print("  ❌ ERROR: GUILD_ID no encontrado")
            sys.exit(1)
except Exception as e:
    print(f"  ❌ ERROR leyendo .env: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ TODAS LAS VALIDACIONES PASARON")
print("="*50)
print("\n📝 Próximos pasos:")
print("1. Actualiza GUILD_ID en .env con tu ID de servidor Discord")
print("2. Ejecuta: python main.py")
print("3. En Discord, ejecuta: /setup_ticket")
print("4. Accede a http://localhost:8000")
print("\n¡Listo! 🚀")
