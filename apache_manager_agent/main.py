import asyncio
import os
from dotenv import load_dotenv
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_agentchat.ui import Console
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import CodeExecutorAgent
from colorama import init, Fore, Style
from datetime import datetime, timedelta

# Inicializa o colorama para Windows
init()

async def main():
    # Carrega variáveis de ambiente
    load_dotenv()
    
    print(Fore.CYAN + "\n[INÍCIO DA EXECUÇÃO DOS AGENTES - STREAMING DAS MENSAGENS]:\n" + Style.RESET_ALL)
    
    # Configura o cliente Azure OpenAI
    az_model_client = AzureOpenAIChatCompletionClient(
        azure_deployment=os.getenv("AZURE_DEPLOYMENT_NAME", "log-analysis-gpt4"),
        seed=48,
        temperature=0.7,
        model="gpt-4o",
        api_version="2023-05-15",
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key=os.getenv("AZURE_API_KEY"),
        streaming=True
    )

    # Agente para leitura controlada de logs
    log_reader = AssistantAgent(
        name="LogReaderAgent",
        model_client=az_model_client,
        system_message="""
        Você é um agente especializado em leitura e filtragem de logs do Apache.
        
        Regras importantes:
        1. Leia apenas os últimos 100 logs por vez
        2. Filtre apenas logs de erro e warning
        3. Não faça suposições sobre logs que não viu
        4. Se precisar ver mais logs, peça explicitamente
        
        Use o terminal para executar comandos como:
        tail -n 100 /var/log/apache2/error.log
        """
    )

    # Agente para análise de logs
    log_analyzer = AssistantAgent(
        name="LogAnalyzerAgent",
        model_client=az_model_client,
        system_message="""
        Você é um especialista em análise de logs do Apache.
        
        Regras importantes:
        1. Analise apenas os logs que foram explicitamente fornecidos pelo LogReaderAgent
        2. Não faça suposições sobre logs que não viu
        3. Se precisar de mais informações, peça ao LogReaderAgent
        4. Mantenha o foco em problemas específicos e mensuráveis
        """
    )

    # Agente para diagnóstico
    root_cause_agent = AssistantAgent(
        name="RootCauseAgent",
        model_client=az_model_client,
        system_message="""
        Você é um especialista em diagnóstico de problemas no Apache.
        
        Regras importantes:
        1. Baseie suas análises apenas em informações confirmadas
        2. Não faça suposições sem evidências
        3. Se precisar de mais informações, peça aos outros agentes
        4. Mantenha o foco em causas específicas e verificáveis
        """
    )

    # Agente para execução de comandos
    terminal = CodeExecutorAgent(
        "ComputerTerminal",
        code_executor=LocalCommandLineCodeExecutor()
    )

    # Agente para verificação de status
    status_verifier = AssistantAgent(
        name="StatusVerifierAgent",
        model_client=az_model_client,
        system_message="""
        Você é um agente verificador.
        
        Regras importantes:
        1. Verifique apenas o que foi explicitamente solicitado
        2. Não faça suposições sobre o estado do sistema
        3. Use comandos específicos para verificar cada aspecto
        4. Se tudo estiver funcionando corretamente, responda com TERMINATE
        """
    )

    # Agente para relatório
    report_agent = AssistantAgent(
        name="ReportAgent",
        model_client=az_model_client,
        system_message="""
        Você é responsável por criar um relatório técnico.
        
        Regras importantes:
        1. Inclua apenas informações confirmadas
        2. Não faça suposições não verificadas
        3. Mantenha o foco em fatos e evidências
        4. Seja específico e objetivo
        """
    )

    # Configura o chat em equipe
    team = MagenticOneGroupChat(
        participants=[
            log_reader,
            log_analyzer,
            root_cause_agent,
            terminal,
            status_verifier,
            report_agent
        ],
        model_client=az_model_client,
        termination_condition=TextMentionTermination("TERMINATE")
    )

    # Define a tarefa inicial
    task = """
    Analise o estado do Apache de forma controlada e sistemática:
    1. Comece lendo apenas os últimos 100 logs de erro
    2. Analise esses logs específicos
    3. Se necessário, solicite mais logs
    4. Mantenha o foco em problemas específicos e verificáveis
    5. Não faça suposições sem evidências
    """

    # Executa o chat em equipe
    await Console(team.run_stream(task=task))

if __name__ == "__main__":
    asyncio.run(main())