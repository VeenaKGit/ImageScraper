from flask import Flask, render_template, request, redirect, url_for
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import os
import time
import pymongo

DRIVER_PATH = './chromedriver.exe'
target_path = r'C:\Users\ameharwade\Downloads'
search_url = 'https://www.google.com/search?tbm=isch&q={q}'
# work with chrome silently
chrome_options = Options()
chrome_options.add_argument("--headless")


search_string = ""
limit = 10
db_name = 'projectDB'
collection_name = 'ImageScraper'


app = Flask(__name__)
dbConn = pymongo.MongoClient("mongodb://localhost:27017/")

# if database 'db_name' not found, it creates one.
db = dbConn[db_name]
# if table/collection 'collection_name' not found, it creates one.
database = db[collection_name]


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html', images="", alt_name="",
                           button=False, msg='', search_placeholder=search_string,
                           limit_placeholder=limit)


def scroll_to_end(wd):
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    wd.implicitly_wait(5)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        global search_string, limit
        search_string = request.form['searchWord'].replace(" ", "+")
        limit = int(request.form['limit'].replace(" ", "")) if request.form['limit'].replace(" ", "") else limit
        stock_limit, found = query_db(search_string)
        if not found:
            create_doc(search_string)
        if limit - stock_limit > 0:
            thumbnail_results = []
            counter = stock_limit
            with webdriver.Chrome(executable_path=DRIVER_PATH, chrome_options=chrome_options) as wd:
                wd.get(search_url.format(q=search_string))  # load the page
                while len(thumbnail_results) < limit:
                    thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")  # thumbnail images
                    scroll_to_end(wd)

                for img in thumbnail_results:
                    if counter < limit:
                        try:
                            img.click()
                            time.sleep(2)
                        except Exception as e:
                            print("Could not click the ThumbNail {}".format(e))
                            continue
                        actual_images = wd.find_elements_by_css_selector('img.n3VNCb')  # enlarged image on right
                        for image in actual_images:
                            if image.get_attribute('src') and 'http' in image.get_attribute('src'):
                                print('image {}- {}'.format(counter, image.get_attribute('src')))
                                if write_db(image.get_attribute('src')):
                                    counter += 1
                    else:
                        break

    return render_template('home.html', images=query_db(search_string)[1], alt_name=search_string,
                           button=True, msg='', search_placeholder=search_string, limit_placeholder=limit)


def write_db(url):
    update_filter = {"search_string": search_string}
    ack = database.update_one(update_filter, {"$addToSet": {'img_urls': url}})
    if ack.modified_count:
        database.update_one(update_filter, {'$set': {'limit': (database.find_one(update_filter)['limit'] + 1)}})
    return ack.modified_count


def create_doc(name):
    doc_format = {
        "search_string": name,
        "limit": 0,
        "img_urls": []
    }
    return database.insert_one(doc_format).acknowledged


def query_db(query_string):
    limit_value = 0
    urls = []
    if database.find_one({'search_string': query_string}):
        limit_value = database.find_one({'search_string': query_string})['limit']
        urls = database.find_one({'search_string': query_string})['img_urls'] \
            [0:limit if (limit <= limit_value) else limit_value]
    return limit_value, urls


def create_folder(name):
    target_folder = os.path.join(target_path, '_'.join(name.lower().split(' ')))
    try:
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
            return True, target_folder
    except Exception as e:
        print('Error: Folder could not be created {}'.format(e))
    return False, None


@app.route('/download', methods=['get', 'POST'])
def download():
    global search_string, limit
    image_urls = query_db(search_string)[1]
    if image_urls:
        status, path = create_folder(search_string)
        counter = 0
        for img_url in image_urls:
            try:
                image_content = requests.get(img_url).content
            except Exception as e:
                print('Error - No content in URL {}-{}'.format(img_url, e))
            if status:
                try:
                    with open(os.path.join(path, search_string + "_" + str(counter) + ".jpg"), 'wb') as f:
                        f.write(image_content)
                    counter += 1
                except Exception as e:
                    print('Error - Download failed {}'.format(e))
    else:
        return render_template('home.html', images=image_urls, alt_name=search_string, button=True,
                               msg='Download Failed! Please try again!!',
                               search_placeholder=search_string, limit_placeholder=limit)
    return render_template('home.html', images=image_urls, alt_name=search_string, button=False,
                           msg='Download Complete! @{}'.format(path),
                           search_placeholder=search_string, limit_placeholder=limit)


@app.route('/about')
def about():
    return render_template('about.html', title='About')


if __name__ == '__main__':
    app.run(debug=True)
