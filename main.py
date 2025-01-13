from openai import OpenAI
from selenium import webdriver
import pathlib
import pyaudio

API_KEY = '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'



def getWebsite(site_url):
    options = webdriver.FirefoxOptions()
    # options.add_argument("-headless")
    driver = webdriver.Firefox(keep_alive=False, options=options)
    driver.get(site_url)
    markup = driver.page_source
    driver.quit()
    return markup


def getArticle(markup):
    openai = OpenAI(api_key=API_KEY)
    completion = openai.chat.completions.create(
        model="gpt-4o-mini", 
        stream=False,
        messages=[ {
                "role": "user", 
                "content": "Given the following website markup, return only the text of the site that is an article, blog post or similar. The ouput MUST be formatted as human readable text with no kind of markup. If there are images include them by mentioning that there's an image and the images alt text - if any.\n-------\n"
                    + markup
            }
        ]
    )
    return completion.choices[0].message.content


def tts(text):

    openai = OpenAI(api_key=API_KEY)
    player_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)

    in_text = text
    chunks = []
    while(len(in_text) > 4000):
        rspc = str.rindex(in_text[:4000], " ")
        chunks.append(in_text[:rspc])
        in_text = in_text[rspc+1:]
    else:
        chunks = [in_text]

    chunks = [(i, c) for i, c in enumerate(chunks)]
    for i, chunk in chunks:
        out_path = pathlib.Path(__file__).parent / ("tmp_" + str(i) + ".mp3")

        with openai.audio.with_streaming_response.speech.create(
            model="tts-1", 
            voice="alloy",
            input=chunk,
            response_format="pcm"
        ) as tts_stream:
            # tts_stream.stream_to_file(out_path)
            for audio_chunk in tts_stream.iter_bytes(chunk_size=1024):
                player_stream.write(audio_chunk)



if __name__ == '__main__':
    print("Fetching page..")
    # page_markup = getWebsite("https://jsrn.net/2024/11/14/choosing-a-todo-app.html")
    page_markup = getWebsite("https://blog.djhaskin.com/blog/why-i-chose-common-lisp/")
    print("Extracting text...")
    article = getArticle(page_markup)
    print("Converting to speech...")
    tts(article)