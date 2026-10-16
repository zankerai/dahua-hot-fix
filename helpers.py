import time

def js_navigate_sidebar(driver, filename):
    """Принудительно переключает вкладку бокового меню через внутреннее API Dahua"""
    js_command = f"""
    if (typeof g_menu !== 'undefined' && g_menu.changePage) {{
        g_menu.changePage('{filename}');
    }} else {{
        var targetLi = document.querySelector("#set-menu li[filename='{filename}']");
        if (targetLi) targetLi.click();
    }}
    """
    driver.execute_script(js_command)
    time.sleep(4)
