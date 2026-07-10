"""
seed.py — Generador de datos de prueba para TechSolutions ERP.

Idempotencia
------------
Cada bloque verifica la existencia de datos ANTES de insertar (por nombre
único, email único, SKU, etc.). Ejecutar este script múltiples veces NO
duplica información: si ya existen registros, ese bloque se omite y se
informa por consola. Esto permite correrlo con seguridad tanto en
desarrollo como después de un despliegue.

Uso:
    python seed.py
"""

import random
import re
import unicodedata
from datetime import timedelta
from decimal import Decimal

from faker import Faker


def _sin_tildes(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9.]", "", texto)


from app.extensions import db
from app.time_utils import ahora
from app.models import (
    Rol,
    Usuario,
    Cliente,
    Categoria,
    Producto,
    MovimientoInventario,
    TipoMovimiento,
    Venta,
    DetalleVenta,
    EstadoVenta,
    MetodoPago,
    Pedido,
    EstadoPedido,
    TicketSoporte,
    ComentarioTicket,
    CategoriaTicket,
    PrioridadTicket,
    EstadoTicket,
    Auditoria,
)

fake = Faker("es_ES")
random.seed(42)  # reproducibilidad entre corridas


def seed_roles():
    if Rol.query.count() > 0:
        print("↷ Roles ya existen, se omite.")
        return
    roles = [
        Rol(nombre="Administrador", descripcion="Acceso total al sistema"),
        Rol(nombre="Ventas", descripcion="Gestión de ventas y clientes"),
        Rol(nombre="Almacén", descripcion="Gestión de inventario y logística"),
        Rol(nombre="Atención al Cliente", descripcion="Gestión de tickets de soporte"),
    ]
    db.session.add_all(roles)
    db.session.commit()
    print(f"✓ {len(roles)} roles creados.")


def seed_usuarios():
    if Usuario.query.count() > 0:
        print("↷ Usuarios ya existen, se omite.")
        return

    rol_admin = Rol.query.filter_by(nombre="Administrador").first()
    rol_ventas = Rol.query.filter_by(nombre="Ventas").first()
    rol_almacen = Rol.query.filter_by(nombre="Almacén").first()
    rol_atencion = Rol.query.filter_by(nombre="Atención al Cliente").first()

    usuarios = []

    admin = Usuario(
        nombre="Admin", apellido="TechSolutions",
        email="admin@techsolutions.pe", rol=rol_admin, activo=True,
    )
    admin.set_password("admin123")
    usuarios.append(admin)

    roles_pool = [rol_ventas, rol_almacen, rol_atencion]
    for i in range(24):
        nombre = fake.first_name()
        apellido = fake.last_name()
        u = Usuario(
            nombre=nombre,
            apellido=apellido,
            email=f"{_sin_tildes(nombre.lower())}.{_sin_tildes(apellido.lower())}{i}@techsolutions.pe",
            rol=random.choice(roles_pool),
            activo=True,
        )
        u.set_password("password123")
        usuarios.append(u)

    db.session.add_all(usuarios)
    db.session.commit()
    print(f"✓ {len(usuarios)} usuarios creados (admin@techsolutions.pe / admin123).")


CATEGORIAS_TECH = {
    "Equipos de Cómputo": ["Laptops Estudiantes", "Laptops Profesionales", "Laptops Gamer"],
    "Periféricos": ["Teclados Mecánicos", "Mouse Ergonómicos", "Audífonos", "Webcams"],
    "Componentes": ["Discos SSD", "Memorias RAM", "Tarjetas Gráficas", "Fuentes de Poder"],
    "Accesorios Gamer": ["Sillas Gamer", "Alfombrillas", "Controles", "Kits de Iluminación"],
    "Monitores": ["Monitores Oficina", "Monitores Gaming"],
}


def seed_categorias():
    if Categoria.query.count() > 0:
        print("↷ Categorías ya existen, se omite.")
        return

    total = 0
    for nombre_padre, hijos in CATEGORIAS_TECH.items():
        padre = Categoria(nombre=nombre_padre, descripcion=f"Categoría {nombre_padre}")
        db.session.add(padre)
        db.session.flush()  # obtener padre.id sin cerrar la transacción
        total += 1
        for nombre_hijo in hijos:
            db.session.add(
                Categoria(
                    nombre=nombre_hijo,
                    descripcion=f"Subcategoría de {nombre_padre}",
                    categoria_padre_id=padre.id,
                )
            )
            total += 1

    db.session.commit()
    print(f"✓ {total} categorías creadas.")


MARCAS_POR_CATEGORIA = {
    "Laptops Estudiantes": ["Lenovo", "HP", "Acer"],
    "Laptops Profesionales": ["Dell", "HP", "Lenovo ThinkPad", "ASUS"],
    "Laptops Gamer": ["ASUS ROG", "MSI", "Lenovo Legion", "Acer Predator"],
    "Teclados Mecánicos": ["Logitech", "Razer", "Redragon", "HyperX"],
    "Mouse Ergonómicos": ["Logitech", "HP", "Microsoft"],
    "Audífonos": ["HyperX", "Razer", "SteelSeries", "JBL"],
    "Webcams": ["Logitech", "HP", "Razer"],
    "Discos SSD": ["Kingston", "Western Digital", "Samsung", "Crucial"],
    "Memorias RAM": ["Kingston", "Corsair", "G.Skill"],
    "Tarjetas Gráficas": ["NVIDIA", "AMD", "ASUS", "MSI"],
    "Fuentes de Poder": ["EVGA", "Corsair", "Cooler Master"],
    "Sillas Gamer": ["Cougar", "DXRacer", "Secretlab"],
    "Alfombrillas": ["Razer", "HyperX", "SteelSeries"],
    "Controles": ["Sony", "Microsoft", "Logitech"],
    "Kits de Iluminación": ["Razer", "Corsair", "Philips Hue"],
    "Monitores Oficina": ["Samsung", "LG", "Dell", "AOC"],
    "Monitores Gaming": ["ASUS ROG", "MSI", "Samsung Odyssey", "LG UltraGear"],
}


def seed_productos():
    if Producto.query.count() > 0:
        print("↷ Productos ya existen, se omite.")
        return

    hojas = Categoria.query.filter(Categoria.categoria_padre_id.isnot(None)).all()
    if not hojas:
        hojas = Categoria.query.all()

    productos = []
    contador_sku = 1000
    for categoria in hojas:
        marcas = MARCAS_POR_CATEGORIA.get(categoria.nombre, ["Genérico"])
        for _ in range(random.randint(9, 16)):
            marca = random.choice(marcas)
            modelo = fake.bothify(text="??-####").upper()
            precio_compra = Decimal(random.randrange(300, 6000))
            margen = Decimal(str(round(random.uniform(1.15, 1.45), 2)))
            precio_venta = (precio_compra * margen).quantize(Decimal("0.01"))
            contador_sku += 1
            stock_inicial = random.randint(0, 80)

            productos.append(
                Producto(
                    sku=f"TS-{contador_sku}",
                    nombre=f"{marca} {categoria.nombre.rstrip('s')} {modelo}",
                    descripcion=fake.sentence(nb_words=14),
                    categoria=categoria,
                    marca=marca,
                    modelo=modelo,
                    precio_compra=precio_compra,
                    precio_venta=precio_venta,
                    stock_actual=stock_inicial,
                    stock_minimo=random.choice([5, 10, 15]),
                )
            )

    db.session.add_all(productos)
    db.session.commit()
    print(f"✓ {len(productos)} productos creados.")

    # Movimiento inicial de inventario para cada producto (trazabilidad)
    admin = Usuario.query.filter_by(email="admin@techsolutions.pe").first()
    movimientos = []
    for p in productos:
        if p.stock_actual > 0:
            movimientos.append(
                MovimientoInventario(
                    producto=p,
                    tipo=TipoMovimiento.ENTRADA,
                    cantidad=p.stock_actual,
                    stock_anterior=0,
                    stock_nuevo=p.stock_actual,
                    motivo="Carga inicial de inventario",
                    usuario=admin,
                    fecha=ahora() - timedelta(days=random.randint(20, 60)),
                )
            )
    db.session.add_all(movimientos)
    db.session.commit()
    print(f"✓ {len(movimientos)} movimientos de inventario iniciales creados.")


def seed_clientes():
    if Cliente.query.count() > 0:
        print("↷ Clientes ya existen, se omite.")
        return

    clientes = []
    for i in range(250):
        nombre = fake.first_name()
        apellido = fake.last_name()
        clientes.append(
            Cliente(
                nombre=nombre,
                apellido=apellido,
                email=f"{_sin_tildes(nombre.lower())}.{_sin_tildes(apellido.lower())}{i}@correo.com",
                telefono=fake.phone_number(),
                dni_ruc=fake.unique.numerify(text="########"),
                direccion=fake.street_address(),
                ciudad=random.choice(["Lima", "Arequipa", "Trujillo", "Cusco", "Piura", "Chiclayo"]),
            )
        )
    db.session.add_all(clientes)
    db.session.commit()
    print(f"✓ {len(clientes)} clientes creados.")


def seed_ventas_pedidos():
    if Venta.query.count() > 0:
        print("↷ Ventas ya existen, se omite.")
        return

    clientes = Cliente.query.all()
    productos = Producto.query.filter(Producto.stock_actual > 0).all()
    vendedores = Usuario.query.all()

    if not clientes or not productos:
        print("⚠ No hay clientes o productos suficientes para generar ventas.")
        return

    IGV = Decimal("0.18")
    ventas_creadas, pedidos_creados, movimientos = [], [], []

    for i in range(400):
        cliente = random.choice(clientes)
        vendedor = random.choice(vendedores)
        fecha_venta = ahora() - timedelta(days=random.randint(0, 89))
        estado = random.choices(
            [EstadoVenta.COMPLETADA, EstadoVenta.PENDIENTE, EstadoVenta.ANULADA],
            weights=[0.75, 0.15, 0.10],
        )[0]

        venta = Venta(
            numero_venta=f"V-{2000 + i}",
            cliente=cliente,
            vendedor=vendedor,
            fecha_venta=fecha_venta,
            metodo_pago=random.choice(list(MetodoPago)),
            estado=estado,
            subtotal=0,
            igv=0,
            total=0,
        )
        db.session.add(venta)
        db.session.flush()

        subtotal_acumulado = Decimal("0")
        productos_venta = random.sample(productos, k=min(random.randint(1, 4), len(productos)))
        for producto in productos_venta:
            cantidad = random.randint(1, min(3, max(1, producto.stock_actual)) or 1)
            precio_unitario = producto.precio_venta
            sub = (precio_unitario * cantidad).quantize(Decimal("0.01"))
            subtotal_acumulado += sub

            db.session.add(
                DetalleVenta(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=sub,
                )
            )

            if estado == EstadoVenta.COMPLETADA and producto.stock_actual >= cantidad:
                stock_anterior = producto.stock_actual
                producto.stock_actual -= cantidad
                movimientos.append(
                    MovimientoInventario(
                        producto=producto,
                        tipo=TipoMovimiento.SALIDA,
                        cantidad=cantidad,
                        stock_anterior=stock_anterior,
                        stock_nuevo=producto.stock_actual,
                        motivo="Venta a cliente",
                        referencia=venta.numero_venta,
                        usuario=vendedor,
                        fecha=fecha_venta,
                    )
                )

        venta.subtotal = subtotal_acumulado.quantize(Decimal("0.01"))
        venta.igv = (venta.subtotal * IGV).quantize(Decimal("0.01"))
        venta.total = (venta.subtotal + venta.igv).quantize(Decimal("0.01"))
        ventas_creadas.append(venta)

        # Pedido logístico solo para ventas completadas
        if estado == EstadoVenta.COMPLETADA:
            estado_pedido = random.choices(
                [EstadoPedido.PROCESANDO, EstadoPedido.EN_CAMINO, EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO],
                weights=[0.2, 0.25, 0.5, 0.05],
            )[0]
            pedido = Pedido(
                numero_pedido=f"P-{3000 + i}",
                venta=venta,
                cliente=cliente,
                direccion_envio=cliente.direccion or fake.street_address(),
                ciudad_envio=cliente.ciudad,
                estado=estado_pedido,
                transportista=random.choice(["Olva Courier", "Shalom", "Servientrega", "Chazki"]),
                numero_seguimiento=fake.bothify(text="TRK########"),
                fecha_pedido=fecha_venta + timedelta(hours=random.randint(1, 24)),
                fecha_entrega_estimada=(fecha_venta + timedelta(days=random.randint(2, 7))).date(),
            )
            pedidos_creados.append(pedido)
            db.session.add(pedido)

    db.session.add_all(movimientos)
    db.session.commit()
    print(f"✓ {len(ventas_creadas)} ventas, {len(pedidos_creados)} pedidos y {len(movimientos)} movimientos de salida creados.")


def seed_tickets_soporte():
    if TicketSoporte.query.count() > 0:
        print("↷ Tickets de soporte ya existen, se omite.")
        return

    clientes = Cliente.query.all()
    agentes = Usuario.query.join(Rol).filter(Rol.nombre == "Atención al Cliente").all()
    if not agentes:
        agentes = Usuario.query.all()

    asuntos = [
        ("Producto llegó con defecto de fábrica", CategoriaTicket.RECLAMO),
        ("Consulta sobre garantía extendida", CategoriaTicket.CONSULTA),
        ("No enciende el equipo tras la compra", CategoriaTicket.SOPORTE_TECNICO),
        ("Solicito cambio de producto por talla/modelo", CategoriaTicket.CAMBIO_DEVOLUCION),
        ("Retraso en la entrega del pedido", CategoriaTicket.RECLAMO),
        ("Duda sobre compatibilidad de componentes", CategoriaTicket.CONSULTA),
    ]

    tickets = []
    for i in range(120):
        asunto, categoria = random.choice(asuntos)
        estado = random.choices(
            [EstadoTicket.ABIERTO, EstadoTicket.EN_PROCESO, EstadoTicket.CERRADO],
            weights=[0.3, 0.3, 0.4],
        )[0]
        fecha_creacion = ahora() - timedelta(days=random.randint(0, 25))

        ticket = TicketSoporte(
            codigo=f"TK-{4000 + i}",
            cliente=random.choice(clientes),
            agente=random.choice(agentes),
            asunto=asunto,
            descripcion=fake.paragraph(nb_sentences=3),
            categoria=categoria,
            prioridad=random.choice(list(PrioridadTicket)),
            estado=estado,
            fecha_creacion=fecha_creacion,
            fecha_cierre=fecha_creacion + timedelta(days=random.randint(1, 4)) if estado == EstadoTicket.CERRADO else None,
        )
        db.session.add(ticket)
        db.session.flush()

        db.session.add(
            ComentarioTicket(
                ticket=ticket,
                usuario=ticket.agente,
                mensaje=fake.sentence(nb_words=16),
                fecha=fecha_creacion + timedelta(hours=random.randint(1, 12)),
            )
        )
        tickets.append(ticket)

    db.session.commit()
    print(f"✓ {len(tickets)} tickets de soporte creados con su primer comentario.")


def seed_auditoria():
    if Auditoria.query.count() > 0:
        print("↷ Auditoría ya tiene registros, se omite.")
        return

    admin = Usuario.query.filter_by(email="admin@techsolutions.pe").first()
    if not admin:
        print("⚠ No hay usuario admin para generar auditoría inicial.")
        return

    db.session.add(
        Auditoria(
            usuario=admin,
            accion="CREATE",
            tabla_afectada="sistema",
            registro_id=None,
            datos_nuevos={"evento": "Inicialización de datos de prueba (seed.py)"},
            ip_address="127.0.0.1",
        )
    )
    db.session.commit()
    print("✓ Registro inicial de auditoría creado.")


def seed_database():
    """
    Ejecuta todos los bloques de seed. Debe llamarse DENTRO de un
    app.app_context() ya abierto (run.py lo hace automáticamente al
    iniciar el servidor; también puede ejecutarse este archivo solo).
    """
    print("== Iniciando seed de TechSolutions ERP ==")
    seed_roles()
    seed_usuarios()
    seed_categorias()
    seed_productos()
    seed_clientes()
    seed_ventas_pedidos()
    seed_tickets_soporte()
    seed_auditoria()
    print("== Seed finalizado. Puede ejecutarse nuevamente sin duplicar datos. ==")


if __name__ == "__main__":
    # Ejecución independiente: python seed.py
    from app import create_app

    app = create_app()
    with app.app_context():
        seed_database()

