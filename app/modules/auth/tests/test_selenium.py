import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def test_login_and_check_element():

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}/login")

        # Wait a little while to make sure the page has loaded completely
        time.sleep(4)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)

        # Wait a little while to ensure that the action has been completed
        time.sleep(4)

        try:

            driver.find_element(By.XPATH, "//h1[contains(@class, 'h2 mb-3') and contains(., 'Latest datasets')]")
            print("Test passed!")

        except NoSuchElementException:
            raise AssertionError("Test failed!")

    finally:

        # Close the browser
        close_driver(driver)


def test_login_rate_limit():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        driver.get(f"{host}/login")
        time.sleep(2)

        def do_login(email: str, password: str):

            email_field = driver.find_element(By.ID, "email")
            password_field = driver.find_element(By.ID, "password")

            email_field.clear()
            password_field.clear()

            email_field.send_keys(email)
            password_field.send_keys(password)

            # Submit the form
            driver.find_element(By.ID, "submit").click()

        # 1) Perform several failed attempts with user1 to trigger the lock
        error_text = "Invalid credentials. Please try again later or reset your password."

        for i in range(4):
            do_login("user1@example.com", "wololo")
            time.sleep(2)
            try:
                driver.find_element(
                    By.XPATH,
                    f"//span[contains(@style, 'color: red') and contains(normalize-space(), \"{error_text}\")]",
                )
            except NoSuchElementException:
                raise AssertionError("Test failed" + str(i))

        do_login("user1@example.com", "wololo")
        time.sleep(2)

        # Look for the lockout message due to too many attempts
        error_text = "Too many failed sign-in attempts. Your access is temporarily blocked."
        try:
            driver.find_element(
                By.XPATH,
                f"//span[contains(@style, 'color: red') and contains(normalize-space(), \"{error_text}\")]",
            )
            print("Test passed")
        except NoSuchElementException:
            raise AssertionError("Test failed")

        # 2) Check that another user (user2) Can log in from the same IP
        do_login("user2@example.com", "1234")
        time.sleep(4)

        # Comprobamos que parece haber login de user2
        try:
            driver.find_element(By.XPATH, "//h1[contains(@class, 'h2 mb-3') and contains(., 'Latest datasets')]")
        except NoSuchElementException:
            raise AssertionError("Test failed")

        # 3) Log out user2
        driver.find_element(By.CSS_SELECTOR, ".text-dark").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, ".dropdown-item:nth-child(2)").click()
        time.sleep(2)

        # Open the login page
        driver.get(f"{host}/login")

        # Wait a little while to make sure the page has loaded completely
        time.sleep(4)

        # 4) Try to log in again with user1, the account should still be locked
        do_login("user1@example.com", "asdfg")
        time.sleep(2)

        try:
            driver.find_element(
                By.XPATH,
                f"//span[contains(@style, 'color: red') and contains(normalize-space(), \"{error_text}\")]",
            )
            print("Test passed")
        except NoSuchElementException:
            raise AssertionError("Test failed")

    finally:
        close_driver(driver)


# Call the test function
test_login_and_check_element()
test_login_rate_limit()
