from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
import os


target_path = r'C:\Users\ameharwade\Downloads'
search_url = 'https://www.google.com/search?tbm=isch&q={q}'
img_urls = []
search_string = ''


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html', button=False, msg='')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        global search_string
        img_urls.clear()
        search_string = request.form['searchWord'].replace(" ", "")
        html = requests.get(search_url.format(q=search_string)).text
        soup = BeautifulSoup(html, 'html5lib')
        for img in soup.find_all('img', class_='t0fcAb'):
            img_urls.append(img['src'])
    return render_template('home.html', images=img_urls,
                           alt_name=search_string, button=True, msg='')


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
                               alt_name=search_string, button=True,
                               msg='Download Failed! Please try again!!')
    return render_template('home.html', images=img_urls,
                           alt_name=search_string, button=False,
                           msg='Download Complete! @{}'.format(path))


@app.route('/about')
def about():
    return render_template('about.html', title='About')


if __name__ == '__main__':
    app.run(debug=True)
