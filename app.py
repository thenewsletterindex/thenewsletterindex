import pymongo
from pymongo import MongoClient
from flask import Flask, redirect, render_template, request, url_for, session, jsonify
from datetime import datetime, date
import base64
import secrets
import pprint
import firebase_admin
from firebase_admin import credentials, auth
import requests



file = open("password.txt", "r") 
password = file.read()


app = Flask(__name__)

cred = credentials.Certificate('firebaseservice.json')
firebase_admin.initialize_app(cred)



app.secret_key = 'YOUR SECRET KEY'

cluster = MongoClient(f"YOUR MONGODB URL")
db = cluster["newsletter"]
collection = db["newsletter"]



def fuzzyMatching(query):
    result = collection.aggregate([
        {
            "$search": {
                "index": "default",
                "text": {
                    "query": query,
                    "path": ["category", "name", "url", "short_description", "long_description", "rss", "rssurl"],
                    "fuzzy": {}
                }
            }
        }
    ])
    x = list(result)
    print(x)
    return x


@app.route("/search/<q>", methods=["GET"])
def search(q):
    if q != "":
        results = fuzzyMatching(q)
        res = []
        for i in results:
            res.append(i)
        print(res)
        try:
            if res:
                return render_template("search.html", list = res, letter2 = True)
            else:
                return render_template("search.html", letter = False)
        except:
            return render_template("search.html", letter = False)
        
    else:
        return redirect("/")

@app.route("/search", methods=["GET", "POST"])
def searchbar():
    if request.method == "POST":
        q = request.form.get("q")
        return redirect(f"/search/{q}")
    return render_template("searchbar.html")
    
@app.route("/", methods=["GET"])
def index():
    results = collection.find({})
    listOfVPD = []
    for i in results:
        listOfVPD.append(i)
    listOfVPD = sorted(listOfVPD, key=lambda x: x["vpd"], reverse=True)
    listOfVPD[:20]
    return render_template("index.html", list = listOfVPD)

@app.route("/category/<category>", methods=["GET"])
def category(category):
    res = collection.find({"category": category})
    resl = []
    for i in res:
        resl.append(i)
    if resl:
        results = collection.find({"category": category})
        listOfVPD = []
        for i in results:
            listOfVPD.append(i)
        listOfVPD = sorted(listOfVPD, key=lambda x: x["vpd"], reverse=True)
        listOfVPD[:20]
        return render_template("category.html", list = listOfVPD, category=category)

    else:
        return redirect("/")


@app.route("/api/search/", methods=["GET"])
def apiSearch():
        q = request.headers.get("query")
        if q:
            results = fuzzyMatching(q)
            res = []
            for i in results:
                del i['logo']
                del i ["creator"]
                res.append(i)
                print(res)
            try:
                if res:
                    return jsonify(res)
                else:
                    x = ["NOTHING"]
                    return jsonify(x)
            except:
                x = ["ERROR"]
                return jsonify(x)
            
@app.route("/api/advancedsearch/", methods=["GET"])
def advancedSearch():
    try:
        query = {}
        id = request.headers.get("_id")
        url = request.headers.get("url")
        rss = request.headers.get("rss")
        rssurl = request.headers.get("rssurl")
        votes = request.headers.get("votes")
        sentat = request.headers.get("sentat")
        free = request.headers.get("free")
        if id:
            query["_id"] = id
        if url:
            query["url"] = url
        if rss:
            query["rss"] = rss
        if rssurl:
            query["rssurl"] = rssurl
        if votes:
            votes = int(votes)
            query["votes"] = votes
        if sentat:
            query["sentat"] = sentat
        if free:
            query["free"] = free
        if query:
            print(query)
            results = collection.find(query)
            res = []
            for i in results:
                del i["logo"]
                del i["creator"]
                res.append(i)
            print(res)
            if res:
                return jsonify(res)
            else:
                x = ["NORESULTS"]
                return jsonify(x)
        else:
            x = ["NOQUERY"]
            return jsonify(x)
            
    except Exception as e:
        print(e)
        x = ["ERROR"]
        return jsonify(x)
    

@app.route("/robots.txt", methods=["GET"])
def robots():
    return "Scraping Is Allowed. Limit To 10 Requests Per Day Though. Absolutely No Request Spamming/DDoS."

@app.route("/api/", methods=["GET"])
def api():
    return redirect("https://colab.research.google.com/drive/1LmVcKBaJdEIe6pWDzxY1WpkqR8NNMENH?usp=sharing")

@app.route("/findanewsletter", methods=["GET", "POST"])
def findanewsletter():
    if request.method == "POST":
        readtime = request.form['readtime']
        writingstyle = request.form['writingstyle']
        category = request.form['category']
        sentat = request.form["sentat"]
        free = request.form["free"]
        rss = request.form["rss"]

        return redirect(f"/findanewsletter/{readtime}/{writingstyle}/{category}/{sentat}/{free}/{rss}")
    return render_template("findanewsletter.html")

@app.route("/findanewsletter/<readtime>/<writingstyle>/<category>/<sentat>/<free>/<rss>", methods={"GET", "POST"})
def resfindanewsletter(readtime, writingstyle, category, sentat, free, rss):
    try:
        results = collection.find({
            "readtime": readtime,
            "category": category,
            "writingstyle": writingstyle,
            "sentat": sentat,
            "free": free,
            "rss": rss

                                    })
        list = []
        print(writingstyle)
        for letter in results:
            list.append(letter)
        if list:
            return render_template("resfindanewsletter.html", results=True, letters=list)
        else:
            return render_template ("resfindanewsletter.html", results=False)
    except Exception as e:
        print(e)
        return redirect("/")

    return render_template("findanewsletter.html")

@app.route("/all/category/<category>", methods=["GET"])
def allcat(category):
    res = collection.find({"category": category})
    resl = []
    for i in res:
        resl.append(i)
    if resl:
        results = collection.find({"category": category})
        listOfVPD = []
        for i in results:
            listOfVPD.append(i)
        listOfVPD = sorted(listOfVPD, key=lambda x: x["vpd"], reverse=True)
        return render_template("allcat.html", list = listOfVPD, category=category)

    else:
        return redirect("/")

@app.route("/rss")
def justrss():
    res = collection.find({"rss": "RSS Feed"})
    resl = []
    for i in res:
        resl.append(i)
    if resl:
        results = collection.find({"rss": "RSS Feed"})
        listOfVPD = []
        for i in results:
            listOfVPD.append(i)
        listOfVPD = sorted(listOfVPD, key=lambda x: x["vpd"], reverse=True)
        listOfVPD[:20]
        return render_template("rss.html", list = listOfVPD)
    
@app.route("/all/rss")
def allrss():
    res = collection.find({"rss": "RSS Feed"})
    resl = []
    for i in res:
        resl.append(i)
    if resl:
        results = collection.find({"rss": "RSS Feed"})
        listOfVPD = []
        for i in results:
            listOfVPD.append(i)
        listOfVPD = sorted(listOfVPD, key=lambda x: x["vpd"], reverse=True)
        return render_template("allrss.html", list = listOfVPD)
    
@app.route("/all/newsletters")
def alln():
    res = collection.find({"rss": "Newsletter"})
    resl = []
    for i in res:
        resl.append(i)
    if resl:
        results = collection.find({"rss": "Newsletter"})
        listOfVPD = []
        for i in results:
            listOfVPD.append(i)
        listOfVPD = sorted(listOfVPD, key=lambda x: x["vpd"], reverse=True)
        return render_template("alln.html", list = listOfVPD)

@app.route("/newsletters")
def n():
    res = collection.find({"rss": "Newsletter"})
    resl = []
    for i in res:
        resl.append(i)
    if resl:
        results = collection.find({"rss": "Newsletter"})
        listOfVPD = []
        for i in results:
            listOfVPD.append(i)
        listOfVPD = sorted(listOfVPD, key=lambda x: x["vpd"], reverse=True)
        listOfVPD[:20]
        return render_template("n.html", list = listOfVPD)


@app.route("/new")
def new():
    datecreated1 = date.today()
    datecreated = str(datecreated1)
    results = collection.find({"datecreated": datecreated})
    listOfVPD = []
    for i in results:
        listOfVPD.append(i)
    try:
        if listOfVPD:
            listOfVPD = sorted(listOfVPD, key=lambda x: x["vpd"], reverse=True)
            listOfVPD[:20]
            return render_template("new.html", list = listOfVPD)
        else:
            return redirect("/")
    except:
        return redirect("/")
    
@app.route("/all/new")
def allnew():
    datecreated1 = date.today()
    datecreated = str(datecreated1)
    results = collection.find({"datecreated": datecreated})
    for i in results:
        listOfVPD.append(i)
    try:
        if listOfVPD:
            listOfVPD = sorted(listOfVPD, key=lambda x: x["vpd"], reverse=True)
            return render_template("allnew.html", list = listOfVPD)
        else:
            return redirect("/")
    except Exception:
        return redirect("/")
    
    

@app.route("/highestrated")
def highestrated():
    results = collection.find({})
    listOfVPD = []
    for i in results:
        listOfVPD.append(i)
    listOfVPD = sorted(listOfVPD, key=lambda x: x["votes"], reverse=True)
    listOfVPD[:20]
    return render_template("highestrated.html", list = listOfVPD)


@app.route("/all", methods=["GET"])
def all():
    results = collection.find({})
    listOfVPD = []
    for i in results:
        listOfVPD.append(i)
    listOfVPD = sorted(listOfVPD, key=lambda x: x["vpd"], reverse=True)
    return render_template("all.html", list = listOfVPD)

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            apiKey = "AIzaSyBkFdllHHhw92zJ18rMv42--AQvzxUrWmY"
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={apiKey}"

            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                user = response.json()
                session['user'] = user
                return redirect("/dash")
            else:
                return render_template("signin.html", error=True)
        except Exception as e:
            print(e)
            return render_template("signin.html", error=True)
            
    return render_template("signin.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            user = auth.create_user(
            email=email,
            password=password,
            )
            return redirect("/signin")
        except Exception as e:
            print(e)
            return render_template("signup.html", error=True)

    return render_template("signup.html")

@app.route("/dash", methods=["GET"])
def dash():
    if "user" in session:
        user = session.get("user")
        email = user["email"]
        results = collection.find({"creator":email})
        rlist = []
        modresultlist = []
        for result in results:
            rlist.append(result)
            
    

        return render_template("dash.html", list = rlist)
    else:
        return redirect("/signin")
    
@app.route("/letters/<id>", methods=["GET", "POST"])
def letters(id):
    results = collection.find({"_id":id})
    x = ""
    for result in results:
        x = "a"
        result = result
    if x == "":
        return render_template("letters.html", error=True)
    else:
        return render_template("letters.html", result=result)
    

@app.route("/vote/<id>")
def vote(id):
    res = collection.find({"_id": id})
    resl = []
    for i in res:
        resl.append(i)
    if resl:
        print("yes result")
        results = collection.update_one({"_id": id}, { "$inc": { "votes": 1 }})
        results2 = collection.find({"_id": id})
        resl2 = []
        for i in results2:
            resl2.append(i)
        date1a = resl2[0]["datecreated"]
        date1aa = datetime.strptime(date1a, '%Y-%m-%d')
        date1 = date1aa.date()
        date2 = date.today()
        delta = date1 - date2
        days = delta.days
        days = abs(days)
        if date2 == date1:
            days += 1
        currentv = resl2[0]["votes"]
        vpd = days/currentv
        update = collection.update_one({"_id": id}, {"$set": {"vpd": vpd}})
        return redirect(f"/letters/{id}")
    else:
        print("no resul")
        return redirect(f"/letters/{id}")
    
@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/create", methods=["GET", "POST"])
def create():
    if "user" in session:
        if request.method == "POST":
            rss = request.form.get("rss")
            if rss == "RSS Feed":
                rssurl = request.form.get("rssurl")
            else:
                rssurl = ""
            free = request.form.get("free")
            sentat = request.form.get("sentat")
            name = request.form.get('name')
            logo = request.files.get('logo')
            short_description = request.form.get('short_description')
            long_description = request.form.get('long_description')
            url = request.form.get('url')
            contact_email = request.form.get('contact_email')
            category = request.form.get("category")
            datecreated1 = date.today()
            datecreated = str(datecreated1)
            user = session.get("user")
            email = user["email"]
            readtime = request.form.get("readtime")
            writingstyle = request.form.get("writingstyle")
            if logo:
                logo2 = base64.b64encode(logo.read()).decode('utf-8')
            else:
                logo = ""
            
            id = secrets.token_urlsafe(16)

            post2Mongo = {
                "_id":id,
                "name":name,
                            "rss": rss,
                           "logo":logo2,
                             "short_description":short_description,
                               "long_description":long_description,
                               "url":url,
                               "contact_email":contact_email,
                               "category":category,
                               "datecreated":datecreated,
                               "creator":email,
                               "writingstyle":writingstyle,
                               "readtime":readtime,
                               "sentat": sentat,
                               "rssurl": rssurl,
                               "free": free,
                               "votes": 0,
                               "vpd": 0

                          }
            print(collection)
            collection.insert_one(post2Mongo)
            return redirect("/dash")
        return render_template("create.html")
    else:
        return redirect("/signin")




if __name__ == "__main__":
    app.run(debug=True)

