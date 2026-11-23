import json
from flask import Flask, render_template, request, session, redirect, url_for
from helpers import deadline_status

app = Flask(__name__)
app.secret_key = "change-this-later"   # needed for cart/likes via session

def load_internships():
    with open("internships.json") as f:
        return json.load(f)

@app.route("/")
def home():
    internships = load_internships()

    # read filters from the URL, e.g. /?major=MIS&season=Summer
    major = request.args.get("major")
    season = request.args.get("season")
    company = request.args.get("company")
    paid = request.args.get("paid")          # "yes" / "no"

    if major:
        internships = [i for i in internships if i["major"] == major]
    if season:
        internships = [i for i in internships if i["season"] == season]
    if company:
        internships = [i for i in internships if i["company"] == company]
    if paid == "yes":
        internships = [i for i in internships if i["paid"]]
    elif paid == "no":
        internships = [i for i in internships if not i["paid"]]

    # add color status, then sort by most urgent deadline
    for i in internships:
        i["status"] = deadline_status(i["deadline"])
    internships.sort(key=lambda i: i["deadline"])

    return render_template("index.html", internships=internships)

@app.route("/add_to_cart/<int:internship_id>")
def add_to_cart(internship_id):
    cart = session.get("cart", [])
    if internship_id not in cart:
        cart.append(internship_id)
    session["cart"] = cart
    return redirect(url_for("home"))

@app.route("/like/<int:internship_id>")
def like(internship_id):
    likes = session.get("likes", [])
    if internship_id not in likes:
        likes.append(internship_id)
    session["likes"] = likes
    return redirect(url_for("home"))

@app.route("/cart")
def cart():
    ids = session.get("cart", [])
    items = [i for i in load_internships() if i["id"] in ids]
    return render_template("cart.html", items=items)

if __name__ == "__main__":
    app.run(debug=True)
    