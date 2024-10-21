from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import mysql.connector
from datetime import datetime, timedelta
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

# Establish connection with Elections database
connection = mysql.connector.connect(
    host='mysql',
    port='3306', 
    user='root',  
    password='root',  
    database='Elections'  
)

cursor = connection.cursor() # To execute SQL queries

print("Connected to the database!")

# Scroll down into page
def scroll_down():
    driver.execute_script("window.scrollBy(0, 800);")
    time.sleep(30)

# Scroll down into popup element
def scroll_popup(element):
    driver.execute_script("arguments[0].scrollBy(0, 800);", element)
    time.sleep(15)

# Extracts text from image
def extract_image_text_from_post(post):
    try:
        xpath_image = ".//div[@class='x10l6tqk x13vifvy']//img"
        image_url = post.find_element(By.XPATH, xpath_image).get_attribute('src')
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        text = pytesseract.image_to_string(img)
        return text
    except Exception:
        return ""

# Extracts caption from text
def extract_caption_from_post(post):
    try:
        xpath_caption_element = ".//span[@class='x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h']"
        caption = post.find_element(By.XPATH, xpath_caption_element).get_attribute('innerText')
        return caption
    except Exception:
        return ""

# Extracts text from post if it is not been scraped 
def get_text_from_post(post):
    try:
        caption = extract_caption_from_post(post)                                        
        image_text = extract_image_text_from_post(post)
        text = f"{caption} {image_text}" if caption and image_text else caption or image_text
        return text
    except Exception:
        return None

# Returns post uuid if text is in db, else returns 0
def search_post_into_database(text):
    query = """
            SELECT uuid 
            FROM Posts 
            WHERE content LIKE %s
            AND candidate = %s
            LIMIT 1
            """
    cursor.execute(query, (text, CANDIDATE))
    result = cursor.fetchone()
    uuid = result[0] if result else 0 
    
    return uuid

# Ectract timestamp from post
def get_timestamp_from_post(post):
    try:
        xpath_timestamp = ".//span[@class='x1rg5ohu x6ikm8r x10wlt62 x16dsc37 xt0b8zv']"
        extracted_timestamp = post.find_element(By.XPATH, xpath_timestamp)
        action.move_to_element(extracted_timestamp).perform()
        time.sleep(2)

        xpath_timestamp_tooltip = "//div[@class='xj5tmjb x1r9drvm x16aqbuh x9rzwcf xjkqk3g xms15q0 x1lliihq xo8ld3r xjpr12u xr9ek0c x86nfjv xz9dl7a xsag5q8 x1ye3gou xn6708d x1n2onr6 x19991ni __fb-dark-mode  x1hc1fzr xhb22t3 xls3em1']"
        timestamp_str = WebDriverWait(post, 20).until(
            EC.presence_of_element_located((By.XPATH, xpath_timestamp_tooltip))
        ).get_attribute('innerText')
        
        timestamp = datetime.strptime(timestamp_str, "%A, %B %d, %Y at %I:%M %p")
        return timestamp
    except Exception:
        return None

def get_comment_reactions(comment_div):
    try:
        reactions = {}

        xpath_reactions_button = ".//div[@class='x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x3nfvp2 x1q0g3np x87ps6o x1lku1pv x1a2a7pz' and contains(@aria-label, 'reactions')]"
        reactions_button = comment_div.find_element(By.XPATH, xpath_reactions_button)
        reactions_button.click()

        time.sleep(5) 

        xpath_reactions_popup = "//div[@class='x1n2onr6 x1ja2u2z x1afcbsf xdt5ytf x1a2a7pz x71s49j x1qjc9v5 xrjkcco x58fqnu x1mh14rs xfkwgsy x78zum5 x1plvlek xryxfnj xcatxm7 x1n7qst7 xh8yej3']"
        reactions_popup = driver.find_element(By.XPATH, xpath_reactions_popup)

        xpath_reaction_panels = ".//div[@class='x1i10hfl xe8uvvx xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz xjyslct xjbqb8w x18o3ruo x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1heor9g x1ypdohk xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg x1vjfegm x3nfvp2 xrbpyxo x1itg65n x16dsc37']"
        reaction_panels = reactions_popup.find_elements(By.XPATH, xpath_reaction_panels)

        for panel in reaction_panels:
            reaction_str = panel.get_attribute("aria-label")
            reaction_type, reaction_count = reaction_str.replace(" ","").lower().split(',')

            if reaction_type == "all":
                continue

            reactions[reaction_type] = convert_reaction_count(reaction_count)

        xpath_close_reactions_button = ".//div[@class='x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xzolkzo x12go9s9 x1rnf11y xprq8jg x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x78zum5 xl56j7k xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 xc9qbxq x14qfxbe x1qhmfi1']"
        close_reactions_button = reactions_popup.find_element(By.XPATH, xpath_close_reactions_button)
        close_reactions_button.click()  
        time.sleep(5)
        return reactions
    
    except Exception:
    
        reactions = {
            "like": 0,
            "love": 0,
            "care": 0,
            "haha": 0,
            "wow": 0,
            "angry": 0,
            "sad": 0
        }

        return reactions
    
# Extract comments from post
def get_comments_from_post(post, post_uuid, max_comments):
    try:
        xpath_comment_button = ".//div[@class='x1i10hfl x1qjc9v5 xjqpnuy xa49m3k xqeqjp1 x2hbi6w x1ypdohk xdl72j9 x2lah0s xe8uvvx x2lwn1j xeuugli x1hl2dhg xggy1nq x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x3nfvp2 x1q0g3np x87ps6o x1lku1pv x1a2a7pz xjyslct xjbqb8w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1heor9g xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1ja2u2z']"
        comments_button = post.find_element(By.XPATH, xpath_comment_button)
        comments_button.click()
        time.sleep(5)

        xpath_post_popup = ".//div[@class='xb57i2i x1q594ok x5lxg6s x78zum5 xdt5ytf x6ikm8r x1ja2u2z x1pq812k x1rohswg xfk6m8 x1yqm8si xjx87ck xx8ngbg xwo3gff x1n2onr6 x1oyok0e x1odjw0f x1iyjqo2 xy5w88m']"
        post_popup = driver.find_element(By.XPATH, xpath_post_popup)
        
        comments_count = 0

        while comments_count < max_comments:
            scroll_popup(post_popup)

            xpath_comments = ".//div[@class='x1n2onr6 x1swvt13 x1iorvi4 x78zum5 x1q0g3np x1a2a7pz']"
            new_comments = post_popup.find_elements(By.XPATH, xpath_comments)

            for new_comment in new_comments:
                try:
                    account_name = new_comment.find_element(By.XPATH, ".//span[@class='x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x676frb x1nxh6w3 x1sibtaa x1s688f xzsf02u']").text 
                    comment_text = new_comment.find_element(By.XPATH, ".//div[@class='x1lliihq xjkvuk6 x1iorvi4']").text
                    
                    if len(comment_text) > 1000:
                        comment_text = comment_text[:999]

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
                    
                    reactions = get_comment_reactions(new_comment)

                    sql_insert_comment = """
                                    INSERT INTO Comments (uuid, post_id, account, content, `like`, love, care, haha, wow, angry, sad)
                                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """
                    
                    cursor.execute(sql_insert_comment, (
                        comment_uuid, 
                        post_uuid,
                        account_name, 
                        comment_text,
                        reactions.get("like", 0),
                        reactions.get("love", 0),
                        reactions.get("care", 0),
                        reactions.get("haha", 0),
                        reactions.get("wow", 0),        
                        reactions.get("angry", 0),
                        reactions.get("sad", 0)
                    ))

                    connection.commit()
                    comments_count += 1
                    time.sleep(1)
                except Exception:
                    continue
    except Exception:
        return

    print(f"Retrieved {comments_count} comments")
    xpath_close_comments_button = "//div[@class='x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xzolkzo x12go9s9 x1rnf11y xprq8jg x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x78zum5 xl56j7k xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 xc9qbxq x14qfxbe x1qhmfi1']"
    close_button = driver.find_element(By.XPATH, xpath_close_comments_button)
    close_button.click()

# Extracts reactions from post
def get_post_reactions(post_div):
    try:
        reactions = {}
        xpath_reactions_button = ".//div[@class='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1n2onr6 x87ps6o x1lku1pv x1a2a7pz x1heor9g xnl1qt8 x6ikm8r x10wlt62 x1vjfegm x1lliihq']"
        reactions_button = post_div.find_element(By.XPATH, xpath_reactions_button)
        reactions_button.click()

        time.sleep(5)
        
        xpath_reaction_panels = ".//div[@class='x1i10hfl xe8uvvx xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz xjyslct xjbqb8w x18o3ruo x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1heor9g x1ypdohk xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg x1vjfegm x3nfvp2 xrbpyxo x1itg65n x16dsc37']"
        reaction_panels = driver.find_elements(By.XPATH, xpath_reaction_panels)
        
        for panel in reaction_panels:
            reaction_str = panel.get_attribute("aria-label")
            reaction_type, reaction_count = reaction_str.replace(" ","").lower().split(',')

            if reaction_type == "all":
                continue
            
            reactions[reaction_type] = convert_reaction_count(reaction_count)

        xpath_close_reactions_button = ".//div[@class='x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xzolkzo x12go9s9 x1rnf11y xprq8jg x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x78zum5 xl56j7k xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 xc9qbxq x14qfxbe x1qhmfi1']"
        close_reactions_button = driver.find_element(By.XPATH, xpath_close_reactions_button)
        close_reactions_button.click()
        time.sleep(5)
        return reactions
    
    except Exception:
        reactions = {
            "like": 0,
            "love": 0,
            "care": 0,
            "haha": 0,
            "wow": 0,
            "angry": 0,
            "sad": 0
        }

        return reactions

# Convert reaction count from string format to integer
def convert_reaction_count(reaction_count):
    if 'k' in reaction_count: 
        return int(float(reaction_count.replace('k', '')) * 1000)
    elif 'm' in reaction_count:  
        return int(float(reaction_count.replace('m', '')) * 1000000)
    else:
        return int(reaction_count)

# Scrapes posts published in 2024 and sends to Elections DB 
def scrape_posts():
    
    scraped_posts_count = 0
    retrieved_timestamp = datetime.now()
    
    while scraped_posts_count < 20 and retrieved_timestamp > datetime(2024, 1, 1, 0, 0, 0):
        
        handle_login()
        xpath_post_panels = "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']"
        new_posts = driver.find_elements(By.XPATH, xpath_post_panels)
        print(f"Retrieved {len(new_posts)} posts.")

        for new_post in new_posts:
            text = get_text_from_post(new_post)
            
            if text is None:
                continue 

            if len(text) > 1000:
                text = text[:999]

            if search_post_into_database(text) != 0:
                continue

            timestamp = get_timestamp_from_post(new_post)

            if timestamp is None or (datetime.now() - timestamp) <= timedelta(hours=3):
                continue 
        
            if timestamp < datetime(2024, 1, 1, 0, 0, 0):
                print("##### Retrieved very old post: " + str(retrieved_timestamp) + " #####")
                return
            
            post_uuid = str(uuid.uuid4()) # Generate UUID for current post
            
            reactions = get_post_reactions(new_post)

            sql_insert_post = """
                                INSERT IGNORE 
                                INTO Posts (uuid, timestamp, candidate, content, `like`, love, care, haha, wow, angry, sad)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
            
            cursor.execute(sql_insert_post, (
                post_uuid, timestamp, CANDIDATE, text,
                reactions.get("like", 0),
                reactions.get("love", 0),
                reactions.get("care", 0),
                reactions.get("haha", 0),
                reactions.get("wow", 0),
                reactions.get("angry", 0),
                reactions.get("sad", 0)
            ))

            connection.commit()
                                
            print(f"Inserted row into table. Candidate: {CANDIDATE} Timestamp: {timestamp}.")
            retrieved_timestamp = timestamp
        
            print("Getting comments ...")
            get_comments_from_post(new_post, post_uuid, max_comments=100)

            scraped_posts_count += 1
            
        scroll_down()
        
    print("##### Scraping finished #####")
    
    return 

scrape_posts()

# Close the driver, cursor and connection
driver.quit()
cursor.close()
connection.close()