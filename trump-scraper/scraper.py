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
    chrome_options.add_argument("--headless=new")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1920x1080")
    chrome_options.add_argument('--disable-gpu')  
    chrome_options.add_argument('--disable-extensions') 
    chrome_options.add_argument('--incognito')  
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
FB_EMAIL_TRUMP: str = os.getenv('FB_EMAIL_TRUMP')
FB_PASSWORD_TRUMP: str = os.getenv('FB_PASSWORD_TRUMP')

# Targets email and password forms, fills them with email and password, targets submit button and clicks it
def handle_login():
    email = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
    password = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']")))
    
    email.clear()
    email.send_keys(FB_EMAIL_TRUMP)
    password.clear()
    password.send_keys(FB_PASSWORD_TRUMP)
    time.sleep(1)

    submit_button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    submit_button.click()
    print("Login completed successfully")
    
handle_login()

time.sleep(20)
driver.get("https://www.facebook.com/DonaldTrump")  
time.sleep(20)

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
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(20)

def scrape_posts():

    post_texts = set()  # Set to track scraped posts 
    
    while len(post_texts) < 100:
        scroll_down()
        time.sleep(20)  # Add a pause to load the page (Low performance, 20s to be sure)
        
        # Search for new posts
        new_posts = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='x1l90r2v x1pi30zi x1swvt13 x1iorvi4']"))
        )

        new_texts = []  # To memorize new text in each round

        for new_post in new_posts:
            text = new_post.text.strip()
            
            # Add text only if it is at least 5 characters long and if it has not already been seen
            if len(text)>=5 and text not in post_texts:    
                    new_texts.append((text,))
                    post_texts.add(text) 

        # If there are new texts add them to the DB
        if new_texts:
            sql_insert_query = """INSERT IGNORE INTO Trump (content) VALUES (%s)"""
            cursor.executemany(sql_insert_query, new_texts)
            connection.commit()
            print(f"Inserted {len(new_texts)} values into Trump table.")
        else:
            print("No new posts found.")
    
    return post_texts

posts = scrape_posts()

print(f"Retrieved {len(posts)} posts.")

# Close the cursor and connection
cursor.close()
connection.close()