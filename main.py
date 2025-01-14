from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
import pyaudio
import tiktoken
import os, sys, pathlib, hashlib, glob

API_KEY = os.environ["OPENAI_KEY"]
PROJECT_ID = os.environ["PROJECT_ID"] 
BASE_DIR = pathlib.Path(__file__).parent / "articles"

def getWebsite(site_url):
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    driver = webdriver.Firefox(keep_alive=False, options=options)
    driver.get(site_url)
    body_elem = driver.find_element(By.TAG_NAME, "body")
    markup = body_elem.get_attribute('innerHTML')
    
    driver.quit()
    return markup


def getArticle(article_hash, markup):
    if (BASE_DIR / article_hash).exists():
        with open(BASE_DIR / article_hash, "rt") as f:
            cached = f.read()
            return cached
    
    messages = [ {
                "role": "user", 
                "content": "Given the following website markup, return only the text of the site that is an article, blog post or similar. The ouput MUST be formatted as human readable text with no kind of markup. It's important to extract the article as verbatim as possible. If there are images include them by mentioning that there's an image and the images alt text - if any.\n-------\n"
                    + markup
            }
        ]
    encoder = tiktoken.encoding_for_model("gpt-4o-mini")

    num_tokens = 0
    for message in messages:
        num_tokens += 3
        for key, value in message.items():
            num_tokens += len(encoder.encode(value))
            if key == "name":
                num_tokens += 1
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    
    print("Extraction message is %d tokens" % num_tokens)

    openai = OpenAI(api_key=API_KEY, project=PROJECT_ID)
    completion = openai.chat.completions.create(
        model="gpt-4o-mini", 
        stream=False,
        messages=messages
    )

    text = completion.choices[0].message.content
    with open(BASE_DIR / article_hash, "wt") as f:
        f.write(text)
    
    return text


def tts(article_hash, text):

    player_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
    if (BASE_DIR / (article_hash + "_0.pcm")).exists():
        files = glob.glob(str(BASE_DIR / (article_hash + "_*.pcm")))
        for file in files:
            with open(file, "rb") as chunk:
                while (audio_chunk := chunk.read(1024)):
                    player_stream.write(audio_chunk)
        return

    openai = OpenAI(api_key=API_KEY, project=PROJECT_ID)

    in_text = text
    chunks = []
    while(len(in_text) > 4000):
        rspc = str.rindex(in_text[:4000], " ")
        chunks.append(in_text[:rspc])
        in_text = in_text[rspc+1:]
    else:
        chunks.append(in_text)

    chunks = [(i, c) for i, c in enumerate(chunks)]
    for i, chunk in chunks:
        out_path = BASE_DIR / (article_hash + "_" + str(i) + ".pcm")
        
        with open(out_path, 'wb') as out_file:
            with openai.audio.with_streaming_response.speech.create(
                model="tts-1", 
                voice="onyx",
                input=chunk,
                response_format="pcm"
            ) as tts_stream:
                for audio_chunk in tts_stream.iter_bytes(chunk_size=1024):
                    player_stream.write(audio_chunk)
                    out_file.write(audio_chunk)




if __name__ == '__main__':
    url = sys.argv[1]

    if not pathlib.Path(BASE_DIR).exists():
        os.mkdir(BASE_DIR)

    print("Fetching page at %s.." % url)
    page_markup = getWebsite(url)
    article_hash = hashlib.sha256(page_markup.encode()).hexdigest()
    print("Article hash is: %s" % article_hash)

    print("Extracting text...")
    article = getArticle(article_hash, page_markup)
    print("Converting to speech...")
    tts(article_hash, article)