import json
D = "eval/runs/pipeline/HU-202/run-3"
frames = json.load(open(f"{D}/frames.json", encoding="utf-8"))["frames"]
ids = [f["frame_id"] for f in frames]


def S(a, e):
    return {"action": a, "expected": e}


def common_steps(cuenta, rango, fmt):
    d, h = rango
    return [
        S("Iniciar sesión en el home banking con un cliente titular de la cuenta", "Se muestra el home banking con el menú principal"),
        S('Ingresar a la sección "Movimientos"', 'Se muestra la pantalla "Movimientos" con la opción de exportar'),
        S(f"Seleccionar la cuenta {cuenta}", f"La cuenta {cuenta} queda seleccionada"),
        S(f"Ingresar la fecha desde {d}", f"El campo desde muestra {d}"),
        S(f"Ingresar la fecha hasta {h}", f"El campo hasta muestra {h}"),
        S(f"Seleccionar el formato {fmt}", f"El formato {fmt} queda seleccionado"),
        S('Tocar el botón "Exportar"', None),
    ]


def pos(fid, cuenta, rango, fmt, ext, cur, title):
    d, h = rango
    steps = common_steps(cuenta, rango, fmt)
    steps[-1]["expected"] = "El sistema inicia la generación del archivo"
    steps.append(S("Observar la descarga del archivo",
                   f"Se descarga un archivo con nombre movimientos_<cuenta>_<desde>_<hasta>.{ext} correspondiente a la cuenta {cuenta}, desde {d} hasta {h} [SUPUESTO: la HU no define el formato de <cuenta> ni de las fechas dentro del nombre del archivo]"))
    steps.append(S(f"Abrir el archivo {ext.upper()} descargado",
                   f"El archivo contiene los movimientos del período {d} a {h}, con fecha, descripción, importe y saldo de cada movimiento"))
    steps.append(S("Revisar los importes y el saldo del archivo", f"Los importes y el saldo se expresan en {cur}, la moneda de la cuenta"))
    return {"frame_id": fid, "title": title,
            "preconditions": f"Cliente autenticado titular de la cuenta {cuenta}, con movimientos registrados entre {d} y {h}; rango de fechas de prueba: desde {d} hasta {h}; servicio operativo",
            "steps": steps,
            "evidence": f"Captura de la pantalla de selección, archivo {ext.upper()} descargado (nombre visible) y su contenido"}


def vacio(fid, cuenta, rango, fmt, title):
    d, h = rango
    steps = common_steps(cuenta, rango, fmt)
    steps[-1]["expected"] = "El sistema procesa la solicitud de exportación"
    steps.append(S("Observar la pantalla tras la solicitud",
                   f"Se muestra un mensaje en pantalla indicando que no hay movimientos en el rango {d} a {h} [SUPUESTO: la HU solo dice \"un mensaje adecuado\"; el texto exacto no está definido]"))
    return {"frame_id": fid, "title": title,
            "preconditions": f"Cliente autenticado titular de la cuenta {cuenta}, sin movimientos registrados entre {d} y {h}; rango de fechas de prueba: desde {d} hasta {h}; servicio operativo",
            "steps": steps, "evidence": "Captura de la pantalla con el mensaje mostrado"}


A = ("01/09/2026", "30/09/2026")
V = ("01/01/2020", "31/01/2020")
ARS = "Caja de ahorro ARS 0012345678"
USD = "Caja de ahorro USD 0087654321"
by = {}
by["F-f19c8ca0"] = pos("F-f19c8ca0", ARS, A, "CSV", "csv", "ARS (pesos)", "Verificar que se exporta en CSV los movimientos de una cuenta en ARS con un rango con movimientos")
by["F-2cc50681"] = pos("F-2cc50681", USD, A, "PDF", "pdf", "USD (dólares)", "Verificar que se exporta en PDF los movimientos de una cuenta en USD con un rango con movimientos")
by["F-81120e0c"] = vacio("F-81120e0c", ARS, V, "PDF", "Verificar que se muestra un mensaje al exportar en PDF un rango sin movimientos de una cuenta en ARS")
by["F-ba68e4b3"] = vacio("F-ba68e4b3", ARS, V, "XLSX", "Verificar que se muestra un mensaje al exportar en XLSX un rango sin movimientos de una cuenta en ARS")
by["F-3b87264a"] = vacio("F-3b87264a", USD, V, "CSV", "Verificar que se muestra un mensaje al exportar en CSV un rango sin movimientos de una cuenta en USD")
by["F-4832d158"] = pos("F-4832d158", USD, A, "XLSX", "xlsx", "USD (dólares)", "Verificar que se exporta en XLSX los movimientos de una cuenta en USD con un rango con movimientos")
by["F-27f3889f"] = vacio("F-27f3889f", USD, V, "XLSX", "Verificar que se muestra un mensaje al exportar en XLSX un rango sin movimientos de una cuenta en USD")


def neg(fid, title, cuenta, d, h, fmt, pre, desc):
    steps = [
        S("Iniciar sesión en el home banking con un cliente titular de la cuenta", "Se muestra el home banking con el menú principal"),
        S('Ingresar a la sección "Movimientos"', 'Se muestra la pantalla "Movimientos" con la opción de exportar'),
        S(f"Seleccionar la cuenta {cuenta}", f"La cuenta {cuenta} queda seleccionada"),
    ]
    if d is None:
        steps.append(S("Dejar vacíos los campos de fecha desde y hasta", "Los campos de fecha desde y hasta permanecen vacíos"))
    else:
        steps.append(S(f"Ingresar la fecha desde {d}", f"El campo desde muestra {d}"))
        steps.append(S(f"Ingresar la fecha hasta {h}", f"El campo hasta muestra {h}"))
    if fmt is None:
        steps.append(S("No seleccionar ningún formato", "Ningún formato (CSV, XLSX o PDF) queda seleccionado"))
    else:
        steps.append(S(f"Seleccionar el formato {fmt}", f"El formato {fmt} queda seleccionado"))
    steps.append(S('Tocar el botón "Exportar"',
                   f"El sistema rechaza la solicitud y muestra un mensaje que explica que {desc}; no se descarga ningún archivo [SUPUESTO: la HU no define el rechazo ni el texto del mensaje]"))
    if d is not None:
        pre = pre + f"; rango de fechas de prueba: desde {d} hasta {h}"
    pre = pre + "; servicio operativo"
    return {"frame_id": fid, "title": title, "preconditions": pre, "steps": steps,
            "evidence": "Captura de la pantalla con el mensaje de error y verificación de que no se descargó archivo"}


pre = f"Cliente autenticado titular de la cuenta {ARS}"
by["F-83703c6e"] = neg("F-83703c6e", "Verificar que se rechaza la exportación cuando la fecha desde es posterior a la fecha hasta", ARS, "30/09/2026", "01/09/2026", "CSV", pre, "la fecha desde no puede ser posterior a la fecha hasta")
by["F-b94ee31a"] = neg("F-b94ee31a", "Verificar que se rechaza la exportación cuando no se completan las fechas desde y hasta", ARS, None, None, "CSV", pre, "deben completarse las fechas desde y hasta")
by["F-26d05388"] = neg("F-26d05388", "Verificar que se rechaza la exportación cuando la fecha hasta es posterior a la fecha actual", ARS, "01/09/2026", "31/12/2030", "CSV", pre, "la fecha hasta no puede ser posterior a la fecha actual")
by["F-d93b95f5"] = neg("F-d93b95f5", "Verificar que se rechaza la exportación cuando no se selecciona ningún formato", ARS, "01/09/2026", "30/09/2026", None, pre, "debe seleccionarse un formato")

by["F-3ed7e423"] = {"frame_id": "F-3ed7e423", "title": "Verificar que un usuario sin permiso no puede exportar movimientos de una cuenta ajena",
    "preconditions": "Existen dos clientes: el titular de la cuenta Caja de ahorro ARS 0012345678 y otro cliente autenticado que no es titular de esa cuenta",
    "steps": [
        S("Iniciar sesión con el cliente que no es titular de la cuenta Caja de ahorro ARS 0012345678", "Se muestra el home banking del cliente"),
        S('Ingresar a la sección "Movimientos"', 'Se muestra la pantalla "Movimientos" con solo las cuentas propias de ese cliente'),
        S("Verificar la lista de cuentas seleccionables", "La cuenta Caja de ahorro ARS 0012345678 no aparece en la lista"),
        S("Enviar el pedido de exportación de la cuenta Caja de ahorro ARS 0012345678 directamente al endpoint (por ejemplo con una herramienta de pruebas de API)",
          "El pedido es rechazado con 403 y no se descarga archivo ni se exponen datos ajenos [SUPUESTO: solo el titular puede exportar; ver roles.permissions]")],
    "evidence": "Captura de la lista de cuentas y respuesta 403 del pedido"}
by["F-ca62321c"] = {"frame_id": "F-ca62321c", "title": "Verificar que una exportación de un período sin datos informa que no hay movimientos y no genera archivo",
    "preconditions": f"Cliente autenticado titular de la cuenta {ARS}, sin movimientos entre 01/01/2020 y 31/01/2020",
    "steps": [
        S('Ingresar a la sección "Movimientos"', 'Se muestra la pantalla "Movimientos"'),
        S(f"Seleccionar la cuenta {ARS}", "La cuenta queda seleccionada"),
        S("Ingresar la fecha desde 01/01/2020", "El campo desde muestra 01/01/2020"),
        S("Ingresar la fecha hasta 31/01/2020", "El campo hasta muestra 31/01/2020"),
        S("Seleccionar el formato CSV", "El formato CSV queda seleccionado"),
        S('Tocar el botón "Exportar"', "Se muestra el mensaje \"No hay movimientos para el período\" y no se descarga ningún archivo [SUPUESTO: texto del mensaje y no generación de archivo vacío; ver export.volume]")],
    "evidence": "Captura del mensaje y verificación de que no hay archivo descargado"}
by["F-22399e44"] = {"frame_id": "F-22399e44", "title": "Verificar que un doble toque en Exportar genera una sola exportación",
    "preconditions": f"Cliente autenticado titular de la cuenta {ARS} con movimientos entre 01/09/2026 y 30/09/2026",
    "steps": [
        S('Ingresar a la sección "Movimientos"', 'Se muestra la pantalla "Movimientos"'),
        S(f"Seleccionar la cuenta {ARS}", "La cuenta queda seleccionada"),
        S("Ingresar la fecha desde 01/09/2026", "El campo desde muestra 01/09/2026"),
        S("Ingresar la fecha hasta 30/09/2026", "El campo hasta muestra 30/09/2026"),
        S("Seleccionar el formato CSV", "El formato CSV queda seleccionado"),
        S('Tocar dos veces seguidas el botón "Exportar" en menos de un segundo', "Se registra una sola operación de exportación [SUPUESTO: la operación es idempotente; ver money.idempotency]"),
        S("Revisar los archivos descargados", "Se descargó un único archivo de exportación, sin duplicados")],
    "evidence": "Captura de la carpeta de descargas y del registro de operaciones"}
by["F-02ba5e93"] = {"frame_id": "F-02ba5e93", "title": "Verificar que se informa el error cuando falla el servicio de generación del archivo",
    "preconditions": f"Cliente autenticado titular de la cuenta {ARS} con movimientos entre 01/09/2026 y 30/09/2026; servicio de exportación caído (simulado); rango de fechas de prueba: desde 01/09/2026 hasta 30/09/2026",
    "steps": [
        S('Ingresar a la sección "Movimientos"', 'Se muestra la pantalla "Movimientos"'),
        S(f"Seleccionar la cuenta {ARS}", "La cuenta queda seleccionada"),
        S("Ingresar la fecha desde 01/09/2026", "El campo desde muestra 01/09/2026"),
        S("Ingresar la fecha hasta 30/09/2026", "El campo hasta muestra 30/09/2026"),
        S("Seleccionar el formato CSV", "El formato CSV queda seleccionado"),
        S('Tocar el botón "Exportar"', "El sistema muestra un mensaje que explica que no se pudo generar el archivo, no se descarga ningún archivo y el cliente permanece en la pantalla \"Movimientos\" con los datos cargados [SUPUESTO: la HU no define el comportamiento ante fallos del servicio]")],
    "evidence": "Captura del mensaje de error y verificación de que no hay archivo descargado"}
by["F-bf34939d"] = {"frame_id": "F-bf34939d", "title": "Verificar que el flujo de exportación se completa igual en los navegadores soportados",
    "preconditions": f"Cliente autenticado titular de la cuenta {ARS} con movimientos entre 01/09/2026 y 30/09/2026; Chrome, Firefox y Safari desktop y Chrome móvil disponibles",
    "steps": [
        S("Abrir el home banking en Chrome desktop", "Se muestra la pantalla de inicio de sesión"),
        S("Iniciar sesión con el cliente titular", "Se muestra el home banking"),
        S(f"Exportar en CSV la cuenta {ARS} del 01/09/2026 al 30/09/2026 desde \"Movimientos\"", "Se descarga el archivo con los movimientos del período"),
        S("Repetir los pasos anteriores en Firefox desktop", "Se descarga el archivo con los mismos movimientos"),
        S("Repetir los pasos anteriores en Safari desktop", "Se descarga el archivo con los mismos movimientos"),
        S("Repetir los pasos anteriores en Chrome móvil", "Se descarga el archivo con los mismos movimientos [SUPUESTO: solo español; Chrome, Firefox y Safari desktop + Chrome móvil; ver context.platform_i18n]")],
    "evidence": "Capturas de cada navegador y archivos descargados"}
assert set(by) == set(ids), (set(ids) - set(by), set(by) - set(ids))
suite = {"story_id": "HU-202", "cases": [by[i] for i in ids]}
json.dump(suite, open(f"{D}/suite.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
