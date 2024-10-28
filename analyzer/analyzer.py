import json
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging
from selenium.webdriver.remote.remote_connection import LOGGER
import mysql.connector
from datetime import datetime, timedelta
import requests
from PIL import Image
from io import BytesIO
import pytesseract
import pandas as pd
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
    chrome_options.add_argument("--log-level=3")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

FB_EMAIL: str = os.getenv('FB_EMAIL')
FB_PASSWORD: str = os.getenv('FB_PASSWORD')
CANDIDATE: str = os.getenv('CANDIDATE')
MAX_COMMENTS: int = int(os.getenv('MAX_COMMENTS'))
LOGGER.setLevel(logging.ERROR)

# Targets email and password forms, fills them with email and password, targets submit button and clicks it
def handle_login(driver: WebDriver):
    try:
        
        xpath_email_form = "//input[@name='email' and @class='x1i10hfl xggy1nq x1s07b3s x1kdt53j x1a2a7pz xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x9f619 xzsf02u x1uxerd5 x1fcty0u x132q4wb x1a8lsjc x1pi30zi x1swvt13 x9desvi xh8yej3 x15h3p50 x10emqs4']"
        email = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_email_form)))

        xpath_pass_form = "//input[@name='pass' and @class='x1i10hfl xggy1nq x1s07b3s x1kdt53j x1a2a7pz xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x9f619 xzsf02u x1uxerd5 x1fcty0u x132q4wb x1a8lsjc x1pi30zi x1swvt13 x9desvi xh8yej3 x15h3p50 x10emqs4']"
        password = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_pass_form)))
        
        email.clear()
        password.clear()
        email.send_keys(FB_EMAIL)
        password.send_keys(FB_PASSWORD)

        time.sleep(3)

        
        xpath_submit_button = "//div[@class='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3']"
        submit_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath_submit_button)))
        submit_button.click()
        print("Login completed successfully.")
    except Exception:
        print("WARNING: Login handler not successfull.")
        pass
    

# Accepts all cookies pop-up
def handle_cookie(driver):
    try:
        xpath_accept_cookies = '//div[@aria-label="Allow all cookies" and @class="x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3"]'
        accept_cookies_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH , xpath_accept_cookies)))
        accept_cookies_button.click()
        print("Allowed all cookies.")
    except Exception:
        print("WARNING: Cookie handler not successfull.")
        pass

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

def scroll_down(driver, element):
    
    initial_position = driver.execute_script("return arguments[0].scrollTop;", element)
    
    driver.execute_script("arguments[0].scrollBy(0, 800);", element)
    time.sleep(2)  

    new_position = driver.execute_script("return arguments[0].scrollTop;", element)
        
    # If scroll was ineffective, scroll the main page instead
    if new_position == initial_position:
        initial_position = driver.execute_script("return window.pageYOffset;")
        driver.execute_script("window.scrollBy(0, 800);")
        new_position = driver.execute_script("return window.pageYOffset;")

    # Check if scrolling was still ineffective after the fallback
    if new_position == initial_position:
        return -1  # Return -1 if it continues to not scroll

    time.sleep(20)

    return 0

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

# Ectracts timestamp from post
def get_timestamp_from_post(post, driver, action):
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

# Extracts reactions from a comment
def get_comment_reactions(comment_div, driver):
    try:
        reactions = {}

        xpath_reactions_button = ".//div[@class='x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x3nfvp2 x1q0g3np x87ps6o x1lku1pv x1a2a7pz' and contains(@aria-label, 'reactions')]"
        reactions_button = comment_div.find_element(By.XPATH, xpath_reactions_button)
        reactions_button.click()

        time.sleep(2) 

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
        time.sleep(2)
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
    
# Extracts comment id from comment
def extract_comment_id(comment):
    xpath_comment_href = ".//div[@class='html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd']//a"
    href_element = comment.find_element(By.XPATH, xpath_comment_href)
    href = href_element.get_attribute("href")
    
    if 'comment_id=' in href:
        comment_id = href.split('comment_id=')[1].split('&')[0]
        return comment_id 

def get_timestamp_from_comment(comment, action):
    try:
        xpath_timestamp = ".//a[@class='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1sur9pj xkrqix3 xi81zsa x1s688f']"
        extracted_timestamp = comment.find_element(By.XPATH, xpath_timestamp)
        action.move_to_element(extracted_timestamp).perform()
        time.sleep(5)
                                                
        xpath_timestamp_tooltip = "//div[@class='xj5tmjb x1r9drvm x16aqbuh x9rzwcf xjkqk3g x972fbf xcfux6l x1qhh985 xm0m39n xms15q0 x1lliihq xo8ld3r x86nfjv xz9dl7a xsag5q8 x1ye3gou xn6708d x1n2onr6 x19991ni __fb-dark-mode  x1hc1fzr xhb22t3 xls3em1']"
        timestamp_str = WebDriverWait(comment, 20).until(
            EC.presence_of_element_located((By.XPATH, xpath_timestamp_tooltip))
        ).get_attribute('innerText')
        
        timestamp = datetime.strptime(timestamp_str, "%A, %B %d, %Y at %I:%M %p")
        return timestamp
    except Exception:
        return None

# Extract comments from post
def get_comments_from_post(post, post_id, driver, action, max_comments) -> bool:
    try:
        print("Getting comments...")   

        comments_set = set()
        errors_count = 0

        while len(comments_set) < max_comments:

            if errors_count > 30:
                break

            scroll_check = scroll_down(driver, post)

            if scroll_check == -1:
                errors_count += 1
            
            xpath_comments = ".//div[@class='x1n2onr6 x1swvt13 x1iorvi4 x78zum5 x1q0g3np x1a2a7pz']"
            new_comments = post.find_elements(By.XPATH, xpath_comments)

            for new_comment in new_comments:
                try:
                    
                    comment_id = extract_comment_id(new_comment)
                    account_name = new_comment.find_element(By.XPATH, ".//span[@class='x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x676frb x1nxh6w3 x1sibtaa x1s688f xzsf02u']").text            
                    comment_text = new_comment.find_element(By.XPATH, ".//div[@class='x1lliihq xjkvuk6 x1iorvi4']").text

                    if comment_text in comments_set:
                        continue

                    comments_set.add(comment_text)

                    timestamp = get_timestamp_from_comment(new_comment, action)

                    if timestamp is None:
                        continue

                    retrieving_time = datetime.now()

                    if len(comment_text) > 1000:
                        comment_text = comment_text[:999]

                    reactions = get_comment_reactions(new_comment, driver)

                    sql_insert_comment = """
                                    INSERT IGNORE 
                                    INTO Comments (uuid, post_id, retrieving_time, timestamp, account, content, `like`, love, care, haha, wow, angry, sad)
                                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """

                    cursor.execute(sql_insert_comment, (
                        comment_id, post_id, retrieving_time, timestamp, account_name, comment_text,
                        reactions.get("like", 0),
                        reactions.get("love", 0),
                        reactions.get("care", 0),
                        reactions.get("haha", 0),
                        reactions.get("wow", 0),        
                        reactions.get("angry", 0),
                        reactions.get("sad", 0)
                    ))

                    time.sleep(1)

                except Exception:
                    continue

        print(f"Retrieved {len(comments_set)} comments.")

        if len(comments_set) < max_comments-30:
            print("### THROTTLING DETECTED | Restarting scraping in 60 minutes ###")
            driver.quit()
            time.sleep(3600)
            return False

        connection.commit()
        return True
    
    except Exception:
        return False

# Extracts reactions from post
def get_post_reactions(post_div, driver):
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

        xpath_close_reactions_button = "//div[@class='x1n2onr6 x1ja2u2z x1afcbsf xdt5ytf x1a2a7pz x71s49j x1qjc9v5 xrjkcco x58fqnu x1mh14rs xfkwgsy x78zum5 x1plvlek xryxfnj xcatxm7 x1n7qst7 xh8yej3']//div[@class='x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xzolkzo x12go9s9 x1rnf11y xprq8jg x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x78zum5 xl56j7k xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 xc9qbxq x14qfxbe x1qhmfi1']"
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

# Extracts the post id from url
def extract_post_id(fb_url):
    start_index = fb_url.find('/posts/') + len('/posts/')
    post_id = fb_url[start_index:]
    return post_id

# Entirely scrapes a post by url. Assumes that the driver is already in the page
def scrape_post(url, driver, action) -> bool:
    try:
        time.sleep(15)
        handle_cookie(driver)
        handle_login(driver)
        time.sleep(15)

        try:
            xpath_post_popup = "//div[@class='xb57i2i x1q594ok x5lxg6s x78zum5 xdt5ytf x6ikm8r x1ja2u2z x1pq812k x1rohswg xfk6m8 x1yqm8si xjx87ck xx8ngbg xwo3gff x1n2onr6 x1oyok0e x1odjw0f x1iyjqo2 xy5w88m']"
            post_popup = driver.find_element(By.XPATH, xpath_post_popup)
        except Exception:
            xpath_post_div = "//div[@class='x1n2onr6 x1ja2u2z x1jx94hy x1qpq9i9 xdney7k xu5ydu1 xt3gfkd x9f619 xh8yej3 x6ikm8r x10wlt62 xquyuld']"
            post_popup = driver.find_element(By.XPATH, xpath_post_div)

        post_id = extract_post_id(url)

        retrieving_time = datetime.now()

        timestamp = get_timestamp_from_post(post_popup, driver, action)

        if timestamp is None or timestamp < datetime(2024, 1, 1, 0, 0, 0) or timestamp > retrieving_time - timedelta(hours=3):
            return

        text = get_text_from_post(post_popup)

        if text is None:
            return
        
        reactions = get_post_reactions(post_popup, driver)

        sql_insert_post = """
                        INSERT IGNORE 
                        INTO Posts (uuid, retrieving_time, timestamp, candidate, content, `like`, love, care, haha, wow, angry, sad)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """

        cursor.execute(sql_insert_post, (
            post_id, retrieving_time, timestamp, CANDIDATE, text,
            reactions.get("like", 0),
            reactions.get("love", 0),
            reactions.get("care", 0),
            reactions.get("haha", 0),
            reactions.get("wow", 0),
            reactions.get("angry", 0),
            reactions.get("sad", 0)
        ))

        connection.commit()
                            
        print(f"Inserted post. Retrieving time: {retrieving_time} | Post timestamp: {timestamp} | Candidate: {CANDIDATE}")
        is_successful = get_comments_from_post(post_popup, post_id, driver, action, max_comments=MAX_COMMENTS)
        return is_successful
    
    except Exception:
        return

# Scrapes all posts from a given link list
def scrape_posts_by_link_list(posts_result):
    post_links = [link[0] for link in posts_result]
    driver = setup_driver()
    driver.maximize_window()
    action = webdriver.ActionChains(driver)

    for link in post_links:

        if "/posts/" not in link:
            continue

        successful_scrape = False

        while not successful_scrape:
            try:
                driver.get(link)
            except Exception:
                driver = setup_driver()
                driver.maximize_window()
                action = webdriver.ActionChains(driver)
                driver.get(link)
                print("Driver set up")
            finally:
                successful_scrape = scrape_post(link, driver, action)

                if successful_scrape is False:
                    print(f"Retrying current link due to scrape failure.")

    driver.quit()

""" 
Scrapes posts based on the `days` parameter.
If `days` is 0, it scrapes posts published within the last 24 hours.
Otherwise, it scrapes posts that were published exactly `days` days ago. 
"""
def scrape_posts_by_days(days: int):
    if days == 0:
        print("Scraping posts published in the last 24 hours...")
        query = """
                SELECT post_link
                FROM Links
                WHERE candidate = %s
                AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY);
                """
        cursor.execute(query, (CANDIDATE,))
        posts_result = cursor.fetchall()
        scrape_posts_by_link_list(posts_result)

    elif days > 0:
        print(f"Scraping posts published exactly {str(days)} ago")
        query = """
                SELECT post_link
                FROM Links
                WHERE candidate = %s
                AND DATE(timestamp) = DATE_SUB(CURDATE(), INTERVAL %s DAY)
                """
        cursor.execute(query, (CANDIDATE, days))
        posts_result = cursor.fetchall()
        scrape_posts_by_link_list(posts_result)

    else:
        print("Days parameter must be a positive number.")
        return

FIRST_DELAY: int = int(os.getenv('FIRST_DELAY'))
SECOND_DELAY: int = int(os.getenv('SECOND_DELAY'))

scrape_posts_by_days(FIRST_DELAY)
scrape_posts_by_days(SECOND_DELAY)





