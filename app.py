import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente de um arquivo .env, se existir
load_dotenv()

def main():
    st.set_page_config(page_title="Essência Espírita - Textos Simples", page_icon="🕊️")

    st.title("🕊️ Essência Espírita")
    st.subheader("Textos resumidos com vocabulário simples e baseados na Doutrina Kardecista")

    # Configuração da Barra Lateral
    st.sidebar.header("Configuração")
    api_key = st.sidebar.text_input("Insira sua OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    
    if not api_key:
        st.info("Por favor, insira sua OpenAI API Key na barra lateral para começar.", icon="🔑")
        st.stop()

    client = OpenAI(api_key=api_key)

    # Entrada do Usuário
    theme = st.text_input("Sobre qual tema você gostaria de ler hoje?", placeholder="Ex: Reencarnação, Lei de Causa e Efeito, Prece...")

    if st.button("Gerar Texto"):
        if theme:
            with st.spinner("Consultando a Espiritualidade..."):
                try:
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

                    response = client.chat.completions.create(
                        model="gpt-4o-mini", # Modelo mais atual e eficiente
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Escreva um texto resumido sobre: {theme}"}
                        ],
                        max_tokens=500,
                        temperature=0.7
                    )

                    text_result = response.choices[0].message.content
                    
                    st.markdown("---")
                    st.markdown(f"### {theme}")
                    st.write(text_result)
                    
                    st.download_button(
                        label="Baixar texto (Arquivo TXT)",
                        data=text_result,
                        file_name=f"essencia_espirita_{theme.lower().replace(' ', '_')}.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"Ocorreu um erro ao gerar o texto: {e}")
        else:
            st.warning("Por favor, digite um tema.")

    st.markdown("---")
    st.caption("Desenvolvido para estudo e divulgação da Doutrina Espírita Kardecista.")

if __name__ == "__main__":
    main()
