import os, time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.action_chains import ActionChains

# ---- Импорт чувствительных данных ----
URL = os.environ.get("URL") #or "http://10.19.10.216:5440" #Убрать после отладки
sys_login = os.environ.get("sys_login") #or "SYSADMIN" #Убрать после отладки
sys_password = os.environ.get("sys_password") #or "Tdm365" #Убрать после отладки
#CHROME_DRIVER_PATH = os.environ.get("CHROME_DRIVER_PATH") or "/usr/bin/chromedriver" #Убрать после отладки

# ---- Настройки / селекторы ----
WAIT = 10
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

SELECTORS = {
    # Авторизация (страница логина)
    "login-authorization": (By.ID, "login-authorization"),
    "password-authorization": (By.ID, "password-authorization"),
    "login_submit": (By.ID, "authorization-button"),
    "menu_objects": (By.ID, "objects-tab"),
    "object_dev": (By.CSS_SELECTOR, '[data-reference="CMD_OBJECT_STRUCTURE_CREATE"]'),
    #Добавляем селекторы сюда. Те селекторы, которые уже есть в шаблоне, повторяются в каждом тесте (Авторизация + переход в раздел "Объекты")
}

def ss(driver, name):
    driver.save_screenshot(f"{name}.png")

def find(driver, selector, timeout=WAIT):
    by, value = selector
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )

def click(driver, selector, timeout=15):
    by, value = selector
    try:
        # Ждём, пока элемент будет видим и кликабелен
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        try:
            element.click()
        except ElementClickInterceptedException:
            # Если клик не сработал, используем JS
            driver.execute_script("arguments[0].click();", element)
    except TimeoutException:
        raise TimeoutException(f"[ERROR] Элемент '{value}' ({by}) не найден или не кликабелен за {timeout} секунд")

def right_click(driver, selector, timeout=10):
    by, value = selector
    element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )
    ActionChains(driver).context_click(element).perform()

# ---- Fixtures ----
@pytest.fixture(params=[b.strip() for b in os.environ.get("BROWSERS","chrome").split(",")])
def driver(request):
    browser_name = request.param.lower()
    driver = None

    if browser_name == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--headless")  # убрать для локальной отладки
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        #options.add_argument("--disable-infobars") #Убрать после отладки
        #options.add_argument("--disable-extensions") #Убрать после отладки
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    elif browser_name == "firefox":
        options = webdriver.FirefoxOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--headless")  # убрать для локальной отладки
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        #options.add_argument("--disable-infobars") #Убрать после отладки
        #options.add_argument("--disable-extensions") #Убрать после отладки
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)

    elif browser_name == "edge":
        options = webdriver.EdgeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--headless") # убрать для локальной отладки
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        #options.add_argument("--disable-infobars") #Убрать после отладки
        #options.add_argument("--disable-extensions") #Убрать после отладки
        driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)

    else:
        raise ValueError(f"Браузер {browser_name} не поддерживается")

    driver.browser_name = browser_name  # сохраняем для отчета
    yield driver
    driver.quit()

# ---- Steps ----
def test_TDM6(driver):
    try:
        print(f"[INFO] Запуск теста на браузере: {driver.browser_name}")
        print("[STEP] Переходим на страницу логина")
        driver.get(URL)
        
        print("[STEP] Вводим логин")
        login_input = find(driver, SELECTORS["login-authorization"])
        login_input.clear()
        login_input.send_keys(sys_login)
        
        print("[STEP] Вводим пароль")
        password_input = find(driver, SELECTORS["password-authorization"])
        password_input.clear()
        password_input.send_keys(sys_password)
        
        print("[STEP] Нажимаем кнопку входа")
        click(driver, SELECTORS["login_submit"])
        print("[SUCCESS] Авторизация прошла успешно!")

        time.sleep(5)  # Пауза
        
        click(driver, SELECTORS["menu_objects"], timeout=15)
        print("[STEP] Открылся раздел 'Объекты'")

        #Шаги добавляем сюда. Те шаги, которые уже есть в шаблоне, повторяются в каждом тесте (Авторизация + переход в раздел "Объекты")

        time.sleep(2)  # Пауза
            
    except Exception as e:
        ss(driver, "TDM6_error")
        pytest.fail(f"[ERROR] Тест упал: {e}", pytrace=True)

# ---- Main ---- Требуется для локальной отладки (Для Jenkins не нужно)
# if __name__ == "__main__":
#     driver = None
#     try:
#         driver = get_driver()
#         try: 
#             driver.maximize_window()
#             print("[INFO] Окно браузера maximized")
#         except Exception as e: 
#             print(f"[WARNING] Не удалось maximize окно: {e}")
        
#         print("[TEST] Запуск теста авторизации...")
        
#         # Шаг 1: Авторизация
#         auth_success = test_TDM6(driver)
        
#         if not auth_success:
#             print("[RESULT] Тест провален на этапе авторизации!")
#             ss(driver, "auth_failed")
#             exit(1)  # Завершаем выполнение
            
#         print("[RESULT] Весь тест пройден успешно!")   
            
#     except Exception as e:
#         print(f"[CRITICAL ERROR]: {e}")
#         if driver:
#             ss(driver, "critical_error")
#     finally:
#         if driver:
#             print("[INFO] Закрываем браузер...")
#             driver.quit()