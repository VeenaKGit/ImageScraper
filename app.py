from flask import Flask, render_template, request
from selenium import webdriver
import requests
import os
import time


target_path = r'C:\Users\ameharwade\Downloads'
search_url = 'https://www.google.com/search?tbm=isch&q={q}'
img_urls = []
search_string = ''
buffer = 10

# chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html', button=False, msg='')


def scroll_to_end(wd):
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    wd.implicitly_wait(5)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        global search_string, img_urls, limit
        img_urls.clear()
        search_string = request.form['searchWord'].replace(" ", "+")
        limit = int(request.form['limit'].replace(" ", "")) if request.form['limit'].replace(" ", "") else 10

        thumbnail_results = []
        counter = 0
        with webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options) as wd:
            wd.get(search_url.format(q=search_string)) # load the page
            while len(thumbnail_results) < (limit + buffer):
                thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")  # thumbnail images
                scroll_to_end(wd)

            for img in thumbnail_results:
                if counter < limit:
                    try:
                        img.click()
                        time.sleep(2)
                    except Exception as e:
                        print("Count not click the ThumbNail {}".format(e))
                        continue
                    actual_images = wd.find_elements_by_css_selector('img.n3VNCb')  # enlarged image on right

                    for image in actual_images:
                        if image.get_attribute('src') and 'http' in image.get_attribute('src'):
                            print('image {}- {}'.format(counter, image.get_attribute('src')))
                            counter += 1
                            img_urls.append(image.get_attribute('src'))
                else:
                    break

    return render_template('home.html', images=img_urls,
                           alt_name=search_string, button=False, msg='')


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
    global img_urls, search_string
    if img_urls:
        status, path = create_folder(search_string)
        counter = 0
        for img_url in img_urls:
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
                    print('Error - Download failed {}'. format(e))
    else:
        return render_template('home.html', images=img_urls,
                               alt_name=search_string, button=False,
                               msg='Download Failed! Please try again!!')
    return render_template('home.html', images=img_urls,
                           alt_name=search_string, button=False,
                           msg='Download Complete! @{}'.format(path))


@app.route('/about')
def about():
    return render_template('about.html', title='About')


if __name__ == '__main__':
    app.run(debug=True)
