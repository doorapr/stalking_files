import re
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException,StaleElementReferenceException,ElementClickInterceptedException
from datetime import datetime
from pathlib import Path
import csv
import time
import random
import json

FOLLOWERS_BUTTON_XPATH = "//a[contains(@href, '/followers')]"
ITEM_XPATH = "//div[@role='dialog']//a[contains(@class, 'notranslate') and starts-with(@href, '/')]"
SCROLL_BOX_XPATH = "//div[@role='dialog']//div[contains(@class, 'x6nl9eh') and contains(@class, 'x1a5l9x9')]"



def click_ok_button(wait):
    try: 
        ok_button=wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and text()='OK']"))
        )
        ok_button.click()
    except TimeoutException:
        print("No OK Button")

def wait_for_dialog_to_disapear(wait):
    try:
        wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
        )
    except TimeoutException:
        print("Dialog is still visible after waiting – may need to close it explicitly.")


def get_follower_count(wait, PATH_FRAGMENT):
    """
    Read the follower count from the profile header and return it as an int.
    Returns None if it can't parse a number.
    """
    
    follower = wait.until(EC.presence_of_element_located(
    (By.XPATH, f"//a[contains(@href, '{PATH_FRAGMENT}')]//span[@title]")
))
    
    followers_raw = follower.get_attribute("title")  
    
    print("Raw follower label:", repr(followers_raw))

    text = followers_raw.lower()

    # 1) handle k / m suffixes (e.g., "1.2k", "3,4m")
    m = re.search(r"([\d.,]+)\s*([km])", text)
    if m:
        number_str = m.group(1).replace(",", ".")
        try:
            base = float(number_str)
        except ValueError:
            base = 0
        suffix = m.group(2)
        if suffix == "k":
            return int(base * 1_000)
        elif suffix == "m":
            return int(base * 1_000_000)

    # 2) otherwise, just grab the biggest integer-looking chunk
    #    and normalize thousands separators
    #    (covers "1,234", "1.234", "12 345" etc.)
    digits = re.findall(r"[\d.,]+", text)
    if not digits:
        return None

    candidate = digits[0]

    # If both ',' and '.' appear, assume one is thousands sep, one decimal
    # For follower counts, we can just strip all non-digits:
    digits_only = re.sub(r"\D", "", candidate)
    if digits_only:
        return int(digits_only)

    return None
#OLD VERSION

# def load_all_followers(
#     expected_total,
#     driver,
#     max_loops=600,
#     stable_height_loops=6,
#     min_delay=1.1,        
#     max_delay=2.4,
            
# ):
#     wait = WebDriverWait(driver, 15)

#     # wait for scroll box once
#     wait.until(EC.presence_of_element_located((By.XPATH, SCROLL_BOX_XPATH)))

#     last_height = 0
#     stable_loops = 0
#     sleeping_after_x_loops=random.randint(25,35)
#     last_round_slept=0
#     for i in range(max_loops):
#         try:
#             # always re-find to avoid stale
#             scroll_box = driver.find_element(By.XPATH, SCROLL_BOX_XPATH)

#             # current total height of the scroll area
#             current_height = driver.execute_script(
#                 "return arguments[0].scrollHeight;", scroll_box
#             )

#             # ----- HUMAN-LIKE SCROLLING START -----
#             # do a few smaller scroll steps instead of 1 big jump
#             steps = random.randint(2, 4)  # how many "finger swipes" this loop
#             for _ in range(steps):
#                 # scroll by a fraction of the visible viewport
#                 driver.execute_script(
#                     """
#                     arguments[0].scrollTo(
#                         0,
#                         arguments[0].scrollTop + arguments[0].clientHeight * arguments[1]
#                     );
#                     """,
#                     scroll_box,
#                     random.uniform(0.4, 0.9),  # 40–90% of a screen per swipe
#                 )
#                 # small pause between swipes
#                 time.sleep(random.uniform(0.25, 0.7))

#             # main pause after a batch of swipes (as if reading)
#             time.sleep(random.uniform(min_delay, max_delay))
#             # ----- HUMAN-LIKE SCROLLING END -----

#             new_height = driver.execute_script(
#                 "return arguments[0].scrollHeight;", scroll_box
#             )

#         except StaleElementReferenceException:
#             print(f"Loop {i+1}: scroll box went stale, retrying…")
#             time.sleep(0.6)
#             continue

#         # count how many followers we have so far
#         items = driver.find_elements(By.XPATH, ITEM_XPATH)
#         count = len(items)
#         print(
#             f"Loop {i+1}: height {new_height}, followers loaded {count} "
#             f"(steps this loop: {steps})"
#         )

#         # stop once expected_total reached
#         if expected_total is not None and count >= expected_total:
#             print(f"Reached expected total: {expected_total}")
#             break
       
#         if i-last_round_slept==sleeping_after_x_loops:
#             last_round_slept=i
#             print("Sleeping for a bit")
#             time.sleep(random.uniform(2,10))   
#         # original stopping condition: scroll height stopped changing
#         if new_height == last_height:
#             stable_loops += 1
#             if stable_loops >= stable_height_loops:
                
#                 print(
#                     "Scroll height stable for several loops → assume full list loaded."
#                 )
#                 break
#         else:
#             stable_loops = 0
#             last_height = new_height

#     # final extraction
#     all_links = driver.find_elements(By.XPATH, ITEM_XPATH)
#     print("Final count:", len(all_links))
#     return all_links


def load_all_followers(
    expected_total,
    driver,
    max_loops=600,
    stable_height_loops=20,
    min_delay=1.1,
    max_delay=3.4,
):
    wait = WebDriverWait(driver, 15)

    # wait for scroll box once
    wait.until(EC.presence_of_element_located((By.XPATH, SCROLL_BOX_XPATH)))

    last_height = 0
    stable_loops = 0

    # how often to take a longer break
    sleeping_after_x_loops = random.randint(25, 35)
    last_round_slept = 0

    # NEW: store every username we've ever seen
    seen_usernames = set()

    for i in range(max_loops):
        try:
            # always re-find to avoid stale
            scroll_box = driver.find_element(By.XPATH, SCROLL_BOX_XPATH)

            # current total height of the scroll area
            current_height = driver.execute_script(
                "return arguments[0].scrollHeight;", scroll_box
            )

            # ----- HUMAN-LIKE SCROLLING START -----
            steps = random.randint(2, 4)  # how many "finger swipes" this loop
            for _ in range(steps):
                driver.execute_script(
                    """
                    arguments[0].scrollTo(
                        0,
                        arguments[0].scrollTop + arguments[0].clientHeight * arguments[1]
                    );
                    """,
                    scroll_box,
                    random.uniform(0.4, 0.9),  # 40–90% of a screen per swipe
                )
                time.sleep(random.uniform(0.25, 0.7))

            # main pause after a batch of swipes (as if reading)
            time.sleep(random.uniform(min_delay, max_delay))
            # ----- HUMAN-LIKE SCROLLING END -----

            new_height = driver.execute_script(
                "return arguments[0].scrollHeight;", scroll_box
            )

        except StaleElementReferenceException:
            print(f"Loop {i+1}: scroll box went stale, retrying…")
            time.sleep(0.6)
            continue

        # everything currently in the DOM
        items = driver.find_elements(By.XPATH, ITEM_XPATH)

        # ✅ add all usernames we see this loop to the global set
        for el in items:
            username = el.text.strip()
            if username:
                seen_usernames.add(username)

        visible_count = len(items)
        unique_count = len(seen_usernames)

        print(
            f"Loop {i+1}: height {new_height}, "
            f"visible rows {visible_count}, unique usernames {unique_count} "
            f"(steps this loop: {steps})"
        )

        # ✅ NEW stopping condition: based on unique usernames, not visible rows
        if expected_total is not None and unique_count >= expected_total:
            print(f"Reached expected total: {expected_total} unique usernames")
            break

        # occasional longer sleep to look more human
        # if i - last_round_slept >= sleeping_after_x_loops:
        #     last_round_slept = i
        #     print("Sleeping for a bit between loops…")
        #     time.sleep(random.randint(2, 10))

        # original stopping condition: scroll height stopped changing
        if new_height == last_height:
            stable_loops += 1
            if stable_loops >= stable_height_loops:
                print(
                    "Scroll height stable for several loops → assume full list loaded."
                )
                break
        else:
            stable_loops = 0
            last_height = new_height

    print("Final unique usernames:", len(seen_usernames))
    return seen_usernames


def click_anmelden_button(driver, timeout=10):
    xpath = "//button[.//span[normalize-space()='Anmelden']]"

    wait = WebDriverWait(driver, timeout)

    try:
        # wait until present
        btn = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

        # scroll into view (in case something covers it)
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
            btn,
        )
        time.sleep(0.5)

        # wait until clickable and click
        clickable = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        try:
            clickable.click()
        except ElementClickInterceptedException:
            print("Normal click intercepted, trying JS click…")
            driver.execute_script("arguments[0].click();", clickable)

        print("Clicked 'Anmelden' button.")

    except TimeoutException:
        print("Could not find 'Anmelden' button within timeout.")