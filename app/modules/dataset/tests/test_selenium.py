import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


@pytest.fixture
def driver():
    driver = initialize_driver()
    yield driver
    close_driver(driver)


@pytest.fixture
def host():
    return get_host_for_selenium_testing()


def test_badge(driver, host):
    driver.get(host)
    driver.set_window_size(886, 969)
    driver.find_element(By.LINK_TEXT, "Login").click()
    driver.find_element(By.ID, "email").click()
    driver.find_element(By.ID, "email").send_keys("user1@example.com")
    driver.find_element(By.ID, "password").send_keys("1234")
    driver.find_element(By.ID, "submit").click()
    driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
    driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .btn:nth-child(4)").click()
    driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(5)").click()
    driver.find_element(By.LINK_TEXT, "Doe, John").click()
    driver.find_element(By.LINK_TEXT, "Log out").click()


def test_download_count(driver, host):
    driver.get(host)
    driver.set_window_size(592, 734)
    driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .row > .badge").click()
    driver.find_element(By.LINK_TEXT, "Download (84 bytes)").click()
    driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .row > .badge").click()
    driver.find_element(By.CSS_SELECTOR, ".sidebar-toggle").click()
    driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .btn:nth-child(2) > .feather").click()
    driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
    driver.find_element(By.LINK_TEXT, "Download all (84 bytes)").click()

def test_recomendation(self):
    self.driver.get("http://127.0.0.1:5000/")
    self.driver.set_window_size(914, 1184)
    self.driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
    self.driver.find_element(By.CSS_SELECTOR,
                             ".list-group-item:nth-child(1) > .d-flex > .mb-1").click()
    self.driver.find_element(By.CSS_SELECTOR,
                             ".list-group-item:nth-child(5) > .d-flex > .mb-1").click()


def test_index():

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the index page
        driver.get(f"{host}/webhook")
        # I hate selenium

        try:
            test_badge(driver, host)
            test_download_count(driver, host)

        except NoSuchElementException:
            raise AssertionError("Test failed!")

    finally:

        # Close the browser
        close_driver(driver)


# Call the test function
test_index()
