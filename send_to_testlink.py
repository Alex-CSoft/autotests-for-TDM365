import os
import xml.etree.ElementTree as ET
import re
from testlink import TestlinkAPIClient


# -----------------------------
# Настройки TestLink
# -----------------------------
API_URL = 'http://10.19.10.112/Testlink/lib/api/xmlrpc.php'  # URL TestLink (Именно ссылка на API)
DEV_KEY = 'abf01b172d2ce387bece913e6638824f'  # API Key TestLink
PROJECT_NAME = 'TDM365'  # имя проекта в TestLink
PLAN_NAME = 'Smoke' # имя тестплана в TestLink
BUILD_NAME = "Build_20250918_01"
#PLATFORM_NAME = "Win 10x64 - Google Chrome - PostgreSQL"

# -----------------------------
# Подключение к TestLink
# -----------------------------
tlc = TestlinkAPIClient(API_URL, DEV_KEY)

# Получаем ID тестплана
testplans = tlc.getTestPlanByName(testprojectname=PROJECT_NAME, testplanname=PLAN_NAME)
if not testplans:
    raise Exception(f'Test Plan "{PLAN_NAME}" в проекте "{PROJECT_NAME}" не найден')
plan_id = testplans[0]['id']

# -----------------------------
# Создаём имя билда: Build_YYYYMMDD_XX
# -----------------------------
# today_str = datetime.now().strftime('%Y%m%d')
# existing_builds = tlc.getBuildsForTestPlan(plan_id)
# existing_names = [b['name'] for b in existing_builds]

# Определяем порядковый номер билда
# counter = 1
# while f"{BUILD_PREFIX}_{today_str}_{counter:02}" in existing_names:
#     counter += 1
# build_name = f"{BUILD_PREFIX}_{today_str}_{counter:02}"

# Создаём билд
# tlc.createBuild(plan_id, build_name, f'Автогенерация билда Jenkins: {build_name}')
# print(f'Создан билд: {build_name}')

# -----------------------------
# Читаем pytest JUnit XML
# -----------------------------
REPORT_FILE = 'report.xml'
if not os.path.exists(REPORT_FILE):
    raise FileNotFoundError(f'{REPORT_FILE} не найден')

tree = ET.parse(REPORT_FILE)
root = tree.getroot()

# -----------------------------
# Вводим словарь соответствий имен тесткейсов в pytest и TestLink
# -----------------------------
NAME_MAP = {
    'test_TDM5': 'Создание пользователя', # pytest имя теста : TestLink имя тесткейса
    'test_TDM6': 'Создание объекта разработки',
    'test_TDM7': 'Создание проекта',
    'test_TDM8': 'Создание, наполнение пользователями и назначение групп на проекте',
    # Добавьте другие соответствия по необходимости
}

# -----------------------------
# Собираем карту external_id для всех тестов из плана
# -----------------------------
all_cases = tlc.getTestCasesForTestPlan(testplanid=plan_id)

PROJECT_PREFIX = "TDM"

case_map = {}
for tc in all_cases:
    if isinstance(tc, dict):
        external_id = f"{PROJECT_PREFIX}-{tc['tc_external_id']}"
        case_map[tc['name']] = external_id
    else:
        info_list = tlc.getTestCase(tc)
        for info in info_list:
            external_id = f"{PROJECT_PREFIX}-{info['tc_external_id']}"
            case_map[info['name']] = external_id

# -----------------------------
# Получаем список браузеров из Jenkins
# -----------------------------
BROWSERS = os.environ.get("BROWSERS", "chrome").split(",")
BROWSERS = [b.strip().lower() for b in BROWSERS]

# -----------------------------
# Формируем платформы для TestLink
# -----------------------------
BROWSER_TO_PLATFORM = {
    "chrome": "Win 10x64 - Google Chrome - PostgreSQL",
    "firefox": "Win 10x64 - Mozilla Firefox - MS SQL Server",
    "edge": "Win 10x64 - Microsoft Edge - MS SQL Server",
}

# -----------------------------
# Отправка результатов в TestLink
# -----------------------------
for browser in BROWSERS:
    platform_name = BROWSER_TO_PLATFORM.get(browser)
    if not platform_name:
        print(f"[WARNING] Неизвестный браузер: {browser}, пропускаем")
        continue

    print(f"[INFO] Отправка результатов для браузера: {browser} ({platform_name})")

    for testcase in root.findall('.//testcase'):
        func_name = testcase.get('name') or ''
        clean_name = re.sub(r"\[.*\]$", "", func_name)  # Убираем параметры в квадратных скобках
        tl_name = NAME_MAP.get(func_name)

        if not tl_name:
            print(f'Для pytest-теста "{func_name}" нет соответствия в NAME_MAP')
            continue

        tc_external_id = case_map.get(tl_name)
        if not tc_external_id:
            print(f'Тесткейc "{tl_name}" не найден в TestLink')
            continue

        # определяем статус
        if testcase.find('failure') is not None:
            status = 'f'
        elif testcase.find('error') is not None:
            status = 'b'
        elif testcase.find('skipped') is not None:
            status = 'b'
        else:
            status = 'p'

        try:
            tlc.reportTCResult(
                testcaseexternalid=tc_external_id,
                testplanid=plan_id,
                buildname=BUILD_NAME,
                status=status,
                notes=f"Автотест {func_name} выполнен через Jenkins",
                platformname=platform_name
            )
            print(f'Результат отправлен: {tl_name} -> {status}')
        except Exception as e:
            print(f'Ошибка при отправке для {tl_name}: {e}')

print('Отправка результатов завершена.')
