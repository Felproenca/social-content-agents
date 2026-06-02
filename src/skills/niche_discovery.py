"""
NicheDiscoverySkill

Responsável por descobrir e construir o perfil de qualquer nicho.
Não tem nichos fixos. Não é partidário.
Serve qualquer mercado com a mesma profundidade.

Princípio: o perfil deve soar como foi escrito por alguém
que viveu dentro do mercado — não por quem pesquisou sobre ele.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from src.core.llm import LLMProvider
from src.core.models import NicheLanguage, NicheProfile

NICHES_DIR = Path("data/niches")

RESEARCH_PROMPT = """
Você é um pesquisador especializado em inteligência de mercado.
Seu trabalho é construir um perfil profundo do nicho: {nicho}

Pesquise e responda cada item com precisão e profundidade.
O perfil deve soar como foi escrito por alguém que viveu
dentro deste mercado por anos — não por um generalista.

Retorne APENAS um JSON válido com esta estrutura exata:

{{
  "nicho": "{nicho}",
  "slug": "{slug}",
  "descricao": "descrição precisa de quem opera neste nicho",
  "audiencia_primaria": "quem contrata / quem é o cliente final",
  "audiencia_secundaria": "público secundário relevante",

  "linguagem": {{
    "usa": [
      "termos técnicos específicos do nicho",
      "palavras que especialistas usam naturalmente",
      "jargão que posiciona como insider",
      "mínimo 8 termos"
    ],
    "evita": [
      "clichês que todos no nicho repetem",
      "promessas genéricas do setor",
      "expressões que soam amador",
      "mínimo 6 termos"
    ],
    "tom": "como fala um especialista sênior deste nicho em uma conversa real",
    "nivel_tecnico": "perfil de quem lê: iniciante / praticante / especialista"
  }},

  "temas_evergreen": [
    "tema que sempre será relevante neste nicho",
    "problema recorrente que nunca é totalmente resolvido",
    "mínimo 5 temas — específicos, não genéricos"
  ],

  "temas_trend": [
    "o que está sendo discutido agora neste nicho",
    "tendência emergente dos últimos 90 dias",
    "mudança no setor que ainda não chegou ao mainstream",
    "mínimo 5 temas — com contexto de por que são relevantes agora"
  ],

  "angulos_inexplorados": [
    "ângulo que existe mas poucos exploram",
    "verdade incômoda do setor que ninguém fala abertamente",
    "perspectiva que vai contra o senso comum do nicho",
    "mínimo 5 ângulos — quanto mais específicos, melhor"
  ],

  "cliches_a_evitar": [
    "frase que todo mundo no nicho usa e ninguém mais lê",
    "promessa batida do setor",
    "mínimo 6 clichês — os mais comuns do nicho"
  ],

  "referencias_setor": [
    "quem são os 3-5 maiores criadores de conteúdo ou líderes de pensamento",
    "incluir por que cada um é referência",
    "podem ser pessoas, publicações, instituições ou estudos"
  ],

  "posicoes_editoriais": [
    "tipo de conteúdo que posiciona como autoridade neste nicho",
    "abordagem que diferencia do conteúdo genérico",
    "mínimo 4 posições editoriais específicas"
  ],

  "gatilhos_emocionais": {{
    "medo": "o maior medo de quem contrata serviço neste nicho",
    "ganancia": "o maior ganho que quem contrata espera",
    "status": "como se sentir ao resolver o problema",
    "curiosidade": "o que as pessoas querem saber mas não perguntam"
  }},

  "formato_por_plataforma": {{
    "instagram": "formato e abordagem que performa neste nicho no Instagram",
    "linkedin": "formato e abordagem para LinkedIn",
    "tiktok": "formato e abordagem para TikTok",
    "youtube": "formato e abordagem para YouTube"
  }}
}}

IMPORTANTE:
- Seja específico. "Gestão de negócios" é genérico. "Como calcular CAC real para e-commerce" é específico.
- Os temas_trend devem refletir o que está acontecendo AGORA — não o que era tendência há 2 anos.
- Os angulos_inexplorados devem ser genuinamente subexplorados — não apenas pouco divulgados.
- O tom deve capturar como especialistas reais deste nicho falam — não como um copywriter descreve o nicho.
"""


class NicheDiscoverySkill:

    def __init__(self, llm: LLMProvider, search_client=None):
        self.llm = llm
        self.search = search_client
        NICHES_DIR.mkdir(parents=True, exist_ok=True)

    async def discover(self, nicho: str) -> NicheProfile:
        """Carrega perfil existente ou descobre novo."""
        slug = self._to_slug(nicho)
        profile_path = NICHES_DIR / f"{slug}.json"

        if profile_path.exists():
            return self._load_profile(profile_path)

        return await self._discover_and_save(nicho, slug, profile_path)

    async def _discover_and_save(
        self, nicho: str, slug: str, path: Path
    ) -> NicheProfile:
        trend_context = ""
        if self.search:
            trend_context = await self._fetch_trend_context(nicho)

        prompt = RESEARCH_PROMPT.format(
            nicho=nicho,
            slug=slug,
            trend_context=trend_context,
        )

        response = await self.llm.generate(
            system="Você é especialista em inteligência de mercado. Retorne apenas JSON válido.",
            user=prompt,
            temperature=0.3,
        )

        profile_data = self._parse_and_validate(response, nicho, slug)
        profile_data["source"] = "descoberto"
        profile_data["updated_at"] = datetime.now().isoformat()
        profile_data["performance_data"] = {}

        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)

        return self._dict_to_profile(profile_data)

    async def update_from_performance(
        self, slug: str, post_data: dict, metrics: dict
    ) -> None:
        """
        Atualiza o perfil do nicho com dados reais de performance.
        O que funcionou vira referência. O que saturou vai para clichês.
        """
        profile_path = NICHES_DIR / f"{slug}.json"
        if not profile_path.exists():
            return

        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        benchmark = self._get_benchmark(profile)
        engagement = metrics.get("engagement_rate", 0)

        if engagement > benchmark * 1.5:
            angulo = post_data.get("angulo", "")
            if angulo and angulo not in profile["temas_trend"]:
                profile["temas_trend"].insert(0, angulo)
            profile.setdefault("performance_data", {}).setdefault("best_angles", []).append({
                "angulo": angulo,
                "hook_type": post_data.get("hook_type"),
                "engagement": engagement,
                "date": datetime.now().isoformat(),
            })
        elif engagement < benchmark * 0.5:
            tema = post_data.get("tema", "")
            if tema:
                label = f"[baixo engajamento] {tema}"
                if label not in profile["cliches_a_evitar"]:
                    profile["cliches_a_evitar"].append(label)

        profile["updated_at"] = datetime.now().isoformat()

        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    # ── helpers ────────────────────────────────────────────────────────────────

    def _to_slug(self, nicho: str) -> str:
        slug = nicho.lower().strip()
        for src, dst in [
            ("[áàãâä]", "a"), ("[éèêë]", "e"), ("[íìîï]", "i"),
            ("[óòõôö]", "o"), ("[úùûü]", "u"), ("[ç]", "c"),
        ]:
            slug = re.sub(src, dst, slug)
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        return slug.strip("-")

    def _load_profile(self, path: Path) -> NicheProfile:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self._dict_to_profile(data)

    def _dict_to_profile(self, data: dict) -> NicheProfile:
        lang = data.get("linguagem", {})
        return NicheProfile(
            nicho=data["nicho"],
            slug=data["slug"],
            descricao=data.get("descricao", ""),
            audiencia_primaria=data.get("audiencia_primaria", ""),
            audiencia_secundaria=data.get("audiencia_secundaria", ""),
            linguagem=NicheLanguage(
                usa=lang.get("usa", []),
                evita=lang.get("evita", []),
                tom=lang.get("tom", ""),
                nivel_tecnico=lang.get("nivel_tecnico", ""),
            ),
            temas_evergreen=data.get("temas_evergreen", []),
            temas_trend=data.get("temas_trend", []),
            angulos_inexplorados=data.get("angulos_inexplorados", []),
            cliches_a_evitar=data.get("cliches_a_evitar", []),
            referencias_setor=data.get("referencias_setor", []),
            posicoes_editoriais=data.get("posicoes_editoriais", []),
            gatilhos_emocionais=data.get("gatilhos_emocionais", {}),
            formato_por_plataforma=data.get("formato_por_plataforma", {}),
            source=data.get("source", "descoberto"),
            updated_at=data.get("updated_at", ""),
            performance_data=data.get("performance_data", {}),
        )

    def _parse_and_validate(self, response: str, nicho: str, slug: str) -> dict:
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            raise ValueError(f"LLM não retornou JSON válido para nicho: {nicho}")
        data = json.loads(match.group())
        data.setdefault("nicho", nicho)
        data.setdefault("slug", slug)
        return data

    def _get_benchmark(self, profile: dict) -> float:
        best = profile.get("performance_data", {}).get("best_angles", [])
        if not best:
            return 0.03
        return sum(b["engagement"] for b in best) / len(best)

    async def _fetch_trend_context(self, nicho: str) -> str:
        try:
            results = await self.search.search(f"tendências {nicho} 2026 Brasil")
            return "\n".join(results[:5])
        except Exception:
            return ""
