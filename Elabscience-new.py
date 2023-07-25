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
    time.sleep(3)
    try:
        cards = driver.find_elements(By.CLASS_NAME, "products_box")
        # for card in cards.find_element(By.TAG_NAME, "a")
        if len(cards) > 1:
            print("Кол-во карточек больше 1: ", len(cards))
        driver.find_element(By.CLASS_NAME, "products_box").find_element(By.TAG_NAME, "a").click()
    except:
        print('can`t find tag a for art ' + art)

    # TODO обработка несуществующих артикулов E-AB-66377
    # TODO ihc dilution with , and without
    # TODO E-AB-40052 10:50-1:10
    # TODO E-AB-66167 no antigen
    # TODO concentrated and rtu
    #

    time.sleep(5)
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
        "R": "крыса",
        "Mk": "обезьяна",
        "Dg": "собака",
        "Ch": "курица",
        "Hm": "хомяк",
        "Rb": "кролик",
        "Sh": "овца",
        "Pg": "свинья",
        "Z": "Данио",
        "X": "Ксенопус",
        "C": "корова"
    }

    application_dict = {
        "WB": "вестерн-блоттинга",
        "IHC": "иммуногистохимии",
        "IHC-P": "иммуногистохимии на парафиновых срезах",
        "IHC-p": "иммуногистохимии на парафиновых срезах",
        "IF/ICC": "иммунофлуоресцентного/иммуноцитохимического анализа",
        "IF": "иммунофлуоресцентного анализа",
        "IP": "иммунопреципитации",
        "ChIP": "иммунопреципитации хроматина",
        "ChIP-seq": "иммунопреципитации хроматина и высокоэффективного секвенирования",
        "RIP": "иммунопреципитации РНК",
        "FC": "проточной цитометрии",
        "FCM": "проточной цитометрии",
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
    volumes = []
    volume_units = []
    prices = []
    if volume_con:
        volumes_f = [volume.get_text().strip() for volume in volume_con.find_all("li")]
        prices = [price["data-price"].strip() for price in volume_con.find_all("li")]
        for volume in volumes_f:
            for i in range(0, len(volume)):
                if volume[i].isdigit():
                    continue
                else:
                    volumes.append(volume[:i])
                    volume_units.append(volume[i:].replace("μ", "u").lower())
                    break
    else:
        print("No volumes and prices")

    antigen_con = soup.find("td", string="Abbre")
    title_path = soup.find("div", class_="details01").find("h1")
    alt_info_con = soup.find("div", class_="pro_b02_btm")
    if antigen_con:
        antigen = antigen_con.find_next_sibling("td").get_text().strip()
    elif title_path:
        title_txt = title_path.get_text().strip()
        if "monoclonal" in title_txt.lower():
            clonality = "Monoclonal"
        elif "polyclonal" in title_txt.lower():
            clonality = "Polyclonal"
        else:
            clonality = ""
        antigen = title_txt[:title_txt.find(clonality)].strip()
    else:
        print("No antigen")
        antigen = ""
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

    clonality_con = soup.find("td", string="Clonality")
    clone_con = soup.find("td", string="Clone No.")
    if clonality_con:
        clonality = clonality_con.find_next_sibling("td").get_text()
    else:
        if clone_con:
            clonality = "Monoclonal"
        else:
            clonality = "Polyclonal"

    if clone_con:
        clone_txt = clone_con.find_next_sibling("td").get_text().strip()
        # print(clone_txt)
        if "Clone:" in clone_txt:
            clone = clone_txt[clone_txt.find("Clone:"):]
        elif "(See Other Available Formats)" in clone_txt:
            clone = clone_txt[:clone_txt.find("(See Other Available Formats)")]
        else:
            clone = clone_txt
    else:
        clone = ""

    title = soup.find("div", class_="details01").find("h1").get_text().strip()
    dilutions = []
    dilus_con = soup.find("h4", string="Dilution")
    ihc_dilut = ""
    if dilus_con:
        dilus = dilus_con.find_next_sibling("p").get_text()
        dilus_cl = re.sub(r'\s+', ' ', dilus).split(" ")
        if len(dilus_cl) // 2:
            for i in range(0, len(dilus_cl), 2):
                appl_dilus = " ".join(dilus_cl[i:i+2])
                dilutions.append(appl_dilus)

                if "IHC-P" in appl_dilus:
                    ihc_dilut = appl_dilus[appl_dilus.find("IHC-P") + 6 : appl_dilus.find(",")]
                elif "IHC" in appl_dilus:
                    ihc_dilut = appl_dilus[appl_dilus.find("IHC") + 4 : appl_dilus.find(",")]
                elif "IHC-p" in appl_dilus:
                    ihc_dilut = appl_dilus[appl_dilus.find("IHC-p") + 6 : appl_dilus.find(",")]
        else:
            dilutions.extend(dilus_cl)
    else:
        print('No dilus')
        dilutions = []
    # print(ihc_dilut)
    if len(ihc_dilut) > 0:
        application_dict["IHC-P"] = "иммуногистохимии на парафиновых срезах (рекомендуемое разведение " + ihc_dilut + ")"
        application_dict["IHC"] = "иммуногистохимии (рекомендуемое разведение " + ihc_dilut + ")"
        application_dict["IHC-p"] = "иммуногистохимии на парафиновых срезах (рекомендуемое разведение " + ihc_dilut + ")"

    if len(dilutions) > 0:
        text = ("\n").join(dilutions) + "\n" + reactivity
    else:
        text = appls + "\n" + reactivity
    appls_ru = ", ".join([application_dict.get(w.strip(), w.strip()) for w in appls.split(",")])
    conjug_con = soup.find("td", string="Conjugation")
    if conjug_con:
        conjug = conjug_con.find_next_sibling("td").get_text().strip()
        if conjug == "Unconjugated":
            conjug = ""
    else:
        conjug = ""
    storage_con = soup.find("td", string="Storage")
    if storage_con:
        storage = storage_con.find_next_sibling("td").get_text().strip()
    else:
        storage =""

    storage_buff_con = soup.find("td", string="Buffer")
    if storage_buff_con:
        storage_buff = storage_buff_con.find_next_sibling("td").get_text().strip()
    else:
        storage_buff = ""

    conc_con = soup.find("td", string="Concentration")
    if conc_con:
        conc = conc_con.find_next_sibling("td").get_text().strip()
    else:
        conc = ""

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
            "Conjugation": conjug,
            "Title": title,
            "Applications": appls,
            "Dilutions": dilutions,
            "Reactivity": reactivity,
            # "Form": form,
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
    articles = [str(art).strip() for art in input().split(",")]
    return articles


service = Service("C:\\Users\\Public\\Parsing programs\\chromedriver.exe")
options = webdriver.ChromeOptions()
options.add_argument("--disable-extensions")
# options.add_argument("--disable-gpu")
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
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
