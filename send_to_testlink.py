import os
import xml.etree.ElementTree as ET
from datetime import datetime
from testlink import TestlinkAPIClient

# -----------------------------
# Настройки TestLink
# -----------------------------
API_URL = 'http://10.19.10.112/Testlink/lib/api/xmlrpc.php'  # URL TestLink (Именно ссылка на API)
DEV_KEY = 'abf01b172d2ce387bece913e6638824f'  # API Key TestLink
PROJECT_NAME = 'TDM365'  # имя проекта в TestLink
PLAN_NAME = 'Smoke' # имя тестплана в TestLink
BUILD_NAME = "Build_20250916_01"
PLATFORM_NAME = "Win 10x64 - Google Chrome - PostgreSQL"

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
    'test_TDM6': 'Создание объекта разработки',  # pytest имя теста : TestLink имя тесткейса
    # Добавьте другие соответствия по необходимости
}

# -----------------------------
# Получаем все тесткейсы проекта один раз
# -----------------------------
all_cases = tlc.getTestCasesForTestPlan(plan_id)
case_map = {tc['name']: tc['id'] for tc in all_cases}

# -----------------------------
# Отправка результатов в TestLink
# -----------------------------
for testcase in root.findall('.//testcase'):
    file_name = testcase.get('file') or ''
    func_name = testcase.get('name') or ''

    # Определяем имя тесткейса для TestLink
    tl_name = NAME_MAP.get(func_name, file_name.split('/')[-1].replace('.py',''))

    # формируем ключ для маппинга
    # key = func_name
    # if key in NAME_MAP:
    #     tl_name = NAME_MAP[key]
    # else:
    #     # если не нашли — пробуем взять имя файла
    #     tl_name = file_name.split('/')[-1].replace('.py', '')

    # определяем статус
    if testcase.find('failure') is not None:
        status = 'f'
    elif testcase.find('error') is not None:
        status = 'b'
    elif testcase.find('skipped') is not None:
        status = 'b'
    else:
        status = 'p'

    #try:
    # Получаем ID тест-кейса
        # tc_info = tlc.getTestCaseIDByName(tl_name, projectname=PROJECT_NAME)
        # if not tc_info:
        #     print(f'Тесткейc "{tl_name}" не найден в TestLink')
        #     continue
        # tc_id = tc_info[0]['id']
        # print(tc_info)

    # Получаем ID тест-кейса
    tc_id = case_map.get(tl_name)
    if not tc_id:
        print(f'Тесткейc "{tl_name}" не найден в TestLink')
        continue        

    # Получаем ID тест-плана
        # plan = tlc.getTestPlanByName(PROJECT_NAME, PLAN_NAME)
        # if not plan:
        #     print(f'Тест-план "{PLAN_NAME}" не найден в TestLink')
        #     continue
        # plan_id = plan[0]['id']
        # print(plan)

    # Отправляем результат
    try:
        tlc.reportTCResult(
            testcaseid=tc_id,
            testplanid=plan_id,
            buildname=BUILD_NAME,
            status=status,
            notes="Автотест выполнен через Jenkins",
            platformname=PLATFORM_NAME
        )
        print(f'Результат отправлен: {tl_name} -> {status}')
    except Exception as e:
        print(f'Ошибка при отправке для {tl_name}: {e}')

print('Отправка результатов завершена.')
