from flask import render_template
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask import Flask, request
from flask_jwt_extended import create_access_token, JWTManager
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import csv
import datetime

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "please-remember-to-change-me"
jwt = JWTManager(app)

mysql = MySQL()
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12qw!@QW'
app.config['MYSQL_DB'] = 'Scraping'
mysql = MySQL(app)
CORS(app)

#url = 'https://www.ubereats.com/au/store/bws-balaclava/6N4qPwGdXAKyJv_acN3cnA/3c4b6860-e5d8-507b-975b-29319623df37/2082e1f3-d2d0-5ebe-99d6-5de7a380ea07/6d10654b-e9d7-5588-9131-2a4ae1548d1f?diningMode=DELIVERY&ps=1'
# url = 'https://www.ubereats.com/au/store/iga-liquor-east-brighton/6ggwdvL3TcGdZ9Qx2qzSTw?diningMode=DELIVERY&pl=JTdCJTIyYWRkcmVzcyUyMiUzQSUyMjc2NUElMjBIYXd0aG9ybiUyMFJkJTIyJTJDJTIycmVmZXJlbmNlJTIyJTNBJTIyQ2hJSkR6RlN3VHBwMW1vUkJYU2d6UXpVc0w0JTIyJTJDJTIycmVmZXJlbmNlVHlwZSUyMiUzQSUyMmdvb2dsZV9wbGFjZXMlMjIlMkMlMjJsYXRpdHVkZSUyMiUzQS0zNy45MTM4NzklMkMlMjJsb25naXR1ZGUlMjIlM0ExNDUuMDE3MTU1JTdE&ps=1'
product =[]

@app.route("/")
def home():
    time = datetime.datetime.now()
    return render_template(
        "hello_there.html",
        date=time
    )

@app.route("/scrapping", methods=['GET', 'POST'])
def scrapping():
    # url = request.json.get("url", None)
    # url = request.form['url']
    url = request.args.get('url')
    
    product.clear()

    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,60000")
    # Replace YOUR-PATH-TO-CHROMEDRIVER with your chromedriver location
    driver = webdriver.Chrome(options=options, executable_path=ChromeDriverManager().install())
    page = driver.get(url) # Getting page HTML through request

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    ul = soup.findAll('ul', {"class": "cf"})
    if ul==[]:
        ul = soup.findAll('ul', {"class": "bu"})

    store = driver.find_element(By.XPATH, "//*[@id='main-content']/div[3]/div/div/h1").text
    if store ==[]:
        store = soup.findAll("h1", {"class": "fj"})

    store_address = soup.findAll("div", {"class": "bb"})[0].text

    j = 1
    for li in ul[0]:
        product_title = li.findAll("div", {"class": "ax"})
        product_price = li.findAll("span", {"class": "ax"})
        if product_price == []:
            product_price = li.findAll("div", {"class": "ee"})
        product_images = li.select('img')
        
        i = 1
        for price in product_price:
            tmp_title = product_title[i].text
            pack_start_location = tmp_title.find("(")
            if pack_start_location > -1:
                pack_end_location = tmp_title.find("Pack")
                title = tmp_title[0:pack_start_location]
                pack = tmp_title[pack_start_location+1: pack_end_location]
            else:    
                title = tmp_title
                pack = ""
            if len(product_images) < i:
                image_url = ""
            else:
                image_url = product_images[i-1].get('src')

            product.append({"No": j, 
                            "Store Name": store,
                            "Store Address": store_address, 
                            "Category": product_title[0].text, 
                            "Sub Category":product_title[0].text, 
                            "Product Name": title, 
                            "Pack Size": pack, 
                            "Price": price.text, 
                            "Image": image_url 
            })
            i += 1
            j += 1
    response = {"scraping": product}
    return render_template(
        "hello_there.html",
        data=product
    )

@app.route("/csv", methods=['get'])
def exportcsv():
    time = datetime.datetime.now()

    filename = time.strftime("%f")+".csv"

    # filename = 'titles.csv'
    with open(filename, 'w', newline='') as f:
        w = csv.DictWriter(f,['No','Store Name','Store Address','Category','Sub Category','Product Name','Pack Size','Price','Image'])
        w.writeheader()
        
        w.writerows(product)
    
    # response = {"filename": filename}
    return render_template(
        "hello_there.html",
        export=filename,
        data = product
    )

@app.route('/register', methods=['POST'])
def register():
    firstName = request.json.get("first_name", None)
    lastName = request.json.get("last_name", None)
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    changepassword = request.json.get("password_confirmation", None)
    access_token = create_access_token(identity=email)

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email LIKE %s", [email])
    user = cursor.fetchone()
    if user:
        return {"msg": "Wrong email or password"}, 401

    cursor.execute("SELECT Max(id) FROM users")
    id = cursor.fetchone()
    cursor.execute(''' INSERT INTO users VALUES(%s, %s, %s, %s, %s, %s)''', (id[0]+1, firstName, lastName, email, password, access_token))
    mysql.connection.commit()
    cursor.close()
    response = {"api_token": access_token}
    return response

@app.route('/login', methods=['POST'])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    user = cursor.fetchone()
    if user:
        access_token = create_access_token(identity=email)
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE users SET token = %s WHERE id = %s", (access_token, user[0]))
        mysql.connection.commit()
        cursor.close()
        response = {"api_token": access_token}
        return response
    else:
        return {"msg": "Wrong email or password"}, 401

@app.route('/verify_token', methods=['POST'])
def verify():
    access_token = request.json.get("api_token", None)
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE token LIKE %s", [access_token])
    userinfo = cursor.fetchone()
    cursor.close()

    if userinfo:
        # response = {"api_token": userinfo}
        response = {"id": userinfo[0], "password":userinfo[4], "email":userinfo[3], "first_name":userinfo[1], "last_name":userinfo[2] }
        return response
    else:
        return {"msg": "Wrong email or password"}, 401
