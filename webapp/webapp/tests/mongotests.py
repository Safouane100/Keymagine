from webapp.blueprints.wordpair.models import Keyword, User, WordList, WordPair

from webapp.app import mongo

class TestModels(object):
    # cd "Documents\School MSc\Thesis\Program\webapp"
    # docker-compose exec website py.test webapp/tests/mongotests.py
    
    def test_wordpair_model(self):
        wordpair = WordPair(native_word="hello", foreign_word="hola")
        assert wordpair.native_word == "hello"
        assert wordpair.foreign_word == "hola"

    def test_wordlist_model(self):
        wordlist = WordList(list_name="Greetings", foreign_lang="Spanish", native_lang="English")
        assert wordlist.list_name == "Greetings"
        assert wordlist.foreign_lang == "Spanish"
        assert wordlist.native_lang == "English"

    def test_keyword_model(self):
        wordpair = WordPair(native_word="hello", foreign_word="hola")
        keyword = Keyword(wordpair=wordpair, keyword="greeting", generated_by="user")
        assert keyword.wordpair == wordpair
        assert keyword.keyword == "greeting"
        assert keyword.generated_by == "user"

    def test_user_model(self):
        user = User(user_id="12345")
        assert user.user_id == "12345"
        assert user.consented == False
        assert user.keywords == []

    def test_get_user(self):
        # id is random
        import random
        foo = str(random.randint(0, 100000))
        user = User(user_id=foo, consented=True)
        user.save()

        retrieved_user = User.get_user(foo)
        user.delete()
        assert retrieved_user.user_id == foo
        assert retrieved_user.consented == True

    def test_add_keyword(self):
        user = User.find_one(User.user_id == "12345").run() or User(user_id="12345")
        wordpair = WordPair(native_word="hello", foreign_word="hola")
        keyword = Keyword(wordpair=wordpair, keyword="greeting", generated_by="user")
        user.add_keyword(keyword)

        same_user = User.find_one(User.user_id == "12345").run()
        assert len(same_user.keywords) > 0
        assert same_user.keywords[0].keyword == "greeting"

    def test_no_duplicate_keywords(self):
        user = User.get_user(user_id="12345123")
        wordpair = WordPair(native_word="hellomate", foreign_word="holamate")
        keyword = Keyword(wordpair=wordpair, keyword="greeting", generated_by="user")
        user.add_keyword(keyword)
        user.add_keyword(keyword)

        same_user = User.get_user("12345")
        assert len(same_user.keywords) == 1

    def test_get_keyword(self):
        user = User.get_user(user_id="12345")
        wordpair = WordPair(native_word="hello", foreign_word="hola")
        keyword = Keyword(wordpair=wordpair, keyword="greeting", generated_by="user")
        user.add_keyword(keyword)

        same_user = User.get_user("12345")
        retrieved_keyword = same_user.get_keyword(wordpair)
        assert retrieved_keyword.keyword == "greeting"

    def test_add_verbal_cue(self):
        user = User.get_user(user_id="12345")
        wordpair = WordPair(native_word="meow", foreign_word="nya")
        keyword = Keyword(wordpair=wordpair, keyword="greeting", generated_by="user")
        user.add_keyword(keyword)
        verbalcue = "Imagine yourself on the beach kicking turtles like Mario :^)"
        user.add_verbal_cue(keyword, verbalcue)

        same_user = User.get_user("12345")
        assert same_user.get_keyword(keyword).verbal_cue == verbalcue
        user.delete()

    def test_add_verbal_cue2(self):
        user = User.get_user(user_id="12345")
        wordpair = WordPair(native_word="hello", foreign_word="hola")
        verbalcue = "Imagine yourself being stupid"
        keyword = Keyword(wordpair=wordpair, keyword="greeting", generated_by="user")
        user.add_keyword(keyword)
        user.add_verbal_cue(wordpair, verbalcue)

        same_user = User.get_user("12345")
        assert same_user.keywords[0].verbal_cue == verbalcue
        user.delete()


from pprint import pprint
user = User.get_user("12345")
pprint(user.keywords)