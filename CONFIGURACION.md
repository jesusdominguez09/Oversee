# 🔧 Guía de Configuración de Oversee

## ⚠️ Configuración Requerida Antes de Iniciar

### 1. GUILD_ID (ID del Servidor Discord)
El archivo `.env` contiene un placeholder que DEBE ser reemplazado:

**Actual (incorrecto):**
```env
GUILD_ID=id_del_servidor_del_cliente
```

**Qué hacer:**
1. Abre Discord
2. Activa "Modo de Desarrollador" (Configuración > Avanzado > Modo de Desarrollador)
3. Haz clic derecho en tu servidor → "Copiar ID del servidor"
4. Reemplaza el placeholder en `.env`:
```env
GUILD_ID=123456789012345678
```

### 2. DISCORD_TOKEN (Token del Bot)
Ya está configurado, pero verifica que sea válido:
- Ve a [Discord Developer Portal](https://discord.com/developers/applications)
- Selecciona tu aplicación → Bot → Reset Token si es necesario

### 3. Iniciar el Bot
```bash
python main.py
```

El bot se iniciará en `http://localhost:8000`

---

## 🎫 Comandos Disponibles

Después de que el bot esté online, ejecuta estos comandos en Discord:

### `/setup_ticket`
Configura el sistema de tickets:
```
/setup_ticket [category] [staff_role] [max_tickets]
```
**Ejemplo:**
```
/setup_ticket category: Tickets staff_role: @Support max_tickets: 3
```

### `/setup_verificar`
Configura el sistema de verificación:
```
/setup_verificar verification_role: @Verificado [verification_channel: #general]
```

### Crear Comandos Personalizados
Desde el dashboard web (`/commands`):
1. Ingresa nombre del comando (sin `/`)
2. Descripción
3. Contenido (puede incluir **negrita** o *cursiva*)
4. Color personalizado
5. Click en "Inyectar en Discord"

---

## 🛠️ Solución de Problemas

### Error: "Error al guardar"
- Verifica que el GUILD_ID sea correcto
- Revisa la consola del bot para mensajes de error
- Asegúrate que el bot está online

### Error: "Sin conexión con el bot"
- El servidor no está corriendo: `python main.py`
- Verifica que el puerto 8000 no está en uso

### Comandos no aparecen en Discord
- Espera 1-2 minutos después de crear el comando
- Intenta cerrar y abrir Discord
- Verifica permisos del bot en el servidor

---

## 📊 Tabla de Base de Datos

La configuración se guarda en `guild_config_kv`:
```sql
-- Ejemplo:
SELECT * FROM guild_config_kv WHERE guild_id = '123456789012345678';

-- Borrar una configuración:
DELETE FROM guild_config_kv WHERE guild_id = '123456789012345678' AND key = 'security_antispam_enabled';
```

---

## 🔄 Reiniciar y Recargar

- **Reiniciar el bot**: `Ctrl+C` y `python main.py`
- **Recargar comandos**: Usa `/setup_ticket` o `/setup_verificar` de nuevo
- **Sincronizar comandos manualmente**: El bot sincroniza automáticamente al iniciarse

---

¡Listo! Si todo está configurado correctamente, la web debería conectarse sin errores. 🎉
