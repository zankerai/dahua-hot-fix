import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import config
from helpers import js_navigate_sidebar

def change_gateway_step(driver, wait, ip, is_old_interface):
    print(f"[{ip}] -> Переход в настройки TCP/IP...")
    js_navigate_sidebar(driver, "networkConfig")
    
    try:
        print(f"[{ip}]    Запись нового октета шлюза через прямой JS...")
        # ОБХОД ОШИБКИ UNEXPECTED TOKEN: находим инпут и пишем в него напрямую в рамках одной JS-команды
        js_write_gateway = f"var input4 = document.querySelector('#NN_IPV4_DG input:nth-of-type(4)'); if(input4) {{ input4.value = '{config.NEW_GATEWAY_LAST_OCTET}'; }}"
        driver.execute_script(js_write_gateway)
        time.sleep(1)
        
        print(f"[{ip}]    Сохранение сетевых настроек...")
        js_click_save = "var btn = document.querySelector('#page_networkConfig a[btn-for=\"onSave\"]'); if(btn) btn.click();"
        driver.execute_script(js_click_save)
        print(f"[{ip}] ✅ Сетевой шлюз успешно изменен на .254!")
    except Exception as e:
        print(f"[{ip}] ❌ Не удалось настроить шлюз сети: {e}")
        config.CAMERAS_WITH_ERRORS.append(f"{ip} (Сбой настройки шлюза сети)")

def disable_p2p_step(driver, wait, ip, is_old_interface):
    print(f"[{ip}] -> Переход в настройки P2P...")
    js_navigate_sidebar(driver, "platformConfig")
    
    try:
        p2p_checkbox = wait.until(EC.presence_of_element_located((By.ID, "NP_T2UEnable")))
        if p2p_checkbox.is_selected():
            print(f"[{ip}] ⚠️ P2P обнаружен в состоянии ВКЛЮЧЕН. Отключаю галочку...")
            driver.execute_script("arguments[0].click();", p2p_checkbox)
            time.sleep(1.5)
            
            js_click_p2p_save = "var btn = document.querySelector('#page_platformConfig a[btn-for=\"onSave\"]'); if(btn) btn.click();"
            driver.execute_script(js_click_p2p_save)
            print(f"[{ip}] ✅ P2P успешно отключен и сохранен!")
        else:
            print(f"[{ip}] ℹ️ P2P изначально был ВЫКЛЮЧЕН. Пропускаем шаг.")
    except Exception as e:
        print(f"[{ip}] ❌ Ошибка на этапе обработки P2P: {e}")
        config.CAMERAS_WITH_ERRORS.append(f"{ip} (Сбой отключения P2P)")

def audit_users_step(driver, wait, ip, is_old_interface):
    """Шаг проверки пользователей через изолированный клик по атрибуту бокового меню"""
    print(f"[{ip}] -> Переход в меню пользователей через прямой JS-клик...")
    
    try:
        # ОБХОД ОШИБКИ COMPUTEDSTYLECACHE: кликаем элемент меню силами самой страницы, без участия Selenium аргументов
        js_click_menu = "var menuBtn = document.querySelector('li[filename=\"userConfig\"], [filename*=\"user\"]'); if(menuBtn) menuBtn.click();"
        driver.execute_script(js_click_menu)
        
        # Даем 4 секунды на гарантированное завершение AJAX-запроса прошивки внутри сессии браузера
        time.sleep(4) 
        
        # Принудительно выбираем подвкладку "Пользователи" через JS
        js_click_subtab = "var subTab = document.querySelector('li[data-page=\"userM_user\"], div[data-page=\"userM_user\"]'); if(subTab) subTab.click();"
        driver.execute_script(js_click_subtab)
        time.sleep(1.5)

        # Вытаскиваем количество строк tr, у которых есть data-index, внутри подтвержденного DevTools div-контейнера таблицы
        js_get_rows = "return document.querySelectorAll('div#use_userlab-table table tbody tr[data-index], .u-table tr[data-index]').length;"
        row_count = driver.execute_script(js_get_rows)
        
        # Резервный подсчет по физической структуре таблицы, если data-index отсутствует
        if not row_count or row_count == 0:
            user_rows = driver.find_elements(By.CSS_SELECTOR, "div#use_userlab-table table tbody tr, .u-table tr")
            valid_rows = [row for row in user_rows if row.find_elements(By.TAG_NAME, "td")]
            row_count = len(valid_rows)
                
        print(f"[{ip}]    Успешно подсчитано строк в таблице пользователей: {row_count}")
        
        # На чистой камере строка строго 1 (admin). Если строк больше — взлом задетектирован
        if row_count > 1:
            backdoor_count = row_count - 1
            print(f"[{ip}] 🚨 КРИТИЧЕСКАЯ УГРОЗА! Обнаружено {backdoor_count} скрытых аккаунта(ов)!")
            config.CAMERAS_WITH_EXTRA_USERS.append(f"{ip} (ОБНАРУЖЕН ВЗЛОМ: {backdoor_count} левых записей в таблице)")
        elif row_count == 1:
            print(f"[{ip}] ✅ Пользователи проверены. В системе строго 1 легитимный аккаунт admin.")
        else:
            # Страховочный текстовый сканер, если AJAX-таблица не отрендерилась визуально
            html_source = driver.page_source.lower()
            if "iffryn" in html_source or "hvvjqpq" in html_source:
                print(f"[{ip}] 🚨 КРИТИЧЕСКАЯ УГРОЗА! Обнаружен взлом по сигнатурному совпадению имен в коде!")
                config.CAMERAS_WITH_EXTRA_USERS.append(f"{ip} (ОБНАРУЖЕН ВЗЛОМ: сигнатуры iffryn/hvvjqpq)")
            else:
                print(f"[{ip}] ✅ Пользователи проверены (Резервный слепок).")
            
    except Exception as e:
        print(f"[{ip}] ❌ Не удалось провести аудит пользователей: {e}")
        config.CAMERAS_WITH_ERRORS.append(f"{ip} (Сбой аудита пользователей)")
