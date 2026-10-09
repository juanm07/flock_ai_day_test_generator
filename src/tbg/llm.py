"""Proveedor de LLM opcional para la app (`tbg ui`). El núcleo de tbg NO depende de esto.

Se configura desde la app (pantalla "Configurar IA", se guarda en ~/.tbg/config.json, fuera del repo) o por
variables de entorno, que tienen prioridad (así se configura un deploy, sin que la key pase por la UI):
  TBG_LLM              anthropic | openai | none
  TBG_MODEL            modelo (anthropic: default claude-opus-5-5)
  TBG_EFFORT           low | medium | high | xhigh | max   (solo anthropic; default: medium)
  TBG_OPENAI_BASE_URL  endpoint OpenAI-compatible (Gemini, GLM, OpenRouter, Azure, local…)
  TBG_API_KEY          key del proveedor (o ANTHROPIC_API_KEY / OPENAI_API_KEY)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


class LLMError(RuntimeError):
    pass


# Proveedores sugeridos en la UI. "openai" = cualquier API compatible con OpenAI (base_url + key).
PRESETS = {
    "anthropic": {"label": "Claude (Anthropic)", "provider": "anthropic", "base_url": "", "model": "claude-opus-5-5",
                  "help": "Key en console.anthropic.com"},
    "gemini": {"label": "Gemini (Google)", "provider": "openai",
               "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "",
               "help": "Key gratis en aistudio.google.com; después «Guardar y probar conexión» para elegir el modelo"},
    "glm": {"label": "GLM (Zhipu / Z.ai)", "provider": "openai", "base_url": "https://open.bigmodel.cn/api/paas/v4/",
            "model": "glm-4.6", "help": "Para la región internacional usá el endpoint de api.z.ai"},
    "openai": {"label": "OpenAI", "provider": "openai", "base_url": "", "model": "", "help": "Key en platform.openai.com"},
    "custom": {"label": "Otro (compatible con OpenAI)", "provider": "openai", "base_url": "", "model": "",
               "help": "OpenRouter, Azure OpenAI, Ollama/LM Studio local…"},
}


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    effort: str = "medium"
    base_url: str | None = None
    api_key: str | None = None
    preset: str = ""
    source: str = "ninguna"  # "entorno" | "archivo" | "ninguna"

    @property
    def label(self) -> str:
        if self.provider == "none":
            return "sin IA"
        name = PRESETS.get(self.preset, {}).get("label", self.provider)
        return f"{name} · {self.model}"

    @property
    def masked_key(self) -> str:
        k = self.api_key or ""
        return f"{k[:4]}…{k[-4:]}" if len(k) > 10 else ("configurada" if k else "")


def config_path() -> Path:
    return Path(os.environ.get("TBG_CONFIG", Path.home() / ".tbg" / "config.json"))


def _store() -> dict:
    """{"active": preset, "profiles": {preset: {model, base_url, api_key, effort, models}}}.
    Acepta el formato viejo (un solo proveedor plano) y lo convierte."""
    try:
        data = json.loads(config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"active": "", "profiles": {}}
    if "profiles" not in data:
        preset = data.get("preset") or ("anthropic" if data.get("provider") == "anthropic" else "custom")
        old = {k: data.get(k) for k in ("model", "base_url", "api_key", "effort")}
        data = {"active": preset if data.get("provider") else "", "profiles": {preset: old} if data.get("provider") else {}}
    return data


def _write_store(data: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)  # solo el usuario actual (en Windows el perfil ya es privado)
    except OSError:
        pass


def profile(preset: str) -> dict:
    return dict(_store()["profiles"].get(preset, {}))


def active_preset() -> str:
    return _store().get("active", "")


def save(preset: str, model: str, base_url: str, api_key: str | None, effort: str = "medium",
         activate: bool = True) -> None:
    """Guarda el perfil de un proveedor. api_key=None conserva la key ya guardada DE ESE proveedor."""
    data = _store()
    prof = data["profiles"].setdefault(preset, {})
    prof.update(model=model.strip(), base_url=base_url.strip(), effort=effort)
    if api_key:
        prof["api_key"] = api_key.strip()
    if activate:
        data["active"] = preset
    _write_store(data)


def save_models(preset: str, models: list[str]) -> None:
    data = _store()
    data["profiles"].setdefault(preset, {})["models"] = models
    _write_store(data)


def clear(preset: str | None = None) -> None:
    """Borra un perfil (y su key) o toda la configuración."""
    if preset is None:
        config_path().unlink(missing_ok=True)
        return
    data = _store()
    data["profiles"].pop(preset, None)
    if data.get("active") == preset:
        data["active"] = ""
    _write_store(data)


def profile_config(preset: str) -> LLMConfig:
    """Config de un perfil guardado (esté activo o no); el modelo puede estar vacío."""
    p, prof = PRESETS.get(preset, PRESETS["custom"]), profile(preset)
    return LLMConfig(provider=p["provider"], model=prof.get("model") or "", effort=prof.get("effort") or "medium",
                     base_url=prof.get("base_url") or p["base_url"] or None, api_key=prof.get("api_key") or None,
                     preset=preset, source="archivo")


def config() -> LLMConfig:
    env = os.environ
    if env.get("TBG_LLM") or env.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_AUTH_TOKEN"):
        provider = (env.get("TBG_LLM") or "anthropic").strip().lower()
        if provider == "none":
            return LLMConfig(provider="none", model="", source="entorno")
        model = env.get("TBG_MODEL", "claude-opus-5-5" if provider == "anthropic" else "")
        key = env.get("TBG_API_KEY") or (env.get("ANTHROPIC_API_KEY") if provider == "anthropic" else env.get("OPENAI_API_KEY"))
        cfg = LLMConfig(provider=provider, model=model, effort=env.get("TBG_EFFORT", "medium"),
                        base_url=env.get("TBG_OPENAI_BASE_URL"), api_key=key, source="entorno",
                        preset="anthropic" if provider == "anthropic" else "custom")
    else:
        active = active_preset()
        if not active:
            return LLMConfig(provider="none", model="")
        cfg = profile_config(active)
    if cfg.provider not in ("anthropic", "openai"):
        raise LLMError(f"Proveedor desconocido: {cfg.provider}")
    if not cfg.model:
        raise LLMError("Falta elegir el modelo")
    return cfg


def available() -> bool:
    try:
        return config().provider != "none"
    except LLMError:
        return False


def list_models(cfg: LLMConfig) -> list[str]:
    """Modelos que ofrece el proveedor con esa key (para no adivinar nombres)."""
    if cfg.provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=cfg.api_key) if cfg.api_key else anthropic.Anthropic()
        return sorted(m.id for m in client.models.list())
    from openai import OpenAI
    client = OpenAI(base_url=cfg.base_url or None, api_key=cfg.api_key or None)
    return sorted(m.id.removeprefix("models/") for m in client.models.list())


def complete(system: str, user: str, max_tokens: int = 32000) -> str:
    """Una llamada: devuelve el texto de la respuesta. Lanza LLMError ante rechazo, truncamiento o error."""
    cfg = config()
    if cfg.provider == "anthropic":
        return _anthropic(cfg, system, user, max_tokens)
    if cfg.provider == "openai":
        return _openai(cfg, system, user, max_tokens)
    raise LLMError("No hay IA configurada: configurala en la app («Configurar IA») o usá el modo agente.")


def _anthropic(cfg: LLMConfig, system: str, user: str, max_tokens: int) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=cfg.api_key) if cfg.api_key else anthropic.Anthropic()
    try:
        # Streaming: salidas largas (suite completa) sin timeouts HTTP. `fallbacks: "default"` reintenta del lado
        # del servidor con otro modelo si el clasificador de seguridad rechaza un pedido legítimo.
        with client.beta.messages.stream(
            model=cfg.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": cfg.effort},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            msg = stream.get_final_message()
    except anthropic.AuthenticationError as e:
        raise LLMError("Credenciales de Anthropic inválidas (ANTHROPIC_API_KEY o `ant auth login`).") from e
    except anthropic.RateLimitError as e:
        raise LLMError("Límite de uso de la API alcanzado; probá de nuevo en un rato.") from e
    except anthropic.APIStatusError as e:
        raise LLMError(f"Error de la API de Anthropic ({e.status_code}): {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise LLMError("No se pudo conectar con la API de Anthropic.") from e
    if msg.stop_reason == "refusal":
        raise LLMError("El modelo rechazó el pedido.")
    if msg.stop_reason == "max_tokens":
        raise LLMError("La respuesta se cortó por longitud (max_tokens).")
    return "".join(b.text for b in msg.content if b.type == "text")


def _openai(cfg: LLMConfig, system: str, user: str, max_tokens: int) -> str:
    from openai import OpenAI, OpenAIError

    client = OpenAI(base_url=cfg.base_url or None, api_key=cfg.api_key or None)
    try:
        # El límite de salida varía mucho entre modelos compatibles (algunos rechazan valores altos): por defecto se
        # usa el máximo del proveedor; TBG_MAX_TOKENS lo fija si hace falta.
        limit = os.environ.get("TBG_MAX_TOKENS")
        resp = client.chat.completions.create(
            model=cfg.model, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            **({"max_tokens": int(limit)} if limit else {}),
        )
    except OpenAIError as e:
        raise LLMError(f"Error del proveedor OpenAI-compatible: {e}") from e
    choice = resp.choices[0]
    if choice.finish_reason == "length":
        raise LLMError("La respuesta se cortó por longitud (max_tokens).")
    return choice.message.content or ""
