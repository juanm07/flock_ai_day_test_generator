import json
D = "eval/runs/pipeline/HU-202/run-2"
frames = {f["case_id"]: f for f in json.load(open(f"{D}/frames.json", encoding="utf-8"))["frames"]}
fid = lambda cp: frames[cp]["frame_id"]
ARS = "Caja de ahorro en pesos 0010-1234567/8 (ARS)"
USD = "Caja de ahorro en dólares 0010-7654321/9 (USD)"
PRE = "El cliente tiene sesión iniciada en home banking y posee las cuentas {c}."
NAME_SUP = "[SUPUESTO: la HU no define el formato de <cuenta> ni de las fechas dentro del nombre]"
Q = '"'


def q(v):
    return Q + v + Q if v else None


def nav():
    return [
        ("Ingresar a la sección \"Movimientos\"", "Se muestra la pantalla \"Movimientos\" con el selector de cuenta, los campos de fecha desde/hasta, el selector de formato y el botón \"Exportar\""),
    ]


def sel(cuenta, desde, hasta, fmt):
    s = []
    s.append(("Seleccionar la cuenta " + q(cuenta) if cuenta else "Dejar el selector de cuenta sin seleccionar",
              "El selector de cuenta muestra " + (q(cuenta) if cuenta else "ninguna cuenta seleccionada")))
    s.append(("Ingresar " + q(desde) + " en el campo de fecha desde" if desde else "Dejar vacío el campo de fecha desde",
              "El campo de fecha desde muestra " + (q(desde) if desde else "vacío")))
    s.append(("Ingresar " + q(hasta) + " en el campo de fecha hasta" if hasta else "Dejar vacío el campo de fecha hasta",
              "El campo de fecha hasta muestra " + (q(hasta) if hasta else "vacío")))
    s.append(("Seleccionar el formato " + q(fmt) if fmt else "Dejar sin seleccionar el formato",
              "El selector de formato muestra " + (q(fmt) if fmt else "ningún formato seleccionado")))
    return s


cases = []


def add(cp, title, pre, steps, evidence, notes=""):
    blob = title + pre + " ".join(a + e for a, e in steps)
    extra = [str(v) for v in frames[cp]["data"].values() if str(v) not in blob]
    if extra:
        pre = pre + " Datos de prueba: " + "; ".join(extra) + "."
    cases.append({"frame_id": fid(cp), "title": title, "preconditions": pre,
                  "steps": [{"action": a, "expected": e} for a, e in steps],
                  "evidence": evidence, "notes": notes})


def ok(cp, cuenta, mon, fmt, title=None):
    ext = fmt.lower()
    steps = nav() + sel(cuenta, "01/09/2026", "30/09/2026", fmt) + [
        ("Tocar el botón \"Exportar\"", "El sistema genera el archivo y la descarga se inicia"),
        ("Verificar el nombre del archivo descargado", f"El archivo se llama movimientos_<cuenta>_<desde>_<hasta>.{ext}, con <cuenta> de {q(cuenta)}, <desde> de 01/09/2026 y <hasta> de 30/09/2026 {NAME_SUP}"),
        (f"Abrir el archivo {fmt} descargado", f"El archivo contiene los movimientos del período 01/09/2026 al 30/09/2026 con fecha, descripción, importe y saldo, y los importes figuran en {mon}"),
    ]
    add(cp, title or f"Verificar que se exportan en {fmt} los movimientos de la cuenta en {mon} del 01/09/2026 al 30/09/2026 con el nombre de archivo esperado",
        PRE.format(c=q(cuenta)) + " La cuenta tiene movimientos entre 01/09/2026 y 30/09/2026.",
        steps, f"Captura de la pantalla \"Movimientos\" y archivo .{ext} descargado")


ok("CP-001", ARS, "ARS", "CSV", title="Verificar que el cliente exporta en CSV los movimientos de su cuenta en ARS del 01/09/2026 al 30/09/2026 y el archivo se descarga con el nombre esperado")
ok("CP-002", USD, "USD", "XLSX")
ok("CP-003", USD, "USD", "PDF")
ok("CP-004", ARS, "ARS", "PDF")
ok("CP-005", ARS, "ARS", "XLSX")
ok("CP-006", USD, "USD", "CSV")


def neg(cp, title, cuenta, desde, hasta, fmt, field):
    steps = nav() + sel(cuenta, desde, hasta, fmt) + [
        ("Tocar el botón \"Exportar\"", f"El sistema no genera ni descarga ningún archivo y muestra un mensaje de error que indica que {field} [SUPUESTO: la HU no define el texto del mensaje ni la validación; se asume rechazo con mensaje explicativo sin cambiar el estado]"),
    ]
    add(cp, title, PRE.format(c=q(ARS)) + " La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026.", steps,
        "Captura del mensaje de error y verificación de que no se descargó ningún archivo")


neg("CP-007", "Verificar que no se exporta si no se selecciona ninguna cuenta", "", "01/09/2026", "30/09/2026", "CSV", "debe seleccionarse una cuenta")
neg("CP-008", "Verificar que no se exporta si la fecha desde está vacía", ARS, "", "30/09/2026", "CSV", "debe completarse la fecha desde")
neg("CP-009", "Verificar que no se exporta si la fecha desde (30/09/2026) es posterior a la fecha hasta (01/09/2026)", ARS, "30/09/2026", "01/09/2026", "CSV", "la fecha desde no puede ser posterior a la fecha hasta")
neg("CP-010", "Verificar que no se exporta si la fecha hasta está vacía", ARS, "01/09/2026", "", "CSV", "debe completarse la fecha hasta")
neg("CP-011", "Verificar que no se exporta si no se selecciona ningún formato", ARS, "01/09/2026", "30/09/2026", "", "debe seleccionarse un formato")

add("CP-012", "Verificar que un usuario sin permiso no puede exportar ni ver los movimientos de una cuenta ajena",
    "Existen dos clientes: qa.usuario01@empresa.com (titular de la cuenta 0010-1234567/8) y qa.usuario02@empresa.com (titular de otra cuenta). Se conoce el identificador de la cuenta 0010-1234567/8.",
    [("Iniciar sesión como qa.usuario02@empresa.com", "Se muestra el home banking del usuario qa.usuario02@empresa.com"),
     ("Ingresar a la sección \"Movimientos\"", "El selector de cuenta lista solo las cuentas de qa.usuario02@empresa.com y no incluye la cuenta 0010-1234567/8"),
     ("Enviar la solicitud de exportación de la cuenta 0010-1234567/8 desde 01/09/2026 hasta 30/09/2026 en CSV con un cliente HTTP usando la sesión de qa.usuario02@empresa.com", "La solicitud es rechazada con respuesta 403 y no se descarga ningún archivo ni se exponen datos de la cuenta ajena [SUPUESTO: solo el titular de la cuenta puede exportar; otro usuario autenticado recibe 403]")],
    "Respuesta HTTP 403 capturada y selector de cuentas del usuario")

add("CP-013", "Verificar que la exportación de un período sin datos informa que no hay movimientos y no genera archivo",
    PRE.format(c=q(ARS)) + " La cuenta no tiene movimientos entre 01/01/2026 y 31/01/2026.",
    nav() + sel(ARS, "01/01/2026", "31/01/2026", "CSV") + [
     ("Tocar el botón \"Exportar\"", "El sistema muestra el mensaje \"No hay movimientos para el período\" y no se genera ni descarga ningún archivo [SUPUESTO: texto del mensaje y máximo de 10.000 filas exportables no definidos en la HU]")],
    "Captura del mensaje mostrado y de la ausencia de descarga")

add("CP-014", "Verificar que un doble submit sobre \"Exportar\" genera una sola exportación",
    PRE.format(c=q(ARS)) + " La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026.",
    nav() + sel(ARS, "01/09/2026", "30/09/2026", "CSV") + [
     ("Tocar dos veces seguidas el botón \"Exportar\" en menos de un segundo", "Se registra una sola operación de exportación y se descarga un único archivo movimientos_<cuenta>_<desde>_<hasta>.csv [SUPUESTO: la operación es idempotente ante doble submit]"),
     ("Revisar la carpeta de descargas", "Existe un solo archivo movimientos_<cuenta>_<desde>_<hasta>.csv y no una segunda copia")],
    "Captura de la carpeta de descargas y del registro de operaciones")


def ca2(cp, cuenta, mon, fmt, con, title):
    ext = fmt.lower()
    if con:
        steps = nav() + sel(cuenta, "01/09/2026", "30/09/2026", fmt) + [
            ("Tocar el botón \"Exportar\"", "El sistema genera el archivo y la descarga se inicia"),
            (f"Abrir el archivo {fmt} descargado", f"El archivo contiene los 25 movimientos del período 01/09/2026 al 30/09/2026 con fecha, descripción, importe y saldo de cada movimiento, y los importes figuran en {mon}"),
            ("Verificar el tiempo de generación", "El archivo se genera dentro del umbral que defina el PO [SUPUESTO: la HU dice \"rápidamente\" sin umbral; se toma como criterio provisional un máximo de 5 segundos]")]
        pre = PRE.format(c=q(cuenta)) + " La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026."
        ev = f"Archivo .{ext} descargado y cronometraje de la generación"
    else:
        steps = nav() + sel(cuenta, "01/01/2026", "31/01/2026", fmt) + [
            ("Tocar el botón \"Exportar\"", f"El sistema muestra un mensaje indicando que no hay movimientos en el rango 01/01/2026 al 31/01/2026 y no descarga ningún archivo {fmt} [SUPUESTO: la HU solo dice \"un mensaje adecuado\"; el texto exacto no está definido]")]
        pre = PRE.format(c=q(cuenta)) + " La cuenta no tiene movimientos entre 01/01/2026 y 31/01/2026."
        ev = "Captura del mensaje mostrado"
    add(cp, title, pre, steps, ev)


ca2("CP-015", ARS, "ARS", "CSV", True, "Verificar que el archivo CSV de la cuenta en ARS incluye fecha, descripción, importe y saldo de los movimientos del 01/09/2026 al 30/09/2026")
ca2("CP-016", USD, "USD", "XLSX", False, "Verificar que al exportar en XLSX una cuenta en USD sin movimientos del 01/01/2026 al 31/01/2026 se muestra un mensaje")
ca2("CP-017", USD, "USD", "PDF", True, "Verificar que el archivo PDF de la cuenta en USD incluye fecha, descripción, importe y saldo de los movimientos del 01/09/2026 al 30/09/2026")
ca2("CP-018", ARS, "ARS", "PDF", False, "Verificar que al exportar en PDF una cuenta en ARS sin movimientos del 01/01/2026 al 31/01/2026 se muestra un mensaje")
ca2("CP-019", ARS, "ARS", "XLSX", True, "Verificar que el archivo XLSX de la cuenta en ARS incluye fecha, descripción, importe y saldo de los movimientos del 01/09/2026 al 30/09/2026")
ca2("CP-020", USD, "USD", "CSV", False, "Verificar que al exportar en CSV una cuenta en USD sin movimientos del 01/01/2026 al 31/01/2026 se muestra un mensaje")

add("CP-021", "Verificar que si el servicio de generación de archivos está caído se informa el error y no se descarga ningún archivo",
    PRE.format(c=q(ARS)) + " La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026. El servicio de generación de archivos está caído.",
    nav() + sel(ARS, "01/09/2026", "30/09/2026", "CSV") + [
     ("Tocar el botón \"Exportar\"", "El sistema muestra un mensaje de error indicando que no se pudo generar el archivo, no descarga ningún archivo y los datos seleccionados siguen cargados en la pantalla [SUPUESTO: la HU no define el comportamiento ante falla del servicio]")],
    "Captura del mensaje de error")

split = []
for b in ["Chrome desktop", "Firefox desktop", "Safari desktop", "Chrome móvil"]:
    split += [(f"Abrir home banking en {b}", f"Se muestra la pantalla de login en {b}"),
              ("Iniciar sesión con el usuario del cliente", f"Se muestra el home banking en {b}"),
              ("Ingresar a la sección \"Movimientos\"", f"Se muestra la pantalla \"Movimientos\" en {b} con el botón \"Exportar\""),
              (f"Seleccionar la cuenta {q(ARS)}, fecha desde \"01/09/2026\", fecha hasta \"30/09/2026\" y formato \"CSV\"", f"Los cuatro campos muestran los valores elegidos en {b}"),
              ("Tocar el botón \"Exportar\"", f"En {b} se descarga el archivo movimientos_<cuenta>_<desde>_<hasta>.csv con los movimientos del período")]
add("CP-022", "Verificar que el flujo de exportación se completa igual en los navegadores soportados",
    PRE.format(c=q(ARS)) + " La cuenta tiene 25 movimientos entre 01/09/2026 y 30/09/2026.",
    split, "Capturas de la descarga en cada navegador [SUPUESTO: navegadores soportados: Chrome, Firefox y Safari desktop + Chrome móvil; solo español]")

assert len(cases) == 22, len(cases)
json.dump({"story_id": "HU-202", "cases": cases}, open(f"{D}/suite.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
