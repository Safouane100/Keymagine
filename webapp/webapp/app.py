import json, csv, datetime, os
from pprint import pprint
from flask import (Flask, abort, request, session, send_from_directory,
    redirect, url_for, render_template, make_response, render_template_string)
from webapp.blueprints.wordpair import wordpair
from webapp.blueprints.wordpair.models import User, WordPair, Keyword, WordList
from celery import Celery, Task
from bunnet import init_bunnet
from beanie import init_beanie
from collections import Counter
from llm_modules.config import LLM
from jinja2_fragments.flask import render_block
from tabulate import tabulate
import pymongo

mongo = pymongo.MongoClient("mongodb://mongodb:27017/")
init_bunnet(database=mongo.test, document_models=[User, WordList])
llm = LLM().get_llm() # Instantiate LLM

CELERY_TASK_LIST = [
    "webapp.blueprints.wordpair.tasks",
]

WORDLIST = "evaluation-ellis-keyword"

def set_transphoner_keywords(user: User) -> None:
    for i, keyword in enumerate(User.get_user("transphoner").keywords):
        if (
            (user.user_id.startswith("T") and i % 2 == 0)
            or (user.user_id.startswith("L") and i % 2 == 1)
            and (user.get_keyword(keyword) is None)
        ):
            user.add_keyword(keyword)

def load_valid_users() -> dict: 
    res = {}
    with open('data/users.json') as f:
        user_list = json.load(f)
        for user_id in user_list:
            u = User.get_user(user_id)
            set_transphoner_keywords(u)
            res[user_id] = u
    return res


# def get_transphoner_keywords() -> list[Keyword]:
#     with open('data/evaluation-transphoner-keyword.csv', newline='') as csvfile:
#         reader = csv.DictReader(csvfile)
#         res = []
#         for row in reader:
#             res.append(Keyword(
#                 wordpair = WordPair(
#                     foreign_word = row['Foreignword'],
#                     native_word = row['Nativeword']
#                 ),
#                 keyword = row['Keyword'],
#                 generated_by = "transphoner",
#             ))
#     return res

# def set_transphoner_user():
#     u = User.get_user("transphoner")
#     u.keywords = get_transphoner_keywords()
#     u.save() 
    
def load_wordlist(wordlist_filename = "testwordlist", foreign_lang = "German", native_lang = "English") -> WordList:
    wordlist = WordList.find_one(WordList.list_name == wordlist_filename).run()
    if not wordlist:
        wordlist = WordList(list_name = wordlist_filename, native_lang = native_lang, foreign_lang = foreign_lang) 
        with open(f'data/{wordlist_filename}.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader):
                w = WordPair(
                        foreign_word = row['Foreignword'],
                        native_word = row['Nativeword'],
                )
                wordlist.words[i+1] = w
        wordlist.save() 
    return wordlist


wordlist: WordList = load_wordlist(WORDLIST)
valid_users: list[User] = load_valid_users()


def create_app(settings_override=None):
    """
    Create the Flask app
    """

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("config.settings")
    app.config.from_pyfile("settings.py", silent=True)
    if settings_override: app.config.update(settings_override)
    app.secret_key = app.config["SECRET_KEY"]
    app.register_blueprint(wordpair)

    @app.get("/") 
    def index():
        print(wordlist.words)
        return render_template('wordlist.jinja', wordlist=wordlist)

    @app.get('/uploads/<path:filename>')
    def download_file(filename):
        return send_from_directory("../data/prodia", filename, as_attachment=True)

    
    @app.get('/resetkeywords')
    def reset_keywords():
        u = User.get_user(session['user_id'])
        u.keywords = []
        u.save()
        return redirect(url_for('index'))

    def is_valid_user(user_id):
        return user_id in valid_users.keys()


    @app.route("/testpage", methods=['GET', 'POST'])
    def testpage():
        start = int(request.args.get('start'))
        end = int(request.args.get('end'))
        if request.method == 'GET':
            return render_template("testpage.jinja", 
                                   wordlist=wordlist, 
                                   start=start, 
                                   end=end)
        if request.method == 'POST':
            user = User.get_user(session['user_id'])
            pprint(request.form)
            user.set_test_answers(request.form)
            return redirect(request.form['redirect_url'])

    @app.get("/break")
    def break_page():
        return render_template("break.jinja")

    @app.route("/finaltest", methods=['GET', 'POST'])
    def finaltest():
        if request.method == 'GET':
            return render_template("finaltest.jinja", wordlist=wordlist)
        if request.method == 'POST':
            user = User.get_user(session['user_id'])
            user.set_final_answers(request.form)
            return redirect(url_for('review'))

    @app.route("/review", methods=['GET', 'POST'])
    def review():
        if request.method == 'GET':
            user = User.get_user(session['user_id'])
            return render_template("review.jinja", user=user, wordlist=wordlist)
        if request.method == 'POST':
            user = User.get_user(session['user_id'])
            user.set_review_answers(request.form)
            return redirect(url_for('thankyou'))
        
    @app.get("/thankyou")
    def thankyou():
        return render_template("thankyou.jinja")

    @app.errorhandler(404)
    def page_not_found(error):
        return "404 Page Not Found", 404
    
    @app.post("/grade/<user_id>")
    def grade(user_id):
        u = User.get_user(user_id)
        for k, v in request.form.items():
            u.set_grade(k, v)
        return "Success"
        
    return app

def create_celery_app(app = None):
    app = app or create_app()

    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
            
    celery = Celery(app.import_name, task_cls=FlaskTask)
    celery.conf.update(app.config.get("CELERY_CONFIG", {}))
    celery.set_default()
    app.extensions["celery"] = celery
    return celery