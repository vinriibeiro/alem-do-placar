"""Orquestra o assistente: LLM quando disponível, fallback determinístico e limites de uso."""

from __future__ import annotations

import logging
import random
import threading
import time
from collections import deque
from datetime import date

from api.assistant import TEMAS, BaseConsultas
from api.config import Config
from api.llm import AgenteLLM, LLMIndisponivel

log = logging.getLogger("alem_do_placar.servico")


class LimiteTaxa:
    """Janela deslizante de 60 s por IP, em memória (instância única)."""

    def __init__(self, limite: int) -> None:
        self.limite = limite
        self._eventos: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def permitir(self, chave: str, agora: float | None = None) -> bool:
        agora = time.monotonic() if agora is None else agora
        with self._lock:
            fila = self._eventos.setdefault(chave, deque())
            while fila and agora - fila[0] > 60:
                fila.popleft()
            if len(fila) >= self.limite:
                return False
            fila.append(agora)
            if len(self._eventos) > 5000:
                self._eventos = {k: v for k, v in self._eventos.items() if v}
            return True


class ContadorDiario:
    def __init__(self, limite: int) -> None:
        self.limite = limite
        self._dia = date.today()
        self._n = 0
        self._lock = threading.Lock()

    def tentar(self) -> bool:
        with self._lock:
            hoje = date.today()
            if hoje != self._dia:
                self._dia, self._n = hoje, 0
            if self._n >= self.limite:
                return False
            self._n += 1
            return True


class Servico:
    def __init__(self, base: BaseConsultas, config: Config, cliente_llm=None) -> None:
        self.base = base
        self.config = config
        self.agente = AgenteLLM(
            base, cliente=cliente_llm, api_key=config.llm_key, modelo=config.llm_modelo
        )
        self.taxa = LimiteTaxa(config.taxa_por_min)
        self.diario = ContadorDiario(config.llm_diario)

    def sugestoes(self, n: int = 8) -> list[str]:
        todas = [e for t in TEMAS for e in t["exemplos"]]
        return random.sample(todas, min(n, len(todas)))

    def contexto(self) -> dict:
        ctx = self.base.contexto()
        hist = self.base._hist
        if hist is not None:
            # Cada partida gera duas linhas (uma por equipe).
            ctx |= {"partidas": len(hist) // 2, "temporadas": len(ctx["anos"])}
        return ctx | {"temas": TEMAS, "llm_ativo": self.agente.disponivel}

    def perguntar(self, pergunta: str, ano: int | None, equipe: str | None) -> dict:
        aviso = None
        if self.agente.disponivel:
            if self.diario.tentar():
                try:
                    return self.agente.responder(pergunta, ano, equipe)
                except LLMIndisponivel as exc:
                    aviso = f"{exc} Resposta gerada pelo modo determinístico."
                    log.info("fallback_deterministico motivo=llm_indisponivel")
            else:
                aviso = "Limite diário de IA atingido; resposta gerada pelo modo determinístico."
                log.info("fallback_deterministico motivo=limite_diario")
        resposta = self.base.responder(pergunta, ano, equipe)
        resposta["modo"] = "deterministico"
        resposta["consultas_usadas"] = []
        if aviso:
            resposta["limitacoes"] = [aviso, *resposta["limitacoes"]]
        return resposta
