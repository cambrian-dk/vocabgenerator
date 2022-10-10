from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib.request
import sys
import csv
from pydub import AudioSegment
from pathlib import Path
from datetime import datetime
from google.cloud import texttospeech
from webdriver_manager.chrome import ChromeDriverManager


import yaml

# load config file
with open("config.yml") as f:
    try:
        config = yaml.safe_load(f)
    except:
        print("Error loading config.yml file")

# enter words one by one
# search thai-dictionary for entry, returns driver containing dictionary entry of the word

WEBSITE_URL = "http://thai-language.com"
MEDIA_LOCATION = config["user"]["media-location"]
GCLOUD_SERVICE_ACCOUNT = config["gcloud"]["filename"]
HIGHLIGHT_FONT_COLOR = "#55aaff"


def search_word(searchString, driver):

    try:
        # search word on website
        driver.implicitly_wait(3)
        driver.get(WEBSITE_URL + "/dict")
        searchBox = driver.find_element("xpath",
            "//dt[text()='Lookup:']/..//input[@type='text']"
        )

        print(searchString)
        searchBox.send_keys(searchString)
        searchBox.find_element("xpath",
            "./..//input[@type='submit']"
        ).click()
        driver.implicitly_wait(2)

        # check destination url
        destinationUrl = driver.current_url
        # if multiple results were returned, url remains the same
        if destinationUrl == "http://thai-language.com/dict":
            # choose the first result
            driver.implicitly_wait(3)
            try:
                firstResult = (
                    driver.find_element("xpath","(//td[text()='1.'])")
                    .find_element("xpath","./../td[2]")
                    .find_element("xpath",
                        ".//img[contains(@src, '/img/phr_link.gif')]/.."
                    )
                )
            except:
                firstResult = (
                    driver.find_element("xpath","(//td[text()='1.'])")
                    .find_element("xpath","./../td[2]")
                    .find_element("xpath",".//a[1]")
                )
            firstResult.click()
            driver.implicitly_wait(3)
        # else we are already at the results page
    except Exception as e:
        print("ERROR IN SEARCHING" + repr(e))
        raise
    
    return driver


def get_definition_and_example(driver, word):

    # find up to 3 definitions
    definitions = ""
    examples = ""
    for x in range(1, 4):

        try:
            definitionRow = driver.find_elements("xpath",
                f"((//td[text()='definition'])[{x}])/.."
            )

            if len(definitionRow) >= 1:
                definition = definitionRow[0]
                definitions += definition.find_element("xpath",
                    "./td[2]").text + "\n"

            exampleRow = driver.find_elements("xpath",
                f'(//td[normalize-space() = "samplesentences"])[{x}]/following-sibling::td[1]//span[@class = "th"]'
            )

            if len(exampleRow) >= 1:
                exampleStr = exampleRow[0].text
                exampleStr = exampleStr.replace(word, f'<font color="{HIGHLIGHT_FONT_COLOR}">{word}</font>' )
                print(exampleStr)
                examples += exampleStr + "\n"

        except Exception as e:
            print("NO MORE DEFINITIONS/ERROR: " + repr(e))
            break
    return definitions, examples


def get_phonetics(driver):

    try:
        driver.implicitly_wait(1)
        phonetics = (
            driver.find_element(By.CLASS_NAME, "th3")
            .find_element("xpath","./../span[2]")
            .text
        )
        print(phonetics)
        return phonetics
    except:
        print("ERROR IN get_phonetics")
        raise


def get_audio_url(driver):
    try:
        url = WEBSITE_URL + (
            driver.find_element(By.CLASS_NAME, "th3")
            .find_element("xpath","./../..//a")
            .get_attribute("onclick")
            .split("'")[1]
        )
        print(url)
        return url
    except:
        print("Error getting audio_url, generating with google TTS instead")
        raise


def download_audio_file(url, location):
    try:
        print(url)
        print(location)
        wordId = url.rsplit("/", 1)[-1]
        urllib.request.urlretrieve(url, location + f"/{wordId}")
        return wordId
    except:
        print("ERROR IN download_audio_file")
        raise


def add_anki_card(csvWriter, word, definition, phonetics, audio_file, example): 
    translit = f"{phonetics}[sound:{audio_file}]"
    print(definition)
    csvWriter.writerow([word, translit, definition, example])
    return
    # order: front(word), phonetics[sound:{audio_file}], definition, examples


def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)


# rip phonetics

# rip audio:
# try to rip audio from thai-dictionary
# if unavailable use google TTS
# store resulting mp3 (with word_name.mp3) in anki media folder directory: MEDIA_LOCATION
# create new csv file using unix timestamp as name
# create anki card following the csv format
# input error catching


def synthesize_text(text, audioFileLocation):
    """Synthesizes speech from the input string of text."""

    client = texttospeech.TextToSpeechClient.from_service_account_json(GCLOUD_SERVICE_ACCOUNT)

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
        language_code="th-TH",
        name="th-TH-Standard-A",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice,
                 "audio_config": audio_config}
    )

    # The response's audio_content is binary.
    with open(audioFileLocation, "wb") as out:
        out.write(response.audio_content)
        print(f"Audio content written to file {audioFileLocation}")


def getWords(filename):
    wordList = []
    if filename == None:
        while True:
            word = input("input word, or press enter to complete:")
            if word != "":
                wordList.append(word)
            else:
                # pressed enter
                break
    else:
        with open(filename) as vocabWords:
            wordList.extend([line.strip() for line in vocabWords.readlines()])

    return wordList
            
        
driver = webdriver.Chrome(ChromeDriverManager().install())

Path("./results").mkdir(parents=True, exist_ok=True)

filename = "results/" + datetime.now().strftime("%d%b%Y %H%M") + ".csv"
with open(filename, "w", newline="") as csvFile:
    csvWriter = csv.writer(csvFile, delimiter=",")
    try:
        wordList = getWords(sys.argv[1])
    except:
        wordList = getWords(None)
    for word in wordList:
        try:
            wordPage = search_word(word, driver)
            definitions, examples = get_definition_and_example(wordPage, word)
            phonetics = get_phonetics(wordPage)
            try:
                wordUrl = get_audio_url(wordPage)
                audioFileLocation = download_audio_file(
                    wordUrl, MEDIA_LOCATION)
            except:
                audioFileLocation = str(datetime.now().timestamp()) + ".mp3"
                synthesize_text(word, f"{MEDIA_LOCATION}/{audioFileLocation}")
            add_anki_card(
                csvWriter, word, definitions, phonetics, f"{audioFileLocation}", examples
            )
            sound = AudioSegment.from_file(
                f"{MEDIA_LOCATION}/{audioFileLocation}", "mp3"
            )
            normalized_sound = match_target_amplitude(sound, -20.0)
            normalized_sound.export(
                f"{MEDIA_LOCATION}/{audioFileLocation}", format="mp3"
            )
        except Exception as e:
            print("ERROR ENCOUNTED, SKIPPING WORD" + repr(e))

driver.close()