import os, time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains

# ---- Импорт чувствительных данных ----
URL = os.environ.get("URL") #or "http://10.19.10.252:5440" #Убрать после отладки
sys_login = os.environ.get("sys_login") #or "SYSADMIN" #Убрать после отладки
sys_password = os.environ.get("sys_password") #or "Tdm365" #Убрать после отладки
CHROME_DRIVER_PATH = os.environ.get("CHROME_DRIVER_PATH") #or "/usr/bin/chromedriver" #Убрать после отладки

# ---- Настройки / селекторы ----
WAIT = 10
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

SELECTORS = {
    # Авторизация (страница логина)
    "login-authorization": (By.ID, "login-authorization"),
    "password-authorization": (By.ID, "password-authorization"),
    "login_submit": (By.ID, "authorization-button"),

    # Кнопка раздела "Объекты"
    "menu_objects": (By.ID, "objects-tab"),

    # Кнопка "Администрирование групп"
    "btn_group_admin": (By.CSS_SELECTOR, '[data-reference="CMD_GROUP_CHANGE"]'),

    #Группы в которые создаются пользователи
    "project_Administrators": (By.XPATH, '//tr[contains(., "Администраторы проектов")]'),

    #Создание пользователя
    "create_user": (By.XPATH, '//*[@id="modalRoot"]//button[4]'),
    "description_field": (By.XPATH, '//*[@id="modalRoot"]/div[4]/div/div/div/div/div[2]/div/div/div[2]/div/input'),
    "login_field": (By.XPATH, '//*[@id="modalRoot"]/div[4]/div/div/div/div/div[2]/div/div/div[4]/div/input'),
    "btn_create_user": (By.CLASS_NAME, "Buttons_selectionsButton__Ll7-A"),
}

# ---- Helpers ----
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")  # убрать во время отладки
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    #options.add_argument("--disable-infobars") #Убрать после отладки
    #options.add_argument("--disable-extensions") #Убрать после отладки
    
    # Используем webdriver-manager для автоматического скачивания подходящего драйвера
    service = ChromeService(ChromeDriverManager().install())

    return webdriver.Chrome(service=service, options=options)

def ss(driver, name):
    driver.save_screenshot(f"{name}.png")

def find(driver, selector, timeout=WAIT):
    by, value = selector
    return WebDriverWait(driver,timeout).until(
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

# ---- Fixtures ----
@pytest.fixture(scope="session")
def driver():
    driver = get_driver()
    yield driver
    driver.quit()

# ---- Steps ----
def test_TDM5(driver):
    try:
        driver.get(URL)
        #Вводим логин
        login_input = find(driver, SELECTORS["login-authorization"])
        login_input.clear()
        login_input.send_keys(sys_login)
        #Вводим пароль
        password_input = find(driver, SELECTORS["password-authorization"])
        password_input.clear()
        password_input.send_keys(sys_password)
        click(driver, SELECTORS["login_submit"])

        # контрольная точка: меню "Объекты"
        click(driver, SELECTORS["menu_objects"])
        assert True

        click(driver, SELECTORS["btn_group_admin"])
        click(driver, SELECTORS["project_Administrators"])
        click(driver, SELECTORS["create_user"])

        description_input = find(driver, SELECTORS["description_field"])
        description_input.clear()
        description_input.send_keys("Администратор проекта")

        login_input = find(driver, SELECTORS["login_field"])
        login_input.clear()
        login_input.send_keys("AP")

        # check = find(driver, SELECTORS["checkbox"])
        # check.clear()
        # check.send_keys(" ")
        #click(driver, SELECTORS["checkbox"])
        click(driver, SELECTORS["btn_create_user"])
        time.sleep(2)  # Пауза

    except Exception as e:
        ss(driver, "TDM5_error")
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
#         auth_success = test_TDM5(driver)
        
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