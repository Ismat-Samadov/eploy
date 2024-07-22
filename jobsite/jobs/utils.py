# jobs/utils.py
import openai
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


openai.api_key = settings.OPENAI_API_KEY


def calculate_similarity(cv_text, job_text):
    vectorizer = TfidfVectorizer().fit_transform([cv_text, job_text])
    vectors = vectorizer.toarray()
    return cosine_similarity(vectors)[0, 1] * 100  # Return percentage

def extract_info(text, info_type):
    prompt = f"Extract the {info_type} from the following text:\n\n{text}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.5
    )
    return response.choices[0].text.strip()

def check_similarity(text1, text2):
    prompt = f"Check the similarity between the following two texts and provide a similarity score between 0 and 100:\n\nText 1: {text1}\n\nText 2: {text2}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=10,
        n=1,
        stop=None,
        temperature=0.5
    )
    return response.choices[0].text.strip()
