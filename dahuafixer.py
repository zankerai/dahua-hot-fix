from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from concurrent.futures import ThreadPoolExecutor
import time

# Импортируем наши модули
import config
from auth_step import perform_auth
from config_steps import change_gateway_step, disable_p2p_step, audit_users_step

# Консервативный стабильный режим пула
MAX_WORKERS = 4

def process_single_camera(ip, options):
    base_url = f"http://{ip}:{config.CUSTOM_PORT}"
    
    local_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=local_service, options=options)
    driver.set_page_load_timeout(15) 
    wait = WebDriverWait(driver, 12)
    
    print(f"[{ip}] --- [ПОТОК]: Запуск браузера Chrome для камеры ---")
    
    try:
        try:
            driver.get(base_url)
        except Exception:
            pass
            
        # 1. Шаг Авторизации
        is_logged_in, is_old_interface = perform_auth(driver, wait, ip)
        if not is_logged_in:
            return

        # 2. Шаг перехода во вкладку "Настройки"
        print(f"[{ip}] -> Переход во вкладку 'Настройки'...")
        if is_old_interface:
            try:
                settings_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Setup') or contains(text(), 'Настройка') or contains(text(), 'Настройки')]")))
                settings_btn.click()
            except Exception:
                driver.get(f"{base_url}/#netConfig-tcpip")
        else:
            settings_span = wait.until(EC.presence_of_element_located((By.XPATH, "//li[@data-for='set']/span[contains(text(), 'Настройки')]")))
            actions = ActionChains(driver)
            actions.move_to_element(settings_span).click().perform()
        time.sleep(5)

        # 3. Шаг настройки шлюза сети
        change_gateway_step(driver, wait, ip, is_old_interface)
        time.sleep(2)

        # 4. Шаг отключения P2P
        disable_p2p_step(driver, wait, ip, is_old_interface)
        time.sleep(2)

        # 5. ИСПРАВЛЕНО: Шаг аудита пользователей возвращен в самый конец цепочки
        audit_users_step(driver, wait, ip, is_old_interface)
        print(f"[{ip}] ✅ [ПОТОК]: Все этапы ротации параметров успешно завершены!")

    except Exception as e:
        print(f"[{ip}] ❌ [ПОТОК ERROR]: Критический сбой автоматизации: {e}")
        config.CAMERAS_WITH_ERRORS.append(f"{ip} (Критическое зависание/Сбой скрипта)")
        
    finally:
        try:
            driver.close()
        except Exception:
            pass
        driver.quit()

def main():
    print(f"--- Запуск массовой автоматизации Dahua PRO (Версия v5.7) ---\n")
    print(f" 🔥 Режим работы: {MAX_WORKERS} параллельных окон Chrome.\n")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") 
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(lambda ip: process_single_camera(ip, options), config.CAMERAS)

    # Итоговый отчет организации
    print("\n" + "="*50)
    print("               ИТОГОВЫЙ ОТЧЕТ ОБ АУДИТЕ СЕТИ               ")
    print("="*50)
    if not config.CAMERAS_WITH_EXTRA_USERS and not config.CAMERAS_WITH_ERRORS:
        print(" 🎉 Успех! На всех камерах применены настройки, отклонений не найдено.")
    if config.CAMERAS_WITH_EXTRA_USERS:
        print(f"\n ⚠️ НАЙДЕНЫ ВРЕДОНОСНЫЕ БЭКДОРЫ ({len(config.CAMERAS_WITH_EXTRA_USERS)}):")
        for cam in config.CAMERAS_WITH_EXTRA_USERS: 
            print(f"  • {cam}")
    if config.CAMERAS_WITH_ERRORS:
        print(f"\n ❌ ОШИБКИ И ПРОПУЩЕННЫЕ КАМЕРЫ ({len(config.CAMERAS_WITH_ERRORS)}):")
        for cam in config.CAMERAS_WITH_ERRORS: 
            print(f"  • {cam}")
    print("="*50)
    input("\nВся сеть успешно обработана. Нажмите Enter для завершения работы...")

if __name__ == "__main__":
    main()
