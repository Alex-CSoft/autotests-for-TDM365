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
    from access import URL, AP_login, AP_password, CHROME_DRIVER_PATH #В зависимости от теста могут меняться!!! А также не забудь поменять переменные в "---Steps---" - можно найти по поиску
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
    "menu_objects": (By.ID, "objects-tab"),

    # Для выполнения теста
    "reveal_dev": (By.XPATH, '//*[@id="application"]/div[3]/div[2]/div[1]/div/ul/li/ul[2]/li/div/div[1]'),
    "reveal_project": (By.XPATH, '//*[@id="application"]/div[3]/div[2]/div[1]/div/ul/li/ul[2]/li/ul[3]/li/div/div[1]'),
    "project": (By.XPATH, '//*[@id="application"]/div[3]/div[2]/div[1]/div/ul/li/ul[2]/li/ul[3]/li/ul/li/div/div[2]/span'),
    "assigning_roles": (By.CSS_SELECTOR, '[data-sysid="CMD_PROJECT_ROLES_SET"]'),
    "btn_user_project": (By.XPATH, '//*[@id="modalRoot"]/div[2]/div/div/div/div/div[2]/div/div/button[1]'),
    "user_project": (By.XPATH, '//tr[contains(., "Участники проекта")]'),
    "btn_acceptance_doc": (By.XPATH, '//*[@id="modalRoot"]/div[2]/div/div/div/div/div[2]/div/div/button[2]'),
    "acceptance_doc": (By.XPATH, '//tr[contains(., "Приемка документации")]'),
    "btn_placement_doc": (By.XPATH, '//*[@id="modalRoot"]/div[2]/div/div/div/div/div[2]/div/div/button[3]'),
    "placement_doc": (By.XPATH, '//tr[contains(., "Размещение")]'#), тут не вызывается, надо что-то решать...
    "btn_ok_project": (By.CSS_SELECTOR, '[data-reference="ok-modal-window-btn"]'),
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

def double_click(driver, selector, timeout=WAIT):
    by, value = selector
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    actions = ActionChains(driver)
    actions.double_click(element).perform()

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
        login_input.send_keys(AP_login)
        
        print("[STEP] Вводим пароль")
        password_input = find(driver, SELECTORS["password-authorization"])
        password_input.clear()
        password_input.send_keys(AP_password)
        
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
        print("[STEP] Расскрываем структуру объекта разработки")
        click(driver, SELECTORS["reveal_dev"])

        print("[STEP] Расскрываем структуру проекта")
        click(driver, SELECTORS["reveal_project"])

        print("[STEP] Нажимаем на проект")
        click(driver, SELECTORS["project"])

        print("[STEP] Вызываем окно 'Определение прав на проекте'")
        click(driver, SELECTORS["assigning_roles"])

        print("[STEP] Открываем форму для выбора группы в 'Участники проекта'")
        click(driver, SELECTORS["btn_user_project"])

        time.sleep(1)  # Пауза

        print("[STEP] Выбираем группу пользователей")
        double_click(driver, SELECTORS["user_project"])

        time.sleep(1)  # Пауза

        print("[STEP] Открываем форму для выбора группы в 'Приемка документации'")
        click(driver, SELECTORS["btn_acceptance_doc"])

        time.sleep(1)  # Пауза

        print("[STEP] Выбираем группу пользователей")
        double_click(driver, SELECTORS["acceptance_doc"])

        time.sleep(1)  # Пауза

        print("[STEP] Открываем форму для выбора группы в 'Размещение документации'")
        click(driver, SELECTORS["btn_placement_doc"])

        time.sleep(1)  # Пауза

        print("[STEP] Выбираем группу пользователей")
        double_click(driver, SELECTORS["placement_doc"])

        print("[STEP] Подтверждаем выбор группы")
        click(driver, SELECTORS["btn_ok_project"])

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

        #Шаг 2: Выполнение тестовых шагов (Описаны в тесте ...(Дописать в каком)...)
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