import re

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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
    driver.find_element(By.CSS_SELECTOR, ".mt-3 > .btn:nth-child(1)").click()
    driver.find_element(By.CSS_SELECTOR, ".mt-3 > .btn:nth-child(2)").click()
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
    driver.find_element(By.LINK_TEXT, "Download (84 bytes)").click()


def test_recomendation(driver, host):
    driver.get(host)
    driver.set_window_size(914, 1184)
    driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
    driver.find_element(By.CSS_SELECTOR, ".list-group-item:nth-child(1) > .d-flex > .mb-1").click()
    driver.find_element(By.CSS_SELECTOR, ".list-group-item:nth-child(5) > .d-flex > .mb-1").click()

def test_trending_dataset(driver, host):


        driver.get(host)
        driver.set_window_size(1850, 1053)
        driver.find_element(By.LINK_TEXT, "Login").click()
        driver.find_element(By.ID, "email").click()
        driver.find_element(By.ID, "email").send_keys("user1@example.com")
        driver.find_element(By.ID, "password").click()
        driver.find_element(By.ID, "password").send_keys("1234")
        driver.find_element(By.ID, "submit").click()
        driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        dataset_url = driver.current_url
        download = driver.find_element(By.LINK_TEXT, "Download (84 bytes)")
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", download
        )
        download.click()
        driver.get(host)
        trending_card = driver.find_element(
            By.XPATH,
            "//h2/b[text()='Trending datasets']/ancestor::div[contains(@class,'card')]"
        )
        trending_links = trending_card.find_elements(By.TAG_NAME, "a")
        target_link = None
        for link in trending_links:
            if link.text.strip() == "Sample dataset 4":
                target_link = link
                break
        assert target_link is not None, "'Sample dataset 4' no aparece en Trending datasets"

        target_link.click()

        assert driver.current_url == dataset_url


def test_index():

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the index page
        driver.get(f"{host}/webhook")
        # I hate selenium

        try:
            test_badge(driver, host)
          #  test_download_count(driver, host)  NO FUNCIONA
            test_trending_dataset(driver, host)

        except NoSuchElementException:
            raise AssertionError("Test failed!")

    finally:

        # Close the browser
        close_driver(driver)


# Call the test function
test_index()


def test_edit_dataset(driver, host):
    driver.get(host)
    driver.set_window_size(1850, 1053)
    driver.find_element(By.LINK_TEXT, "Login").click()
    driver.find_element(By.ID, "email").click()
    driver.find_element(By.ID, "email").send_keys("user1@example.com")
    driver.find_element(By.ID, "password").click()
    driver.find_element(By.ID, "password").send_keys("1234")
    driver.find_element(By.ID, "submit").click()
    driver.find_element(By.CSS_SELECTOR, ".sidebar-item:nth-child(7) .align-middle:nth-child(2)").click()
    driver.find_element(By.LINK_TEXT, "Sample dataset 1").click()
    driver.find_element(By.LINK_TEXT, "Edit").click()
    driver.find_element(By.ID, "descriptionInput").click()
    driver.find_element(By.ID, "descriptionInput").send_keys(
        "Description for dataset 1\\nChange 1Description for dataset 1 edit selenium\\nChange 2\\nChanged metadata"
    )
    driver.find_element(By.ID, "publicationTypeInput").click()
    driver.find_element(By.CSS_SELECTOR, "option:nth-child(19)").click()
    driver.find_element(By.ID, "updateButton").click()
    assert (
        driver.switch_to.alert.text
        == "This will create a new version of the dataset:\n\nMetadata will be updated\n\nContinue?"
    )
    driver.switch_to.alert.accept()
    WebDriverWait(driver, 10).until(EC.alert_is_present())
    alert_text = driver.switch_to.alert.text
    assert alert_text.startswith("Dataset updated successfully!")
    version_match = re.search(r"New version: v(\d+)", alert_text)
    assert version_match is not None
    driver.switch_to.alert.accept()



def test_trending_dataset(driver, host):
    try:

        driver.get(host)
        driver.set_window_size(1850, 1053)
        driver.find_element(By.LINK_TEXT, "Login").click()
        driver.find_element(By.ID, "email").click()
        driver.find_element(By.ID, "email").send_keys("user1@example.com")
        driver.find_element(By.ID, "password").click()
        driver.find_element(By.ID, "password").send_keys("1234")
        driver.find_element(By.ID, "submit").click()
        driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        dataset_url = driver.current_url
        download = driver.find_element(By.LINK_TEXT, "Download (84 bytes)")
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", download
        )
        download.click()
        driver.get(host)
        trending_card = driver.find_element(
            By.XPATH,
            "//h2/b[text()='Trending datasets']/ancestor::div[contains(@class,'card')]"
        )
        trending_links = trending_card.find_elements(By.TAG_NAME, "a")
        target_link = None
        for link in trending_links:
            if link.text.strip() == "Sample dataset 4":
                target_link = link
                break
        assert target_link is not None, "'Sample dataset 4' no aparece en Trending datasets"

        print("Pasado.")

        target_link.click()

        assert driver.current_url == dataset_url

    finally:
        close_driver(driver)

