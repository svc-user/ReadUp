# ReadUp
A small python application for getting blog posts and news articles read out loud with natural speech. Uses the magic of ✨*AI*✨.

## To build and run

### With Docker
Run these two commands to get running.
1) `docker build -t read-up .`
2) `docker run --env-file .\.env -d -p 1235:1235 read-up`

#### Persisting the cache
If you wish to persist already downloaded sites, text extractions and audio files you can add the parameter `-v local_folder_here:/app/articles` do your `docker run` command above.

### Without Docker
If you don't have or want to use Docker you can run it without.

1) Have Firefox installed (used headless for fetching pages)
2) **Optional**: Setup a virtualenv with `python -m venv .venv`
    - 2.1) **Optional**: Activate the virtualenv
3) Run `python -m pip install -r requirements.txt`
4) Run the application with `python main.py`



## Environment variables
`.env` needs to contain two keys:
```.env
PROJECT_ID=proj_xxxxxxxxxxxxxxxxxxxx
OPENAI_KEY=sk-proj-xxxxxxxxxxxxx...
```
Get your API key [here](https://platform.openai.com/settings/organization/api-keys).




## Todo
 - [ ] Settings for voice
 - [ ] Settings for playback speed
 - [ ] Highlighting of (approximately) the currently read line/word
 - [ ] Prettiness 
 - [ ] Configurable app settings