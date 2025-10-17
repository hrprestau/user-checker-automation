import requests
from bs4 import BeautifulSoup
import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- CONFIGURAÇÕES E CREDENCIAIS ---
URL_HABBO = "https://habborp.city/corporacao/5"
URL_DASHBOARD_LOGIN = "https://funcionarios-mu.vercel.app/admin" # Geralmente a URL base
URL_DASHBOARD_DATA = "https://funcionarios-mu.vercel.app/admin/dashboard"

# Credenciais (Puxadas dos GitHub Secrets)
HABBO_USER = os.environ.get('HABBO_USER')
HABBO_PASSWORD = os.environ.get('HABBO_PASSWORD')
VERCEL_USER = os.environ.get('VERCEL_USER')
VERCEL_PASSWORD = os.environ.get('VERCEL_PASSWORD')

# --- FUNÇÃO DE CRIAÇÃO DO DRIVER ---
def setup_driver():
    """Configura e retorna o driver do Chrome em modo headless."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# --- FUNÇÃO 1: EXTRAÇÃO DO HABBO RP ---
def get_habbo_users_with_shifts(driver):
    """Faz login no Habbo RP e extrai a lista de nicks e turnos."""
    users_habbo = {} 
    
    try:
        driver.get(URL_HABBO)
        wait = WebDriverWait(driver, 10)

        # ***** INSPECIONE AQUI: LOGIN HABBO RP *****
        # Altere o (By.NAME, 'user') e (By.NAME, 'pass') se necessário
        wait.until(EC.presence_of_element_located((By.NAME, 'user'))).send_keys(HABBO_USER)
        driver.find_element(By.NAME, 'pass').send_keys(HABBO_PASSWORD)
        driver.find_element(By.CLASS_NAME, 'btn-login').click()
        
        # Espera a página de corporação carregar (ajuste o seletor de espera)
        wait.until(EC.url_to_be(URL_HABBO))
        # ***** FIM DA INSPEÇÃO HABBO RP *****
        
        # Web Scraping Pós-Login
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # ***** PERSONALIZAR AQUI (EXTRAÇÃO NICK/TURNO HABBO RP) *****
        # Lógica para extrair nick e turno da página logada.
        # Exemplo:
        ranking_rows = soup.find_all('div', class_='user-ranking-row') 
        for row in ranking_rows:
            nick = row.find('a', class_='user-nick').get_text().strip()
            shifts = row.find('span', class_='shift-info').get_text().strip()
            users_habbo[nick] = shifts
        # ***** FIM DA PERSONALIZAÇÃO *****
        
        return users_habbo

    except Exception as e:
        print(f"ERRO ao extrair Habbo RP (Login/Scraping): {e}", file=sys.stderr)
        return {} 


# --- FUNÇÃO 2: EXTRAÇÃO DO DASHBOARD VERCEL ---
def get_dashboard_users(driver):
    """Faz login no Dashboard Vercel e extrai a lista de nicks."""
    users_dashboard = set() 
    
    try:
        driver.get(URL_DASHBOARD_LOGIN)
        wait = WebDriverWait(driver, 10)

        # ***** INSPECIONE AQUI: LOGIN VERCEL DASHBOARD *****
        # Altere o (By.ID, 'email') e (By.ID, 'password') se necessário
        wait.until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(VERCEL_USER)
        driver.find_element(By.ID, 'password').send_keys(VERCEL_PASSWORD)
        driver.find_element(By.XPATH, '//button[text()="Logar"]').click() # Exemplo para botão com texto "Logar"
        
        # Espera a navegação para o dashboard
        wait.until(EC.url_to_be(URL_DASHBOARD_DATA))
        # ***** FIM DA INSPEÇÃO VERCEL DASHBOARD *****

        # Web Scraping Pós-Login (Dashboard)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # ***** PERSONALIZAR AQUI (EXTRAÇÃO NICK VERCEL) *****
        # Lógica para extrair a lista de nicks da página logada.
        # Exemplo:
        nick_elements = soup.find_all('td', class_='employee-name')
        for element in nick_elements:
             users_dashboard.add(element.get_text().strip())
        # ***** FIM DA PERSONALIZAÇÃO *****
        
        return users_dashboard

    except Exception as e:
        print(f"ERRO ao extrair Dashboard Vercel (Login/Scraping): {e}", file=sys.stderr)
        return set()


# --- FUNÇÃO PRINCIPAL (CRUZAMENTO DE DADOS) ---
def check_for_new_users():
    """Compara as listas e imprime Issue se encontrar um novato."""
    
    # 1. Verifica se as credenciais estão disponíveis
    if not all([HABBO_USER, HABBO_PASSWORD, VERCEL_USER, VERCEL_PASSWORD]):
        print("ERRO CRÍTICO: Credenciais incompletas. Verifique os GitHub Secrets.", file=sys.stderr)
        sys.exit(1)
        
    driver = setup_driver()
    
    try:
        habbo_users = get_habbo_users_with_shifts(driver)
        dashboard_users = get_dashboard_users(driver) 
    finally:
        driver.quit() # Garante que o driver feche

    # 2. Identificar usuários no Habbo RP, mas NÃO no Dashboard
    novatos = {}
    for nick, shifts in habbo_users.items():
        if nick not in dashboard_users:
            novatos[nick] = shifts
            
    if novatos:
        # Imprime a notificação para o Issue
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        print(f"[{current_time}] ⚠️ NOVATOS ENCONTRADOS! Usuários no Habbo RP, mas fora do Dashboard.")
        print("Detalhes:")
        
        for nick, shifts in novatos.items():
            print(f"- **{nick}** (Turnos: {shifts})")
            
        print("\n**Ação Requerida:** Cadastrar estes usuários no sistema de funcionários.")

if __name__ == "__main__":
    check_for_new_users()