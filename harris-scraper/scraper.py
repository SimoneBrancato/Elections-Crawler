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
import requests
from PIL import Image
from io import BytesIO
import pytesseract
import uuid
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
    time.sleep(25)

def scroll_popup(element):
    driver.execute_script("arguments[0].scrollBy(0, 800);", element)
    time.sleep(10)

action = webdriver.ActionChains(driver) # To extract timestamp from tooltip

# Download image from an image_url
def download_image(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    return img

# Step 2: Apply OCR
def extract_image_text_from_post(post):
    try:
        image_url = post.find_element(By.XPATH, ".//div[@class='x10l6tqk x13vifvy']//img").get_attribute('src')
        img = download_image(image_url)
        text = pytesseract.image_to_string(img)
        return " " + text
    except Exception:
        return ""

# Extracts caption from text
def extract_caption_from_post(post):
    try:
        caption = post.find_element(By.XPATH, ".//span[@class='x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h']").get_attribute('innerText')
        return caption
    except Exception:
        return ""

# Extracts text from post if it is not been scraped 
def get_text_from_post(post):
    try:
        caption = extract_caption_from_post(post)                                        
        image_text = extract_image_text_from_post(post)
        text = caption + image_text                                        

        query = """
                SELECT COUNT(*) 
                FROM Posts 
                WHERE content LIKE %s
                AND candidate = 'Harris'
                """
        cursor.execute(query, (text,))
        count = cursor.fetchone()[0]
    except Exception:
        count = 0
        text = "NULL"

    return text, count

# Ectract timestamp from post
def get_timestamp_from_post(post):
    try:
        extracted_timestamp = post.find_element(By.XPATH, ".//span[@class='x1rg5ohu x6ikm8r x10wlt62 x16dsc37 xt0b8zv']")
        action.move_to_element(extracted_timestamp).perform()
        time.sleep(2)

        timestamp_str = WebDriverWait(post, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='xj5tmjb x1r9drvm x16aqbuh x9rzwcf xjkqk3g xms15q0 x1lliihq xo8ld3r xjpr12u xr9ek0c x86nfjv xz9dl7a xsag5q8 x1ye3gou xn6708d x1n2onr6 x19991ni __fb-dark-mode  x1hc1fzr xhb22t3 xls3em1']"))
        ).get_attribute('innerText')
        
        timestamp = datetime.strptime(timestamp_str, "%A, %B %d, %Y at %I:%M %p")
    except Exception:
        timestamp = "NULL"

    return timestamp

# Scrapes posts published in 2024 and sends to Elections DB 
def scrape_posts():
    
    inserted_timestamp = datetime.now()

    while inserted_timestamp > datetime(2024, 1, 1, 0, 0, 0):

        new_posts = WebDriverWait(driver, 50).until(
            EC.visibility_of_all_elements_located((By.XPATH, "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']"))
        )

        print(f"Retrieved {len(new_posts)} posts.")

        for new_post in new_posts:

            text, count = get_text_from_post(new_post)

            if text is None or count > 0:
                continue 

            post_uuid = str(uuid.uuid4()) # Generate UUID for current post  
            timestamp = get_timestamp_from_post(new_post)

            if timestamp is None:
                continue 

            if timestamp < datetime(2024, 1, 1, 0, 0, 0):
                print(f"### RETRIEVED VERY OLD POST {timestamp} ###")
                return

            sql_insert_post = """
                                INSERT IGNORE 
                                INTO Posts (uuid, timestamp, candidate, content)
                                VALUES (%s, %s, %s, %s)
                                """
            cursor.execute(sql_insert_post, (post_uuid, timestamp, "Harris", text))
            connection.commit()
                                
            print(f"Inserted row into Harris table. Timestamp: {timestamp}.")
            inserted_timestamp = timestamp     
            
            comments_button = new_post.find_element(By.XPATH, ".//div[@class='x1i10hfl x1qjc9v5 xjqpnuy xa49m3k xqeqjp1 x2hbi6w x1ypdohk xdl72j9 x2lah0s xe8uvvx x2lwn1j xeuugli x1hl2dhg xggy1nq x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x3nfvp2 x1q0g3np x87ps6o x1lku1pv x1a2a7pz xjyslct xjbqb8w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1heor9g xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1ja2u2z']")
            comments_button.click()
            time.sleep(5)

            post_popup = driver.find_element(By.XPATH, ".//div[@class='xb57i2i x1q594ok x5lxg6s x78zum5 xdt5ytf x6ikm8r x1ja2u2z x1pq812k x1rohswg xfk6m8 x1yqm8si xjx87ck xx8ngbg xwo3gff x1n2onr6 x1oyok0e x1odjw0f x1iyjqo2 xy5w88m']")

            inserted_comments = 0

            while inserted_comments<100:
                scroll_popup(post_popup)
                new_comments = post_popup.find_elements(By.XPATH, ".//div[@class='x1lliihq xjkvuk6 x1iorvi4']")

                for new_comment in new_comments:
                    comment_text = new_comment.text
                    query = """
                            SELECT COUNT(*) 
                            FROM Comments 
                            WHERE content LIKE %s
                            """
                    cursor.execute(query, (comment_text,))
                    count = cursor.fetchone()[0]

                    if count > 0:
                        continue

                    comment_uuid = str(uuid.uuid4())
                    sql_insert_comment = """
                                        INSERT IGNORE
                                        INTO Comments (uuid, post_id, content)
                                        VALUES(%s, %s, %s)
                                        """
                                
                    cursor.execute(sql_insert_comment, (comment_uuid, post_uuid, comment_text))
                    connection.commit()
                    inserted_comments += 1
                    time.sleep(1)

            print(f"Retrieved {inserted_comments} comments")
            close_button = driver.find_element(By.XPATH, '//div[@class="x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xzolkzo x12go9s9 x1rnf11y xprq8jg x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x78zum5 xl56j7k xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 xc9qbxq x14qfxbe x1qhmfi1"]')
            close_button.click()
        scroll_down()
        
    print("##### Scraping finished #####")
    return 

scrape_posts()

# Close the cursor and connection
cursor.close()
connection.close()