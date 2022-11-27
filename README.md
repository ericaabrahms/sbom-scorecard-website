# sbom-scorecard-website

# Installation

You'll need a .env file in the root of the repo to specify environment variables.
```
SPACES_KEY=""
SPACES_SECRET=""
SPACES_REGION=""
SPACES_BUCKET=""
```

Then install python bits
```
pipenv install
pipenv run flask --debug run
```

And node bits
```
cd static
npm i
npx tailwindcss -i .\src\style.css -o .\css\main.css --watch
```
