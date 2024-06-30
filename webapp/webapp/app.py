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

    @app.before_request
    def check_user():
        if request.endpoint in ('static', 'logout'): return
        if 'user_id' not in session:
            if request.endpoint == 'login': return
            return redirect(url_for('login'))

    @app.get("/") 
    def index():
        print(wordlist.words)
        return render_template('wordlist.jinja', wordlist=wordlist)

    @app.get('/uploads/<path:filename>')
    def download_file(filename):
        return send_from_directory("../data/prodia", filename, as_attachment=True)

    @app.get("/login")
    def login():
        user_id = request.args.get('id')
        if user_id is None:
            return render_template("login.jinja", error=False)
        elif is_valid_user(user_id): 
            session['user_id'] = user_id  # Set the user_id in the session
            return redirect(url_for('index'))
        else:
            return render_template("login.jinja", error=True)

    @app.get('/logout')
    def logout():
        session.pop('user_id', None)
        return redirect(url_for('login'))
    
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
    
    @app.errorhandler(401)
    def unauthorized(error):
        return "Unauthorized login", 401
    
    @app.get("/meowy")
    def meowy():
        from llm_modules.keywordgen import KeywordGenerator
        keywordgen = KeywordGenerator()
        from webapp.blueprints.wordpair.tasks import generate_keywords
        for wp in wordlist.words.values():
            # words = keywordgen.generate_keywords(wordlist.foreign_lang, wp.foreign_word)
            words = generate_keywords(None, wordlist.foreign_lang, wp)
            print(wp.foreign_word, "\t", words)
            
        print("Mädchen:", "\t", generate_keywords(None, wordlist.foreign_lang, WordPair(foreign_word="Mädchen", native_word="")))
        print("Hören", "\t", generate_keywords(None, wordlist.foreign_lang, WordPair(foreign_word="Hören", native_word="")))
        print("Grüße", "\t", generate_keywords(None, wordlist.foreign_lang, WordPair(foreign_word="Grüße", native_word="")))
        return "hey"
    
    @app.get("/report")
    def report():
        make_p = lambda s: f"<p>{s}</p>"
        make_br = lambda arr: "<br>".join(arr)
        arr2str = lambda arr: "".join(arr)
        users = [user for user in User.find_all().run() if 
                 user.user_id[0] in ("T", "L") and user.user_id not in ("L.test2", "L.test")]
        all_keywords = [kw for u in users for kw in u.keywords]
        generated_by = set(kw.generated_by for kw in all_keywords) | {"myLLM", "personalized"}
        def is_gen_by(kw, g):
            gb = kw.generated_by
            if g == "personalized": return gb == "user" or gb.startswith("myLLM")
            return kw.generated_by.startswith(g)
        
        total_counter, transphoner_counter, personalized_counter = Counter(), Counter(), Counter(), 
        user_counter, myllm_counter, other_counter = Counter(), Counter(), Counter()
        for user in users:
            split_results = user.get_split_results()
            total_counter.update(split_results['transphoner_grades'])
            total_counter.update(split_results['personalized_grades'])
            transphoner_counter.update(split_results['transphoner_grades'])
            personalized_counter.update(split_results['personalized_grades'])
            user_counter.update(split_results['user_grades'])
            myllm_counter.update(split_results['myllm_grades'])

        total_help, transphoner_help, personalized_help = Counter(), Counter(), Counter()
        for user in users:
            split_results = user.get_split_results()
            split_results = {k: [i[0] for i in v] for k, v in split_results.items()}
            total_help.update(split_results['transphoner_helpfulness'])
            total_help.update(split_results['personalized_helpfulness'])
            transphoner_help.update(split_results['transphoner_helpfulness'])
            personalized_help.update(split_results['personalized_helpfulness'])

        results_per_word = [{
                "foreign_word": wordlist.get(i).foreign_word,
                "native_word": wordlist.get(i).native_word,
                # "correct":              sum([1 for user in users if user.is_correct(i)]),
                # "correctTransphoner":   sum([1 for user in users if user.is_transphoner_value(i) and user.is_correct(i)]),
                # "correctLLM":           sum([1 for user in users if not user.is_transphoner_value(i) and user.is_correct(i)]),
                "correctPercentage":    round(sum([1 for user in users if user.is_correct(i)]) / len(users) / 2 * 100, 1),
                "correctTransphonerPercentage": round(sum([1 for user in users if user.is_transphoner_value(i) and user.is_correct(i)]) / len(users) * 100, 1),
                "correctLLMPercentage": round(sum([1 for user in users if not user.is_transphoner_value(i) and user.is_correct(i)]) / len(users) * 100, 1),
            } for i in range(1, 37)]

        results_per_user = [{
                "user_id": user.user_id,
                "correctPercentage": round(sum([1 for i in range(1, 37) if user.is_correct(i)]) / 36 * 100, 2),
                "correctTransphonerPercentage": round(sum([1 for i in range(1, 37) if user.is_transphoner_value(i) and user.is_correct(i)]) / 18 * 100, 2),
                "correctLLMPercentage": round(sum([1 for i in range(1, 37) if not user.is_transphoner_value(i) and user.is_correct(i)]) / 18 * 100, 2),
            } for user in users]


        avg_helpfulness_per_generated_by = {}
        for gen in generated_by:
            amount = sum([1 for kw in all_keywords if is_gen_by(kw, gen)])
            all_helpfulness = [int(u.get_helpfulness(i)[0]) for u in users for i in range(1, 37) if u.get_keyword(i) and is_gen_by(u.get_keyword(i), gen)]
            print(f"Gen: {gen}, amount: {amount}, all_helpfulness length: {len(all_helpfulness)}")
            total_helpfulness = sum(all_helpfulness)
            standard_deviation = round(sum([(i - total_helpfulness / amount) ** 2 for i in all_helpfulness]) / amount, 3)
            avg_helpfulness_per_generated_by[gen] = dict(
                amount_of_ratings=amount,
                avg_helpfulness=round(total_helpfulness / amount, 3),
                standard_deviation=standard_deviation,
            )

        transphoner_keywords = [str(User.get_user("transphoner").get_keyword(i)) for i in range(1, 37)]

        participants_comments = [str({
            "id": user.user_id,
            "Differences": user.review_answers.get("differences", ""),
            "Feedback": user.review_answers.get("feedback", "")
        }) for user in users]

        participants_comments = [["id", "differences", "feedback"]] + \
            [[user.user_id, 
              user.review_answers.get("differences", "-"), 
              user.review_answers.get("feedback", "-")] for user in users]
        participants_comments = tabulate(participants_comments, tablefmt='html')

        all_keywords = [str(dict(
            n=i, 
            foreign_word=wordlist.get(i).foreign_word, 
            keywordcount = Counter([u.get_keyword(i).keyword for u in users if u.get_keyword(i) and not u.get_keyword(i).generated_by.startswith("transphoner")]), 
            )) + "," for i in range(1, 37)]

        return make_br(["Total: " + str(total_counter)] +
                       ["Transphoner: " + str(transphoner_counter)] +
                       ["Personalized: " + str(personalized_counter)] +
                       ["User: " + str(user_counter)] +
                       ["MyLLM: " + str(myllm_counter)] + 
                       ["Total help: " + str(total_help)] +
                       ["Transphoner helpfulness: " + str(transphoner_help)] +
                       ["Personalized helpfulness: " + str(personalized_help)] +
                       [make_br(map(str, results_per_word))] + 
                       [make_br(map(str, results_per_user))] + 
                       ["Average helpfulness per generated by:"] +
                       [make_br(map(str, avg_helpfulness_per_generated_by.items()))] +
                       ["-----Transphoner keywords-----"] + 
                       transphoner_keywords +
                       ["-----All keywords-----"] + 
                       all_keywords +
                       ["-----Participant ID, Did you notice any difference between transphoner and personalized?, Open feedback-----"]
                       ) + participants_comments

    
    @app.get("/grading")
    def grading():
        make_td = lambda s: f"<td style='min-width: 150px;'>{s}</td>"
        make_th = lambda s: f"<th>{s}</th>" 
        make_tr = lambda s: f"<tr>{s}</tr>"
        list2str = lambda arr: "".join(arr)
        def make_cell(u, i): 
            final_answer = u.final_answers.get(f"answer{i}", "")
            current_grade = u.get_grade(str(i))
            kw = u.get_keyword(i)
            return render_template("grading/cell.jinja", u = u, i = i, 
                                   final_answer = final_answer,
                                   current_grade = current_grade,
                                   keyword = kw)
        def make_line(u: User) -> str:
            return make_tr(list2str(map(make_td, [u.user_id] + [make_cell(u, i) for i in range(1, 37)])))

        users = [user for user in User.find_all().run() if 
                 user.user_id[0] in ("T", "L") and user.user_id not in ("L.test2", "L.test")]
        header = "<thead>" +\
            make_tr(list2str(map(make_th, ["UserID"] + [f"{wordlist.get(i).foreign_word} - {wordlist.get(i).native_word}" for i in range(1, 37)]))) +\
            "</thead>"
        
        content = "<table class='striped'>" + header + list2str([make_line(u) for u in users]) + "</table>"
        overflow = "<div class='overflow-auto'>" + content + "</div>"
        final = "{% extends 'base.jinja' %}" + "{% block content %}" + overflow + "{% endblock %}"
        
        return render_template_string(final).replace('class="container"', 'class="container-fluid"')

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