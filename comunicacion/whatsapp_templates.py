class WhatsAppTemplates:
    @staticmethod
    def reserva_confirmada(nombre, ruta, fecha, asiento, codigo_reserva):
        return (
            f"✅ *RESERVA CONFIRMADA*\n\n"
            f"Hola *{nombre}*,\n"
            f"Tu viaje a *{ruta}* está listo.\n\n"
            f"📅 Fecha: {fecha}\n"
            f"💺 Asiento: {asiento}\n"
            f"🔢 Código: *{codigo_reserva}*\n\n"
            f"Por favor llega 15 min antes. ¡Buen viaje!\n"
            f"_Sindicato Integración Taipiplaya_"
        )

    @staticmethod
    def pago_recibido(nombre, concepto, monto, fecha, nro_recibo):
        return (
            f"💰 *PAGO RECIBIDO*\n\n"
            f"Estimado/a *{nombre}*,\n"
            f"Hemos recibido tu pago correctamente.\n\n"
            f"📝 Concepto: {concepto}\n"
            f"💵 Monto: Bs. {monto}\n"
            f"📅 Fecha: {fecha}\n"
            f"🧾 Recibo Nro: {nro_recibo}\n\n"
            f"Gracias por cumplir con tus aportes.\n"
            f"_Sindicato Integración Taipiplaya_"
        )

    @staticmethod
    def alerta_deuda(nombre, monto_total, cantidad_sanciones):
        return (
            f"⚠️ *AVISO DE SANCIONES*\n\n"
            f"Hola *{nombre}*,\n"
            f"Te recordamos que tienes sanciones pendientes.\n\n"
            f"🔴 Cantidad: {cantidad_sanciones}\n"
            f"💲 Deuda Total: Bs. {monto_total}\n\n"
            f"Por favor pasa por tesorería para regularizar tu situación y evitar bloqueos en el sistema.\n"
            f"_Sindicato Integración Taipiplaya_"
        )

    @staticmethod
    def reporte_diario(fecha, total_ingresos, cantidad_pagos, detalle_top):
        return (
            f"📊 *REPORTE DIARIO DE CAJA*\n"
            f"📅 Fecha: {fecha}\n\n"
            f"💵 Total Ingresos: Bs. {total_ingresos}\n"
            f"🔢 Cantidad Pagos: {cantidad_pagos}\n\n"
            f"🏆 *Top Ingresos:*\n{detalle_top}\n\n"
            f"_Sitema de Administración_"
        )

    @staticmethod
    def alerta_morosos(cantidad_criticos, deuda_total, detalle_morosos):
        return (
            f"🚨 *ALERTA SEMANAL DE MOROSIDAD*\n\n"
            f"⚠️ Afiliados Críticos: {cantidad_criticos}\n"
            f"💸 Deuda Total Sistema: Bs. {deuda_total}\n\n"
            f"📉 *Top Deudores:*\n{detalle_morosos}\n\n"
            f"Se sugiere revisión inmediata.\n"
            f"_Sitema de Administración_"
        )
