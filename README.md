# FormJA MCP Server

Servidor [Model Context Protocol (MCP)](https://modelcontextprotocol.io) para o [FormJA](https://formja.com.br) — plataforma SaaS de forms conversacionais, CRM e agendamentos.

Permite que clientes LLM (Claude Desktop, Cursor, Windsurf, etc.) interajam com os dados do FormJA: contatos, pipelines, oportunidades, agendamentos e inteligência de leads.

## Ferramentas disponíveis

| #   | Ferramenta                  | Descrição                                                   |
| --- | --------------------------- | ----------------------------------------------------------- |
| 1   | `list_contacts`             | Listar contatos com filtros (nome, email, telefone, página) |
| 2   | `get_contact`               | Detalhes de um contato específico                           |
| 3   | `create_contact`            | Criar um novo contato                                       |
| 4   | `list_pipelines`            | Listar pipelines com estágios                               |
| 5   | `get_pipeline`              | Detalhes de um pipeline (estágios, tipos, cores)            |
| 6   | `list_stage_opportunities`  | Oportunidades em um estágio do pipeline                     |
| 7   | `create_opportunity`        | Criar oportunidade no pipeline                              |
| 8   | `update_opportunity`        | Atualizar título, valor, probabilidade ou mover de estágio  |
| 9   | `list_professionals`        | Listar profissionais disponíveis                            |
| 10  | `get_professional_schedule` | Horários disponíveis de um profissional                     |
| 11  | `list_appointments`         | Listar agendamentos com filtros                             |
| 12  | `create_appointment`        | Criar um novo agendamento                                   |
| 13  | `cancel_appointment`        | Cancelar um agendamento                                     |
| 14  | `reschedule_appointment`    | Remarcar um agendamento                                     |
| 15  | `lead_intelligence`         | Visão omnichannel + funil do pipeline com filtros completos |

## Pré-requisitos

- **API Token** do FormJA — gere em **Painel > Developer > Tokens**
- [Python 3.10+](https://python.org) e [uv](https://docs.astral.sh/uv/) (recomendado) **ou** pip

## Instalação

### Via uv (recomendado)

```bash
uv pip install git+https://github.com/jesaiasmaia/formja-mcp.git
```

### Via pip

```bash
pip install git+https://github.com/jesaiasmaia/formja-mcp.git
```

## Configuração

Variáveis de ambiente:

| Variável          | Obrigatória | Padrão                      | Descrição                               |
| ----------------- | ----------- | --------------------------- | --------------------------------------- |
| `FORMJA_API_KEY`  | Sim         | —                           | API Token do FormJA (prefixo `api_...`) |
| `FORMJA_BASE_URL` | Não         | `https://app.formja.com.br` | URL base da instância FormJA            |

## Uso com Claude Desktop

Adicione ao arquivo de configuração do Claude Desktop:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Opção 1 — Via uvx (sem instalação manual)

```json
{
  "mcpServers": {
    "formja": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jesaiasmaia/formja-mcp.git",
        "formja-mcp"
      ],
      "env": {
        "FORMJA_API_KEY": "api_SEU_TOKEN_AQUI",
        "FORMJA_BASE_URL": "https://app.formja.com.br"
      }
    }
  }
}
```

### Opção 2 — Via uv run (com repositório clonado)

```json
{
  "mcpServers": {
    "formja": {
      "command": "uv",
      "args": ["run", "--directory", "/caminho/para/formja-mcp", "formja-mcp"],
      "env": {
        "FORMJA_API_KEY": "api_SEU_TOKEN_AQUI"
      }
    }
  }
}
```

### Opção 3 — Via Docker (servidor remoto HTTP)

```bash
docker run -d \
  --name formja-mcp \
  -p 8000:8000 \
  -e FORMJA_API_KEY=api_SEU_TOKEN_AQUI \
  -e MCP_TRANSPORT=http \
  ghcr.io/jesaiasmaia/formja-mcp:latest
```

Então configure o cliente para apontar para `http://seu-servidor:8000/mcp`.

## Uso com Cursor

Adicione ao `.cursor/mcp.json` do seu projeto:

```json
{
  "mcpServers": {
    "formja": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jesaiasmaia/formja-mcp.git",
        "formja-mcp"
      ],
      "env": {
        "FORMJA_API_KEY": "api_SEU_TOKEN_AQUI"
      }
    }
  }
}
```

## Desenvolvimento

```bash
# Clonar
git clone https://github.com/jesaiasmaia/formja-mcp.git
cd formja-mcp

# Instalar dependências
uv sync

# Rodar local (stdio)
FORMJA_API_KEY=api_... uv run formja-mcp

# Rodar local (HTTP)
FORMJA_API_KEY=api_... MCP_TRANSPORT=http uv run formja-mcp
```

## Arquitetura

```
formja-mcp/
├── server.py                          # Entry point FastMCP
├── pyproject.toml                     # Dependências (fastmcp, httpx)
└── src/formja_mcp/
    ├── config.py                      # Variáveis de ambiente
    ├── client.py                      # HTTP client + tratamento de erros
    └── tools/
        ├── contacts.py                # Contatos (list, get, create)
        ├── pipeline.py                # Pipelines e oportunidades
        ├── appointments.py            # Agendamentos e profissionais
        └── lead_intelligence.py       # Inteligência de leads
```

O MCP consome as rotas REST existentes em `/api/dashboard/*` do FormJA via API Token — zero endpoints novos no FormJA.

## Segurança

- Autenticação via API Token (SHA256 hash, rate limit 10 req/min)
- Tokens com prefixo `api_` — gere e revogue pelo painel
- Tokens com role `owner` — acesso total aos dados da conta
- Nunca exponha o token em código ou repositórios

## Licença

Proprietário — Jesaias Maia. Todos os direitos reservados.
