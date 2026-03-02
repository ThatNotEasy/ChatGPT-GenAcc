"""
ChatGPT Account Creator module - Core automation logic
"""
import asyncio
import os
import random
import re
import tempfile
import uuid
import shutil
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from faker import Faker
from playwright.async_api import async_playwright


class ChatGPTAccountCreator:
    """Automates the creation of ChatGPT accounts using temporary browser data"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.accounts_file = "accounts.txt"
        self.created_accounts = []
        self.current_first_name = None
        self.current_last_name = None
        self.fake = Faker()

    def randstr(self, length):
        """Generate a random string of specified length"""
        chars = "abcdefghijklmnopqrstuvwxyz0123456789"
        return "".join(random.choices(chars, k=length))

    def random_float(self, min_val, max_val):
        """Generate a random float between min and max"""
        return random.uniform(min_val, max_val)

    async def generate_random_email(self):
        """Generate a random email using generator.email service"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                    "accept-encoding": "gzip, deflate, br"
                }
                response = await client.get("https://generator.email/", headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                domains = []

                # Try multiple selectors for domain extraction
                suggestions = soup.select(".e7m.tt-suggestions div > p")
                if not suggestions:
                    suggestions = soup.select(".tt-suggestions p")
                if not suggestions:
                    suggestions = soup.select("[class*='suggestion'] p")
                
                for elem in suggestions:
                    domain_text = elem.get_text().strip()
                    # Validate domain format
                    if domain_text and '.' in domain_text and ' ' not in domain_text:
                        domains.append(domain_text)

                if domains:
                    domain = random.choice(domains)

                    # Generate and store names for later use
                    self.current_first_name = self.fake.first_name().replace("'", "").replace('"', "")
                    self.current_last_name = self.fake.last_name().replace("'", "").replace('"', "")

                    random_str = self.randstr(5)
                    email = f"{self.current_first_name}{self.current_last_name}{random_str}@{domain}".lower()

                    self.logger.log(f"Generated email: {email}")
                    return email
                else:
                    # Fallback domains if generator.email fails
                    fallback_domains = ["xezo.live", "muahetbienhoa.com", "gmailvn.xyz", "mailvn.top"]
                    domain = random.choice(fallback_domains)
                    
                    self.current_first_name = self.fake.first_name().replace("'", "").replace('"', "")
                    self.current_last_name = self.fake.last_name().replace("'", "").replace('"', "")
                    
                    random_str = self.randstr(5)
                    email = f"{self.current_first_name}{self.current_last_name}{random_str}@{domain}".lower()
                    
                    self.logger.log(f"Generated email (fallback): {email}")
                    return email
        except Exception as e:
            raise Exception(f"Error generating email: {e}")

    def generate_random_name(self):
        """Generate a random full name"""
        # Use stored names from generate_random_email if available
        if self.current_first_name and self.current_last_name:
            return f"{self.current_first_name} {self.current_last_name}"

        # Fallback: generate new names using faker
        first_name = self.fake.first_name().replace("'", "").replace('"', "")
        last_name = self.fake.last_name().replace("'", "").replace('"', "")
        return f"{first_name} {last_name}"

    def generate_random_birthday(self):
        """Generate a random birthday for someone between 18-65 years old"""
        today = datetime.now()
        min_year = today.year - 65
        max_year = today.year - 18

        year = random.randint(min_year, max_year)
        month = random.randint(1, 12)

        if month in [1, 3, 5, 7, 8, 10, 12]:
            max_day = 31
        elif month in [4, 6, 9, 11]:
            max_day = 30
        else:
            # February - check leap year
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                max_day = 29
            else:
                max_day = 28

        day = random.randint(1, max_day)

        return {"year": year, "month": month, "day": day}

    def save_account(self, email, password):
        """Save a created account to the accounts file"""
        try:
            self.created_accounts.append({"email": email, "password": password})
            with open(self.accounts_file, "a", encoding="utf-8") as f:
                f.write(f"{email}|{password}\n")
            self.logger.log(f"Saved account to {self.accounts_file}: {email}")
        except Exception as e:
            self.logger.log(f"Error saving account: {e}", "ERROR")

    async def get_verification_code(self, email, max_retries=10, delay=3):
        """Get verification code from the email inbox"""
        # Extract username and domain from email
        username, domain = email.split("@")

        # First, get the main page to find the dynamic inbox URL
        inbox_url = None
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                headers = {
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "accept-language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                # Get main page to find inbox URL
                main_response = await client.get("https://generator.email/", headers=headers)
                main_response.raise_for_status()
                
                # Parse to find the inbox URL pattern
                main_soup = BeautifulSoup(main_response.text, "html.parser")
                
                # Look for inbox link in the page (e.g., inbox3, inbox7, etc.)
                inbox_link = main_soup.select_one("a[href*='inbox']")
                if inbox_link:
                    href = inbox_link.get("href", "")
                    # Extract inbox path (e.g., "inbox3" from "/inbox3/something")
                    inbox_match = re.search(r'/(inbox\d+)', href)
                    if inbox_match:
                        inbox_path = inbox_match.group(1)
                        inbox_url = f"https://generator.email/{inbox_path}/{domain}/{username}"
                        self.logger.log(f"Found dynamic inbox URL: {inbox_path}")
                
                # Fallback to direct URL if no inbox pattern found
                if not inbox_url:
                    inbox_url = f"https://generator.email/{domain}/{username}"
                    
        except Exception as e:
            self.logger.log(f"Error finding inbox URL: {e}, using fallback", "WARNING")
            inbox_url = f"https://generator.email/{domain}/{username}"

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    headers = {
                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                        "accept-language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                    
                    self.logger.log(f"Checking email at: {inbox_url}")
                    response = await client.get(inbox_url, headers=headers)
                    response.raise_for_status()

                    html_content = response.text
                    soup = BeautifulSoup(html_content, "html.parser")

                    # Debug: Save HTML on first attempt
                    if attempt == 0:
                        await self.debug_save_email_html(email, html_content)

                    # Try to get verification code from email content
                    # Look for the subject div that contains the code
                    otp_elem = soup.select_one("div.e7m.subj_div_45g45gg")
                    otp_text = otp_elem.get_text().strip() if otp_elem else ""

                    if otp_text and len(otp_text) > 0:
                        self.logger.log(f"Found OTP text: {otp_text}")
                        # Extract numeric code if present (6 digits)
                        code_match = re.search(r"\d{6}", otp_text)
                        if code_match:
                            code = code_match.group(0)
                            self.logger.log(f"Retrieved verification code: {code}")
                            return code

                    # Fallback: search entire page for 6-digit code patterns
                    email_content = soup.get_text()
                    code_match = re.search(r"\b\d{6}\b", email_content)
                    if code_match:
                        code = code_match.group(0)
                        self.logger.log(f"Retrieved verification code (page search): {code}")
                        return code

                    if attempt < max_retries - 1:
                        self.logger.log(f"Code not found, waiting {delay}s before retry {attempt + 1}/{max_retries}...")
                        await asyncio.sleep(delay)

            except Exception as e:
                self.logger.log(f"Error fetching verification code (attempt {attempt + 1}): {e}", "WARNING")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)

        self.logger.log(f"Failed to get verification code after {max_retries} attempts", "ERROR")
        return None

    async def debug_save_email_html(self, email, html_content):
        """Save email HTML content for debugging purposes"""
        try:
            debug_dir = "debug"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            username, domain = email.split("@")
            filename = f"{debug_dir}/email_{username}_{domain}.html"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            self.logger.log(f"Debug: Saved email HTML to {filename}")
        except Exception as e:
            self.logger.log(f"Debug: Could not save HTML: {e}", "WARNING")

    async def create_account(self, account_number, total_accounts):
        """Create a single ChatGPT account"""
        # Set progress for logging
        self.logger.set_progress(f"{account_number}/{total_accounts}")

        email = await self.generate_random_email()
        password = self.config.get("password")

        if not password:
            self.logger.log("Error: No password found in config.json! Please add a 'password' field to config.json", "ERROR")
            return False

        if len(password) < 12:
            self.logger.log(f"Warning: Password in config.json is only {len(password)} characters. ChatGPT requires at least 12 characters.", "WARNING")

        name = self.generate_random_name()
        birthday = self.generate_random_birthday()

        unique_id = str(uuid.uuid4())[:8]
        timestamp = int(datetime.now().timestamp() * 1000)
        temp_dir = tempfile.mkdtemp(prefix=f"chatgpt_browser_{account_number}_{timestamp}_{unique_id}_")

        try:
            async with async_playwright() as p:
                firefox_version = "131.0"
                user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{firefox_version}) Gecko/20100101 Firefox/{firefox_version}"

                extra_http_headers = {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                }

                firefox_user_prefs = {
                    "dom.webdriver.enabled": False,
                    "useAutomationExtension": False,
                    "marionette.enabled": False,
                }

                context = await p.firefox.launch_persistent_context(
                    temp_dir,
                    headless=self.config.get("headless", False),
                    viewport={"width": 1366, "height": 768},
                    user_agent=user_agent,
                    locale="en-US",
                    timezone_id="America/New_York",
                    device_scale_factor=0.9,
                    has_touch=False,
                    is_mobile=False,
                    ignore_https_errors=True,
                    bypass_csp=True,
                    extra_http_headers=extra_http_headers,
                    firefox_user_prefs=firefox_user_prefs,
                    timeout=30000,
                )

                pages = context.pages
                page = pages[0] if pages else await context.new_page()

                firefox_stealth_script = """
                (function() {
                    // Hide webdriver property (Firefox)
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                        configurable: true
                    });
                    
                    // Override plugins to look realistic
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => {
                            return {
                                length: 0,
                                item: function() { return null; },
                                namedItem: function() { return null; },
                                refresh: function() {}
                            };
                        },
                        configurable: true
                    });
                    
                    // Override languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                        configurable: true
                    });
                    
                    // Override permissions query
                    const originalQuery = window.navigator.permissions.query;
                    if (originalQuery) {
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                    }
                    
                    // Remove automation indicators
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                    
                    // Firefox-specific: Hide marionette
                    delete navigator.__marionette;
                    delete navigator.__fxdriver;
                    delete navigator._driver;
                    delete navigator._selenium;
                    delete navigator.__driver_evaluate;
                    delete navigator.__webdriver_evaluate;
                    delete navigator.__selenium_evaluate;
                    delete navigator.__fxdriver_evaluate;
                    delete navigator.__driver_unwrapped;
                    delete navigator.__webdriver_unwrapped;
                    delete navigator.__selenium_unwrapped;
                    delete navigator.__fxdriver_unwrapped;
                })();
                """

                await page.add_init_script(firefox_stealth_script)

                # Step 1: Navigate to ChatGPT
                try:
                    await page.goto("https://chatgpt.com/", wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(2)

                    await page.evaluate("""() => {
                        return {
                            webdriver: navigator.webdriver,
                            userAgent: navigator.userAgent,
                            languages: navigator.languages,
                            platform: navigator.platform,
                            plugins: navigator.plugins.length,
                            cookieEnabled: navigator.cookieEnabled,
                            onLine: navigator.onLine
                        };
                    }""")

                except Exception as e:
                    self.logger.log(f"Error navigating to ChatGPT: {e}", "ERROR")
                    await context.close()
                    return False

                # Click Sign up button - try multiple selectors
                self.logger.log("Processing 'Sign up'")
                try:
                    # Try multiple selectors for the signup button
                    signup_clicked = False
                    
                    # Strategy 1: Try role-based locator (most resilient)
                    try:
                        signup_button = page.get_by_role("button", name="Sign up")
                        if await signup_button.is_visible(timeout=5000):
                            await signup_button.click(force=True, timeout=10000)
                            signup_clicked = True
                            self.logger.log("Clicked Sign up button (role-based)")
                    except Exception as e:
                        self.logger.log(f"Role-based signup failed: {e}", "WARNING")
                    
                    # Strategy 2: Try text-based locator
                    if not signup_clicked:
                        try:
                            signup_button = page.locator('button:has-text("Sign up")')
                            if await signup_button.is_visible(timeout=5000):
                                await signup_button.click(force=True, timeout=10000)
                                signup_clicked = True
                                self.logger.log("Clicked Sign up button (text-based)")
                        except Exception as e:
                            self.logger.log(f"Text-based signup failed: {e}", "WARNING")
                    
                    # Strategy 3: Try old XPath as fallback
                    if not signup_clicked:
                        try:
                            signup_button_xpath = '/html/body/div[2]/div[1]/div/div[2]/div/header/div[3]/div[2]/div/div/div/button[2]'
                            signup_button = page.locator(f"xpath={signup_button_xpath}")
                            await signup_button.wait_for(state="visible", timeout=5000)
                            await signup_button.click(force=True, timeout=10000)
                            signup_clicked = True
                            self.logger.log("Clicked Sign up button (xpath fallback)")
                        except Exception as e:
                            self.logger.log(f"XPath signup failed: {e}", "WARNING")
                    
                    if not signup_clicked:
                        raise Exception("Could not find Sign up button with any selector strategy")

                    await asyncio.sleep(self.random_float(1, 2))

                    try:
                        email_input_check = page.get_by_role("textbox", name="Email address")
                        await email_input_check.wait_for(state="visible", timeout=5000)
                    except:
                        self.logger.log("Dialog might not have appeared, continuing anyway...", "WARNING")

                except Exception as e:
                    self.logger.log(f"Error processing signup: {e}")
                    await context.close()
                    return False

                # Fill email
                try:
                    email_input = page.get_by_role("textbox", name="Email address")
                    await email_input.wait_for(state="visible", timeout=15000)

                    await email_input.fill(email)
                    await email_input.blur()

                    await asyncio.sleep(self.random_float(2, 3))

                    continue_button = page.get_by_role("button", name="Continue", exact=True)
                    await continue_button.wait_for(state="visible", timeout=10000)

                    is_enabled = await continue_button.is_enabled()
                    if not is_enabled:
                        self.logger.log("Continue button not enabled yet, waiting for validation...")
                        await asyncio.sleep(2)

                    await asyncio.sleep(self.random_float(0.5, 1))

                except Exception as e:
                    self.logger.log(f"Error filling email: {e}", "ERROR")
                    await context.close()
                    return False

                # Click Continue
                try:
                    continue_button = page.get_by_role("button", name="Continue", exact=True)
                    await continue_button.wait_for(state="visible", timeout=10000)

                    # Use force click to avoid timeout issues
                    try:
                        await continue_button.click(force=True, timeout=5000)
                    except:
                        # Fallback to regular click with longer timeout
                        await continue_button.click(timeout=15000)

                    await asyncio.sleep(2)

                    current_url = page.url

                    if "password" in current_url.lower() or "auth.openai.com" in current_url.lower():
                        self.logger.log(f"Setting up password")
                    elif "error" in current_url.lower():
                        await context.close()
                        return False

                except Exception as e:
                    current_url = page.url
                    if "error" in current_url.lower():
                        await context.close()
                        return False
                    else:
                        await asyncio.sleep(2)
                        new_url = page.url
                        if "error" in new_url.lower():
                            await context.close()
                            return False
                        elif "password" not in new_url.lower():
                            await context.close()
                            return False

                # Fill password
                try:
                    password_input = page.get_by_role("textbox", name="Password")
                    await password_input.wait_for(state="visible", timeout=15000)

                    await password_input.fill(password)
                    await asyncio.sleep(self.random_float(1, 2))
                except Exception as e:
                    self.logger.log(f"Error filling password: {e}", "ERROR")
                    await context.close()
                    return False

                # Click Continue after password
                try:
                    continue_button = page.get_by_role("button", name="Continue")
                    await continue_button.wait_for(state="visible", timeout=15000)

                    is_enabled = await continue_button.is_enabled()
                    if not is_enabled:
                        self.logger.log("Button not enabled yet, waiting...")
                        await asyncio.sleep(2)

                    box = await continue_button.bounding_box()
                    if box:
                        await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                        await asyncio.sleep(self.random_float(0.3, 0.7))

                    # Use force click to avoid timeout issues
                    try:
                        await continue_button.click(force=True, timeout=5000)
                    except:
                        await continue_button.click(timeout=15000)
                    
                    await asyncio.sleep(self.random_float(2, 3))
                except Exception as e:
                    self.logger.log(f"Error clicking Continue: {e}", "ERROR")
                    await context.close()
                    return False

                # Wait for verification code - give more time for email to arrive
                self.logger.log("Waiting for verification code...")
                await asyncio.sleep(10)  # Increased from 8 to 10 seconds initial wait

                verification_code = await self.get_verification_code(email)

                if not verification_code:
                    self.logger.log(f"Failed to get verification code for {email}", "ERROR")
                    await context.close()
                    return False

                # Enter verification code
                try:
                    code_input = page.get_by_role("textbox", name="Code")
                    await code_input.fill(verification_code)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    self.logger.log(f"Error entering verification code: {e}", "ERROR")
                    await context.close()
                    return False

                # Click Continue after code
                try:
                    continue_button = page.get_by_role("button", name="Continue")
                    await continue_button.click(force=True, timeout=10000)
                    await asyncio.sleep(3)
                except Exception as e:
                    self.logger.log(f"Error clicking Continue after code: {e}", "ERROR")
                    await context.close()
                    return False

                # Fill name
                try:
                    name_input = page.get_by_role("textbox", name="Full name")
                    await name_input.fill(name)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    self.logger.log(f"Error filling name: {e}", "ERROR")
                    await context.close()
                    return False

                # Handle birthday - simplified approach
                month_num = birthday["month"]
                day_num = birthday["day"]
                year_num = birthday["year"]

                self.logger.log(f"Setting birthday: {month_num}/{day_num}/{year_num}")

                try:
                    # Wait for birthday fields to be visible
                    await asyncio.sleep(1)

                    # Format birthday as MMDDYYYY (with leading zeros)
                    month_str = str(month_num).zfill(2)
                    day_str = str(day_num).zfill(2)
                    year_str = str(year_num)
                    birthday_string = f"{month_str}{day_str}{year_str}"

                    # First click on the Birthday label to activate the field
                    birthday_xpath = "/html/body/div[1]/div/fieldset/form/div[1]/div/div[2]/div/div/div/div"
                    birthday_form = page.locator(f"xpath={birthday_xpath}")

                    if await birthday_form.is_visible(timeout=5000):
                        await birthday_form.click()
                        await asyncio.sleep(0.5)

                    # Now find and click the month spinbutton
                    month_spin = page.locator('[role="spinbutton"][aria-label*="month"]').first

                    if await month_spin.is_visible(timeout=5000):
                        await month_spin.click()
                        await asyncio.sleep(0.3)

                        # Type all digits at once - form will auto-distribute
                        await page.keyboard.type(birthday_string, delay=100)

                        await asyncio.sleep(0.5)
                    else:
                        raise Exception("Birthday field not found")
                except Exception as birthday_error:
                    self.logger.log(f"Error setting birthday: {birthday_error}", "ERROR")
                    await context.close()
                    return False

                # Click Continue to complete signup
                try:
                    continue_button = page.get_by_role("button", name="Continue")
                    await continue_button.wait_for(state="visible", timeout=10000)

                    is_enabled = await continue_button.is_enabled()
                    if not is_enabled:
                        await asyncio.sleep(2)

                    # Use force click to avoid timeout issues
                    try:
                        await continue_button.click(force=True, timeout=5000)
                    except:
                        await continue_button.click(timeout=15000)

                    await asyncio.sleep(2)
                except Exception as e:
                    self.logger.log(f"Error clicking final Continue: {e}", "ERROR")
                    await context.close()
                    return False

                # Verify account creation
                try:
                    current_url = page.url
                    if "chatgpt.com" in current_url:
                        self.logger.log(f"Account created successfully!")
                        self.save_account(email, password)
                        await context.close()
                        return True
                    else:
                        self.logger.log(f"Unexpected Error after signup", "WARNING")
                        self.save_account(email, password)
                        await context.close()
                        return True
                except Exception as e:
                    self.logger.log(f"Error verifying account creation", "WARNING")
                    self.save_account(email, password)
                    await context.close()
                    return True

        except Exception as e:
            self.logger.log(f"Unexpected error in create_account: {e}", "ERROR")
            # Try to capture screenshot on failure if page is available
            try:
                if 'page' in locals():
                    screenshot_path = f"error_screenshot_{account_number}.png"
                    await page.screenshot(path=screenshot_path)
                    self.logger.log(f"Screenshot saved to {screenshot_path}", "ERROR")
            except:
                pass
            return False
        finally:
            try:
                await asyncio.sleep(1)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                # Ignore cleanup errors
                pass

    async def create_accounts(self, num_accounts):
        """Create multiple ChatGPT accounts sequentially"""
        print(f"Starting account creation for {num_accounts} accounts...")

        successful = 0
        failed = 0

        # Sequential processing - one account at a time
        for account_num in range(1, num_accounts + 1):
            # Set progress for logging
            self.logger.set_progress(f"{account_num}/{num_accounts}")

            try:
                success = await self.create_account(account_num, num_accounts)

                if success:
                    successful += 1
                    self.logger.log(f"Account completed successfully\n")
                else:
                    failed += 1
                    self.logger.log(f"Account failed\n")

                # Delay between accounts if not the last one
                if account_num < num_accounts:
                    delay = self.random_float(2, 4)
                    await asyncio.sleep(delay)

            except Exception as e:
                self.logger.log(f"Error: {e}\n")
                failed += 1

        # Reset progress
        self.logger.clear_progress()

        self.print_summary(successful, failed)

    def print_summary(self, successful, failed):
        """Print a summary of account creation results"""
        print("\n" + "=" * 60)
        print("ACCOUNT CREATION SUMMARY")
        print("=" * 60)
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total accounts saved: {len(self.created_accounts)}")
        print(f"Accounts saved to: {self.accounts_file}")

        if self.created_accounts:
            print("\nCREATED ACCOUNTS:")
            for i, account in enumerate(self.created_accounts, 1):
                print(f"  {i}. {account['email']}")

        print("=" * 60)
