# Import general libraries
import datetime
import pandas as pd
from bs4 import BeautifulSoup as soup
import time
import csv
import json


# Requests package
import requests
requests.packages.urllib3.disable_warnings()
import random
import os

# Improt Selenium packages
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException as NoSuchElementException
from selenium.common.exceptions import WebDriverException as WebDriverException
from selenium.common.exceptions import ElementNotVisibleException as ElementNotVisibleException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
        

def request_page(url_string, verification, robust):
    """HTTP GET Request to URL.
    Args:
        url_string to request.
        verification: Boolean certificate is to be verified
        robust: if to be run in robust mode to recover blocking
    Returns:
        HTML code
    """
    loop = False
    first = True
    if robust:
        # Scrape contents in recovery mode
        c = 0
        while loop or first:
            first = False
            try:
                uclient = requests.get(url_string, timeout = 60, verify = verification)
                page_html = uclient.text
                loop = False
                return page_html
            except requests.exceptions.ConnectionError:
                c += 10
                print("Request blocked, .. waiting and continuing...")
                time.sleep(random.randint(10,60) + c)
                loop = True
                continue
            except (requests.exceptions.ReadTimeout,requests.exceptions.ConnectTimeout):
                print("Request timed out, .. waiting one minute and continuing...")
                time.sleep(60)
                loop = True
                continue
    else:
        uclient = requests.get(url_string, timeout = 60, verify = verification)
        page_html = uclient.text
        loop = False
        return page_html

def open_webpage(driver, url):
    """Opens web page
    Args:
        web driver from previous fct and URL
    Returns:
        opened and maximized webpage
    """
    driver.set_page_load_timeout(200)
    driver.get(url)
    driver.maximize_window()


def request_page_fromselenium(url_string, driver, robust):
    """ Request HTML source code from Selenium web driver to circumvent mechanisms
    active with HTTP requests
    Args:
        Selenium web driver
        URL string
    Returns:
        HTML code
    """
    if robust:
        loop = False
        first = True
        # Scrape contents in recovery mode
        c = 0
        while loop or first:
            first = False
            try:
                open_webpage(driver, url_string)
                time.sleep(5)
                page_html = driver.page_source
                loop = False
                return page_html
            except WebDriverException:
                c += 10
                print("Web Driver problem, .. waiting and continuing...")
                time.sleep(random.randint(10,60) + c)
                loop = True
                continue
    else:
        open_webpage(driver, url_string)
        time.sleep(5)
        page_html = driver.page_source
        loop = False
        return page_html

def set_driver(webdriverpath, headless):
    """Opens a webpage in Chrome.
    Args:
        url of webpage.
    Returns:
        open and maximized window of Chrome with webpage.
    """
    options = Options()  
    if headless:
        options.add_argument("--headless")
    elif not headless:
        options.add_argument("--none")
    return webdriver.Chrome(webdriverpath, chrome_options = options)

def create_object_soup(object_link, driver, robust):
    """ Create page soup out of an object link for a product
    Args:
        object link
        certificate verification parameter
        robustness parameter
    Returns:
        tuple of beautiful soup object and object_link
    """
    html_code = request_page_fromselenium(object_link, driver, robust)
    object_soup = soup(html_code , 'html.parser')
    return (object_soup, object_link)

def make_soup(link, verification):
    """ Create soup of listing-specific webpage
    Args:
        object_id
    Returns:
        soup element containing listings-specific information
    """
    return soup(request_page(link, verification), 'html.parser')

def accept_cookies(driver):
    """ Accepts cookies in order to proceed with clicking elements
    Args:
        web driver
    Returns:
        clicked cookies
    """
    clicked = False
    while not clicked:
#        page_html = driver.page_source
#        page_soup = soup(page_html, 'html.parser')
#        cookies_button_container = page_soup.findAll('div', {'class': 'cc-compliance cc-highlight'})
        try:
            driver.find_element_by_css_selector("body > div.cc-window.cc-banner.cc-type-opt-out.cc-theme-edgeless.cc-bottom.cc-color-override-1243961077 > div > a.cc-btn.cc-allow").click()
        except (NoSuchElementException, ElementNotVisibleException, WebDriverException):
            clicked = True
            break
    print("Successfully accepted Cookies! Continuing process ....")

def reveal_all_items(driver):
    """ Reveal all items by clicking on "view all" button
    Args:
        web driver
    Returns:
        Boolean if all items have been revealed
    """
    hidden = True
    print("Revealing all items...")
    while hidden:
        # Check existence of button
        page_html = driver.page_source
        page_soup = soup(page_html, 'html.parser')
        show_more_button = page_soup.findAll('div', {'class': 'show-more-button-tablet'})
        try:
            time.sleep(random.randint(8,15))
            element = driver.find_element_by_css_selector("section#home-view-container div.show-more-button > button")
            actions = ActionChains(driver)                                                 
            actions.move_to_element(element).perform()
            time.sleep(random.randint(1,2))
            driver.find_element_by_css_selector('section#home-view-container div.show-more-button > button').click()
        except (NoSuchElementException, ElementNotVisibleException, WebDriverException):
            if len(show_more_button) == 0:
                hidden = False
                break
            else:
                print("Button to reveal not clicked well, retrying...")
                continue
    print("All items revealed!")
    return True

def make_jobs_list(base_url, robust, driver):
    """ Extract item URL links and return list of all item links on web page
    Args:
        Base URL
        Robustness parameter
        web driver
    Returns:
        Dictionary with item URLs
    """
    print("Start retrieving item links...")
    on_repeat = False
    first_run = True
    item_links = []
    while on_repeat or first_run:
        first_run = False
        open_webpage(driver, base_url)
        time.sleep(3)
        # Accept cookies
        accept_cookies(driver)
        if reveal_all_items(driver):
            page_html = driver.page_source
            page_soup = soup(page_html, 'html.parser')
            p_link_containers = page_soup.findAll('nb-card', {'class': 'premium__card'})
            n_link_containers = page_soup.findAll('div', {'class': 'card-job'})
            link_containers = p_link_containers +  n_link_containers
            item_links = item_links + [item.a['href'] for item in link_containers]
            # Check if links where extracted
            try:
                assert len(item_links) != 0
                print('Retrieved', len(item_links), 'item links!')
                on_repeat = False
            except AssertionError:
                print("No links extracted", "Repeating process...")
                on_repeat = True
                break
    return item_links 

def open_company_subpage(object_link, driver):
    """ Opens webpage with listings subpage and then gets back to main listings page.
    Args:
        driver
        obect link
    Returns:
        Page soup from subpage
    """
    time.sleep(20)
    try:
        driver.find_element_by_css_selector('div > p.view-company').click()
        time.sleep(random.randint(15,18))
        subpage_soup = soup( driver.page_source, 'html.parser')
        if driver.current_url != object_link:
            driver.back()
            time.sleep(random.randint(2,8))
        else:
            pass
        return subpage_soup
    except (NoSuchElementException, ElementNotVisibleException, WebDriverException):
        return ""
    
def save_page_to_pdf(webdriverpath, object_link, dpath, now_sub_str, idcount):
    """ Saves full webpage to PDF in a given path
    Args:
        webdriver
        object link from Portalpune
        data path
        time stamp
        artificial ID counter for file
    Returns:
        saved PDF in folder with timestamp of scraping
    """
    # Set app state
    appState = {
    "recentDestinations": [
        {
            "id": "Save as PDF",
            "origin": "local",
            "account": ""
        }
    ],
    "selectedDestinationId": "Save as PDF",
    "version": 2
    }
    print("Printing PDF to folder....")
    # Set profile with downloadpath
    profile = {'printing.print_preview_sticky_settings.appState': json.dumps(appState), 
               'savefile.default_directory':dpath}
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs', profile)
    chrome_options.add_argument('--kiosk-printing')
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs', profile)
    chrome_options.add_argument('--kiosk-printing')
    tempdriver = webdriver.Chrome(webdriverpath, chrome_options=chrome_options)
    tempdriver.get(object_link) 
    time.sleep(random.randint(20,25))
    tempdriver.execute_script('window.print();')
    tempdriver.close()
    os.rename(dpath + "Portalpune.pdf", dpath + now_sub_str + "_" + str(idcount) + ".pdf")
  
def save_html_to_text(page_html, time_folder,  now_sub_str, idcount):
    """ Saves each listing as backup in a seperate text file.
    Args:
        bs4 soup element for listing
        output path
        now string for timestamp
    """
    tfile_name = time_folder + "\\" + now_sub_str + "_" + str(idcount) + "_listing" + ".txt"
    with open(tfile_name, "wb") as text_file:
        text_file.write(page_html)

def create_elements(object_link, verification, driver, robust, webdriverpath, dpath, now_sub_str, idcount):
    """Extracts the relevant information form the html container, i.e. object_id, ... + saves PDFs
    Args:
        object_link: URL to scrape
        verification: Boolean certificate is to be verified
        web driver
        robustness parameter
        web driver path
        dpath: data path
        now_sub_str
        idcount
    Returns:
        A dictionary containing the information for one listing
    """
    doc_saved = False
    object_id = str(idcount)
    object_soup = soup(request_page_fromselenium(object_link, driver, robust), 'html.parser')
    # Parse contents
    object_link = object_link
    page_html = object_soup.prettify("utf-8")
    main_container = object_soup.findAll("div", {'class': 'all-basic-details'})
    main_sub_container = object_soup.findAll('div',{'class': 'applied-job-details'})[0].findAll("div", {'class': 'content'})[0]
    # 1.1  Extract company name, phone numbert and residence city of company
    try:
        company_name = main_container[0].findAll('div', {'class': 'jobs-content'})[0].findAll('p', {'class': 'company-title'})[0].text.strip()
    except:
        company_name = ""
    try:
        object_title = main_sub_container.p.text
    except:
        object_title = ''
    try:
       date_container = main_sub_container.findAll('div', {'class':'date'})[0].findAll('span')
       assert len(date_container) == 3
       posting_date = date_container[0].text.strip()
       expiration_date = date_container[2].text.strip()
    except:
       posting_date = ''
       expiration_date = ''
    try:
       job_category = main_container[0].findAll('p', {'class': 'job-categories'})[0].text.strip()
    except:
       job_category = ''
    try:
       contract_type = main_container[0].findAll('p', {'class': 'job-categories'})[1].text.strip()
    except:
       contract_type = ''
    try:
       city =  main_container[0].findAll('p', {'class': 'cities'})[0].text.strip()
    except:
       city = ''
    try:
       vacancy_number = main_sub_container.findAll('div', {'class':'open-positions'})[0].text.replace(" Numri i pozitave të hapura : ","")
    except:
       vacancy_number = ""
    try:
        job_description = main_sub_container.findAll('p', {'class': 'job-content'})[0].text.strip().replace('\xa0','')
        if job_description == "":
            save_page_to_pdf(webdriverpath, object_link, dpath, now_sub_str)
            doc_saved = True
    except:
        job_description = ""
    # Try to find PDF document or JPEG and save it in folder
    try:
        # insrt fct here for subpage
        subpage_soup = open_company_subpage(object_link, driver)
        company_info_container = subpage_soup.findAll('div', {'class': 'company-profile__left-container'})[0].findAll('p', {'class':'details'})
    except:
        company_info_container = []
    try:
        phone_number = company_info_container[1].text.strip()
    except:    
        phone_number = ""
    try:
        company_headoffice = company_info_container[0].text.strip() 
    except:
        company_headoffice = ""
    try:
        # Print page to PDF
        pdf_container = main_sub_container.findAll('div', {'class', 'pdf-container'})
        pdf_container_content = pdf_container[0].findAll('div', {'class': 'textLayer'})
        pdf_description = ""
        for t in pdf_container_content:
            pdf_description = pdf_description + t.text.strip()
        has_document = 1
        if doc_saved == False:
            save_page_to_pdf(webdriverpath, object_link, dpath, now_sub_str, idcount)
    except:
        pdf_description = ""
        has_document = 0
    # Create a dictionary as output
    return  dict([("object_id", object_id),
                 ("object_link", object_link), 
                 ("object_title", object_title),
                 ('company_name', company_name),
                 ('phone_number', phone_number),
                 ('company_headoffice', company_headoffice),
                 ('posting_date', posting_date),
                 ('expiration_date', expiration_date),
                 ('job_category', job_category),
                 ('contract_type',contract_type),
                 ('city', city),
                 ('job_description', job_description),
                 ('pdf_description', pdf_description),
                 ('vacancy_number', vacancy_number),
                 ('has_document', has_document),
                 ('page_html', page_html)])

    
def scrape_portalpune(verification, robust, item_links, time_folder, driver, webdriverpath, dpath):
    """Scraper for portalpune job portal based on specified parameters. Loads website and extracts all containers.
    Then opens subpages, extracts content and then finally returns a dataframe for export. PDFs encountered are saved
    Args:
        verification
        robust
        item_links
    Returns: 
        Appended pandas dataframe with crawled content.
    """
    # Define dictionary for output
    input_dict = {}
    frames = []
    counter = 0
    idcount = 0
    #skipper = 0
    # Loop links
    for item_link in item_links:
        time.sleep(random.randint(20,25))
        print('Parsing next URL...')
        # Set scraping time
        now = datetime.datetime.now()
        try:
            idcount += 1
            now_sub_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            elements = create_elements(item_link, verification, driver, robust, webdriverpath, dpath, now_sub_str, idcount)
            save_html_to_text(elements['page_html'], time_folder, now_sub_str, idcount) 
            del elements['page_html']
            input_dict.update(elements)
            time.sleep(0.5)
            # Create a dataframe   
            df = pd.DataFrame(data = input_dict, index =[now])
            df.index.names = ['scraping_time']
            frames.append(df)
        except requests.exceptions.ConnectionError:
            error_message = "Connection was interrupted, waiting a few moments before continuing..."
            print(error_message)
            time.sleep(random.randint(2,5) + counter)
            continue
    return pd.concat(frames).drop_duplicates(subset = 'object_link')

def main():
    try:
        """ Note: Set parameters in this function
        """
        # Set time stamp 
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
        # Set scraping parameters
        base_url = 'https://www.portalpune.com/'
        robust = True
        webdriverpath = "C:\\Users\\Calogero\\Documents\\GitHub\\job_portal_scrapers\\chromedriver.exe"
        
        # Set up a web driver
        driver = set_driver(webdriverpath, False)
        
        # Start timer
        start_time = time.time() # Capture start and end time for performance
        
        # Set verification setting for certifiates of webpage. Check later also certification
        verification = True
        
        # Enter folders for HTML files, data and final output
        listing_textfile_path = "C:\\Users\\Calogero\\Documents\\GitHub\\job_portal_scrapers\\data\\single_listing_htmls\\"
        dpath = "C:\\Users\\Calogero\\Documents\\GitHub\\job_portal_scrapers\\data\\listing_files\\"
        export_path = 'C:\\Users\\Calogero\\Documents\GitHub\\job_portal_scrapers\\data\\daily_scraping\\'
    
        time_folder = listing_textfile_path + now_str
        os.mkdir(time_folder)
        
        # Execute functions for scraping
        start_time = time.time() # Capture start and end time for performance
        item_links = make_jobs_list(base_url, robust, driver)
        appended_data =  scrape_portalpune(verification, robust, item_links, time_folder, driver, webdriverpath, dpath)
        driver.close()
    
        # Write output to Excel
        print("Writing to Excel file...")
        time.sleep(1)
        file_name = '_'.join([export_path +
        str(now_str), 'portalpune.xlsx'])
        writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
        appended_data.to_excel(writer, sheet_name = 'jobs')
        writer.save()
        
        # Write to CSV
        print("Writing to CSV file...")
        appended_data.to_csv(file_name.replace('.xlsx', '.csv'), sep =";",quoting=csv.QUOTE_ALL)
                    
        end_time = time.time()
        duration = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))
        
        # For interaction and error handling
        final_text = "Your query was successful! Time elapsed:" + str(duration)
        print(final_text)
        time.sleep(0.5)
    except Exception as e:
        print(e)
        input("Press enter to continue...")
        
if __name__ == "__main__":
    main()
