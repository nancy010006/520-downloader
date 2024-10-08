import subprocess
import re
import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
import concurrent.futures

# 設置Chrome驅動程式選項
def get_driver_options():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('start-maximized')
    options.add_argument('disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--lang=zh-CN')
    options.add_argument('--log-level=3')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
    options.add_argument('--referer=https://www.520cc.cc/')
    options.add_argument('--disable-site-isolation-trials')
    options.add_argument('--ignore-ssl-errors')  # 禁用SSL錯誤檢查
    return options

# 使用youtube-dl下載m3u8文件
def download_m3u8(base_file_name, m3u8_list):
    # 確保 downloads 資料夾存在
    downloads_dir = os.path.join(os.getcwd(), 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    
    print(m3u8_list)
    for index, m3u8 in enumerate(m3u8_list):
        filename = os.path.join(downloads_dir, base_file_name + str(index + 1))
        cmd = 'START cmd.exe /k "youtube-dl --no-check-certificate --all-subs -f mp4 -o \"{filename}.mp4\" {m3u8} && exit"'.format(filename=filename, m3u8=m3u8)
        subprocess.call(cmd, shell=True)

# 從iframe中獲取m3u8鏈接
def get_m3u8_links(driver):
    m3u8List = []
    iframes = driver.find_elements(By.XPATH, "//iframe[starts-with(@id, 'allmyplayer')]")
    print('iframes',iframes)
    for iframe in iframes:
        driver.switch_to.frame(iframe)
        try:
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'video')))
            source = driver.find_element(By.TAG_NAME, 'source')
            src = source.get_attribute('src')
            m3u8List.append(src)
            driver.switch_to.default_content()
        except NoSuchElementException:
            continue
    return m3u8List

# 設置請求的headers
def get_headers():
    headers = {
        'Cookie': '填入登入網站後的 cookie'
    }
    return headers

# 獲取要下載文件的基本文件名
def get_base_file_name(driver):
    subject_element = driver.find_element(By.ID, 'thread_subject')
    subject_text = subject_element.text
    cleaned_subject_text = re.sub('[^\w\d]+', '-', subject_text)
    base_file_name = cleaned_subject_text
    return base_file_name

def process_url(url):
    # 獲取Chrome驅動程式選項和headers
    options = get_driver_options()
    headers = get_headers()

    # 使用Chrome瀏覽器
    try:
        chrome_driver_path = ChromeDriverManager().install()
        print(f"原始 ChromeDriver 路徑: {chrome_driver_path}")
        
        # 修正 ChromeDriver 路徑
        if 'chromedriver-win32' in chrome_driver_path:
            chrome_driver_path = os.path.join(os.path.dirname(chrome_driver_path), 'chromedriver.exe')
        
        print(f"修正後的 ChromeDriver 路徑: {chrome_driver_path}")
        print(f"ChromeDriver 是否存在: {os.path.exists(chrome_driver_path)}")
        
        if not os.path.exists(chrome_driver_path):
            raise FileNotFoundError(f"ChromeDriver 不存在於路徑: {chrome_driver_path}")
        
        service = Service(chrome_driver_path)
        with webdriver.Chrome(service=service, options=options) as driver:
            # 設置cookie
            driver.get(url)
            for cookie_str in headers['Cookie'].split(';'):
                name, value = cookie_str.strip().split('=')
                driver.add_cookie({'name': name, 'value': value})

            driver.get(url)

            # 獲取要下載文件的基本文件名
            base_file_name = get_base_file_name(driver)

            # 從iframe中獲取m3u8鏈接
            m3u8_list = get_m3u8_links(driver)

            print('開始下載' + base_file_name)
            # 使用youtube-dl下載m3u8文件
            download_m3u8(base_file_name, m3u8_list)
    except Exception as e:
        print(f"發生錯誤：{e}")
        print(f"錯誤類型：{type(e).__name__}")
        import traceback
        print(traceback.format_exc())
        

def main():
    # 檢查 Chrome 版本
    try:
        chrome_version = subprocess.check_output(["reg", "query", "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon", "/v", "version"]).decode()
        chrome_version = chrome_version.strip().split()[-1]
        print(f"Chrome 版本: {chrome_version}")
    except:
        print("無法檢測 Chrome 版本")
    # 讀取URL列表
    urls = []
    with open('520.txt', 'r') as f:
        urls = f.read().splitlines()

        # 同時處理多個URL
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(process_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as e:
                print(f"URL {url} 發生錯誤：{e}")

main()