import os

from fastmcp import FastMCP

from formja_mcp.client import FormJAClient
from formja_mcp.config import validate_config
from formja_mcp.tools.contacts import register_contact_tools
from formja_mcp.tools.pipeline import register_pipeline_tools
from formja_mcp.tools.appointments import register_appointment_tools
from formja_mcp.tools.lead_intelligence import register_lead_intelligence_tools


def main():
    validate_config()

    mcp = FastMCP(
        "FormJA",
        instructions=(
            "FormJA CRM MCP Server. Gerencia contatos/leads, pipelines (funis de vendas), "
            "oportunidades, agendamentos e inteligencia de leads.\n\n"
            "Fluxo tipico:\n"
            "1. Use lead_intelligence para ter uma visao geral dos leads com filtros de data, canal, pipeline\n"
            "2. Use list_contacts para encontrar contatos especificos\n"
            "3. Use list_pipelines / get_pipeline para ver estagios disponiveis\n"
            "4. Use list_professionals / get_professional_schedule para verificar disponibilidade\n"
            "5. Use create_opportunity ou create_appointment para criar registros\n\n"
            "Sempre que precisar de um ID, use as ferramentas de listagem primeiro."
        ),
    )

    client = FormJAClient()

    register_contact_tools(mcp, client)
    register_pipeline_tools(mcp, client)
    register_appointment_tools(mcp, client)
    register_lead_intelligence_tools(mcp, client)

    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))
        mcp.run(transport=transport, host=host, port=port)
