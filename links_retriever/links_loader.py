from datetime import datetime, timedelta
from selenium import webdriver
from typing import Set
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import mysql.connector
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

FB_EMAIL: str = os.getenv('FB_EMAIL')
FB_PASSWORD: str = os.getenv('FB_PASSWORD')
CANDIDATE: str = os.getenv('CANDIDATE')

# Establish connection with Elections database
connection = mysql.connector.connect(
    host='mysql',
    port='3306', 
    user='root',  
    password='root',  
    database='Elections'  
)

print("Connected to the database!")
cursor = connection.cursor() # To execute SQL queries

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

# Ectracts timestamp from post
def get_timestamp_from_post(post):
    try:
        
        xpath_timestamp = ".//div[@class='html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1q0g3np']//span[@class='x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j']"
        extracted_timestamp = post.find_element(By.XPATH, xpath_timestamp)
        action.move_to_element(extracted_timestamp).perform()
        time.sleep(5)
                              
        xpath_timestamp_tooltip = "//div[@class='xj5tmjb x1r9drvm x16aqbuh x9rzwcf xjkqk3g x972fbf xcfux6l x1qhh985 xm0m39n xms15q0 x1lliihq xo8ld3r x86nfjv xz9dl7a xsag5q8 x1ye3gou xn6708d x1n2onr6 x19991ni __fb-dark-mode  x1hc1fzr xhb22t3 xls3em1']"
        timestamp_str = driver.find_element(By.XPATH, xpath_timestamp_tooltip).get_attribute('innerText')

        timestamp = datetime.strptime(timestamp_str, "%A, %B %d, %Y at %I:%M %p")
        return timestamp
    except Exception:
        return None
    
def retrieve_links():
    retrieved_timestamp = datetime.now()
    links = set()

    sql_max_timestamp = """
                        SELECT MAX(timestamp)
                        FROM Links
                        WHERE candidate = %s
                        """
    cursor.execute(sql_max_timestamp, (CANDIDATE,))
    max_timestamp = cursor.fetchone()[0]

    if max_timestamp is None:
        max_timestamp = datetime.now() - timedelta(days=2)
        
    print(f"Fetching until {max_timestamp}")

    while retrieved_timestamp > max_timestamp:
        xpath_post_panels = "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']"
        new_posts = driver.find_elements(By.XPATH, xpath_post_panels)
        
        for new_post in new_posts:
            try:
                xpath_post_link = ".//div[@class='xabvvm4 xeyy32k x1ia1hqs x1a2w583 x6ikm8r x10wlt62']//a[@class='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1sur9pj xkrqix3 xi81zsa x1s688f']"
                post_link = new_post.find_element(By.XPATH, xpath_post_link).get_attribute('href')
                
                if post_link in links:
                    continue
                
                if "/posts/" not in post_link:
                    continue

                idx = post_link.find('?')
                base_url = post_link[:idx] if idx != -1 else post_link

                timestamp = get_timestamp_from_post(new_post)
                
                if timestamp is None:
                    continue
                
                retrieved_timestamp = timestamp 

                if timestamp < max_timestamp:
                    break

                sql_insert_link = """
                                INSERT IGNORE
                                INTO Links (timestamp, candidate, post_link)
                                VALUES (%s, %s, %s)
                                """
                cursor.execute(sql_insert_link, (timestamp, CANDIDATE, base_url))
                connection.commit()

                links.add(post_link)
                
            except Exception :
                continue

            print(f"Inserted link into database | Post timestamp: {timestamp} | Candidate: {CANDIDATE}")

        scroll_down()
        
retrieve_links()

# Close the driver, cursor and connection
driver.quit()
