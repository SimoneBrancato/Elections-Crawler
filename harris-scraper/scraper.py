from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import mysql.connector
from datetime import datetime
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

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

driver = setup_driver()
driver.maximize_window()
driver.get("http://www.facebook.com")

# Accepts all cookies pop-up
def handle_cookie():
    accept_cookies_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH , '//div[@aria-label="Allow all cookies" and @class="x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3"]')))
    accept_cookies_button.click()
    print("Allowed all cookies on Facebook")

handle_cookie()

load_dotenv('.env')
FB_EMAIL_HARRIS: str = os.getenv('FB_EMAIL_HARRIS')
FB_PASSWORD_HARRIS: str = os.getenv('FB_PASSWORD_HARRIS')

# Targets email and password forms, fills them with email and password, targets submit button and clicks it
def handle_login():
    email = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
    password = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']")))
    
    email.clear()
    email.send_keys(FB_EMAIL_HARRIS)
    password.clear()
    password.send_keys(FB_PASSWORD_HARRIS)
    time.sleep(1)

    submit_button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    submit_button.click()
    print("Login completed successfully")
    
handle_login()

# Pause to load homepage, then go to Harris profile and wait again
time.sleep(20)
driver.get("http://www.facebook.com/KamalaHarris")
time.sleep(20)

# Establish connection with Elections database
connection = mysql.connector.connect(
    host='mysql',
    port='3306', 
    user='root',  
    password='root',  
    database='Elections'  
)

print("Connected to the database!")

# Cursor to execute SQL queries
cursor = connection.cursor()

def scroll_down():
    driver.execute_script("window.scrollBy(0, 800);")
    time.sleep(20)

# Parses FB timestamp format to datetime format
def parse_timestamp_to_datetime(timestamp):
    current_timestamp_format = "%A, %B %d, %Y at %I:%M %p"

    try:
        dt_object = datetime.strptime(timestamp, current_timestamp_format)
        mysql_datetime = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        mysql_datetime = "2020-01-01 12:00:00"

    return mysql_datetime


action = webdriver.ActionChains(driver) # To extract timestamp from tooltip

# Scrapes the first 100 posts, extracting timestamp and text
def scrape_posts():
    posts_txt = set()  # Set to track scraped posts 
    
    while len(posts_txt) < 100:
        
        time.sleep(30)  # Add a long pause to load the page due to low performances

        # Search for new posts
        new_posts = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']"))
        )

        print(f"Retrieved {len(new_posts)} posts.")

        for new_post in new_posts:
            timestamp_str = "NULL"
            text = "NULL"

            try:                                        
                text = new_post.find_element(By.XPATH, ".//span[@class='x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h']").get_attribute('innerText')
            except Exception:
                print("#### SKIPPING CURRENT POST ####")

            if text != "NULL" and text not in posts_txt:
                try:
                    extracted_timestamp = new_post.find_element(By.XPATH, ".//span[@class='x1rg5ohu x6ikm8r x10wlt62 x16dsc37 xt0b8zv']")
                    action.move_to_element(extracted_timestamp).perform()
                    time.sleep(5)

                    timestamp_str = WebDriverWait(new_post, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@class='xj5tmjb x1r9drvm x16aqbuh x9rzwcf xjkqk3g xms15q0 x1lliihq xo8ld3r xjpr12u xr9ek0c x86nfjv xz9dl7a xsag5q8 x1ye3gou xn6708d x1n2onr6 x19991ni __fb-dark-mode  x1hc1fzr xhb22t3 xls3em1']"))
                    ).get_attribute('innerText')

                except Exception:
                    pass

                if timestamp_str != "NULL":
                    timestamp = parse_timestamp_to_datetime(timestamp_str)
                    posts_txt.add(text)

                    sql_insert_query = """INSERT IGNORE INTO Harris (timestamp,content) VALUES (%s, %s)"""
                    cursor.execute(sql_insert_query, (timestamp,text))
                    connection.commit()

                    print("Inserted row into Harris table.")

        scroll_down()

    return posts_txt

posts = scrape_posts()

print(f"Retrieved {len(posts)} posts.")

# Close the cursor and connection
cursor.close()
connection.close()