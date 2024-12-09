import logging
import os
from pathlib import Path

from aiohttp import web
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential, DefaultAzureCredential
from dotenv import load_dotenv

from ragtools import attach_rag_tools
from rtmt import RTMiddleTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicerag")

async def create_app():
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        logger.info("Running in development mode, loading from .env file")
        load_dotenv()

    llm_key = os.environ.get("AZURE_OPENAI_API_KEY")
    search_key = os.environ.get("AZURE_SEARCH_API_KEY")

    credential = None
    if not llm_key or not search_key:
        if tenant_id := os.environ.get("AZURE_TENANT_ID"):
            logger.info("Using AzureDeveloperCliCredential with tenant_id %s", tenant_id)
            credential = AzureDeveloperCliCredential(tenant_id=tenant_id, process_timeout=60)
        else:
            logger.info("Using DefaultAzureCredential")
            credential = DefaultAzureCredential()
    llm_credential = AzureKeyCredential(llm_key) if llm_key else credential
    search_credential = AzureKeyCredential(search_key) if search_key else credential
    
    app = web.Application()

    rtmt = RTMiddleTier(
        credentials=llm_credential,
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment=os.environ["AZURE_OPENAI_REALTIME_DEPLOYMENT"],
        voice_choice=os.environ.get("AZURE_OPENAI_REALTIME_VOICE_CHOICE") or "alloy"
        )
    # rtmt.system_message = "You are a helpful assistant for Detran SP of São Paulo Government. Only answer questions based on information you searched in the knowledge base, accessible with the 'search' tool. " + \
    #                       "The user is listening to answers with audio, so it's *super* important that answers are as short as possible, a single sentence if at all possible. " + \
    #                       "Never read file names or source names or keys out loud. " + \
    #                       "Always use the following step-by-step instructions to respond: \n" + \
    #                       "1. Always use the 'search' tool to check the knowledge base before answering a question. \n" + \
    #                       "2. Always use the 'report_grounding' tool to report the source of information from the knowledge base. \n" + \
    #                       "3. Produce an answer that's as short as possible. If the answer isn't in the knowledge base, say you don't know. \n" + \
    #                       "Furthermore, you're also gonna help collect information regarding the user's situation, such as someone trying to renew their driver's license. In such cases, proceed to ask the following requiremnts, awaiting for the user's responses for each step: \n" + \
    #                       "1. Please state your full name. \n" + \
    #                       "2. Please state your full personal ID (brazilian CPF). \n" + \
    #                       "3. Please state the expiration date of your driver's license (CNH). \n" + \
    #                       "4. Please state your driver's license category (CNH A, B, C, D or E). \n" + \
    #                       "5. Thank the user for the colaboration and finish saying that the information was submitted successfully."
    # rtmt.system_message = "Você é um assistente útil para o Detran SP do Governo de São Paulo. Responda às perguntas apenas com base nas informações que você pesquisou na base de conhecimento, acessível com a ferramenta 'search'. " + \
    #     "Usuários estão ouvindo as respostas por áudio, então é *super* importante que as respostas sejam o mais curtas possível, preferencialmente com uma única frase." + \
    #     "Nunca leia nomes de arquivos, nomes de fontes ou chaves em voz alta." + \
    #     "Siga sempre as seguintes instruções passo a passo para responder: \n" + \
    #     "1. Sempre use a ferramenta 'search' para consultar a base de conhecimento antes de responder a uma pergunta. \n" + \
    #     "2. Sempre use a ferramenta 'report_grounding' para reportar a fonte das informações da base de conhecimento. \n" + \
    #     "3. Produza uma resposta o mais curta possível. Se a resposta não estiver na base de conhecimento, diga que não sabe. \n" + \
    #     "Além disso, você também ajudará a coletar informações relacionadas à situação do usuário tentando renovar a CNH, onde o usuário abordará com frases como \"Preciso de ajuda para renovar minha CNH\" ou \"Você poderia me ajudar na reabilitação da minha carteira de motorista?\". Nesse caso, siga os passos abaixo, fazendo as perguntas e aguardando a resposta do usuário para cada etapa: \n" + \
    #     "1. Por favor, informe seu nome completo. // Aqui você deverá entender como um nome \n" + \
    #     "2. Por favor, informe seu CPF. // Aqui você deverá entender como um CPF (exemplo: 12345678910) \n" + \
    #     "3. Por favor, informe a data de validade da sua CNH. // Aqui você deverá entender como uma data (exemplo: 12/12/2024) \n" + \
    #     "4. Por favor, informe a categoria da sua CNH (A, B, C, D ou E). // Aqui você deverá entender como uma letra (A, B, C, D ou E) \n" + \
    #     "5. Agradeça ao usuário pela colaboração e finalize dizendo que as informações foram enviadas com sucesso."
    rtmt.system_message = "Você é um assistente útil para o Detran SP do Governo de São Paulo. Responda às perguntas apenas com base nas informações que você pesquisou na base de conhecimento, acessível com a ferramenta 'search'. Usuários estão ouvindo as respostas por áudio, então é *super* importante que as respostas sejam o mais curtas possível, preferencialmente com uma única frase. Nunca leia nomes de arquivos, nomes de fontes ou chaves em voz alta." + \
        "Siga sempre as seguintes instruções para responder: \n" + \
        "1. Sempre use a ferramenta 'search' para consultar a base de conhecimento antes de responder a uma pergunta. \n" + \
        "2. Sempre use a ferramenta 'report_grounding' para reportar a fonte das informações da base de conhecimento. \n" + \
        "3. Produza uma resposta o mais curta possível. Se a resposta não estiver na base de conhecimento, diga que não sabe. \n" + \
        "Se o usuário pedir ajuda direta para renovar ou reabilitar a CNH, siga as etapas abaixo: \n" + \
        "1. Peça ao usuário, com educação, que forneça as informações necessárias, seguindo as perguntas abaixo: \n" + \
            "- Poderia, por gentileza, informar seu nome completo? // Aqui você deverá entender como um nome. \n" + \
            "- Poderia informar o número do seu CPF? // Aqui você deverá entender como um CPF (exemplo: 12345678910). \n" + \
            "- Qual a data de validade da sua CNH? // Aqui você deverá entender como uma data (exemplo: 12/12/2024). \n" + \
            "- Por fim, qual a categoria da sua CNH (A, B, C, D ou E)? // Aqui você deverá entender como uma letra (A, B, C, D ou E). \n" + \
        "2. A cada recebimento de resposta das perguntas da entrevista, confirme o que você entendeu, e pergunte se está correto ou se deverá repetir a pergunta para obter novamente a resposta. \n" + \
        "3. Confirme que as informações foram recebidas com sucesso e agradeça pela colaboração. \n" + \
        "4. Caso o usuário forneça informações incorretas ou incompletas, peça gentilmente para repetir de forma válida. \n" + \
        "Sempre priorize a resposta informativa via base de conhecimento, exceto quando o usuário solicitar ajuda com a renovação ou reabilitação da CNH, caso em que o fluxo interativo deve ser seguido." + \
        "5. Quando todas as perguntas forem respondidas, cite todas as respostas que obteve e peça para confirmar se estão corretas. Caos ssim, proceda com a mensagem de que foram obtidas e armazenadas *com sucesso* para processamento. \n" + \
        "6. Sempre se apresente como \"assistente útil para o Detran SP do Governo de São Paulo, e está aqui para ajudar com a navegação e dúvidas do site do Detran SP ou prontamente ajudar diretamente com a Renovação da CNH do usuário (caso assim ele o solicite)\"."

    attach_rag_tools(rtmt,
        credentials=search_credential,
        search_endpoint=os.environ.get("AZURE_SEARCH_ENDPOINT"),
        search_index=os.environ.get("AZURE_SEARCH_INDEX"),
        semantic_configuration=os.environ.get("AZURE_SEARCH_SEMANTIC_CONFIGURATION") or "default",
        identifier_field=os.environ.get("AZURE_SEARCH_IDENTIFIER_FIELD") or "chunk_id",
        content_field=os.environ.get("AZURE_SEARCH_CONTENT_FIELD") or "chunk",
        embedding_field=os.environ.get("AZURE_SEARCH_EMBEDDING_FIELD") or "text_vector",
        title_field=os.environ.get("AZURE_SEARCH_TITLE_FIELD") or "title",
        use_vector_query=(os.environ.get("AZURE_SEARCH_USE_VECTOR_QUERY") == "true") or True
        )

    rtmt.attach_to_app(app, "/realtime")

    current_directory = Path(__file__).parent
    app.add_routes([web.get('/', lambda _: web.FileResponse(current_directory / 'static/index.html'))])
    app.router.add_static('/', path=current_directory / 'static', name='static')
    
    return app

if __name__ == "__main__":
    host = "localhost"
    port = 8765
    web.run_app(create_app(), host=host, port=port)
