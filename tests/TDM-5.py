import os, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---- Импорт чувствительных данных ----
#try:
#    from access import CHROME_DRIVER_PATH, URL, sys_login, sys_password
#except Exception as e:
#    raise ImportError from e

URL = os.environ.get("URL")
sys_login = os.environ.get("sys_login")
sys_password = os.environ.get("sys_password")
CHROME_DRIVER_PATH = os.environ.get("/usr/bin/chromedriver")

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
    #"checkbox": (By.XPATH, '/html/body/div[2]/div[2]/div/div/div/div/div[2]/div/div/div[5]/div/span'),
    #"checkbox": (By.CSS_SELECTOR, '[data-signature="checkbox-body"]'),
    #"btn_create_user": (By.XPATH, '/html/body/div[2]/div[4]/div/div/div/div/div[3]/button[1]'),
    "btn_create_user": (By.CLASS_NAME, "Buttons_selectionsButton__Ll7-A"),
    #"btn_create_user": (By.CSS_SELECTOR, '[data-reference="ok-modal-window-btn"]'),
}

# ---- Helpers ----
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    if CHROME_DRIVER_PATH:
        service = ChromeService(executable_path=CHROME_DRIVER_PATH)
    else:
        service = ChromeService(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def ss(driver, name="err"):
    path = os.path.join(SCREENSHOT_DIR, f"{name}_{int(time.time())}.png")
    try:
        driver.save_screenshot(path)
    except Exception:
        pass
    return path

def find(driver, selector, timeout=WAIT):
    by, value = selector
    return WebDriverWait(driver,timeout).until(
        EC.presence_of_element_located((by, value))
    )

def click(driver, selector, timeout=WAIT):
    by, value = selector
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    element.click()

# ---- Steps ----
def login(driver):
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
    return True

#Создание пользователя (Администратор проекта)
def create_user_in_group(driver):
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

# ---- Main ----
if __name__ == "__main__":
    driver = None
    try:
        driver = get_driver()
        try: driver.maximize_window()
        except Exception: pass

        login(driver)
        create_user_in_group(driver)
        print("[RESULT] Успешно — пользователь создан")
    except Exception as e:
        print("[ERROR]", e)
        if driver:
            print("Скрин:", ss(driver, "failure"))
    finally:
        if driver:
            driver.quit()