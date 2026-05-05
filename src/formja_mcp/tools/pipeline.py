from __future__ import annotations

from fastmcp import FastMCP

from formja_mcp.client import FormJAClient, FormJAError, extract_list, extract_item


def register_pipeline_tools(mcp: FastMCP, client: FormJAClient) -> None:

    @mcp.tool
    async def list_pipelines() -> str:
        """Listar todos os pipelines (funis de vendas) do FormJA com seus estágios."""
        try:
            result = await client.get("/api/dashboard/pipelines")
        except FormJAError as e:
            return f"Erro ao buscar pipelines: {e.message}"

        items, _ = extract_list(result, "pipelines")
        if not items:
            return "Nenhum pipeline encontrado."

        lines = []
        for p in items:
            pid = p.get("id", "")
            active = p.get("activeOpportunitiesCount", 0)
            total = p.get("totalOpportunitiesCount", 0)
            try:
                detail = await client.get(f"/api/dashboard/pipelines/{pid}")
                pipeline = extract_item(detail, "pipeline")
                stages = pipeline.get("stages", []) if pipeline else []
            except FormJAError:
                stages = []

            stage_names = " → ".join(s.get("name", "?") for s in stages)
            lines.append(
                f"- {p.get('name', '-')} | ID: {pid}\n"
                f"  Estágios: [{stage_names}]\n"
                f"  Oportunidades: {active} ativas / {total} total"
            )
        return "\n".join(lines)

    @mcp.tool
    async def get_pipeline(pipeline_id: str) -> str:
        """Detalhes de um pipeline específico com seus estágios e estatísticas."""
        try:
            result = await client.get(f"/api/dashboard/pipelines/{pipeline_id}")
        except FormJAError as e:
            return f"Erro ao buscar pipeline: {e.message}"

        p = extract_item(result, "pipeline")
        if not p:
            return "Pipeline não encontrado."

        stages = p.get("stages", [])
        stage_lines = []
        for s in stages:
            stage_lines.append(
                f"  {s.get('position', '?')}. {s.get('name', '-')} "
                f"(ID: {s['id']}) | Tipo: {s.get('stageType', '-')} | "
                f"Cor: {s.get('color', '-')}"
            )

        return (
            f"Pipeline: {p.get('name', '-')}\n"
            f"Descrição: {p.get('description') or '-'}\n"
            f"Ícone: {p.get('icon') or '-'} | Cor: {p.get('color') or '-'}\n"
            f"Padrão: {'Sim' if p.get('isDefault') else 'Não'}\n"
            f"Estágios:\n" + "\n".join(stage_lines)
        )

    @mcp.tool
    async def list_stage_opportunities(
        pipeline_id: str,
        stage_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> str:
        """Listar oportunidades em um estágio específico do pipeline.

        Use list_pipelines ou get_pipeline para obter pipeline_id e stage_id.
        """
        try:
            result = await client.get(
                "/api/dashboard/pipeline/opportunities",
                {
                    "pipelineId": pipeline_id,
                    "pipelineStageId": stage_id,
                    "page": page,
                    "limit": limit,
                },
            )
        except FormJAError as e:
            return f"Erro ao buscar oportunidades: {e.message}"

        items, meta = extract_list(result, "opportunities")
        if not items:
            return "Nenhuma oportunidade encontrada neste estágio."

        lines = []
        for o in items:
            respondent = o.get("respondent") or {}
            assigned = o.get("assignedUserName") or "-"
            value = o.get("value")
            value_str = f"R$ {value:,.2f}" if value else "-"
            prob = o.get("probability")
            prob_str = f"{prob}%" if prob is not None else "-"

            lines.append(
                f"- {o.get('title', '-')} | ID: {o['id']}\n"
                f"  Valor: {value_str} | Prob: {prob_str} | Responsável: {assigned}\n"
                f"  Contato: {respondent.get('name') or '-'} (ID: {o.get('respondentId', '-')})"
            )

        total = meta.get("total", len(items))
        header = f"Oportunidades ({total} total, mostrando {len(items)}):\n"
        return header + "\n".join(lines)

    @mcp.tool
    async def create_opportunity(
        pipeline_id: str,
        stage_id: str,
        contact_id: str,
        title: str,
        value: float | None = None,
        description: str | None = None,
        probability: int | None = None,
    ) -> str:
        """Criar uma nova oportunidade no pipeline para um contato existente.

        Use list_pipelines / get_pipeline para descobrir IDs de pipeline e estágio.
        Use list_contacts ou create_contact para obter o contact_id.
        """
        payload: dict = {
            "pipelineId": pipeline_id,
            "pipelineStageId": stage_id,
            "respondentId": contact_id,
            "title": title,
        }
        if value is not None:
            payload["value"] = value
        if description:
            payload["description"] = description
        if probability is not None:
            payload["probability"] = probability

        try:
            result = await client.post("/api/dashboard/pipeline/opportunities", payload)
        except FormJAError as e:
            return f"Erro ao criar oportunidade: {e.message}"

        opp = extract_item(result, "opportunity")
        return (
            f"Oportunidade criada com sucesso!\n"
            f"ID: {opp.get('id', '-')}\n"
            f"Título: {opp.get('title', '-')}\n"
            f"Valor: R$ {opp.get('value', 0):,.2f}\n"
            f"Pipeline: {opp.get('pipelineId', '-')}\n"
            f"Estágio: {opp.get('pipelineStageId', '-')}"
        )

    @mcp.tool
    async def update_opportunity(
        opportunity_id: str,
        title: str | None = None,
        value: float | None = None,
        description: str | None = None,
        probability: int | None = None,
        stage_id: str | None = None,
    ) -> str:
        """Atualizar uma oportunidade existente. Permite alterar título, valor, descrição, probabilidade ou mover de estágio.

        Use list_stage_opportunities para encontrar o opportunity_id.
        Use get_pipeline para encontrar o stage_id de destino (para mover de estágio).
        """
        payload: dict = {}
        if title is not None:
            payload["title"] = title
        if value is not None:
            payload["value"] = value
        if description is not None:
            payload["description"] = description
        if probability is not None:
            payload["probability"] = probability
        if stage_id is not None:
            payload["pipelineStageId"] = stage_id

        if not payload:
            return "Nenhum campo para atualizar. Forneça ao menos um: title, value, description, probability, stage_id."

        try:
            result = await client.put(
                f"/api/dashboard/pipeline/opportunities/{opportunity_id}",
                payload,
            )
        except FormJAError as e:
            return f"Erro ao atualizar oportunidade: {e.message}"

        opp = extract_item(result, "opportunity")
        return (
            f"Oportunidade atualizada com sucesso!\n"
            f"ID: {opp.get('id', '-')}\n"
            f"Título: {opp.get('title', '-')}\n"
            f"Valor: R$ {opp.get('value', 0):,.2f}\n"
            f"Probabilidade: {opp.get('probability', '-')}%\n"
            f"Estágio: {opp.get('pipelineStageId', '-')}"
        )
