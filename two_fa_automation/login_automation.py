"""
Example: Automated login with 2FA for Amazon and Walmart.
Requires: pip install selenium
ChromeDriver must match your Chrome version.
"""

import time
import os
from otp_fetcher import OTPFetcher


# -----------------------------------------------------------------------
# Config — fill in or load from environment variables
# -----------------------------------------------------------------------
EMAIL_ADDRESS = os.environ.get("TWO_FA_EMAIL", "your-email@gmail.com")
EMAIL_PASSWORD = os.environ.get("TWO_FA_EMAIL_PASSWORD", "your-app-password")
EMAIL_PROVIDER  = os.environ.get("TWO_FA_EMAIL_PROVIDER", "gmail")  # gmail / outlook / yahoo


def get_otp_fetcher() -> OTPFetcher:
    return OTPFetcher(
        email_address=EMAIL_ADDRESS,
        password=EMAIL_PASSWORD,
        provider=EMAIL_PROVIDER,
    )


# -----------------------------------------------------------------------
# Amazon login
# -----------------------------------------------------------------------
def login_amazon(driver, username: str, password: str) -> bool:
    """
    Logs into Amazon, handling email 2FA automatically.
    Returns True on success.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    wait = WebDriverWait(driver, 15)

    driver.get("https://www.amazon.com/ap/signin")
    wait.until(EC.presence_of_element_located((By.ID, "ap_email")))

    driver.find_element(By.ID, "ap_email").send_keys(username)
    driver.find_element(By.ID, "continue").click()

    wait.until(EC.presence_of_element_located((By.ID, "ap_password")))
    driver.find_element(By.ID, "ap_password").send_keys(password)
    driver.find_element(By.ID, "signInSubmit").click()

    time.sleep(2)

    # Check if 2FA screen appeared
    if "verification" in driver.page_source.lower() or "otp" in driver.current_url.lower():
        print("Amazon 2FA requested, fetching OTP from email...")
        with get_otp_fetcher() as fetcher:
            otp = fetcher.wait_for_otp(
                timeout_seconds=120,
                service="amazon",
                max_age_minutes=5,
            )
        if not otp:
            print("Failed to retrieve Amazon OTP.")
            return False

        otp_input = wait.until(EC.presence_of_element_located((By.ID, "auth-mfa-otpcode")))
        otp_input.send_keys(otp)
        driver.find_element(By.ID, "auth-signin-button").click()
        time.sleep(2)

    print("Amazon login successful.")
    return True


# -----------------------------------------------------------------------
# Walmart login
# -----------------------------------------------------------------------
def login_walmart(driver, username: str, password: str) -> bool:
    """
    Logs into Walmart, handling email/SMS 2FA automatically.
    Returns True on success.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    wait = WebDriverWait(driver, 15)

    driver.get("https://www.walmart.com/account/login")
    wait.until(EC.presence_of_element_located((By.ID, "email")))

    driver.find_element(By.ID, "email").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    time.sleep(2)

    # Check if 2FA screen appeared
    if any(k in driver.page_source.lower() for k in ["verification", "one-time", "2-step"]):
        print("Walmart 2FA requested, fetching OTP from email...")
        with get_otp_fetcher() as fetcher:
            otp = fetcher.wait_for_otp(
                timeout_seconds=120,
                service="walmart",
                max_age_minutes=5,
            )
        if not otp:
            print("Failed to retrieve Walmart OTP.")
            return False

        otp_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[name='otpCode'], input[aria-label*='code']")
        ))
        otp_input.send_keys(otp)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)

    print("Walmart login successful.")
    return True


# -----------------------------------------------------------------------
# Example usage
# -----------------------------------------------------------------------
if __name__ == "__main__":
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    # options.add_argument("--headless")  # Uncomment to run without browser window
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        # Amazon example
        login_amazon(
            driver,
            username=os.environ.get("AMAZON_EMAIL", "your-amazon@email.com"),
            password=os.environ.get("AMAZON_PASSWORD", "your-password"),
        )
    finally:
        driver.quit()
