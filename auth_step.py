import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import config

def perform_auth(driver, wait, ip):
    """Возврат к эталонной нативной авторизации, которая успешно заходила в v2.36"""
    time.sleep(4)  
    
    is_old_interface = False
    if len(driver.find_elements(By.ID, "username")) > 0 or \
       len(driver.find_elements(By.ID, "loginbtn")) > 0 or \
       len(driver.find_elements(By.CSS_SELECTOR, "input[name='username']")) > 0:
        is_old_interface = True
        print(f"[{ip}] [Детектор]: Обнаружили классический старый веб-интерфейс Dahua.")
    else:
        print(f"[{ip}] [Детектор]: Обнаружили современный веб-интерфейс Dahua.")

    print(f"[{ip}] -> Ввод учетных данных через эталонные нативные методы...")
    try:
        if is_old_interface:
            login_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#username, input[name='username']")))
            pass_input = driver.find_element(By.CSS_SELECTOR, "#password, input[name='password']")
            login_btn = driver.find_element(By.CSS_SELECTOR, "#loginbtn, input[type='button'], .login_btn")
            
            login_input.clear()
            login_input.send_keys(config.USERNAME)
            pass_input.clear()
            pass_input.send_keys(config.PASSWORD)
            
            driver.execute_script("arguments.click();", login_btn)
        else:
            login_input = wait.until(EC.presence_of_element_located((By.ID, "login_user")))
            pass_input = driver.find_element(By.ID, "login_psw")
            login_btn = driver.find_element(By.CSS_SELECTOR, "a[btn-for='onLogin']")
            
            login_input.clear()
            login_input.send_keys(config.USERNAME)
            pass_input.clear()
            pass_input.send_keys(config.PASSWORD)
            time.sleep(1)
            
            pass_input.send_keys(Keys.ENTER)
            
    except Exception as e:
        print(f"[{ip}] ❌ Ошибка ввода данных формы: {e}")
        config.CAMERAS_WITH_ERRORS.append(f"{ip} (Элементы формы входа заблокированы)")
        return False, is_old_interface
    
    print(f"[{ip}]    Ожидание загрузки интерфейса камеры...")
    time.sleep(8)
    
    page_source = driver.page_source
    if "login_user" in page_source and ("Неверное имя" in page_source or "осталось" in page_source or "wrong" in page_source.lower()):
         print(f"[{ip}] ❌ КРИТИЧЕСКАЯ ОШИБКА: Камера отвергла пароль.")
         config.CAMERAS_WITH_ERRORS.append(f"{ip} (Ошибка авторизации / Неверный пароль)")
         return False, is_old_interface
         
    print(f"[{ip}] ✅ Вход выполнен успешно! Личный кабинет открыт.")
    return True, is_old_interface
