#!/usr/bin/env python3

import os
import sys
import subprocess
import datetime

from flask import Flask, render_template, request, redirect, url_for, make_response

# import logging
import sentry_sdk
from sentry_sdk.integrations.flask import (
    FlaskIntegration,
)  # delete this if not using sentry.io

# from markupsafe import escape
import pymongo
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from dotenv import load_dotenv

# load credentials and configuration options from .env file
# if you do not yet have a file named .env, make one based on the template in env.example
load_dotenv(override=True)  # take environment variables from .env.

# initialize Sentry for help debugging... this requires an account on sentrio.io
# you will need to set the SENTRY_DSN environment variable to the value provided by Sentry
# delete this if not using sentry.io
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    # enable_tracing=True,
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
    integrations=[FlaskIntegration()],
    send_default_pii=True,
)

# instantiate the app using sentry for debugging
app = Flask(__name__)

# # turn on debugging if in development mode
# app.debug = True if os.getenv("FLASK_ENV", "development") == "development" else False

# try to connect to the database, and quit if it doesn't work
try:
    cxn = pymongo.MongoClient(os.getenv("MONGO_URI"))
    db = cxn[os.getenv("MONGO_DBNAME")]  # store a reference to the selected database

    # verify the connection works by pinging the database
    cxn.admin.command("ping")  # The ping command is cheap and does not require auth.
    print(" * Connected to MongoDB!")  # if we get here, the connection worked!
except ConnectionFailure as e:
    # catch any database errors
    # the ping command failed, so the connection is not available.
    print(" * MongoDB connection error:", e)  # debug
    sentry_sdk.capture_exception(e)  # send the error to sentry.io. delete if not using
    sys.exit(1)  # this is a catastrophic error, so no reason to continue to live


# set up the routes

@app.route("/")
def home():
    """
    Route for the home page.
    Simply returns to the browser the content of the index.html file located in the templates folder.
    """
    return render_template("index.html")


@app.route("/read")
def read():
    """
    Route for GET requests to the read page.
    Displays some information for the user with links to other pages.
    """
    docs = db.reviews.find({}).sort(
        "created_at", -1
    )  # sort in descending order of created_at timestamp
    return render_template("read.html", docs=docs)  # render the read template


@app.route("/create")
def create():
    """
    Route for GET requests to the create page.
    Displays a form users can fill out to create a new document.
    """
    return render_template("create.html")  # render the create template


@app.route("/create", methods=["POST"])
def create_post():
    """
    Route for POST requests to the create page.
    Accepts the form submission data for a new document and saves the document to the database.
    """
    username = request.form["username"]
    recipe_name = request.form["recipe_name"]
    review = request.form["review"]

    # create a new document with the data the user entered
    doc = {"username": username, "recipe_name": recipe_name, "review": review, "created_at": datetime.datetime.utcnow()}
    db.reviews.insert_one(doc)  # insert a new document

    return redirect(
        url_for("read")
    )  # tell the browser to make a request for the /read route


@app.route("/edit_review/<mongoid>")
def edit(mongoid):
    """
    Route for GET requests to the edit page.
    Displays a form users can fill out to edit an existing record.

    Parameters:
    mongoid (str): The MongoDB ObjectId of the record to be edited.
    """
    doc = db.reviews.find_one({"_id": ObjectId(mongoid)})
    username = doc["username"]
    return render_template(
        "edit.html", mongoid=mongoid, doc=doc, username = username
    )  # render the edit template


@app.route("/edit_review/<mongoid>", methods=["POST"])
def edit_post(mongoid):
    """
    Route for POST requests to the edit page.
    Accepts the form submission data for the specified document and updates the document in the database.

    Parameters:
    mongoid (str): The MongoDB ObjectId of the record to be edited.
    """

    review = request.form["review"]

    db.reviews.update_one(
        {"_id": ObjectId(mongoid)},
        {"$set": {"review": review}},
    )

    review_doc = db.reviews.find_one({"_id": ObjectId(mongoid)})
    username = review_doc["username"]

    return redirect(url_for("dashboard", username=username))

@app.route("/edit_recipe/<mongoid>")
def edit_recipe(mongoid):
    recipe = db.recipes.find_one({"_id": ObjectId(mongoid)})
    username = recipe["username"]
    return render_template("edit_recipe.html", recipe=recipe, mongoid=mongoid, username=username)


@app.route("/edit_recipe/<mongoid>", methods=["POST"])
def edit_recipe_post(mongoid):
    recipe = request.form["recipe"]
    ingredients = request.form["ingredients"]
    instructions = request.form["instructions"]

    db.recipes.update_one(
        {"_id": ObjectId(mongoid)},
        {"$set": {"recipe": recipe, "ingredients": ingredients, "instructions": instructions}},
    )

    recipe_doc = db.recipes.find_one({"_id": ObjectId(mongoid)})
    username = recipe_doc["username"]

    return redirect(url_for("dashboard", username=username))



@app.route("/delete_recipe/<mongoid>")
def delete_recipe(mongoid):
    """
    Route for GET requests to the delete page.
    Deletes the specified record from the database, and then redirects the browser to the read page.

    Parameters:
    mongoid (str): The MongoDB ObjectId of the record to be deleted.
    """
    recipe= db.recipes.find_one({"_id": ObjectId(mongoid)})
    username = recipe["username"]

    db.recipes.delete_one({"_id": ObjectId(mongoid)})

    return redirect(
        url_for("dashboard", username = username)
    )  # tell the web browser to make a request for the /read route.


@app.route("/delete/<mongoid>")
def delete(mongoid):
    """
    Route for GET requests to the delete page.
    Deletes the specified record from the database, and then redirects the browser to the read page.

    Parameters:
    mongoid (str): The MongoDB ObjectId of the record to be deleted.
    """
    review= db.reviews.find_one({"_id": ObjectId(mongoid)})
    username = review["username"]

    db.reviews.delete_one({"_id": ObjectId(mongoid)})

    return redirect(
        url_for("dashboard", username = username)
    )  # tell the web browser to make a request for the /read route.

@app.route("/search")
def search():
    query = request.args.get("query")

    db.recipes.create_index([("recipe", "text"), ("ingredients", "text"), ("instructions", "text")])
    results = db.recipes.find({"$text": {"$search": query}})

    if db.recipes.count_documents({"$text": {"$search": query}}) > 0:
        return render_template("read_recipes.html", docs=results)
    else:
        return render_template("read_recipes.html", message="No recipes found for the search query: '{}'".format(query))
    

@app.route("/create_recipe")
def create_recipe():
    """
    Route for GET requests to the post_recipe page.
    Displays a form users can fill out to create a new document.
    """
    return render_template("post_recipe.html")  # render the create template

# posting recipes
@app.route("/create_recipe", methods=["POST"])
def post_recipe():
    username = request.form["username"]
    recipe = request.form["recipe"]
    ingredients = request.form["ingredients"]
    instructions = request.form["instructions"]
    
    new_recipe = {
            # "_id": ObjectId(mongoid),
            "username": username,
            "recipe": recipe,
            "ingredients": ingredients,
            "instructions": instructions,
            "created_at": datetime.datetime.utcnow(),
        }

    db.recipes.insert_one(new_recipe)

    return redirect(
        url_for("post_recipe")
    ) 

@app.route("/read_recipes")
def read_recipes():
    """
    Route for GET requests to the read page. = specifically for recipes.
    Displays some information for the user with links to other pages.
    """
    docs = db.recipes.find({}).sort("created_at", -1)  # sort in descending order of created_at timestamp
    return render_template("read_recipes.html", docs=docs)  # render the read template

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_form():
    username = request.form["username"]
    password = request.form["password"]

    user = db.users.find_one({"username": username})
    if user:
        if user["password"] == password:
            return redirect(url_for("dashboard", username=username))
        else:
            error = "Incorrect password. Please try again."
            return render_template("login.html", error=error)
    else:
        error = "Username does not exist. Please try again or sign up."
        return render_template("login.html", error=error)


@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup_form():
    username = request.form["username"]
    password = request.form["password"]

    existing_user = db.users.find_one({"username": username})
    if existing_user:
        error = "Username already exists. Please choose a different username."
        return render_template("signup.html", error=error)

    new_user = {
        "username": username,
        "password": password,
    }

    db.users.insert_one(new_user)

    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    return render_template("logout.html")

@app.route("/logout", methods=["POST"])
def logout_post():
    return redirect(url_for("home"))


@app.route("/dashboard/<username>")
def dashboard(username):
    user_reviews = db.reviews.find({"username": username})
    user_recipes = db.recipes.find({"username": username})
    return render_template("dashboard.html", username=username, user_reviews=user_reviews, user_recipes=user_recipes)

@app.route("/dashboard/<username>", methods=["POST"])
def dashboard_view(username):
    return redirect(url_for("dashboard", username=username))


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    GitHub can be configured such that each time a push is made to a repository, GitHub will make a request to a particular web URL... this is called a webhook.
    This function is set up such that if the /webhook route is requested, Python will execute a git pull command from the command line to update this app's codebase.
    You will need to configure your own repository to have a webhook that requests this route in GitHub's settings.
    Note that this webhook does do any verification that the request is coming from GitHub... this should be added in a production environment.
    """
    # run a git pull command
    process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE)
    pull_output = process.communicate()[0]
    # pull_output = str(pull_output).strip() # remove whitespace
    process = subprocess.Popen(["chmod", "a+x", "flask.cgi"], stdout=subprocess.PIPE)
    chmod_output = process.communicate()[0]
    # send a success response
    response = make_response(f"output: {pull_output}", 200)
    response.mimetype = "text/plain"
    return response


@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template("error.html", error=e)  # render the edit template


# run the app
if __name__ == "__main__":
    # logging.basicConfig(filename="./flask_error.log", level=logging.DEBUG)
    app.run(load_dotenv=True)
