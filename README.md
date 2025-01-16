### To build and run
1) `docker build -t read-up .`
2) `docker run --env-file .\.env -p 1235:1235 read-up`




`.env` needs to contain two keys:
```.env
PROJECT_ID=proj_xxxxxxxxxxxxxxxxxxxx
OPENAI_KEY=sk-proj-xxxxxxxxxxxxx...
```
