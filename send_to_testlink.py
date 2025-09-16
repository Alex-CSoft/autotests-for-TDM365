import os
import xml.etree.ElementTree as ET
from datetime import datetime
from testlink import TestlinkAPIClient

# -----------------------------
# Настройки TestLink
# -----------------------------
API_URL = 'http://10.19.10.112/Testlink/lib/api/xmlrpc.php'  # URL TestLink (Именно ссылка на API)
DEV_KEY = '55fe2c4903ae7b14b5a6c1d150bf7d14'  # API Key TestLink
PROJECT_NAME = 'TDM365'  # имя проекта в TestLink
PLAN_NAME = 'Smoke' # имя тестплана в TestLink
BUILD_PREFIX = 'Build' # префикс для имени билда

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
today_str = datetime.now().strftime('%Y%m%d')
existing_builds = tlc.getBuildsForTestPlan(plan_id)
existing_names = [b['name'] for b in existing_builds]

# Определяем порядковый номер билда
counter = 1
while f"{BUILD_PREFIX}_{today_str}_{counter:02}" in existing_names:
    counter += 1
build_name = f"{BUILD_PREFIX}_{today_str}_{counter:02}"

# Создаём билд
# tlc.createBuild(plan_id, build_name, f'Автогенерация билда Jenkins: {build_name}')
# print(f'Создан билд: {build_name}')

# -----------------------------
# Читаем pytest JUnit XML
# -----------------------------
REPORT_FILE = 'report.xml'  # путь к pytest --junitxml=report.xml
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
# Отправка результатов в TestLink
# -----------------------------
for testcase in root.findall('.//testcase'):
    # берем имя файла и имя функции
    file_name = testcase.get('file') or ''
    func_name = testcase.get('name') or ''

    # формируем ключ для маппинга
    key = func_name
    if key in NAME_MAP:
        tl_name = NAME_MAP[key]
    else:
        # если не нашли — пробуем взять имя файла
        tl_name = file_name.split('/')[-1].replace('.py', '')

    # определяем статус
    if testcase.find('failure') is not None:
        status = 'f'
    elif testcase.find('error') is not None:
        status = 'b'
    elif testcase.find('skipped') is not None:
        status = 'b'
    else:
        status = 'p'

    # получаем ID тесткейса и отправляем
    try:
        tc_info = tlc.getTestCaseIDByName(tl_name, projectname=PROJECT_NAME)
        if not tc_info:
            print(f'Тесткейc "{tl_name}" не найден в TestLink')
            continue
        tc_id = tc_info[0]['id']
    
        # Отправляем результат
        tlc.reportTCResult(tc_id, PLAN_NAME, buildname=build_name, status=status)
        print(f'Результат отправлен: {tl_name} -> {status}')
    except Exception as e:
        print(f'Ошибка при отправке для {tl_name}: {e}')


print('Отправка результатов завершена.')
