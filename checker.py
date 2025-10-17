import requests
from bs4 import BeautifulSoup
import sys
from datetime import datetime

# --- CONFIGURAÇÕES ---
# URL da página que você deseja verificar
TARGET_URL = "https://habborp.city/corporacao/5"  # Substitua pela URL real (ex: 'https://site.com/user/hrprestau')

# A string (texto) que indica que o usuário ESTÁ inativo/banido ou ausente.
# Ajuste este texto conforme o site que você está monitorando.
STRING_DE_ERRO = "Usuário não cadastrado"
# Exemplo de outras strings: "User not found", "Conta Suspensa", "Banned"

# O nome ou ID do usuário que você está verificando (para o relatório)
USER_ID = "hrprestau"

# --- FUNÇÃO PRINCIPAL DE VERIFICAÇÃO ---
def check_user_status():
    """
    Faz o web scraping, verifica o status e imprime uma mensagem se encontrar uma diferença.
    A saída (print) é o que o GitHub Actions transforma em um Issue.
    """
    try:
        # 1. Faz a requisição HTTP para a página
        response = requests.get(TARGET_URL)
        response.raise_for_status()  # Gera exceção para erros 4xx/5xx

        # 2. Analisa o conteúdo HTML da página
        soup = BeautifulSoup(response.text, 'html.parser')

        # 3. Procura pela string de erro no texto completo da página
        page_text = soup.get_text().strip()

        if STRING_DE_ERRO in page_text:
            # STATUS ATUAL: Encontrou a string de erro (o usuário está INATIVO/AUSENTE)
            
            # Se o usuário *deveria* estar ativo, mas está inativo/ausente, disparamos a notificação.
            # *******************************************************************
            # Lógica de notificação: Se ele está INATIVO, gere um Issue.
            # *******************************************************************
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # ESTA SAÍDA SERÁ CAPTURADA PELO GITHUB ACTIONS!
            print(f"[{current_time}] O monitoramento de '{USER_ID}' encontrou a string de erro.")
            print("--- Detalhes da Notificação ---")
            print(f"Status Atual: INATIVO/AUSENTE")
            print(f"String Encontrada: '{STRING_DE_ERRO}'")
            print(f"URL: {TARGET_URL}")
            print("\n**Ação Requerida:** Verifique a página e o estado do usuário.")
            
            # Para garantir que o GitHub Actions capture a saída, podemos usar sys.exit(1)
            # MAS, como estamos usando 'continue-on-error: true' no YAML, basta o 'print'
            # para alimentar o Issue, e o código pode terminar normalmente.
        
        else:
            # STATUS ATUAL: Não encontrou a string de erro (o usuário parece estar ATIVO/PRESENTE)
            
            # Se o usuário está na situação ESPERADA (ativo), o script não imprime nada.
            # O GitHub Actions captura uma saída VAZIA e NÃO cria um Issue.
            pass
            # print(f"[{USER_ID}] Status OK. Nenhuma string de erro encontrada.") # (Comentado, não imprima se estiver OK)

    except requests.exceptions.RequestException as e:
        # Captura erros de rede ou 4xx/5xx HTTP
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{current_time}] ERRO DE CONEXÃO ou HTTP ao verificar {USER_ID}: {e}")
        print("--- Detalhes ---")
        print(f"URL: {TARGET_URL}")


if __name__ == "__main__":
    check_user_status()