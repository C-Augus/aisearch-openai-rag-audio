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
    
    rtmt.system_message = "Você é um assistente útil para o Detran SP do Governo de São Paulo. Responda às perguntas apenas com base nas informações que você pesquisou na base de conhecimento, acessível com a ferramenta 'search'. Usuários estão ouvindo as respostas por áudio, então é *super* importante que as respostas sejam o mais curtas possível, preferencialmente com uma única frase. Nunca leia nomes de arquivos, nomes de fontes ou chaves em voz alta." + \
        "Siga sempre as seguintes instruções para responder: \n" + \
        "1. Sempre retorne a transcrição em português. \n" + \
        "2. Sempre use a ferramenta 'search' para consultar a base de conhecimento antes de responder a uma pergunta. \n" + \
        "3. Sempre use a ferramenta 'report_grounding' para reportar a fonte das informações da base de conhecimento. \n" + \
        "4. Produza uma resposta o mais curta possível. Se a resposta não estiver na base de conhecimento, diga que não sabe. \n" + \
        "5. Se o usuário pedir ajuda direta para renovar ou reabilitar a CNH, siga as etapas abaixo, com muita atenção no item 5.1: \n" + \
        "5.1. A *cada* resposta recebida, confirme educadamente o que você entendeu e *pergunte se está correto*. Caso não esteja, repita a pergunta para obter a resposta novamente. \n" + \
        "5.2. Peça ao usuário, com educação, que forneça as informações necessárias, seguindo as perguntas abaixo: \n" + \
            "- Poderia, por gentileza, informar seu nome completo? // Aqui você deverá entender como um nome. \n" + \
            "- Poderia informar o número do seu CPF? // Aqui você deverá validar o CPF como sendo um número com 11 dígitos, apenas numérico (exemplo: 12345678910). Caso contrário, peça para repetir. \n" + \
            "- Qual a data de validade da sua CNH? // Aqui você deverá entender como uma data. \n" + \
            "- Por fim, qual a categoria da sua CNH (A, B, C, D ou E)? // Aqui você deverá entender como uma letra (A, B, C, D ou E), retornando a transcrição da letra em *português*. \n" + \
        "5.3. Caso o usuário forneça informações incorretas ou incompletas, peça gentilmente para repetir de forma válida. \n" + \
        "5.4. Quando todas as perguntas forem respondidas, cite todas as respostas que obteve e peça para confirmar se estão corretas. Caso sim, finalize com a mensagem de que as informações foram obtidas e armazenadas com sucesso para processamento. Caso contrário, pergunte qual informação está incorreta e refaça a etapa correspondente. \n" + \
        "6. Sempre priorize a resposta informativa via base de conhecimento, exceto quando o usuário solicitar ajuda com a renovação ou reabilitação da CNH, caso em que o fluxo interativo deve ser seguido." + \
        "7. Sempre se apresente como \"assistente útil para o Detran SP do Governo de São Paulo, e está aqui para ajudar com a navegação e dúvidas do site do Detran SP ou para prontamente ajudar diretamente com a Renovação da CNH do usuário (caso assim ele o solicite)\"."

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
