# 🚀 Guía de Ejecución — Oversee Web Dashboard

## Requisitos

- Python 3.9+
- pip (gestor de paquetes)
- Un bot Discord registrado

## Instalación Rápida

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Edita `.env` y completa:
```env
DISCORD_TOKEN=tu_token_del_bot
CLIENT_ID=tu_client_id
GUILD_ID=id_de_tu_servidor
```

### 3. Iniciar el servidor

```bash
python main.py
```

El panel estará disponible en: **http://localhost:8000**

---

## 🎨 Características del Dashboard

### Dashboard (Inicio)
- 📊 Estadísticas en tiempo real
- 📈 Gráfico de actividad (últimas 7 horas)
- 🔴 Feed en vivo de eventos

### Configuración
- ⚙️ **General**: Bienvenidas, autoroles, prefijo del bot
- 🛡️ **Automod**: Anti-spam, anti-links, filtro de palabras, anti-raid
- 📝 **Logs**: Configurar canales de auditoría
- 🎫 **Tickets**: Sistema de soporte

### Comandos
- ➕ Crear comandos personalizados
- 🎨 Personalizar embed (color, título, descripción)
- 🗑️ Eliminar comandos

### Tickets
- 📋 Ver tickets abiertos
- 🔍 Filtrar por estado
- ✅ Marcar como resueltos

---

## 🔌 API Endpoints

### Stats
```
GET /api/stats
→ Retorna estadísticas del servidor
```

### Comandos
```
GET  /api/commands          # Listar comandos
POST /api/commands          # Crear comando
DELETE /api/commands/{id}   # Eliminar comando
```

### Config
```
POST /api/config/{section}  # Guardar configuración
                           # Secciones: general, security, logs, tickets
```

### WebSocket
```
WS  /ws                     # Conexión en tiempo real
                           # Eventos: security_alert, system, chat_activity
```

---

## 🌐 Responsive Design

✅ **Desktop** (> 1200px): Layout completo con sidebar
✅ **Tablet** (768px - 1200px): Comprimido, menos columnas
✅ **Móvil** (< 768px): Sidebar colapsable
✅ **Móvil Pequeño** (< 480px): Optimizado para pantalla pequeña

---

## 🔧 Troubleshooting

### Bot no conecta
- Verifica que `DISCORD_TOKEN` sea válido
- Comprueba que el bot tiene permisos en el servidor

### API retorna 503
- La base de datos podría no estar disponible
- Verifica que `database/oversee.db` existe

### WebSocket no conecta
- Verifica que los sockets WebSocket están habilitados
- Comprueba la consola del navegador (F12)

---

## 📚 Tecnologías

### Backend
- **FastAPI** — Framework HTTP rápido
- **discord.py** — Cliente de bot Discord
- **aiosqlite** — Acceso async a SQLite
- **uvicorn** — Servidor ASGI

### Frontend
- **HTML5** — Estructura semántica
- **CSS3** — Diseño moderno y responsive
- **Vanilla JS** — Sin dependencias innecesarias
- **Chart.js** — Gráficos de datos
- **Font Awesome** — Iconos

---

## 💡 Tips

1. **Guardar configuración**: Usa el botón "Aplicar al bot" en cada sección
2. **Crear comandos**: Usa el generador con preview en tiempo real
3. **Ver logs**: El feed en vivo muestra eventos del servidor en tiempo real
4. **Tickets**: Abre un ticket desde Discord y aparecerá en el dashboard

---

## 📧 Soporte

Para reportar bugs o sugerencias, contacta con el equipo de desarrollo.

---

**¡Disfruta tu dashboard mejorado! 🎉**
