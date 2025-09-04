import os, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains 

# ---- Импорт чувствительных данных ----
try:
    from access import URL, sys_login, sys_password, CHROME_DRIVER_PATH #В зависимости от теста могут меняться!!!
except Exception as e:
    raise ImportError("Создайте access.py с URL, sys_login, sys_password, CHROME_DRIVER_PATH (опционально).") from e

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
    "object_dev": (By.CSS_SELECTOR, '[data-reference="CMD_OBJECT_STRUCTURE_CREATE"]'),
    "field_cod_object": (By.CSS_SELECTOR, '[data-signature="input-body"]'),
    "name_object": (By.XPATH, '//*[@id="modalRoot"]/div[2]/div/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[4]/div/textarea'),
    "ok_button": (By.CSS_SELECTOR, '[data-reference="ok-modal-window-btn"]'), 
}

# ---- Helpers ----
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    if CHROME_DRIVER_PATH:
        service = ChromeService(executable_path=CHROME_DRIVER_PATH)
    else:
        service = ChromeService(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def ss(driver, name="err"):
    path = os.path.join(SCREENSHOT_DIR, f"{name}_{int(time.time())}.png")
    try:
        driver.save_screenshot(path)
        print(f"[SCREENSHOT] Сохранен: {path}")
    except Exception as e:
        print(f"[SCREENSHOT ERROR] {e}")
    return path

def find(driver, selector, timeout=WAIT):
    by, value = selector
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )

def click(driver, selector, timeout=WAIT):
    by, value = selector
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    element.click()

def right_click(driver, selector, timeout=10):
    by, value = selector
    element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )
    ActionChains(driver).context_click(element).perform()

# ---- Steps ----
def login(driver):
    try:
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

        time.sleep(2)  # Пауза
        
        try:
            click(driver, SELECTORS["menu_objects"], timeout=15)
            print("[STEP] Открылся раздел 'Объекты'")
            return True
        except TimeoutException:
            print("[ERROR] Не удалось найти меню 'Объекты' после авторизации")
            return False
            
    except Exception as e:
        print(f"[ERROR в login()]: {e}")
        ss(driver, "login_error")
        return False
    
def test(driver):
    try:
        print("[STEP] Открываем форму 'Редактирование объекта'")
        click(driver, SELECTORS["object_dev"])

        print("[STEP] Вводим код объекта")
        login_input = find(driver, SELECTORS["field_cod_object"])
        login_input.clear()
        login_input.send_keys("001.1-1")

        print("[STEP] Вводим намиенование объекта")
        name_input = find(driver, SELECTORS["name_object"])
        name_input.clear()
        name_input.send_keys("TDM_Тестовый объект разработки")

        print("[STEP] Создаем объект разработки")
        click(driver, SELECTORS["ok_button"])

        time.sleep(2)  # Пауза

        return True

    except Exception as e:
        print(f"[ERROR в login()]: {e}")
        ss(driver, "login_error")
        return False


# ---- Main ----
if __name__ == "__main__":
    driver = None
    try:
        driver = get_driver()
        try: 
            driver.maximize_window()
            print("[INFO] Окно браузера maximized")
        except Exception as e: 
            print(f"[WARNING] Не удалось maximize окно: {e}")
        
        print("[TEST] Запуск теста авторизации...")
        
        # Шаг 1: Авторизация
        auth_success = login(driver)
        
        if not auth_success:
            print("[RESULT] Тест провален на этапе авторизации!")
            ss(driver, "auth_failed")
            exit(1)  # Завершаем выполнение
            
        print("[INFO] Авторизация успешна, запускаем тестовые действия...")

        #Шаг 2: Выполнение тестовых шагов (Описаны в тесте TDM-6:Создание объекта разработки)
        test_success = test(driver)
        
        if not test_success:
            print("[RESULT] Тест провален на этапе тестовых действий!")
            ss(driver, "test_failed")
            exit(1) #Завершаем выполнение

        print("[RESULT] Весь тест пройден успешно!")        
            
    except Exception as e:
        print(f"[CRITICAL ERROR]: {e}")
        if driver:
            ss(driver, "critical_error")
    finally:
        if driver:
            print("[INFO] Закрываем браузер...")
            driver.quit()