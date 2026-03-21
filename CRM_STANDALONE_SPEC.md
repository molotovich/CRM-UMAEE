# 🎓 Definición Técnica: CRM Universitario Standalone

Este documento define la arquitectura, diseño y requisitos técnicos para la creación de un sistema CRM independiente dedicado a la captación y seguimiento de prospectos universitarios.

## 1. Visión General
El objetivo es desacoplar el módulo de captación del núcleo escolar (SCE) para permitir que el equipo de admisiones trabaje de forma ágil, con herramientas de seguimiento modernas y un diseño visual premium.

## 2. Stack Tecnológico Recomendado

| Componente | Tecnología | Razón |
|---|---|---|
| **Frontend** | React + Vite | Reactividad instantánea y desarrollo veloz. |
| **Estilos** | CSS Moderno / Tailwind | Control total sobre la estética premium y responsive. |
| **Backend** | Python (FastAPI / Flask) | Compatibilidad con la lógica existente y rapidez de APIs. |
| **Base de Datos** | PostgreSQL | Robustez para manejar logs de seguimiento y relaciones complejas. |
| **Comunicación** | REST API / Webhooks | Para "sincronizar" prospectos hacia el SCE al inscribirse. |

---

## 3. Arquitectura de Datos (CRM Schema)

### 3.1 Prospecto (Entidad Principal)
Un prospecto es la base del CRM. A diferencia de un alumno, un prospecto no tiene matrícula inicial.

```sql
CREATE TABLE prospectos (
    id_prospecto SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100),
    email VARCHAR(150),
    telefono VARCHAR(20),
    curp VARCHAR(18),
    id_carrera_interes INTEGER, -- Relación con catálogo de carreras
    fase_crm VARCHAR(50) DEFAULT 'NUEVO', -- NUEVO, CONTACTADO, CITA, INSCRITO, PERDIDO
    origen_prospecto VARCHAR(50), -- FACEBOOK, WEB, RECOMENDACION
    id_vendedor_asignado INTEGER,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Seguimiento (Bitácora)
Permite registrar cada interacción humana.

```sql
CREATE TABLE crm_seguimiento (
    id_seguimiento SERIAL PRIMARY KEY,
    id_prospecto INTEGER REFERENCES prospectos(id_prospecto),
    tipo_contacto VARCHAR(50), -- LLAMADA, WHATSAPP, EMAIL, VISITA
    comentarios TEXT NOT NULL,
    proxima_accion_fecha DATE,
    proxima_accion_nota VARCHAR(255),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Diseño y UX (Premium Aesthetics)

El sistema debe proyectar profesionalismo y modernidad:
- **Glassmorphism**: Uso de fondos traslúcidos y desenfoques (frosted glass) en tarjetas de prospectos.
- **Paleta de Colores**: Tonos profundos (Midnight Blue #0f172a) combinados con acentos vibrantes (Indigo #6366f1).
- **Micro-interacciones**: Transiciones suaves al cambiar a un prospecto de "fase" (drag and drop estilo Kanban).
- **Dashboard Visual**: Gráficos circulares de conversión y embudos de ventas dinámicos.

---

## 5. Funcionalidades Clave

1.  **Kanban de Ventas**: Visualización del embudo (Prospectos -> Contactados -> Cita -> Inscrito).
2.  **Agenda de Seguimiento**: Vista diaria de "Llamadas pendientes" basada en `proxima_accion_fecha`.
3.  **Timeline de Impacto**: Historial visual de todo lo ocurrido con un prospecto en una vista vertical.
4.  **Botón de WhatsApp Seguro**: Integración con API de WhatsApp para abrir chats con plantillas predefinidas.
5.  **Conversión a Alumno**: Un botón que, al activarse, envía vía API los datos del prospecto al SCE principal para generar su matrícula.

---

## 6. Estrategia de Integración (Webhooks)

Para mantener la independencia, el CRM notificará al SCE mediante un endpoint seguro:

```python
# Ejemplo de notificación de inscripción
POST /api/integracion/nuevo_alumno
{
    "token_crm": "XYZ123",
    "datos_prospecto": {
        "nombre": "Juan",
        "email": "juan@mail.com",
        "id_carrera": 5,
        "documentos": ["url_acta", "url_curp"]
    }
}
```

---

> [!TIP]
> **Seguridad**: Se recomienda usar OAuth2 para que los vendedores usen su cuenta institucional y el sistema herede los permisos del CRM de forma centralizada.
