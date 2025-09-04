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
    from access import URL, RD_login, RD_password, CHROME_DRIVER_PATH #В зависимости от теста могут меняться!!! А также не забудь поменять переменные в "---Steps---" - можно найти по поиску
except Exception as e:
    raise ImportError("Создайте access.py с URL, sys_login, sys_password, CHROME_DRIVER_PATH (опционально).") from e

# ---- Настройки / селекторы ----
WAIT = 15
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

SELECTORS = {
    # Авторизация (страница логина)
    "login-authorization": (By.ID, "login-authorization"),
    "password-authorization": (By.ID, "password-authorization"),
    "login_submit": (By.ID, "authorization-button"),
    "menu_objects": (By.ID, "objects-tab"),

    # Для выполнения теста
    "reveal_dev": (By.XPATH, '//*[@id="application"]/div[3]/div[2]/div[1]/div/ul/li/ul/li/div/div[1]'),
    "reveal_project": (By.XPATH, '//*[@id="application"]/div[3]/div[2]/div[1]/div/ul/li/ul/li/ul[3]/li/div/div[1]'),
    "reveal_my_project": (By.XPATH, '//*[@id="application"]/div[3]/div[2]/div[1]/div/ul/li/ul/li/ul[3]/li/ul/li/div/div[1]'),
    "doc_placement": (By. XPATH, '//*[@id="application"]/div[3]/div[2]/div[1]/div/ul/li/ul/li/ul[3]/li/ul/li/ul[4]/li/div/div[2]'),
    "dev_map": (By.CSS_SELECTOR, '[data-reference="CMD_FOLDER_CREATE_DOXS_PLACE"]'),
    "name_map": (By.XPATH, '//*[@id="modalRoot"]/div[2]/div/div/div/div/div[2]/div/div[2]/div[2]/div[2]/div/div[2]/div/input'),
    "ok_modal_btn": (By.CSS_SELECTOR, '[data-reference="ok-modal-window-btn"]'),
    "reveal_folder": (By. XPATH, '//tbody[contains(., "Тестовая папка")]'),
    "folder": (By. XPATH, '//*[@id="application"]/div[2]/div[2]/div[1]/div/ul/li/ul/li/ul[3]/li/ul/li/ul[4]/li/ul/li/div/div[2]'),
    "tech_doc": (By.CSS_SELECTOR, '[data-reference="CMD_DOCUMENT_CREATE"]'),
    #"tech_doc": (By.XPATH, '//*[@id="application"]/div[3]/div[1]/div[2]/button[3]'),
    "designation": (By. XPATH, '//*[@id="modalRoot"]/div[2]/div/div/div/div/div[2]/div/div[2]/div[2]/div[2]/div/div[2]/div/input'),
    "name": (By. XPATH, '//*[@id="modalRoot"]/div[2]/div/div/div/div/div[2]/div/div[2]/div[2]/div[2]/div/div[4]/div/input'),
    "change": (By. XPATH, '//*[@id="modalRoot"]/div[2]/div/div/div/div/div[2]/div/div[2]/div[2]/div[2]/div/div[6]/div/input'),

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

def right_click(driver, selector, timeout=WAIT):
    by, value = selector
    element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )
    driver.execute_script(
        "var evt = new MouseEvent('contextmenu', {bubbles: true, cancelable: true});"
        "arguments[0].dispatchEvent(evt);",
        element
    )
    menu = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-signature='context-menu-wrapper']"))
    )
    return menu


# ---- Steps ----
def login(driver):
    try:
        print("[STEP] Переходим на страницу логина")
        driver.get(URL)
        
        print("[STEP] Вводим логин")
        login_input = find(driver, SELECTORS["login-authorization"])
        login_input.clear()
        login_input.send_keys(RD_login)
        
        print("[STEP] Вводим пароль")
        password_input = find(driver, SELECTORS["password-authorization"])
        password_input.clear()
        password_input.send_keys(RD_password)
        
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

        print("[STEP] Расскрываем структуру проектов")
        click(driver, SELECTORS["reveal_project"])

        print("[STEP] Расскрываем структуру проекта")
        click(driver, SELECTORS["reveal_my_project"])

        print("[STEP] Выбираем элемент проекта 'Размещение документации'")
        click(driver, SELECTORS["doc_placement"])

        print("[STEP] Открываем форму создания папки")
        click(driver, SELECTORS["dev_map"]) 

        print("[STEP] Отчищаем поле 'Наименование' и вводим свое значение")
        input_name_map = find(driver, SELECTORS["name_map"])
        input_name_map.clear()
        input_name_map.send_keys("Тестовая папка")

        print("[STEP] Подтверждаем создание папки")
        click(driver, SELECTORS["ok_modal_btn"])

        print("[STEP] Расскрываем струтуру раздела 'Размещение документации'")
        click(driver, SELECTORS["reveal_folder"])

        print("[STEP] Выбираем ранее созданную папку")
        click(driver, SELECTORS["folder"])

        print("[STEP] Выбираем ранее созданную папку")
        right_click(driver, SELECTORS["folder"])

        print("[STEP] Вызываем форму создания технического документа")
        click(driver, SELECTORS["tech_doc"])

        print("[STEP] Заполняем поле 'Обозначение'")
        input_designation = find(driver, SELECTORS["designation"])
        input_designation.clear()
        input_designation.send_keys("100-ТД.1")

        print("[STEP] Заполняем поле 'Наименование'")
        input_name = find(driver, SELECTORS["name"])
        input_name.clear()
        input_name.send_keys("Технический документ")

        print("[STEP] Заполняем поле 'Изм. №'")
        input_change = find(driver, SELECTORS["change"])
        input_change.clear()
        input_change.send_keys("1")

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