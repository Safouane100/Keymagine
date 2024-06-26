from webapp.app import create_celery_app
from llm_modules.keywordgen import KeywordGenerator
from llm_modules.verbalcuegen import VerbalCueGenerator
from llm_modules.visualcuegen import VisualCueGenerator
from webapp.blueprints.wordpair.models import WordPair, Keyword
from prodiapy import Prodia
from time import sleep
import os, requests

celery = create_celery_app()
keywordgen = KeywordGenerator()
verbalcuegen = VerbalCueGenerator()
visualcuegen = VisualCueGenerator()
prodia = Prodia(api_key=os.getenv("PRODIA_API_KEY"))

@celery.task()
def generate_keywords(user, foreign_lang, wordpair):
    words = keywordgen.generate_keywords(foreign_lang, wordpair.foreign_word)
    return words

@celery.task()
def generate_verbalcue(kw: Keyword) -> str:
    sentence = verbalcuegen(word1 = kw.wordpair.native_word, word2 = kw.keyword)
    return sentence

@celery.task()
def generate_visualcue(kw: Keyword) -> str:
    if any(x is None for x in (kw.keyword, kw.verbal_cue, kw.wordpair)):
        raise ValueError("Keyword, verbal_cue, or wordpair.foreign_word is None")
    
    prompt = visualcuegen(verbal_cue=kw.verbal_cue)
    job = prodia.sdxl.generate(prompt=prompt, 
                               cfg_scale=10, 
                               model="sd_xl_base_1.0.safetensors [be9edd61]",
                               negative_prompt="((NSFW)), sexual content, cleavage, explicit, lewd, skin")
    result = prodia.wait(job)
    print(result.image_url)

    filename = os.path.split(result.image_url)[1]
    image_path = os.path.join("data", "prodia", filename)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)

    response = requests.get(result.image_url)
    response.raise_for_status()

    with open(image_path, "wb") as f:
        f.write(response.content)

    return filename
