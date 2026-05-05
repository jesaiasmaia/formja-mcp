from __future__ import annotations

from fastmcp import FastMCP

from formja_mcp.client import FormJAClient, FormJAError, extract_list, extract_item


def register_contact_tools(mcp: FastMCP, client: FormJAClient) -> None:

    @mcp.tool
    async def list_contacts(
        search: str | None = None,
        status: str | None = None,
        pipeline_stage_id: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> str:
        """Listar contatos/leads do FormJA. Use 'search' para buscar por nome, email ou telefone."""
        params: dict = {"page": page, "limit": limit}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        if pipeline_stage_id:
            params["pipelineStageId"] = pipeline_stage_id

        try:
            result = await client.get("/api/dashboard/respondents", params)
        except FormJAError as e:
            return f"Erro ao buscar contatos: {e.message}"

        items, meta = extract_list(result, "respondents")
        if not items:
            return "Nenhum contato encontrado."

        lines = []
        for c in items:
            lines.append(
                f"- {c.get('name') or 'Sem nome'} | ID: {c['id']} | "
                f"Email: {c.get('email') or '-'} | "
                f"Tel: {c.get('phone') or '-'} | "
                f"Status: {c.get('status', '-')}"
            )
        total = meta.get("total", len(items))
        header = f"Contatos ({total} total, mostrando {len(items)}):\n"
        return header + "\n".join(lines)

    @mcp.tool
    async def get_contact(contact_id: str) -> str:
        """Obter detalhes completos de um contato específico do FormJA pelo ID."""
        try:
            result = await client.get(f"/api/dashboard/respondents/{contact_id}")
        except FormJAError as e:
            return f"Erro ao buscar contato: {e.message}"

        c = extract_item(result)
        if not c or not c.get("id"):
            return "Contato não encontrado."

        address = c.get("address") or {}
        addr_str = ""
        if address:
            parts = [
                address.get("street", ""),
                address.get("number", ""),
                address.get("neighborhood", ""),
                address.get("city", ""),
                address.get("state", ""),
            ]
            addr_str = ", ".join(p for p in parts if p)

        return (
            f"Nome: {c.get('name') or '-'}\n"
            f"Email: {c.get('email') or '-'}\n"
            f"Telefone: {c.get('phone') or '-'}\n"
            f"CPF/CNPJ: {c.get('taxId') or '-'}\n"
            f"Tipo: {c.get('personType') or '-'}\n"
            f"Status: {c.get('status', '-')}\n"
            f"Pipeline Stage ID: {c.get('pipelineStageId') or '-'}\n"
            f"Endereço: {addr_str or '-'}\n"
            f"Criado em: {c.get('createdAt', '-')}\n"
            f"Atualizado em: {c.get('updatedAt', '-')}\n"
            f"Última interação: {c.get('lastInteractionAt') or '-'}\n"
            f"Total de submissões: {c.get('totalSubmissions', '-')}"
        )

    @mcp.tool
    async def create_contact(
        name: str,
        phone: str | None = None,
        email: str | None = None,
        tax_id: str | None = None,
    ) -> str:
        """Criar um novo contato/lead no FormJA.

        Use para cadastrar leads antes de criar oportunidades ou agendamentos.
        Phone deve incluir código do país (ex: 5511999640874).
        """
        payload: dict = {"name": name}
        if phone:
            payload["phone"] = phone
        if email:
            payload["email"] = email
        if tax_id:
            payload["taxId"] = tax_id

        try:
            result = await client.post("/api/dashboard/respondents", payload)
        except FormJAError as e:
            return f"Erro ao criar contato: {e.message}"

        c = extract_item(result)
        return (
            f"Contato criado com sucesso!\n"
            f"ID: {c.get('id', '-')}\n"
            f"Nome: {c.get('name', '-')}\n"
            f"Email: {c.get('email') or '-'}\n"
            f"Telefone: {c.get('phone') or '-'}\n"
            f"Status: {c.get('status', '-')}"
        )
