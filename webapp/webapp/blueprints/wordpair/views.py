from flask import Blueprint, render_template, request, flash, session, render_template_string, Response
from jinja2_fragments.flask import render_block
from webapp.blueprints.wordpair.models import User, Keyword
from celery.result import AsyncResult
from pprint import pprint

wordpair = Blueprint('wordpair', __name__, template_folder='templates', url_prefix="/pair/<int:id>")
def oobify(html, swap_value='true'):
    return html.replace('>', f' hx-swap-oob="{swap_value}">', 1)

@wordpair.route("/")
def wordpairpage(id):
    from webapp.app import wordlist
    user = User.get_user(session['user_id'])
    wp = wordlist.get(id)
    kw = user.get_keyword(wp)
    if kw is None:
        return render_template("wordpair.jinja", wordlist=wordlist, 
                               wordpair=wp, currentid=id)
    keyword = kw.keyword
    visual_cue = kw.visual_cue
    verbal_cue = kw.verbal_cue
    generated_by = kw.generated_by
    return render_template("wordpair.jinja", wordlist=wordlist, 
                           wordpair=wp, keyword=keyword, 
                           verbal_cue=verbal_cue,
                           visual_cue=visual_cue,
                           generated_by=generated_by,
                           currentid=id) 
    

@wordpair.route("/keyword", methods=["GET", "POST"])
def keyword(id):
    from webapp.app import wordlist
    wp = wordlist.get(id)
    if request.method == "POST":
        from webapp.blueprints.wordpair.tasks import generate_keywords
        print("A")
        result = generate_keywords.delay(user=None, foreign_lang=wordlist.foreign_lang, wordpair=wp)
        return render_template("loadingwords.jinja", get_url='keyword', result=result)
    if request.method == "GET":
        taskid = request.args.get("taskid")
        result = AsyncResult(taskid)
        if result.ready():
            print("B") 
            return render_template("threewords.jinja", get_url='keyword', 
                                   result=result, limit = 1, wordpair=wp)
        else:
            print("C")
            return render_template("loadingwords.jinja", get_url='keyword', result=result)

@wordpair.route("/verbalcue", methods=["GET", "POST"])
def generateverbalcue(id):
    from webapp.blueprints.wordpair.tasks import generate_verbalcue
    from webapp.app import wordlist
    wp = wordlist.get(id)
    kw = User.get_user(session['user_id']).get_keyword(wp)
    if request.method == "POST":
        result = generate_verbalcue.delay(kw=kw)
        return render_template("loadingwords.jinja", get_url="verbalcue", result=result)
    if request.method == "GET":
        u = User.get_user(session['user_id'])
        taskid = request.args.get("taskid")
        result = AsyncResult(taskid)
        if result.ready():
            u.add_verbal_cue(wp, result.result)
            return render_block("wordpair.jinja", "verbalcueblock", verbal_cue=result.result) \
            + render_block("wordpair.jinja", "visualcueblock", verbal_cue=True)
        else:
            return render_template("loadingwords.jinja", get_url="verbalcue", result=result)

@wordpair.route("/visualcue", methods=["GET", "POST"])
def generatevisualcue(id):
    from webapp.blueprints.wordpair.tasks import generate_visualcue
    if request.method == "POST":
        kw = User.get_user((session['user_id'])).get_keyword(id)
        result = generate_visualcue.delay(kw = kw)
        return render_template("loadingwords.jinja", get_url="visualcue", result=result)
    if request.method == "GET":
        from webapp.app import wordlist
        wp = wordlist.get(id)
        u = User.get_user(session['user_id'])
        # vsc = u.get_visual_cue(wp)
        # if vsc:
        #     return render_block("wordpair.jinja", "visualcueblock", visual_cue=result.result)
        taskid = request.args.get("taskid")
        result = AsyncResult(taskid)
        if result.ready():
            u.add_visual_cue(wp, result.result)
            return render_block("wordpair.jinja", "visualcueblock", visual_cue=result.result) \
            + oobify(render_block("wordpair.jinja", "footerblock", visual_cue=True, verbal_cue=True))
        else:
            return render_template("loadingwords.jinja", get_url="visualcue", result=result)

@wordpair.route("/disagree", methods=["POST"])
def generate(id):
    from webapp.app import wordlist
    taskid = request.form.get("taskid")
    result = AsyncResult(taskid)
    return render_template("threewords.jinja", result=result,
                           wordpair=wordlist.get(id))

@wordpair.post("/regen")
def regen(id):
    type = request.form.get("type")
    if type == "visualcue":
        return render_block("wordpair.jinja", "visualcueblock", verbal_cue=True)
    if type == "verbalcue":
        return render_block("wordpair.jinja", "verbalcueblock", keyword=True) \
        + "<div id='visualcue' hx-swap-oob='true'></div>"


@wordpair.route("/testoob", methods=["GET", "POST"])
def testoob(id):
    if request.method == "POST":
        text = '''
        <div>I have been swapped</div> 
        <div id="lol1">Lol1 has been swapped too!</div>
        '''
        resp = Response(text)
        resp.headers['HX-Swap-Oob'] = "#lol1"
        return resp
    if request.method == "GET":
        return render_template("testdeleteme.jinja")

@wordpair.post("/submitpreference")
def submitpreference(id):
    from webapp.app import wordlist
    if request.form.get('selectedOption') == 'customOption':
        preference = request.form['text'].strip().lower()
        generated_by = "user"
    else:
        preference = request.form.get('selectedOption').split(".")[1]
        generated_by = "myLLM" + request.form.get('selectedOption').split(".")[0]

    print("Preference:", preference)
    print(preference in (None, ''))
    taskid = request.form.get("taskid")
    result = AsyncResult(taskid)
    if preference in (None, ''): 
        flash("Cannot be empty")
        return render_template("threewords.jinja", result=result, 
                               isempty=True, wordpair=wordlist.get(id))
    print("pref:", preference)
    print("generated by:", generated_by)
    # Save keyword to mongo db
    from webapp.app import wordlist
    wp = wordlist.get(id)
    kw = Keyword(wordpair=wp, keyword=preference, generated_by=generated_by)
    User.get_user(session['user_id']).add_keyword(kw)

    return render_block("wordpair.jinja", "keywordblock", keyword=preference, wordpair=wp) \
        + render_block("wordpair.jinja", "verbalcueblock", keyword=True)

@wordpair.route("/keywords")
def topwords(id):
    return "list of top keywords"

