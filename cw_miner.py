from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (NoSuchElementException,
                                        MoveTargetOutOfBoundsException,
                                        StaleElementReferenceException, TimeoutException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import time
import random
import traceback
import datetime
import os
import re


def locate(xpath: str) -> WebElement | None:
    """Найти элемент на странице по xpath. """

    try:
        element = driver.find_element(By.XPATH, xpath)
        return element
    except NoSuchElementException:
        if is_cw3_disabled():
            refresh()
            locate(xpath)
        else:
            return None


def click(xpath="xpath", offset_range=(0, 0), given_element=None) -> bool:
    """Клик по элементу element с оффсетом offset_range.
    Возвращает True, если был совершён клик по элементу. """

    if xpath != "xpath" and not given_element:
        element = locate(xpath)
    elif given_element:
        element = given_element
    else:
        return False

    if not element or not element.is_displayed():
        return False

    random_offset = (random.randint(-offset_range[0], offset_range[0]),
                     random.randint(-offset_range[1], offset_range[1]))
    try:
        action_chain = ActionChains(driver)
        action_chain.scroll_to_element(element).perform()
        action_chain.move_to_element_with_offset(to_element=element,
                                                 xoffset=random_offset[0],
                                                 yoffset=random_offset[1]
                                                 ).perform()
        action_chain.click_and_hold().perform()
        time.sleep(random.uniform(0, 0.1))
        action_chain.release().perform()
    except MoveTargetOutOfBoundsException:
        print("MoveTargetOutOfBoundsException raised for reasons unknown to man :<")
        print("random offset =", random_offset)
        return False
    return True


def crash_handler(exception_type: Exception):
    """Создать крашлог в папке crashlogs, которая находится на том же уровне, что и main.py"""

    if type(exception_type).__name__ == "KeyboardInterrupt":
        return
    now = datetime.datetime.now()
    crash_time = now.strftime("%y-%m-%d_%H.%M.%S")
    path = os.path.dirname(__file__)
    if not os.path.exists(f"{path}/crashlogs"):
        os.mkdir(f"{path}/crashlogs")
    crash_path = os.path.join(path, f"crashlogs/crash-{crash_time}.txt")
    print(f"Майнер кролей вылетел, exception: {type(exception_type).__name__}. Крашлог находится по пути {crash_path}")
    with open(crash_path, "w") as crashlog:
        stacktrace = traceback.format_exc()
        crashlog.writelines(["---CWMINER CRASHLOG---", "\n", "time: ", crash_time, "\n", stacktrace])


def refresh():
    """Перезагрузить страницу"""
    driver.refresh()
    print("Страница обновлена!")


def start_rabbit_game(games_played: int):
    driver.get("https://catwar.su/chat")
    time.sleep(random.uniform(1, 3))
    click(xpath="//a[@data-bind='openPrivateWith_form']")
    type_in_chat("Системолап", entry_xpath="//input[@id='openPrivateWith']")
    click(xpath="//*[@id='openPrivateWith_form']/p/input[2]")  # OK button

    while games_played != 5:
        rabbit_game()
        games_played += 1
        write_log(games_played)


def write_log(games_played: int):
    now = datetime.datetime.now()
    with open("log.txt", "a") as log:
        if games_played == 1:
            log.writelines([now.strftime("%d/%m/%y"), "\n"])
        log.writelines(["rabbit game #", str(games_played), " - ", now.strftime("%y-%m-%d_%H.%M.%S"), "\n"])


def read_log():
    print("Открывается локальный лог...")
    date = datetime.datetime.now().strftime("%d/%m/%y")
    is_mining_done = False

    if not os.path.exists("log.txt"):
        log = open("log.txt", "w")
        log.close()
        print("Создан новый лог кролей.")
        games_played = get_games_played()
        return games_played

    with open("log.txt", "r") as log:
        for line in log:
            if date in line:
                is_mining_done = True
    if is_mining_done:
        game_number = line.split("#")[0]
        if game_number == 5:
            print("Уже сыграно 5 игр в числа...")
            return 5

    games_played = get_games_played()
    return games_played


def get_games_played() -> int:
    driver.get("https://catwar.su/rabbit_log")
    print("Открыт лог кролей: https://catwar.su/rabbit_log...")
    rabbit_log = []
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    for i in range(4):
        timestamp = locate(xpath=f"/html/body/div[3]/div/table/tbody/tr[{2 + i}]/td[1]").text
        if locate(f"/html/body/div[3]/div/table/tbody/tr[{2 + i}]/td[2]").text != "Получение кролей за игру в числа":
            continue
        date_played = re.findall(pattern=r"(\d*-\d*-\d*)", string=timestamp)[0]
        if date_played == current_date:
            rabbit_log.append(timestamp)
        else:
            break
    print("Сегодня было сыграно игр в числа:", len(rabbit_log))
    return len(rabbit_log)


def get_last_message() -> str:
    last_message = locate(xpath="//div[@class='mess_div']/div[@class='parsed']").text
    while not bool(last_message):
        print("cant detect last message, trying again...")
        refresh()
        time.sleep(random.uniform(1, 2))
        last_message = get_last_message()

    return last_message


def rabbit_game(lower_bound=-9999999999, upper_bound=9999999999) -> bool:
    """max 35 guesses"""

    last_message = ""
    while "это" not in last_message:
        time.sleep(random.uniform(0.8, 2.5))
        guess = (upper_bound + lower_bound) // 2

        type_in_chat(text=f"/number {guess}", entry_xpath="//div[@id='mess']")
        click(xpath="//input[@id='mess_submit']")

        time.sleep(random.uniform(1.5, 3))
        last_message = get_last_message()

        if "Меньше" in last_message:
            # guess = 50, (0, 100), < 50 -> (0, 49)
            if guess - 1 in range(lower_bound, upper_bound + 1):
                upper_bound = guess - 1
            else:
                upper_bound = lower_bound
        elif "Больше" in last_message:
            # guess = 50, (0, 100), > 50 -> (51, 100)
            if guess + 1 in range(lower_bound + 1, upper_bound):
                lower_bound = guess + 1
            else:
                lower_bound = upper_bound
        elif "это" in last_message:
            print("число угадано, +4 кроля!")
            return True
        else:
            print(f"Произошла ошибка при парсинге сообщения с текстом {last_message}")
            return False

        print(last_message.split(", ")[0])
        print(f"({lower_bound}, {upper_bound}), difference = {upper_bound - lower_bound}")


def type_in_chat(text: str, entry_xpath: str):
    text = list(text)
    chatbox: WebElement = locate(entry_xpath)
    for i in range(len(text)):
        chatbox.send_keys(text[i])
        if text[i - 1] == text[i]:
            time.sleep(random.uniform(0, 0.1))
            continue
        time.sleep(random.uniform(0, 0.3))
    if len(text) < 5:
        time.sleep(random.uniform(1, 3))


print("Майнер кролей chronominer v1.0 запускается...\nПаблик ВК с обновлениями и инструкциями: "
      "https://vk.com/chronoclicker, там же и автокликер. Если что-то не работает, пишите в ЛС паблика.\n"
      "Вебдрайвер запускается...")
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")  # windows....
options.add_argument("--remote-debugging-port=9222")
options.add_argument("user-data-dir=selenium")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)
stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True)
driver.implicitly_wait(3)
print("Вебдрайвер запущен!")

try:
    games_number = read_log()
    start_rabbit_game(games_number)
    print("На сегодня кроли заработаны!")
except Exception as exception:
    crash_handler(exception)
