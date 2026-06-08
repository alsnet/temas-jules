import streamlit as st
from openai import OpenAI
import os
import re
import time
import logging
from dotenv import load_dotenv, set_key

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/free"
DEFAULT_MAX_TOKENS = 2000
DEFAULT_TEMPERATURE = 0.7
APP_TITLE = "Estudos Doutrinários"
GITHUB_URL = "https://github.com/jules-agent/spiritist-app"
MAX_THEME_LENGTH = 200

FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-120b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-31b-it:free",
    "qwen/qwen3-coder:free",
    "z-ai/glm-4.5-air:free",
    "moonshotai/kimi-k2.6:free",
    "poolside/laguna-m.1:free",
    "poolside/laguna-xs.2:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "google/gemma-4-26b-a4b-it:free",
]

DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

SAFETY_FILTER_PATTERNS = [
    "user safety",
    "safety filter",
    "i cannot",
    "i can't",
    "i'm not able",
    "i am not able",
    "not appropriate",
    "cannot assist",
    "can't assist",
    "not comfortable",
    "against my guidelines",
    "content policy",
    "harmful",
    "unsafe",
    "sensitive topic",
]

FALLBACK_MODELS = [
    "openai/gpt-oss-120b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-31b-it:free",
    "qwen/qwen3-coder:free",
]

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


def build_questionnaire_prompt(book: str, author: str, chapters: str) -> str:
    return (
        f"Você é um assistente especializado na Doutrina Espírita Kardecista. "
        f"O usuário está estudando o livro '{book}' de {author}, capítulos: {chapters}. "
        f"REGRAS IMPORTANTES:\n"
        f"1. Responda APENAS com base no conteúdo do livro '{book}' de {author}.\n"
        f"2. Cite sempre a referência exata do trecho ou capítulo quando possível.\n"
        f"3. Escreva EM PRIMEIRA PESSOA, como se você estivesse explicando o conteúdo do livro.\n"
        f"4. Seja claro, didático e objetivo.\n"
        f"5. Inclua a explicação do contexto doutrinário quando relevante.\n"
        f"6. Use vocabulário simples e acessível.\n"
        f"7. Mantenha um tom acolhedor e esclarecedor."
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


def is_safety_filter_response(text: str) -> bool:
    if not text or len(text.strip()) < 20:
        return True
    text_lower = text.lower()
    for pattern in SAFETY_FILTER_PATTERNS:
        if pattern in text_lower:
            return True
    if text_lower.strip() in ["safe", "unsafe", "rejected", "blocked"]:
        return True
    return False


def generate_with_retry(client, system_prompt, user_message, model, max_tokens, temperature):
    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]

    for attempt, current_model in enumerate(models_to_try):
        try:
            stream = client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content

            if not is_safety_filter_response(full_response):
                return full_response, current_model

            logger.warning(f"Modelo {current_model} retornou filtro de segurança. Tentando próximo...")

        except Exception as e:
            logger.error(f"Erro no modelo {current_model}: {e}")
            continue

    return None, model


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
    error_str = str(e).lower()
    if "insufficient_quota" in error_str or "429" in error_str:
        return "Erro: Limite de uso atingido ou falta de créditos no OpenRouter. Verifique sua conta."
    if "api_key" in error_str or "401" in error_str:
        return "Erro: A chave da API do OpenRouter fornecida parece ser inválida."
    if "model" in error_str and ("not found" in error_str or "unavailable" in error_str):
        return "Erro: O modelo selecionado não está disponível. Tente outro modelo gratuito."
    if "timeout" in error_str or "timed out" in error_str:
        return "Erro: A requisição expirou. Tente novamente mais tarde."
    if "connection" in error_str or "connect" in error_str:
        return "Erro: Não foi possível conectar ao OpenRouter. Verifique sua conexão."
    logger.error(f"Erro não mapeado: {e}", exc_info=True)
    return f"Erro: {str(e)[:200]}"


def render_settings_page() -> dict:
    st.title("⚙️ Configurações")

    st.markdown("##### Modelo")
    model = st.selectbox(
        "Modelo de IA",
        options=FREE_MODELS,
        index=0,
        label_visibility="collapsed",
        help="Modelo gratuito do OpenRouter usado para gerar o texto.",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        temperature = st.slider(
            "Temperatura", 0.0, 2.0, DEFAULT_TEMPERATURE, 0.1,
            help="Valores mais altos geram textos mais criativos.",
        )
    with col_b:
        max_tokens = st.slider(
            "Máximo de tokens", 100, 4000, DEFAULT_MAX_TOKENS, 100,
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

    # Botão de salvar
    if st.button("Salvar Configurações", use_container_width=True, type="primary"):
        new_config = {
            "api_key": api_key,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "base_url": base_url,
            "routing_strategy": routing_strategy,
            "allow_fallbacks": allow_fallbacks,
        }
        st.session_state.config = new_config

        # Salvar API key no .env
        saved_key = os.getenv("OPENROUTER_API_KEY", "")
        if api_key and api_key != saved_key:
            set_key(".env", "OPENROUTER_API_KEY", api_key)
            os.environ["OPENROUTER_API_KEY"] = api_key

        st.success("✅ Configurações salvas com sucesso!")
        st.balloons()

    # Mostrar configurações atuais
    st.markdown("---")
    st.markdown("##### Configurações Atuais")
    current = st.session_state.get("config", {})
    if current:
        st.json({
            "Modelo": current.get("model", "N/A"),
            "Temperatura": current.get("temperature", "N/A"),
            "Max Tokens": current.get("max_tokens", "N/A"),
            "API Key": "***" + current.get("api_key", "")[-4:] if current.get("api_key") else "Não configurada",
        })

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

    st.markdown("""
        <style>
        [data-testid="InputInstructions"] {
            font-size: 0 !important;
            line-height: 0 !important;
        }
        [data-testid="InputInstructions"]::after {
            content: "Pressione Enter para aplicar";
            font-size: 12px !important;
            line-height: normal !important;
            color: rgb(128, 128, 128);
        }
        </style>
    """, unsafe_allow_html=True)

    # Criando o menu lateral
    st.sidebar.title("Navegação")
    
    # Menu com quatro opções
    menu_option = st.sidebar.radio(
        "Escolha uma opção:",
        ["Temas", "Questionário", "Estudo Literal", "Configurações"]
    )

    # Página de Configurações
    if menu_option == "Configurações":
        config = render_settings_page()
        return

    # Para as outras páginas, usar configurações salvas ou defaults
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.getenv("OPENROUTER_API_KEY", "")
    if "config" not in st.session_state:
        st.session_state.config = {
            "api_key": st.session_state.api_key,
            "model": DEFAULT_MODEL,
            "temperature": DEFAULT_TEMPERATURE,
            "max_tokens": DEFAULT_MAX_TOKENS,
            "base_url": OPENROUTER_BASE_URL,
            "routing_strategy": "Padrão (balanceamento por preço)",
            "allow_fallbacks": True,
        }
    config = st.session_state.config

    saved_key = os.getenv("OPENROUTER_API_KEY", "")
    if config["api_key"] and config["api_key"] != saved_key:
        set_key(".env", "OPENROUTER_API_KEY", config["api_key"])
        os.environ["OPENROUTER_API_KEY"] = config["api_key"]

    if not config["api_key"]:
        st.info("🔑 Acesse **Configurações** no menu lateral para inserir sua chave do OpenRouter. Apenas modelos gratuitos são utilizados.")
        st.stop()

    client = OpenAI(base_url=config["base_url"], api_key=config["api_key"])

    # Página Temas
    if menu_option == "Temas":
        st.title("🕊️ Estudos Doutrinários")
        st.subheader("Geramos explicações de textos para ter auxiliar em estudos e reflexões")
        
        theme_input = st.text_input(
            "Digite o tema espiritual desejado",
            placeholder="Ex: Reencarnação, Lei de Causa e Efeito, Prece...",
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

                    system_prompt = build_system_prompt()
                    user_message = f"Escreva um texto resumido sobre: {theme}"
                    full_response, used_model = generate_with_retry(
                        client, system_prompt, user_message,
                        config["model"], config["max_tokens"], config["temperature"]
                    )

                    if full_response:
                        placeholder.markdown(full_response)
                        st.session_state.cache[cache_key] = full_response
                        elapsed = time.time() - start_time
                        st.caption(f"⏱️ Gerado em {elapsed:.1f}s | Modelo: {used_model}")
                    else:
                        placeholder.error("❌ Não foi possível gerar o texto. Todos os modelos retornaram filtro de segurança.")

                safe_name = sanitize_filename(theme) or "texto"
                st.download_button(
                    label="Baixar texto (Arquivo TXT)",
                    data=st.session_state.cache[cache_key],
                    file_name=f"estudos_doutrinarios_{safe_name}.txt",
                    mime="text/plain",
                )

            except Exception as e:
                logger.error(f"Erro ao gerar texto para tema '{theme}': {e}", exc_info=True)
                st.error(map_api_error(e))
            finally:
                st.session_state.generating = False

        st.markdown("---")
        st.caption("Desenvolvido para estudo e divulgação da Doutrina Espírita Kardecista via OpenRouter.")
        
    elif menu_option == "Questionário":
        st.title("🕊️ Estudos Doutrinários")
        st.subheader("Questionário para auxiliar no estudo")

        # Se já tem respostas prontas, exibir
        if "quiz_results" in st.session_state and st.session_state.quiz_results:
            for i, result in enumerate(st.session_state.quiz_results):
                if i > 0:
                    st.markdown("---")
                st.markdown(f"**Pergunta {i + 1}:** {result['question']}")
                st.markdown(result["answer"])
                st.caption(f"⏱️ Gerado em {result['elapsed']:.1f}s")

            st.markdown("---")
            st.success(f"✅ {len(st.session_state.quiz_results)} pergunta(s) respondida(s) com sucesso!")

            if st.button("Nova Consulta", use_container_width=True):
                st.session_state.quiz_results = []
                st.session_state.quiz_book = ""
                st.session_state.quiz_author = ""
                st.session_state.quiz_chapters = ""
                st.session_state.quiz_questions = []
                st.rerun()

        # Se está processando, executar as chamadas API
        elif st.session_state.get("quiz_processing"):
            system_prompt = build_questionnaire_prompt(
                st.session_state.quiz_book, st.session_state.quiz_author, st.session_state.quiz_chapters
            )

            results = []
            for i, question in enumerate(st.session_state.quiz_questions):
                st.markdown("---")
                st.markdown(f"**Pergunta {i + 1}:** {question}")

                start_time = time.time()
                placeholder = st.empty()

                full_response, used_model = generate_with_retry(
                    client, system_prompt, question,
                    config["model"], config["max_tokens"], config["temperature"]
                )

                if full_response:
                    placeholder.markdown(full_response)
                    elapsed = time.time() - start_time
                    st.caption(f"⏱️ Gerado em {elapsed:.1f}s | Modelo: {used_model}")
                else:
                    full_response = "❌ Não foi possível gerar resposta. Filtro de segurança bloqueou."
                    placeholder.error(full_response)
                    elapsed = time.time() - start_time

                results.append({
                    "question": question,
                    "answer": full_response,
                    "elapsed": elapsed,
                })

            st.session_state.quiz_results = results
            st.session_state.quiz_processing = False
            st.rerun()

        # Formulário de entrada
        else:
            book = st.text_input(
                "Qual livro?",
                value=st.session_state.get("quiz_book", ""),
                placeholder="Ex: O Livro dos Espíritos, O Evangelho Segundo o Espiritismo...",
            )
            author = st.text_input(
                "Qual autor?",
                value=st.session_state.get("quiz_author", ""),
                placeholder="Ex: Allan Kardec",
            )
            chapters = st.text_input(
                "Quais capítulos? (separados por vírgula)",
                value=st.session_state.get("quiz_chapters", ""),
                placeholder="Ex: 1, 3, 5, 10",
            )

            num_questions = st.number_input(
                "Quantas questões serão feitas?",
                min_value=1,
                max_value=20,
                value=max(len(st.session_state.get("quiz_questions", [])), 1),
                step=1,
            )

            questions = []
            saved_questions = st.session_state.get("quiz_questions", [])
            for i in range(num_questions):
                default_val = saved_questions[i] if i < len(saved_questions) else ""
                question = st.text_input(
                    f"Pergunta {i + 1}",
                    value=default_val,
                    placeholder=f"Digite a pergunta {i + 1}...",
                    key=f"quiz_q_{i}",
                )
                questions.append(question)

            if st.button("Enviar Questionário", use_container_width=True):
                if not book or not author or not chapters:
                    st.warning("⚠️ Por favor, preencha o livro, autor e capítulos.")
                elif not any(q.strip() for q in questions):
                    st.warning("⚠️ Por favor, escreva pelo menos uma pergunta.")
                else:
                    st.session_state.quiz_book = book
                    st.session_state.quiz_author = author
                    st.session_state.quiz_chapters = chapters
                    st.session_state.quiz_questions = [q.strip() for q in questions if q.strip()]
                    st.session_state.quiz_processing = True
                    st.session_state.quiz_results = []
                    st.rerun()
        
    elif menu_option == "Estudo Literal":
        st.title("🕊️ Estudos Doutrinários")
        st.subheader("Estudo literal da doutrina")
        st.info("Em desenvolvimento...")


if __name__ == "__main__":
    main()
