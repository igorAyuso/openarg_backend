"""Connector: BCRA (Banco Central de la República Argentina).

Supports exchange-rate endpoints AND the Central de Deudores API
(credit status, 24-month history, rejected checks) — all public and
free, no authentication required.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.domain.entities.connectors.data_result import DataResult, PlanStep

if TYPE_CHECKING:
    from app.infrastructure.adapters.connectors.bcra_adapter import BCRAAdapter

logger = logging.getLogger(__name__)


async def execute_bcra_step(
    step: PlanStep,
    bcra: BCRAAdapter | None,
) -> list[DataResult]:
    if not bcra:
        logger.warning("BCRAAdapter not configured, skipping step %s", step.id)
        return []
    params = step.params
    tipo = params.get("tipo", "cotizaciones")
    try:
        # ── Exchange-rate / monetary-variable endpoints ──────────
        if tipo == "cotizaciones":
            result = await bcra.get_cotizaciones(
                moneda=params.get("moneda", "USD"),
                fecha_desde=params.get("fecha_desde"),
                fecha_hasta=params.get("fecha_hasta"),
            )
        elif tipo == "variables":
            result = await bcra.get_principales_variables()
        elif tipo == "historica":
            id_variable = params.get("id_variable")
            if not id_variable:
                result = await bcra.get_principales_variables()
            else:
                result = await bcra.get_variable_historica(
                    id_variable=int(id_variable),
                    fecha_desde=params.get("fecha_desde", "2024-01-01"),
                    fecha_hasta=params.get("fecha_hasta", datetime.now(UTC).strftime("%Y-%m-%d")),
                )

        # ── Central de Deudores endpoints ────────────────────────
        elif tipo == "deudas":
            identificacion = params.get("identificacion", "")
            result = await bcra.get_deudas(identificacion)
        elif tipo == "deudas_historicas":
            identificacion = params.get("identificacion", "")
            result = await bcra.get_deudas_historicas(identificacion)
        elif tipo == "cheques_rechazados":
            identificacion = params.get("identificacion", "")
            result = await bcra.get_cheques_rechazados(identificacion)

        else:
            result = await bcra.get_cotizaciones()
        return [result] if result else []
    except Exception:
        logger.warning("BCRA step %s failed", step.id, exc_info=True)
        return []
