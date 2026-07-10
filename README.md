# ERP TechSolutions Perú S.A.C.

ERP para la tienda online de TechSolutions Perú S.A.C. (equipos de cómputo,
periféricos, componentes, accesorios gamer y monitores). Backend Flask +
SQLAlchemy, frontend Bootstrap 5 con arquitectura de plantilla base (Jinja2).

Proyecto académico de Ingeniería Económica: caso de estudio para automatizar
la gestión interna (inventario, ventas, atención al cliente) actualmente
llevada en Excel.

## Instalación rápida (desarrollo — SQLite)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # dejar FLASK_ENV=development

python run.py                   # ¡y listo! http://localhost:5000
```

**No hace falta correr `flask db upgrade` ni `python seed.py` a mano.**
`run.py` aplica las migraciones automáticamente (crea la base de datos si
no existe) y siembra datos de prueba con Faker la primera vez que arranca.
En arranques posteriores no se duplica nada: el seed es idempotente.

Usuario de prueba: **admin@techsolutions.pe** / **admin123**

### Volumen de datos de prueba (seed automático)

| Entidad | Cantidad aprox. |
|---|---|
| Usuarios internos | 25 |
| Clientes | 250 |
| Categorías (con subcategorías) | 20 |
| Productos | ~165 |
| Ventas (con detalle) | 400 |
| Pedidos | ~300 |
| Movimientos de inventario | ~870 |
| Tickets de atención al cliente | 120 |

Si en algún momento quieres repoblar desde cero, basta con borrar
`instance/techsolutions.db` (SQLite) y volver a correr `python run.py`.

## Producción (PostgreSQL / Render)

En `.env` (o variables de entorno del servicio):

```
FLASK_ENV=production
DATABASE_URL=postgresql://usuario:password@host:5432/basededatos
SECRET_KEY=una-clave-larga-y-aleatoria
```

El mismo código y las mismas migraciones funcionan sin cambios: SQLAlchemy
resuelve las diferencias de dialecto entre SQLite y PostgreSQL.

## Estructura del proyecto

```
app/
  models/       # Entidades SQLAlchemy (13 tablas)
  routes/       # Blueprints: auth, dashboard, categorias, productos,
                #   inventario, ventas, clientes, pedidos, atencion_cliente,
                #   auditoria
  services/     # Lógica de negocio (una regla de oro: el stock de un
                #   producto NUNCA se edita directo; siempre pasa por
                #   inventario_service, que deja el movimiento en el kardex)
  templates/    # Jinja2, heredan de base.html
  static/       # CSS, JS
  config.py     # Config única, arma el URI de BD según entorno
  extensions.py # db, migrate, login_manager
migrations/     # Historial de Alembic
seed.py         # Datos de prueba con Faker, idempotente
run.py          # Punto de entrada (migra + siembra + levanta el server)
```

## Módulos implementados (Etapa 2 — completa)

| Módulo | CRUD | Detalle |
|---|---|---|
| Categorías | ✅ | Con subcategorías |
| Productos | ✅ | Precios, stock mínimo, imagen |
| Inventario | ✅ | Kardex de entradas/salidas/ajustes, alertas de stock bajo |
| Ventas | ✅ | Estilo POS, cálculo automático de IGV, descuenta stock, genera pedido, anulación con reposición |
| Clientes | ✅ | Historial de compras y tickets |
| Pedidos / Logística | ✅ (solo cambio de estado, con transiciones válidas) | Timeline visual: procesando → en camino → entregado |
| Atención al Cliente | ✅ | Tickets con hilo de comentarios, cambio de estado |
| Auditoría | ✅ (solo lectura) | Quién hizo qué, cuándo, con filtros |

Todas las búsquedas tienen filtros y paginación. Las confirmaciones de
eliminar/anular usan SweetAlert2.

## Estado del proyecto

- ✅ **Etapa 1**: Arquitectura, modelos, configuración BD, autenticación,
  plantilla base, dashboard inicial, seed.
- ✅ **Etapa 2**: CRUD completo de todos los módulos, integrados vía
  SQLAlchemy con capa de servicios (SOLID/DRY).
- ⏳ **Etapa 3** (pendiente): Reportes con Chart.js, KPIs avanzados,
  seguridad adicional, optimización de consultas, despliegue en Render,
  documentación final.
