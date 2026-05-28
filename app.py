import streamlit as st
from openai import OpenAI
import os
import re
import time
import logging
from dotenv import load_dotenv, set_key, get_key

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/auto"
DEFAULT_MAX_TOKENS = 500
DEFAULT_TEMPERATURE = 0.7
APP_TITLE = "Temas Espíritas"
GITHUB_URL = "https://github.com/jules-agent/spiritist-app"
MAX_THEME_LENGTH = 200

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sanitize_filename(text: str) -> str:
    text = text.strip().lower().replace(" ", "_")
    return re.sub(r'[\\/*?:"<>|]', "", text)


def validate_theme(theme: str) -> tuple[str, str | None]:
    theme = theme.strip()
    if not theme:
        return "", "Por favor, digite um tema."
    if len(theme) > MAX_THEME_LENGTH:
        return theme[:MAX_THEME_LENGTH], f"O tema foi truncado para {MAX_THEME_LENGTH} caracteres."
    return theme, None


def build_system_prompt() -> str:
    return (
        "Você é um assistente especializado na Doutrina Espírita Kardecista. "
        "Sua tarefa é criar textos resumidos sobre o tema fornecido pelo usuário. "
        "REGRAS IMPORTANTES:\n"
        "1. Baseie-se ÚNICA E EXCLUSIVAMENTE na doutrina espírita kardecista (obras de Allan Kardec).\n"
        "2. Use um vocabulário simples, acessível a todas as idades e níveis de instrução.\n"
        "3. Utilize ortografia e gramática da língua portuguesa atualizadas.\n"
        "4. O texto deve ser resumido e direto ao ponto.\n"
        "5. Não utilize termos complexos sem explicá-los de forma simples.\n"
        "6. Mantenha um tom acolhedor e esclarecedor.\n"
        "7. Escreva o texto EM PRIMEIRA PESSOA, como se você mesmo estivesse explicando o conceito."
    )


def build_provider_routing(strategy: str, allow_fallbacks: bool) -> dict | None:
    sort_map = {
        "Menor preço": "price",
        "Maior throughput": "throughput",
        "Menor latência": "latency",
    }
    sort_val = sort_map.get(strategy)
    if not sort_val:
        return None
    result: dict = {"sort": sort_val}
    if not allow_fallbacks:
        result["allow_fallbacks"] = False
    return result


def generate_text_stream(client: OpenAI, theme: str, model: str, max_tokens: int, temperature: float, provider_routing: dict | None = None):
    system_prompt = build_system_prompt()
    extra_body = {"provider": provider_routing} if provider_routing else None
    stream = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": GITHUB_URL,
            "X-OpenRouter-Title": "Temas Espiritas App",
        },
        extra_body=extra_body,
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Escreva um texto resumido sobre: {theme}"}
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def map_api_error(e: Exception) -> str:
    if "insufficient_quota" in str(e) or "429" in str(e):
        return "Erro: Limite de uso atingido ou falta de créditos no OpenRouter. Verifique sua conta."
    if "api_key" in str(e).lower() or "401" in str(e):
        return "Erro: A chave da API do OpenRouter fornecida parece ser inválida."
    return "Ocorreu um erro inesperado ao gerar o texto. Tente novamente mais tarde."


def render_settings() -> dict:
    with st.popover("⚙️ Configurações", use_container_width=True):
        st.markdown("##### Modelo")
        model = st.selectbox(
            "Modelo de IA",
            options=[
                "openrouter/auto",
                "openai/gpt-4o-mini",
                "openai/gpt-4o",
                "anthropic/claude-sonnet",
                "google/gemini-flash",
            ],
            index=0,
            label_visibility="collapsed",
            help="Modelo de IA usado para gerar o texto.",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            temperature = st.slider(
                "Temperatura", 0.0, 2.0, DEFAULT_TEMPERATURE, 0.1,
                help="Valores mais altos geram textos mais criativos.",
            )
        with col_b:
            max_tokens = st.slider(
                "Máximo de tokens", 100, 2000, DEFAULT_MAX_TOKENS, 50,
                help="Controla o tamanho máximo do texto gerado.",
            )

        st.markdown("##### API")
        if "api_key" not in st.session_state:
            st.session_state.api_key = os.getenv("OPENROUTER_API_KEY", "")

        api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            value=st.session_state.api_key,
            help="Sua chave de API do OpenRouter persistida entre sessões.",
        )
        st.session_state.api_key = api_key

        with st.expander("Avançado"):
            base_url = st.text_input(
                "URL da API",
                value=os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
                help="URL base para APIs compatíveis com OpenAI.",
            )

            st.markdown("##### Roteamento OpenRouter")
            routing_strategy = st.selectbox(
                "Estratégia",
                options=[
                    "Padrão (balanceamento por preço)",
                    "Menor preço",
                    "Maior throughput",
                    "Menor latência",
                ],
                index=0,
                help="Como o OpenRouter seleciona o provedor para sua requisição.",
            )

            allow_fallbacks = st.checkbox(
                "Permite fallbacks",
                value=True,
                help="Se desativado, usa apenas o melhor provedor sem tentar alternativas.",
            )

    return {
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "base_url": base_url,
        "routing_strategy": routing_strategy,
        "allow_fallbacks": allow_fallbacks,
    }


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🕊️")

    st.title("🕊️ Temas Espíritas")
    st.subheader("Gerador de textos resumidos com vocabulário simples, baseados na Doutrina Kardecista")

    config = render_settings()

    saved_key = os.getenv("OPENROUTER_API_KEY", "")
    if config["api_key"] and config["api_key"] != saved_key:
        set_key(".env", "OPENROUTER_API_KEY", config["api_key"])
        os.environ["OPENROUTER_API_KEY"] = config["api_key"]

    if not config["api_key"]:
        st.info("🔑 Abra as **Configurações** acima e insira sua chave do OpenRouter para começar.")
        st.stop()

    client = OpenAI(base_url=config["base_url"], api_key=config["api_key"])

    theme_input = st.text_input(
        "Tema",
        placeholder="Ex: Reencarnação, Lei de Causa e Efeito, Prece...",
        label_visibility="collapsed",
    )

    if "generating" not in st.session_state:
        st.session_state.generating = False
    if "cache" not in st.session_state:
        st.session_state.cache = {}

    theme, warning = validate_theme(theme_input) if theme_input else ("", None)
    if warning:
        st.warning(warning)

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        clicked = st.button("Gerar Texto", disabled=st.session_state.generating or not theme, use_container_width=True)

    if clicked:
        st.session_state.generating = True
        try:
            cache_key = theme.lower().strip()
            if cache_key in st.session_state.cache:
                st.markdown("---")
                st.markdown(f"### {theme}")
                st.write(st.session_state.cache[cache_key])
                st.info("📋 Resultado do cache (mesmo tema consultado anteriormente nesta sessão).")
            else:
                st.markdown("---")
                st.markdown(f"### {theme}")

                start_time = time.time()
                placeholder = st.empty()
                full_response = ""
                tokens_used = None

                provider_routing = build_provider_routing(config["routing_strategy"], config["allow_fallbacks"])
                extra_body = {"provider": provider_routing} if provider_routing else None

                stream = client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": GITHUB_URL,
                        "X-OpenRouter-Title": "Temas Espiritas App",
                    },
                    extra_body=extra_body,
                    model=config["model"],
                    messages=[
                        {"role": "system", "content": build_system_prompt()},
                        {"role": "user", "content": f"Escreva um texto resumido sobre: {theme}"}
                    ],
                    max_tokens=config["max_tokens"],
                    temperature=config["temperature"],
                    stream=True,
                    stream_options={"include_usage": True},
                )

                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        placeholder.markdown(full_response + "▌")
                    if hasattr(chunk, "usage") and chunk.usage:
                        tokens_used = chunk.usage

                placeholder.markdown(full_response)
                st.session_state.cache[cache_key] = full_response

                elapsed = time.time() - start_time
                parts = [f"⏱️ Gerado em {elapsed:.1f}s"]
                if tokens_used:
                    parts.append(f"Tokens: {tokens_used.total_tokens}")
                st.caption(" | ".join(parts))

            safe_name = sanitize_filename(theme) or "texto"
            st.download_button(
                label="Baixar texto (Arquivo TXT)",
                data=st.session_state.cache[cache_key],
                file_name=f"temas_espiritas_{safe_name}.txt",
                mime="text/plain",
            )

        except Exception as e:
            logger.error(f"Erro ao gerar texto para tema '{theme}': {e}", exc_info=True)
            st.error(map_api_error(e))
        finally:
            st.session_state.generating = False

    st.markdown("---")
    st.caption("Desenvolvido para estudo e divulgação da Doutrina Espírita Kardecista via OpenRouter.")


if __name__ == "__main__":
    main()
