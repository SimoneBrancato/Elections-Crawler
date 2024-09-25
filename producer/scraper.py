from dotenv import load_dotenv
from selenium import webdriver
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
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
    return driver

driver = setup_driver()

# Search for Facebook Login
driver.get("http://www.facebook.com")

# Handle cookie pop-up
def handle_cookie():
    accept_cookies_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH , '//div[@aria-label="Allow all cookies" and @class="x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3"]')))
    accept_cookies_button.click()
    print("Allowed all cookies on Facebook")
handle_cookie()

load_dotenv('.env')
FB_EMAIL: str = os.getenv('FB_EMAIL')
FB_PASSWORD: str = os.getenv('FB_PASSWORD')

print(FB_PASSWORD)
print(FB_EMAIL)

def handle_login():
    
    # Target email and password forms
    email = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
    password = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']")))

    # Enter email and password
    email.clear()
    email.send_keys(FB_EMAIL)
    password.clear()
    password.send_keys(FB_PASSWORD)
    time.sleep(1)

    submit_button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    submit_button.click()
    print("Login completed successfully")
    
handle_login()



def scroll_down():
    driver.execute_script("window.scrollBy(0, 800);")
    time.sleep(10)

driver.get("http://www.facebook.com/KamalaHarris")


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

def scrape_posts():
    post_texts = []
    count = 0

    while count<20:
        scroll_down()
        new_posts = driver.find_elements(By.XPATH, "//div[@class='x1l90r2v x1pi30zi x1swvt13 x1iorvi4']")
        for new_post in new_posts:
            text = new_post.text
            if text not in post_texts and text is not None:
                post_texts.append((text,))

        sql_insert_query = """INSERT IGNORE INTO Harris (content) VALUES (%s)"""
        value = post_texts
        cursor.executemany(sql_insert_query, value)

        print("Inserted values into Harris table.")
        count += 1

    return post_texts

posts = scrape_posts()
print(f"Retrieved {len(posts)} posts.")

# Close the cursor and connection
cursor.close()
connection.close()