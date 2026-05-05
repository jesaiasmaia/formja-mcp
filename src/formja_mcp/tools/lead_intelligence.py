from __future__ import annotations

from fastmcp import FastMCP

from formja_mcp.client import FormJAClient, FormJAError, extract_item


def register_lead_intelligence_tools(mcp: FastMCP, client: FormJAClient) -> None:

    @mcp.tool
    async def lead_intelligence(
        start: str | None = None,
        end: str | None = None,
        pipeline_id: str | None = None,
        assigned_to: str | None = None,
        status: str | None = None,
        channel: str | None = None,
    ) -> str:
        """Inteligência de Leads: visão geral omnichannel + funil do pipeline com filtros.

        Retorna:
        - Overview: total de leads por canal (WhatsApp, Instagram, etc.), leads abertos, aguardando resposta
        - Funil do Pipeline: Leads que chegaram (top), oportunidades em andamento (middle), oportunidades ganhas (bottom)

        Filtros disponíveis:
        - start: data inicial (YYYY-MM-DD), padrão últimos 30 dias
        - end: data final (YYYY-MM-DD), padrão hoje
        - pipeline_id: ID do pipeline (use list_pipelines para descobrir). Padrão: pipeline padrão da conta
        - assigned_to: ID do usuário responsável
        - status: status da conversa (open, closed, waiting_response)
        - channel: canal de origem (whatsapp, instagram, email, sms, web_chat)

        Use list_pipelines para descobrir o pipeline_id.
        """
        params: dict = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if pipeline_id:
            params["pipeline"] = pipeline_id
        if assigned_to:
            params["assignedTo"] = assigned_to
        if status:
            params["status"] = status
        if channel:
            params["channel"] = channel

        overview_result = None
        funnel_result = None
        errors = []

        try:
            raw_overview = await client.get(
                "/api/dashboard/lead-intelligence/overview", params=params or None
            )
            overview_result = extract_item(raw_overview)
        except FormJAError as e:
            errors.append(f"Overview: {e.message}")

        try:
            raw_funnel = await client.get(
                "/api/dashboard/lead-intelligence/pipeline-funnel",
                params=params or None,
            )
            funnel_result = extract_item(raw_funnel)
        except FormJAError as e:
            errors.append(f"Funil: {e.message}")

        if errors and not overview_result and not funnel_result:
            return f"Erros ao buscar inteligência de leads:\n" + "\n".join(
                f"- {e}" for e in errors
            )

        lines = ["=== INTELIGÊNCIA DE LEADS ===\n"]

        if overview_result:
            totals = overview_result.get("totals", {})
            lines.append("📊 VISÃO OMNICHANNEL")
            lines.append(
                f"  Total de leads: {totals.get('totalLeads', 0)}\n"
                f"  Canal dominante: {totals.get('dominantLabel', '-')} "
                f"({totals.get('dominantTotal', 0)} leads)\n"
            )

            channels = overview_result.get("channels", [])
            if channels:
                lines.append("  Por canal:")
                for ch in channels:
                    sel = " ◀" if ch.get("selected") else ""
                    lines.append(
                        f"    - {ch.get('label', ch.get('channel', '-'))}: "
                        f"{ch.get('total', 0)} leads | "
                        f"{ch.get('open', 0)} abertos | "
                        f"{ch.get('waitingResponse', 0)} aguardando resposta | "
                        f"{ch.get('percent', 0)}%{sel}"
                    )

        if funnel_result:
            stages = funnel_result.get("stages", {})
            lines.append(
                f"\n🔁 FUNIL DO PIPELINE (ID: {funnel_result.get('pipelineId', '-')})"
            )
            top = stages.get("top", 0)
            middle = stages.get("middle", 0)
            bottom = stages.get("bottom", 0)
            top_pct = (bottom / top * 100) if top > 0 else 0
            mid_pct = (bottom / middle * 100) if middle > 0 else 0

            lines.append(
                f"  1️⃣ {stages.get('firstStageLabel', '1º estágio')}: {top} leads chegaram"
            )
            lines.append(f"  2️⃣ Em andamento: {middle} oportunidades ativas")
            lines.append(f"  3️⃣ Ganho: {bottom} oportunidades convertidas")
            lines.append(f"  📈 Taxa de conversão geral: {top_pct:.1f}%")
            lines.append(f"  📈 Taxa conversão (mid→bottom): {mid_pct:.1f}%")

        if errors:
            lines.append(f"\n⚠️ Avisos:")
            for e in errors:
                lines.append(f"  - {e}")

        return "\n".join(lines)
