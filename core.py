from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
import asyncio
import tiktoken
import os, sys, pathlib, hashlib, glob

API_KEY = os.environ["OPENAI_KEY"]
PROJECT_ID = os.environ["PROJECT_ID"] 
BASE_DIR = pathlib.Path(__file__).parent / "articles"
FILE_FORMAT = "mp3"
STREAM_BASE = "/stream/"
openai = OpenAI(api_key=API_KEY, project=PROJECT_ID)


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
        with open(BASE_DIR / article_hash, "rt", encoding="utf8") as f:
            cached = f.read()
            if len(cached) == 0:
                f.close()
                os.remove((BASE_DIR / article_hash))
                return getArticle(article_hash, markup)
            
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

    completion = openai.chat.completions.create(
        model="gpt-4o-mini", 
        stream=False,
        messages=messages
    )

    text = completion.choices[0].message.content
    with open(BASE_DIR / article_hash, "wt", encoding="utf8") as f:
        f.write(text)
    
    return text


async def tts_stream(article_hash, text, chunk_handler):

    # player_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
    if (BASE_DIR / (article_hash + "_000." + FILE_FORMAT)).exists():
        files = glob.glob(str(BASE_DIR / (article_hash + "_*." + FILE_FORMAT)))
        for file in files:
            fn = pathlib.Path(file).name
            await chunk_handler({"stream_url": STREAM_BASE + fn})
            # with open(file, "rb") as chunk:
            #     while (audio_chunk := chunk.read(1024)):
            #         await chunk_handler({"audio": list(audio_chunk)})
                    # player_stream.write(audio_chunk)
        return

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
        fn = (article_hash + "_" + str(i).rjust(3, "0") + "." + FILE_FORMAT)
        out_path = BASE_DIR / fn

        await chunk_handler({"stream_url": STREAM_BASE + fn})

        with open(out_path, 'wb') as out_file:
            with openai.audio.with_streaming_response.speech.create(
                model="tts-1", 
                voice="onyx",
                input=chunk,
                response_format=FILE_FORMAT
            ) as tts_stream:
                for audio_chunk in tts_stream.iter_bytes(chunk_size=1024):
                    out_file.write(audio_chunk)
                    # await chunk_handler({"audio": list(audio_chunk)})




async def do_heavy_lifting(url, stream_handler):
    # url = sys.argv[1]

    if not pathlib.Path(BASE_DIR).exists():
        os.mkdir(BASE_DIR)

    print("Fetching page at %s.." % url)
    page_markup = getWebsite(url)
    article_hash = hashlib.sha256(page_markup.encode()).hexdigest()
    print("Article hash is: %s" % article_hash)

    print("Extracting text...")
    article = getArticle(article_hash, page_markup)
    print("Converting to speech...")
    
    await stream_handler({"article": article})
    await tts_stream(article_hash, article, stream_handler)
    print("Done..")


async def _main():
    async def mock_handler(chunk):
        pass

    await do_heavy_lifting("https://blog.yoshuawuyts.com/gen-auto-trait-problem/", mock_handler)

if __name__ == "__main__":
    asyncio.run(_main())
    