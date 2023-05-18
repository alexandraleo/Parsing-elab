from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
# import html5lib
import lxml
import re
import time
from datetime import datetime
from random import randrange
import csv
# import requests

# ARTS = "E-AB-65896, E-AB-65844, E-AB-62136, E-AB-19675, E-AB-15566, E-AB-16323, E-AB-18660, E-AB-14885, E-AB-13160"

SITE_URL = "https://www.elabscience.com/"
# SITE_URL = "https://www.elabscience.com/p-syndecan_1_polyclonal_antibody-389148.html"
# SITE_URL = "https://www.elabscience.com/p-cd20_monoclonal_antibody-24663.html"

# def get_data(url):
#     headers = {
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
#     }
#     # req = requests.get(url, headers)

#     # with open("data\\article-1.html", "w", encoding="utf-8") as file:
#     #     file.write(req.text)
#     with open("data\\article.html", encoding="utf-8") as file:
#         src = file.read()
#     return src

def get_art_page(driver, art):

    time.sleep(2)
    driver.find_element(By.ID, "keywords").send_keys(art + Keys.ENTER)
    time.sleep(5)
    try:
        driver.find_element(By.CLASS_NAME, "products_box").find_element(By.TAG_NAME, "a").click()
    except:
        print('can`t find tag a for art ' + art)
    time.sleep(7)
    driver.switch_to.window(driver.window_handles[1])
    return driver.page_source

def get_soup(html):
    try:
        soup = BeautifulSoup(html, "lxml")
        return soup
    except:
        print('No soup!')

def get_art_structure(soup, art):
    # art = article
    reactivity_dict = {
        "H": "человек",
        "M": "мышь",
        "R": "крыса"
    }

    application_dict = {
        "WB": "вестерн-блоттинга",
        "IHC": "иммуногистохимии",
        "IHC-P": "иммуногистохимии на парафиновых срезах",
        "IF/ICC": "иммунофлуоресцентного/иммуноцитохимического анализа",
        "IF": "иммунофлуоресцентного анализа",
        "IP": "иммунопреципитации",
        "ChIP": "иммунопреципитации хроматина",
        "ChIP-seq": "иммунопреципитации хроматина и высокоэффективного секвенирования",
        "RIP": "иммунопреципитации РНК",
        "FC": "проточной цитометрии",
        "FC(Intra)": "проточной цитометрии (Intra)",
        "ELISA": "ИФА",
        "MeDIP": "иммунопреципитации метилированной ДНК",
        "Nucleotide Array": "исследования нуклеотидных последовательностей",
        "DB": "дот-блоттинга",
        "FACS": "сортировки клеток, активируемых флуоресценцией",
        "CoIP": "коиммунопреципитации",
        "CUT&Tag": "CUT&Tag секвенирование",
        "meRIP": "иммунопреципитации метилированной РНК"
    }

    volume_con = soup.find("ul", class_="mid_xial")
    volumes_f = [volume.get_text().strip() for volume in volume_con.find_all("li")]
    volumes = []
    volume_units = []
    for volume in volumes_f:
        for i in range(0, len(volume)):
            if volume[i].isdigit():
                continue
            else:
                volumes.append(volume[:i])
                volume_units.append(volume[i:].replace("μ", "u").lower())
                break
    prices = [price["data-price"].strip() for price in volume_con.find_all("li")]
    antigen = soup.find("td", string="Abbre").find_next_sibling("td").get_text().strip()
    base_info_cont = soup.find("div", class_="base_info").find_all("li")
    cat_no = art
    reactivity = ""
    host = ""
    appls =""

    for li in base_info_cont:
        if li.get_text().startswith("Cat.No.:"):
            cat_no = li.get_text()[len("Cat.No.:"):].strip()
        elif li.get_text().startswith("Reactivity:"):
            reactivity = li.get_text()[len("Reactivity:"):].strip()
        elif li.get_text().startswith("Host:"):
            host = li.get_text()[len("Host:"):].strip()
        elif li.get_text().startswith("Applications:"):
            appls = li.get_text()[len("Applications:"):].strip()
        else:
            print("no info")
    reactivity_ru = ", ".join([reactivity_dict.get(w.strip(), w.strip()) for w in reactivity.split(",")])
    try:
        clonality = soup.find("td", string="Clonality").find_next_sibling("td").get_text()
    except:
        clonality = "Polyclonal"
    try:
        clone = soup.find("td", string="Clone No.").find_next_sibling("td").get_text()[len("Clone:"):]
    except:
        clone = ""
    title = soup.find("div", class_="details01").find("h1").get_text().strip()
    dilutions = []
    try:
        dilus = soup.find("h4", string="Dilution").find_next_sibling("p").get_text()
        dilus_cl = re.sub(r'\s+', ' ', dilus).split(" ")
        if len(dilus_cl) // 2:
            for i in range(0, len(dilus_cl), 2):
                appl_dilus = " ".join(dilus_cl[i:i+2])
                dilutions.append(appl_dilus)
                # print(appl_dilus)
                if "IHC-P" in appl_dilus:
                    ihc_dilut = appl_dilus[appl_dilus.find("IHC-P") + 6 :]
                    ihc_dilut_text = "иммуногистохимии на парафиновых срезах (рекомендуемое разведение " + ihc_dilut + ")"
                    application_dict["IHC-P"] = ihc_dilut_text
                elif "IHC" in appl_dilus:
                    # print("IHC found")
                    ihc_dilut = appl_dilus[appl_dilus.find("IHC") + 4 :]
                    ihc_dilut_text = "иммуногистохимии (рекомендуемое разведение " + ihc_dilut + ")"
                    # print(ihc_dilut_text)
                    application_dict["IHC"] = ihc_dilut_text
                    # print(application_dict["IHC"])
        else:
            dilutions.extend(dilus_cl)
    except:
        print('An exception occurred')
    text = ("\n").join(dilutions) + "\n" + reactivity
    appls_ru = ", ".join([application_dict.get(w.strip(), w.strip()) for w in appls.split(",")])
    conjug = soup.find("td", string="Conjugation").find_next_sibling("td").get_text().strip()
    storage = soup.find("td", string="Storage").find_next_sibling("td").get_text().strip()
    storage_buff = soup.find("td", string="Buffer").find_next_sibling("td").get_text().strip()
    conc = soup.find("td", string="Concentration").find_next_sibling("td").get_text().strip()

    dict_art_list = []
    for i in range(0, len(volumes)):
        dict_art = {
            "Article": cat_no,
            "Volume": volumes[i],
            "Volume units": volume_units[i],
            "Antigen": antigen,
            "Host": host,
            "Clonality": clonality,
            "Clone_num": clone,
            "Text": text,
            "Applications_ru": appls_ru,
            "Reactivity_ru": reactivity_ru,
            "Title": title,
            "Applications": appls,
            "Dilutions": dilutions,
            "Reactivity": reactivity,
            # "Form": form,
            "Conjugation": conjug,
            "Storage instructions": storage,
            "Storage buffer": storage_buff,
            "Concentration": conc,
            "Price": prices[i],
        }
        dict_art_list.append(dict_art)
    # print(dict_art_list)
    return dict_art_list

def write_csv(result):
    date = datetime.now().strftime('%d.%m.%Y_%H.%M')
    # columns = set(i for d in result for i in d)
    with open("data-elab\\Elabscience_{}.csv".format(date), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=result[0].keys())
        writer.writeheader()
        writer.writerows(result)

def get_articles_list():
    print("Введите список артикулов:")
    articles = [str(art) for art in input().split(",")]
    return articles

# TODO strip art



service = Service("C:\\Users\\Public\\Parsing programs\\chromedriver.exe")
options = webdriver.ChromeOptions()
options.add_argument("--disable-extensions")
# options.add_argument("--disable-gpu")
options.add_argument("--headless")
options.add_argument("--ignore-certificate-errors-spki-list")
options.add_argument("--ignore-ssl-errors")
options.add_argument("--disable-infobars")
options.add_argument('--log-level=3')
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=service, options=options)
driver.maximize_window()
driver.get(SITE_URL)
print("Main site opened")
time.sleep(3)

try:
    cookies = driver.find_element(By.ID, "accept_cookie")
    ActionChains(driver).move_to_element(cookies).click(cookies).perform()
    time.sleep(1)
except:
    print('Can`t find button to accept cookies')
try:
    close_form = driver.find_element(By.ID, "msg_cls")
    ActionChains(driver).move_to_element(close_form).click(close_form).perform()
except:
    print('Can`t close the form')

try:
    # time.sleep(1)
    # src = get_data(SITE_URL)
    # src = driver.page_source ???
    arts = get_articles_list()
    start_time = datetime.now()
    result = []
    counter = 0
    for art in arts:
        # Close a form?
        counter += 1
        print(counter, " art No ", art)
        src = get_art_page(driver, art)
        soup = get_soup(src)
        art_info = get_art_structure(soup, art)
        result.extend(art_info)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    # print(result)
    write_csv(result)
    finish_time = datetime.now()
    spent_time = finish_time - start_time
    print(spent_time)

except Exception as ex:
    print(ex)
finally:
    # driver.close()
    driver.quit()
    print('Driver closed')
