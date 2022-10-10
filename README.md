# Vocabgenerator

Vocabgenerator is a python utility that scrapes [thai-language.com](http://thai-language.com/) to make Anki flashcards with voiceovers of words.

## Installation

Clone this repo to your device

This project uses [poetry](https://python-poetry.org/) as its dependency manager, so have that installed

```bash
pip install poetry
```

In the main folder, run `poetry install` to install all required packages and dependencies

Sign up for Google Cloud, and create a project. Create a [JSON key](https://cloud.google.com/iam/docs/creating-managing-service-account-keys) for TTS and add it to the root folder.

Next, figure out the [directory](https://docs.ankiweb.net/files.html#file-locations) where Anki stores all media for flashcards

In the main folder, create a `config.yml` file as follows:

```yml
gcloud:
  filename: SERVICE_ACCOUNT_JSON_LOCATION

user:
  media-location: ANKI_MEDIA_LOCATION
```

## Usage

Vocabgenerator takes a .txt file containing line-separated words to process, or manual entry of words.

### example .txt file

```txt
แอปเปิ้ล
ส้ม
กล้วย
```

```bash
poetry run python bot.py words.txt

poetry run python bot.py
```

The created flashcards will be stored in `./results`, and are output as a csv of `[word, transliteration, definition, example]`

Then, [import](https://docs.ankiweb.net/importing.html) the deck into Anki. A sample card type:

```.txt
Front:
{{Front}}

Back:
{{FrontSide}}
<br>
{{Translit}}

<hr id=answer>
{{Back}}

<hr>
{{Back2}}
```

## License

[MIT](https://choosealicense.com/licenses/mit/)
