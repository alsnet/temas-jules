import streamlit as st
from openai import OpenAI
import os
import re
import logging
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/auto"
DEFAULT_MAX_TOKENS = 500
DEFAULT_TEMPERATURE = 0.7
APP_TITLE = "Essência Espírita - Textos Simples"
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


def generate_text_stream(client: OpenAI, theme: str, model: str, max_tokens: int, temperature: float):
    system_prompt = (
        "Você é um assistente especializado na Doutrina Espírita Kardecista. "
        "Sua tarefa é criar textos resumidos sobre o tema fornecido pelo usuário. "
        "REGRAS IMPORTANTES:\n"
        "1. Baseie-se ÚNICA E EXCLUSIVAMENTE na doutrina espírita kardecista (obras de Allan Kardec).\n"
        "2. Use um vocabulário simples, acessível a todas as idades e níveis de instrução.\n"
        "3. Utilize ortografia e gramática da língua portuguesa atualizadas.\n"
        "4. O texto deve ser resumido e direto ao ponto.\n"
        "5. Não utilize termos complexos sem explicá-los de forma simples.\n"
        "6. Mantenha um tom acolhedor e esclarecedor."
    )
    stream = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": GITHUB_URL,
            "X-OpenRouter-Title": "Essencia Espirita App",
        },
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


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🕊️")

    st.title("🕊️ Essência Espírita")
    st.subheader("Textos resumidos com vocabulário simples e baseados na Doutrina Kardecista")

    st.sidebar.header("Configuração")
    api_key = st.sidebar.text_input(
        "Insira sua OpenRouter API Key",
        type="password",
        value=os.getenv("OPENROUTER_API_KEY", ""),
    )

    if not api_key:
        st.info("Por favor, insira sua OpenRouter API Key na barra lateral para começar.", icon="🔑")
        st.stop()

    client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)

    theme_input = st.text_input(
        "Sobre qual tema você gostaria de ler hoje?",
        placeholder="Ex: Reencarnação, Lei de Causa e Efeito, Prece...",
    )

    if "generating" not in st.session_state:
        st.session_state.generating = False
    if "cache" not in st.session_state:
        st.session_state.cache = {}

    theme, warning = validate_theme(theme_input) if theme_input else ("", None)
    if warning:
        st.warning(warning)

    if st.button("Gerar Texto", disabled=st.session_state.generating):
        if not theme:
            st.warning("Por favor, digite um tema.")
        else:
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
                    full_response = st.write_stream(
                        generate_text_stream(client, theme, DEFAULT_MODEL, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE)
                    )
                    st.session_state.cache[cache_key] = full_response

                safe_name = sanitize_filename(theme) or "texto"
                st.download_button(
                    label="Baixar texto (Arquivo TXT)",
                    data=st.session_state.cache[cache_key],
                    file_name=f"essencia_espirita_{safe_name}.txt",
                    mime="text/plain",
                )

            except Exception as e:
                logger.error(f"Erro ao gerar texto para tema '{theme}': {e}", exc_info=True)
                if "insufficient_quota" in str(e) or "429" in str(e):
                    st.error("Erro: Limite de uso atingido ou falta de créditos no OpenRouter. Verifique sua conta.")
                elif "api_key" in str(e).lower() or "401" in str(e):
                    st.error("Erro: A chave da API do OpenRouter fornecida parece ser inválida.")
                else:
                    st.error("Ocorreu um erro inesperado ao gerar o texto. Tente novamente mais tarde.")
            finally:
                st.session_state.generating = False

    st.markdown("---")
    st.caption("Desenvolvido para estudo e divulgação da Doutrina Espírita Kardecista via OpenRouter.")


if __name__ == "__main__":
    main()
