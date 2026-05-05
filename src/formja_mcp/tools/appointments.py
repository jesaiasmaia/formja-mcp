from __future__ import annotations

from fastmcp import FastMCP

from formja_mcp.client import FormJAClient, FormJAError, extract_list, extract_item


def register_appointment_tools(mcp: FastMCP, client: FormJAClient) -> None:

    @mcp.tool
    async def list_professionals(active_only: bool = True) -> str:
        """Listar profissionais disponíveis para agendamento no FormJA."""
        params: dict = {}
        if active_only:
            params["active"] = "true"

        try:
            result = await client.get("/api/dashboard/calendar/professionals", params)
        except FormJAError as e:
            return f"Erro ao buscar profissionais: {e.message}"

        items, _ = extract_list(result, "professionals")
        if not items:
            return "Nenhum profissional encontrado."

        lines = []
        for p in items:
            lines.append(
                f"- {p.get('name', '-')} | ID: {p['id']} | "
                f"Especialidade: {p.get('specialty') or '-'} | "
                f"Email: {p.get('email') or '-'} | "
                f"Telefone: {p.get('phone') or '-'}"
            )
        return "\n".join(lines)

    @mcp.tool
    async def get_professional_schedule(
        professional_id: str,
        date: str | None = None,
    ) -> str:
        """Obter a disponibilidade/agenda de um profissional.

        Use 'date' (YYYY-MM-DD) para verificar slots em uma data específica.
        Sem data, retorna a configuração semanal de horários.
        """
        params: dict = {"professionalId": professional_id}
        if date:
            params["date"] = date

        try:
            result = await client.get(
                "/api/dashboard/calendar/availability/slots",
                params,
            )
        except FormJAError as e:
            return f"Erro ao buscar agenda: {e.message}"

        items, _ = extract_list(result, "slots")
        if not items:
            return "Nenhum horário disponível encontrado para este profissional."

        days = {
            0: "Dom",
            1: "Seg",
            2: "Ter",
            3: "Qua",
            4: "Qui",
            5: "Sex",
            6: "Sáb",
        }

        lines = []
        for s in items:
            day = days.get(s.get("dayOfWeek", -1), "?")
            is_exception = s.get("isException", False)
            exc_label = " [EXCEÇÃO]" if is_exception else ""
            lines.append(
                f"- {day}: {s.get('startTime', '-')} → {s.get('endTime', '-')}{exc_label}"
            )
        return "\n".join(lines)

    @mcp.tool
    async def list_appointments(
        contact_id: str | None = None,
        professional_id: str | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> str:
        """Listar agendamentos do FormJA. Filtre por contato, profissional, status ou período.

        Status possíveis: scheduled, confirmed, cancelled, completed, no_show.
        Datas no formato YYYY-MM-DD ou ISO 8601.
        """
        params: dict = {"page": page, "limit": limit}
        if contact_id:
            params["respondentId"] = contact_id
        if professional_id:
            params["professionalId"] = professional_id
        if status:
            params["status"] = status
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to

        try:
            result = await client.get("/api/dashboard/calendar/appointments", params)
        except FormJAError as e:
            return f"Erro ao buscar agendamentos: {e.message}"

        items, meta = extract_list(result, "appointments")
        if not items:
            return "Nenhum agendamento encontrado."

        lines = []
        for a in items:
            start = a.get("startTime", "-")
            end = a.get("endTime", "-")
            lines.append(
                f"- {a.get('title', '-')} | ID: {a['id']}\n"
                f"  Início: {start} | Fim: {end}\n"
                f"  Status: {a.get('status', '-')} | "
                f"Profissional ID: {a.get('professionalId', '-')}\n"
                f"  Contato ID: {a.get('respondentId', '-')} | "
                f"Duração: {a.get('durationMinutes', '-')} min"
            )

        total = meta.get("total", len(items))
        header = f"Agendamentos ({total} total, mostrando {len(items)}):\n"
        return header + "\n".join(lines)

    @mcp.tool
    async def create_appointment(
        professional_id: str,
        contact_id: str,
        start_time: str,
        end_time: str,
        title: str,
        description: str | None = None,
        location: str | None = None,
    ) -> str:
        """Criar um novo agendamento no FormJA.

        Datas/horas no formato ISO 8601 (ex: 2025-01-15T10:00:00-03:00).
        Use list_professionals para obter o professional_id.
        Use list_contacts para obter o contact_id.
        """
        payload: dict = {
            "professionalId": professional_id,
            "respondentId": contact_id,
            "startTime": start_time,
            "endTime": end_time,
            "title": title,
        }
        if description:
            payload["description"] = description
        if location:
            payload["location"] = location

        try:
            result = await client.post("/api/dashboard/calendar/appointments", payload)
        except FormJAError as e:
            return f"Erro ao criar agendamento: {e.message}"

        apt = extract_item(result, "appointment")
        return (
            f"Agendamento criado com sucesso!\n"
            f"ID: {apt.get('id', '-')}\n"
            f"Título: {apt.get('title', '-')}\n"
            f"Início: {apt.get('startTime', '-')}\n"
            f"Fim: {apt.get('endTime', '-')}\n"
            f"Status: {apt.get('status', '-')}"
        )

    @mcp.tool
    async def cancel_appointment(
        appointment_id: str,
        reason: str | None = None,
    ) -> str:
        """Cancelar um agendamento existente pelo ID."""
        payload: dict = {"status": "cancelled"}
        if reason:
            payload["notes"] = reason

        try:
            await client.put(
                f"/api/dashboard/calendar/appointments/{appointment_id}",
                payload,
            )
        except FormJAError as e:
            return f"Erro ao cancelar agendamento: {e.message}"

        return f"Agendamento {appointment_id} cancelado com sucesso."

    @mcp.tool
    async def reschedule_appointment(
        appointment_id: str,
        new_start_time: str,
        new_end_time: str,
    ) -> str:
        """Remarcar um agendamento para um novo horário.

        Datas/horas no formato ISO 8601 (ex: 2025-01-15T14:00:00-03:00).
        """
        payload = {
            "startTime": new_start_time,
            "endTime": new_end_time,
        }

        try:
            result = await client.put(
                f"/api/dashboard/calendar/appointments/{appointment_id}",
                payload,
            )
        except FormJAError as e:
            return f"Erro ao remarcar agendamento: {e.message}"

        apt = extract_item(result, "appointment")
        return (
            f"Agendamento remarcado com sucesso!\n"
            f"ID: {apt.get('id', '-')}\n"
            f"Novo início: {apt.get('startTime', '-')}\n"
            f"Novo fim: {apt.get('endTime', '-')}"
        )
