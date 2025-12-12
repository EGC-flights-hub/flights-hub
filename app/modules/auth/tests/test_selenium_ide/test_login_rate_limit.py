from selenium.webdriver.common.by import By

from core.selenium.common import initialize_driver


class TestLoginRateLimit():
    def setup_method(self, method):
        self.driver = initialize_driver()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_login_rate_limit(self):
        self.driver.get("http://127.0.0.1:5000/login")
        self.driver.set_window_size(1920, 1080)
        self.driver.find_element(By.CSS_SELECTOR, ".row:nth-child(2) > .col-md-6").click()
        self.driver.find_element(By.ID, "email").click()
        self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("wololo")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("wololo")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("wololo")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("wololo")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("wololo")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("wololo")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.ID, "email").click()
        self.driver.find_element(By.ID, "email").send_keys("user2@example.com")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.CSS_SELECTOR, ".text-dark").click()
        self.driver.find_element(By.CSS_SELECTOR, ".dropdown-item:nth-child(2)").click()
        self.driver.find_element(By.CSS_SELECTOR, ".nav-link:nth-child(1)").click()
        self.driver.find_element(By.ID, "email").click()
        self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("asdfg")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.ID, "email").click()
        self.driver.find_element(By.ID, "email").click()
