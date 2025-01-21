from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
import asyncio
import tiktoken
import os, re, pathlib, hashlib, glob

API_KEY = os.environ["OPENAI_KEY"]
PROJECT_ID = os.environ["PROJECT_ID"] 
BASE_DIR = pathlib.Path(__file__).parent / "articles"
FILE_FORMAT = "mp3"
STREAM_BASE = "/stream/"
openai = OpenAI(api_key=API_KEY, project=PROJECT_ID)


def getWebsite(article_hash, site_url):
    if (BASE_DIR / (article_hash + ".html")).exists():
        with open(BASE_DIR / (article_hash + ".html"), "rt", encoding="utf8") as f:
            cached = f.read()
            if len(cached) == 0:
                f.close()
                os.remove((BASE_DIR / (article_hash + ".html")))
                return getWebsite(article_hash, site_url)
            
            return cached
        
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    driver = webdriver.Firefox(keep_alive=False, options=options)
    driver.get(site_url)
    body_elem = driver.find_element(By.TAG_NAME, "body")
    markup = body_elem.get_attribute('innerHTML')
    
    driver.quit()
    with open(BASE_DIR / (article_hash + ".html"), "wt", encoding="utf8") as f:
        f.write(markup)

    return markup


def getArticle(article_hash, markup):
    if (BASE_DIR / (article_hash + ".txt")).exists():
        with open(BASE_DIR / (article_hash + ".txt"), "rt", encoding="utf8") as f:
            cached = f.read()
            if len(cached) == 0:
                f.close()
                os.remove((BASE_DIR / (article_hash + ".txt")))
                return getArticle(article_hash, markup)
            
            return cached
    
    messages = [ {
                "role": "user", 
                "content": "Given the following website markup, return the text of the site that is an article, blog post or similar. Include the title and date, if noted. " +
                "Take the whole article. Omit comments in the end of the article if there are any. "+
                "The ouput MUST be formatted as human readable text with no kind of markup. " +
                "It's important to extract the article as verbatim as possible.\n-------\n"
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

    completion = openai.chat.completions.create(
        model="gpt-4o-mini", 
        stream=False,
        messages=messages
    )

    text = completion.choices[0].message.content
    with open(BASE_DIR / (article_hash + ".txt"), "wt", encoding="utf8") as f:
        f.write(text)
    
    return text


async def tts_stream(article_hash, text, voice_in, chunk_handler):
    chunks = []
    while(len(text) > 2000):
        rspc = str.rindex(text[:2000], " ")
        chunks.append(text[:rspc])
        text = text[rspc+1:]
    else:
        chunks.append(text)


    if (BASE_DIR / (article_hash + "_000." + FILE_FORMAT)).exists():
        files = glob.glob(str(BASE_DIR / (article_hash + "_*." + FILE_FORMAT)))
        files = [(i, f) for i, f in enumerate(files)]
        for (i, file) in files:
            fn = pathlib.Path(file).name
            all_words = re.findall(r'\w*\S', chunks[i])
            [word.pos for word in all_words]
            await chunk_handler({"stream_url": STREAM_BASE + fn, "wc": wc})
        return



    chunks = [(i, c) for i, c in enumerate(chunks)]
    for i, chunk in chunks:
        fn = (article_hash + "_" + str(i).rjust(3, "0") + "." + FILE_FORMAT)
        out_path = BASE_DIR / fn

        with open(out_path, 'wb') as out_file:
            with openai.audio.with_streaming_response.speech.create(
                model="tts-1", 
                voice=voice_in,
                input=chunk,
                response_format=FILE_FORMAT
            ) as tts_stream:
                for audio_chunk in tts_stream.iter_bytes(chunk_size=512000):
                    out_file.write(audio_chunk)

        wc = len([c for c in re.split(' |\n', chunk) if not c.isspace()])
        await chunk_handler({"stream_url": STREAM_BASE + fn, "wc": wc})


def clear_cache(article_hash):
    files = glob.glob(str(BASE_DIR / (article_hash + "*")))
    for file in files:
        os.remove(file)


async def do_heavy_lifting(url, config, stream_handler):
    # url = sys.argv[1]

    if not pathlib.Path(BASE_DIR).exists():
        os.mkdir(BASE_DIR)

    article_hash = hashlib.sha256(url.encode()).hexdigest()

    no_cache = config["no_cache"] if "no_cache" in config  else False
    if no_cache == True:
        clear_cache(article_hash)

    print("Article hash is: %s" % article_hash)

    print("Fetching page at %s.." % url)
    await stream_handler({"status":"Fetching page source.."})
    page_markup = getWebsite(article_hash, url)


    print("Extracting text...")
    await stream_handler({"status":"Extracting article text.."})
    article = getArticle(article_hash, page_markup)
    await stream_handler({"article": article})
    
    voice = config["voice"] if "voice" in config else "alloy"

    print("Converting to speech...")
    await stream_handler({"status":"Converting to speech using the '%s' voice.." % voice})
    await tts_stream(article_hash, article, voice, stream_handler)
    
    print("Done..")
    await stream_handler({"status":"Conversion complete.."})


async def _main():
    import json
    async def mock_handler(chunk):
        print("HANDLER: ")
        print(json.dumps(chunk, indent=2))

    await do_heavy_lifting("https://blog.yoshuawuyts.com/gen-auto-trait-problem/", {}, mock_handler)

if __name__ == "__main__":
    asyncio.run(_main())
    