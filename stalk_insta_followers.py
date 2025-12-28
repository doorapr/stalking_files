from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException,StaleElementReferenceException,ElementClickInterceptedException
from datetime import datetime
from pathlib import Path
import functions as fc
import csv

username="USER YOU ARE LOOKING FOR"
login_email="YOUR LOGIN EMAIL OR USERNAME"
login_password="YOUR LOGIN PASSWORD"
searching_for="followers"
PATH_FRAGMENT="/"+username+"/"+searching_for+"/"
driver = webdriver.Chrome() 
driver.get("https://www.instagram.com")

wait = WebDriverWait(driver, 15)
try:
    decline_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[text()='Optionale Cookies ablehnen']")
        )
    )
    decline_btn.click()
    print("Cookie dialog closed.")
except TimeoutException:
    print("No cookie dialog or couldn't find the decline button.")

username_field = wait.until(
    EC.presence_of_element_located((By.NAME, "username"))
)
password_field = wait.until(
    EC.presence_of_element_located((By.NAME, "password"))
)
username_field.send_keys(login_email)
password_field.send_keys(login_password)


fc.wait_for_dialog_to_disapear(wait)

login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
login_button.click()


fc.click_ok_button(wait)
try: 
    no_button=wait.until(
        EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and text()='Jetzt nicht']"))
    )
    no_button.click()
except TimeoutException:
    print("No NO Button")

fc.wait_for_dialog_to_disapear(wait)
fc.click_ok_button(wait)
fc.wait_for_dialog_to_disapear(wait)
try:
    search_button = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//a[.//span[text()='Suche']]")
    )
)

    search_button.click()
except TimeoutException:
    print("Couldn't find svg")

try:    
    search = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'Suche')]"))
    )

    search.send_keys(username)
    search.send_keys(Keys.ENTER)
except TimeoutException:
    print("Couldn't find searchbar.")

try:
    profil= wait.until(  EC.element_to_be_clickable(
        (By.XPATH, f"//span[normalize-space()='{username}']/ancestor::a[1]")
    ))
    profil.click()
except TimeoutException:
    print("Didn't find profil")
try:
    expected_count= fc.get_follower_count(wait,PATH_FRAGMENT=PATH_FRAGMENT)
except Exception:
    expected_count= None
    print("Couldn't find follower count")    

try:
    follower= wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//a[contains(@href, '{PATH_FRAGMENT}')]")
    ))
    follower.click()
except TimeoutException:
    print("Didn't find follower")



try:

    all_links = fc.load_all_followers(expected_total=expected_count,driver=driver)
    print("Final count:", len(all_links))

    ts_str = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    csv_name=ts_str+"current_followers:"+str(expected_count)+ ".csv"
    output_dir = Path("Persona/"+username)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / csv_name

    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for u in sorted(all_links):
            writer.writerow([u])
    
    
except StaleElementReferenceException:
    print("Didn't find users")


driver.quit() # Browser schließen






