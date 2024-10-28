from datetime import datetime
from selenium import webdriver
from typing import Set
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import os

def setup_driver():
    chrome_options = Options()  
    chrome_options.add_argument("--headless=new")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1920x1080")
    chrome_options.add_argument('--disable-gpu')  
    chrome_options.add_argument('--disable-extensions') 
    chrome_options.add_argument('--incognito')
    chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications" : 2})
    chrome_options.add_argument("--disable-search-engine-choice-screen")
    chrome_options.add_argument("--lang=en")
    chrome_options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--force-device-scale-factor=0.75")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

driver = setup_driver()
driver.maximize_window()
driver.get("http://www.facebook.com")
action = webdriver.ActionChains(driver)

# Accepts all cookies pop-up
def handle_cookie():
    try:
        xpath_accept_cookies = '//div[@aria-label="Allow all cookies" and @class="x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3"]'
        accept_cookies_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH , xpath_accept_cookies)))
        accept_cookies_button.click()
        print("Allowed all cookies on Facebook")
    except Exception:
        pass

handle_cookie()

LOGSTASH_URL: str = "http://logstash-fb:9700"
FB_EMAIL: str = os.getenv('FB_EMAIL')
FB_PASSWORD: str = os.getenv('FB_PASSWORD')
CANDIDATE: str = os.getenv('CANDIDATE')

# Targets email and password forms, fills them with email and password, targets submit button and clicks it
def handle_login():
    try:
        email = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
        password = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']")))
        
        email.clear()
        email.send_keys(FB_EMAIL)
        password.clear()
        password.send_keys(FB_PASSWORD)
        time.sleep(1)

        submit_button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        submit_button.click()
        print("Login completed successfully")
    except Exception:
        return
    
handle_login()

# Pause to load homepage, then go to profile and wait again
time.sleep(20)
driver.get(f"http://www.facebook.com/{CANDIDATE}")
time.sleep(20)


# Scroll down into page
def scroll_down():
    driver.execute_script("window.scrollBy(0, 800);")
    time.sleep(30)

def retrieve_links(max_links) -> Set[str]:
    links = set()

    while len(links) < max_links:
        xpath_post_panels = "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']"
        new_posts = driver.find_elements(By.XPATH, xpath_post_panels)
        print(f"Retrieved {len(new_posts)} posts div.")

        for new_post in new_posts:
            try:
                xpath_post_link = ".//div[@class='xabvvm4 xeyy32k x1ia1hqs x1a2w583 x6ikm8r x10wlt62']//a[@class='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1sur9pj xkrqix3 xi81zsa x1s688f']"
                post_link = new_post.find_element(By.XPATH, xpath_post_link).get_attribute('href')
                
                if post_link in links:
                    continue
                
                if "post" not in post_link:
                    continue

                idx = post_link.find('?')
                base_url = post_link[:idx] if idx != -1 else post_link
                retrieving_time = datetime.now()
                
                print(f"Sending link to Logstash | Retrieving time: {retrieving_time} | Candidate: {CANDIDATE}")

                data = {
                    'candidate': CANDIDATE,
                    'link': base_url
                }

                requests.post(LOGSTASH_URL, json=data)
                links.add(post_link)
                
            except Exception:
                continue

        scroll_down()
        
links = retrieve_links(max_links=15)














# Close the driver, cursor and connection
driver.quit()
