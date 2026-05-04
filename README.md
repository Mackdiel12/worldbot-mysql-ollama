# WorldBot - Asistente de Base de Datos con IA Local 🤖

Sistema inteligente que permite realizar consultas a bases de datos MySQL mediante lenguaje natural en español, utilizando inteligencia artificial local con Ollama.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)
![Ollama](https://img.shields.io/badge/Ollama-llama3.1:8b-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 Características Principales

- ✅ **Consultas en lenguaje natural**: Pregunta en español cotidiano, sin necesidad de conocer SQL
- ✅ **IA completamente local**: Usa Ollama con LLaMA 3.1 - sin enviar datos a servicios externos
- ✅ **Privacidad total**: Todos tus datos permanecen en tu equipo
- ✅ **Sin costos de API**: No requiere suscripciones a servicios de IA comerciales
- ✅ **Interfaz moderna**: Chat intuitivo desarrollado con CustomTkinter
- ✅ **Consultas complejas**: Soporta JOIN, agregaciones, filtros múltiples

## 📸 Capturas de Pantalla

*[Capturas de la aplicación funcionando]*

## 🎓 Proyecto Académico

Este proyecto fue desarrollado como Trabajo Final del curso de Base de Datos en la Universidad Tecnológica de Panamá (UTP), bajo la supervisión del MSc. Rafael Vejarano.

**Objetivo:** Demostrar la integración de bases de datos relacionales con modelos de inteligencia artificial local para facilitar el acceso a información mediante lenguaje natural.

## 🚀 Inicio Rápido

### Requisitos Previos

- **Python 3.11 o superior**
- **MySQL Server 8.0+**
- **Ollama** instalado en tu sistema
- **32 GB RAM** (recomendado para llama3.1:8b)
- **5 GB de espacio libre** (para el modelo de IA)

### Instalación

**1. Clonar el repositorio:**
```bash
git clone https://github.com/Mackdiel12/worldbot-mysql-ollama.git
cd worldbot-mysql-ollama
```

**2. Instalar dependencias de Python:**
```bash
pip install -r requirements.txt
```

**3. Instalar y configurar Ollama:**

Descarga Ollama desde [ollama.ai](https://ollama.ai) e instálalo.

Luego descarga el modelo:
```bash
ollama pull llama3.1:8b
```

Verifica que Ollama esté corriendo:
```bash
ollama list
```

**4. Configurar MySQL:**

Importa la base de datos `world` en MySQL. Puedes descargarla desde [MySQL Sample Databases](https://dev.mysql.com/doc/index-other.html).

**5. Configurar variables de entorno:**

Copia el archivo de ejemplo:
```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:
```
DB_HOST=localhost
DB_PORT=****
DB_NAME=world
DB_USER=****
DB_PASS=tu_contraseña_aqui
OLLAMA_URL=http://localhost:11434/api/generate
MODELO_IA=llama3.1:8b
```

**6. Ejecutar la aplicación:**
```bash
python app.py
```

## 💬 Ejemplos de Uso

Una vez iniciada la aplicación, puedes hacer preguntas como:

### Consultas Simples
```
¿Cuáles son los 5 países más grandes del mundo?
¿Cuál es la población de Panamá?
¿Cuál es la esperanza de vida de Japón?
```

### Consultas con Filtros
```
¿Qué países tienen más de 100 millones de habitantes?
¿Cuáles son los países de América Central?
¿Qué idiomas oficiales tiene México?
```

### Consultas con JOIN
```
¿Cuáles son las ciudades más pobladas de Asia?
¿Qué idiomas se hablan en los países de Europa?
¿En qué país está la ciudad más poblada del mundo?
```

### Consultas con Agregación
```
¿Cuántas ciudades tiene Brasil?
¿Cuántos países hay en Europa?
¿Cuál es el promedio de población de los países de Asia?
```

## 🏗️ Arquitectura del Sistema

```
Usuario → Interfaz Python/CustomTkinter
            ↓
        Ollama (LLaMA 3.1:8b)
            ↓
        Genera SQL automáticamente
            ↓
        MySQL ejecuta consulta
            ↓
        Python formatea respuesta natural
            ↓
        Usuario ve resultados
```

## 📂 Estructura del Proyecto

```
worldbot-mysql-ollama/
├── app.py                 # Aplicación principal
├── .env.example          # Ejemplo de configuración
├── requirements.txt      # Dependencias Python
├── README.md            # Este archivo
└── LICENSE              # Licencia MIT
```

## 🛠️ Tecnologías Utilizadas

- **Python 3.11**: Lenguaje principal
- **MySQL 8.0**: Base de datos relacional
- **Ollama**: Motor de IA local
- **LLaMA 3.1 (8B)**: Modelo de lenguaje
- **CustomTkinter**: Interfaz gráfica moderna
- **mysql-connector-python**: Conector MySQL
- **python-dotenv**: Gestión de variables de entorno

## ⚙️ Configuración Avanzada

### Cambiar el Modelo de IA

Puedes usar otros modelos de Ollama. Modelos probados:

- `llama3.1:8b` (Recomendado) - Balance óptimo
- `qwen2.5:3b` - Más rápido, menos preciso
- `llama3.1:70b` - Más preciso, requiere GPU

Para cambiar, edita `.env`:
```
MODELO_IA=nombre_del_modelo
```

### Optimizar Rendimiento

Si experimentas lentitud:

1. Reduce `num_predict` en `app.py` (línea ~80)
2. Usa modelos más pequeños (3B parámetros)
3. Aumenta RAM disponible
4. Considera usar GPU

## 🐛 Solución de Problemas

### Error: "Access denied for user 'root'@'localhost'"
- Verifica tus credenciales en `.env`
- Asegúrate que MySQL esté corriendo
- Prueba conectarte manualmente: `mysql -u root -p`

### Error: "Ollama timeout"
- Verifica que Ollama esté corriendo: `ollama list`
- Aumenta el timeout en `app.py` (línea ~85)
- Considera usar un modelo más pequeño

### Respuestas muy lentas
- Normal en CPU sin GPU (20-40 segundos)
- Usa números en palabras ("cinco" en vez de "5")
- Considera hardware con GPU dedicada

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para cambios importantes:

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📋 Roadmap

- [ ] Soporte para múltiples bases de datos
- [ ] Memoria conversacional
- [ ] Exportación de resultados (CSV, Excel, PDF)
- [ ] Versión web con Flask
- [ ] Caché de consultas frecuentes
- [ ] Soporte para más idiomas

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👨‍💻 Autor

**Estudiante de Ingeniería de Sistemas**

- Proyecto Final - Base de Datos
- Universidad Tecnológica de Panamá
- Facultad de Ingeniería de Sistemas Computacionales
- 2026

## 🙏 Agradecimientos

- MSc. Rafael Vejarano - Profesor del curso
- Meta AI - Modelo LLaMA
- Ollama Team - Framework de IA local
- MySQL - Base de datos de ejemplo "world"

## 📞 Contacto

Para consultas sobre el proyecto:
- GitHub Issues: [Crear issue](https://github.com/Mackdiel12/worldbot-mysql-ollama/issues)
- GitHub: [@Mackdiel12](https://github.com/Mackdiel12)
- Linkedin: https://www.linkedin.com/in/mackdiel-manuel-dom%C3%ADnguez-francisco-258a2470/

---

⭐ Si este proyecto te resultó útil, considera darle una estrella en GitHub

---

## 📊 Estadísticas del Proyecto

**Tecnologías utilizadas:**
- Base de datos: 3 tablas, 239 países, 4,079 ciudades, 984 idiomas
- Modelo IA: LLaMA 3.1 (8 mil millones de parámetros)
- Tiempo de respuesta: 20-40 segundos promedio
- Precisión: 95% en consultas probadas

**Desarrollado con ❤️ en Panamá 🇵🇦**
