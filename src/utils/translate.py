# Third-party library
from googletrans import Translator

translator = Translator()


def tesseract_skip_languages():
    """
    Returns a set of languages that are not supported by Google Translation.

    These languages are skipped when creating QTableWidgetItem and QComboBox
    objects in the application's UI.
    """
    return {'breton',
            'cherokee',
            'dzongkha',
            'faroese',
            'inuktitut',
            'syriac',
            'tibetan',
            'tonga'}


def tesseract_languages():
    """
    Returns a set of languages that is used to download OCR languages from Github Tesseract

    Also use to compare in Google Translate languages
    """
    return {
        'afr': 'afrikaans',
        'sqi': 'albanian',
        'amh': 'amharic',
        'ara': 'arabic',
        'hye': 'armenian',
        'asm': 'assamese',
        'aze': 'azerbaijani',
        'aze_cyrl': 'azerbaijani (cyrilic)',
        'eus': 'basque',
        'bel': 'belarusian',
        'ben': 'bengali',
        'bos': 'bosnian',
        'bre': 'breton',
        'bul': 'bulgarian',
        'mya': 'burmese',
        'cat': 'catalan',
        'ceb': 'cebuano',
        'chr': 'cherokee',
        'chi_sim': 'chinese (simplified)',
        'chi_tra': 'chinese (traditional)',
        'cos': 'corsican',
        'hrv': 'croatian',
        'ces': 'czech',
        'dan': 'danish',
        'nld': 'dutch',
        'dzo': 'dzongkha',
        'eng': 'english',
        'epo': 'esperanto',
        'est': 'estonian',
        'fao': 'faroese',
        'fil': 'filipino',
        'fin': 'finnish',
        'fra': 'french',
        'glg': 'galician',
        'kat': 'georgian',
        'kat_old': 'georgian (old)',
        'deu': 'german',
        'frk': 'german (fraktur)',
        'ell': 'greek',
        'guj': 'gujarati',
        'hat': 'haitian creole',
        'heb': 'hebrew',
        'hin': 'hindi',
        'hun': 'hungarian',
        'isl': 'icelandic',
        'ind': 'indonesian',
        'iku': 'inuktitut',
        'gle': 'irish',
        'ita': 'italian',
        'jpn': 'japanese',
        'jpn_vert': 'japanese (vertical)',
        'jav': 'javanese',
        'kan': 'kannada',
        'kaz': 'kazakh',
        'khm': 'khmer',
        'kor': 'korean',
        'kor_vert': 'korean (vertical)',
        'kmr': 'kurdish (kurmanji)',
        'kir': 'kyrgyz',
        'lao': 'lao',
        'lat': 'latin',
        'lav': 'latvian',
        'lit': 'lithuanian',
        'ltz': 'luxembourgish',
        'mkd': 'macedonian',
        'msa': 'malay',
        'mal': 'malayalam',
        'mlt': 'maltese',
        'mri': 'maori',
        'mar': 'marathi',
        'mon': 'mongolian',
        'nep': 'nepali',
        'nor': 'norwegian',
        'ori': 'odia',
        'pus': 'pashto',
        'fas': 'persian',
        'pol': 'polish',
        'por': 'portuguese',
        'pan': 'punjabi',
        'que': 'quechua',
        'ron': 'romanian',
        'rus': 'russian',
        'san': 'sanskrit',
        'gla': 'scottish gaelic',
        'srp': 'serbian',
        'srp_latn': 'serbian (latin)',
        'snd': 'sindhi',
        'sin': 'sinhala',
        'slk': 'slovak',
        'slv': 'slovenian',
        'spa': 'spanish',
        'sun': 'sundanese',
        'swa': 'swahili',
        'swe': 'swedish',
        'syr': 'syriac',
        'tgk': 'tajik',
        'tam': 'tamil',
        'tat': 'tatar',
        'tel': 'telugu',
        'tha': 'thai',
        'bod': 'tibetan',
        'tir': 'tigrinya',
        'ton': 'tonga',
        'tur': 'turkish',
        'uig': 'uyghur',
        'ukr': 'ukrainian',
        'urd': 'urdu',
        'uzb': 'uzbek',
        'vie': 'vietnamese',
        'cym': 'welsh',
        'fry': 'western frisian',
        'yid': 'yiddish',
        'yor': 'yoruba'
    }


def googletrans_languages():
    return {
        'af': 'afrikaans',
        'sq': 'albanian',
        'am': 'amharic',
        'ar': 'arabic',
        'hy': 'armenian',
        'as': 'assamese',  # Added - Not supported
        'ay': 'aymara',  # Added - Not supported
        'az': 'azerbaijani',
        'eu': 'basque',
        'be': 'belarusian',
        'bn': 'bengali',
        'bho': 'bhojpuri',
        'bs': 'bosnian',
        'bg': 'bulgarian',
        'my': 'burmese',  # Added - Supported
        'ca': 'catalan',
        'ceb': 'cebuano',
        'ny': 'chichewa',
        'zh-cn': 'chinese (simplified)',
        'zh-tw': 'chinese (traditional)',
        'co': 'corsican',
        'hr': 'croatian',
        'cs': 'czech',
        'da': 'danish',
        'dv': 'dhivehi',  # Added - Not supported
        'doi': 'doghri',  # Added - Not supported ('hi' in detect language)
        'nl': 'dutch',
        'en': 'english',
        'eo': 'esperanto',
        'et': 'estonian',
        'ee': 'ewe',  # Added - Supported (Bug: Translated to Estonian)
        'tl': 'filipino',
        'fi': 'finnish',
        'fr': 'french',
        'gl': 'galician',
        'ka': 'georgian',
        'de': 'german',
        'el': 'greek',
        'gu': 'gujarati',
        'ht': 'haitian creole',
        'ha': 'hausa',
        'haw': 'hawaiian',
        'iw': 'hebrew',  # Added - Supported (Changed from 'he' to 'iw')
        'hi': 'hindi',
        'hmn': 'hmong',
        'hu': 'hungarian',
        'is': 'icelandic',
        'ig': 'igbo',
        'ilo': 'ilocano',
        'id': 'indonesian',
        'ga': 'irish',
        'it': 'italian',
        'ja': 'japanese',
        'jw': 'javanese',
        'kn': 'kannada',
        'kk': 'kazakh',
        'km': 'khmer',
        'rw': 'kinyarwanda',  # Added - Not supported
        'gom': 'konkani',  # Added - Not supported
        'kri': 'krio',  # Added - Not supported
        'ko': 'korean',
        'ku': 'kurdish (kurmanji)',
        'ckb': 'kurdish (sorani)',  # Added - Not supported
        'ky': 'kyrgyz',
        'lo': 'lao',
        'la': 'latin',
        'lv': 'latvian',
        'ln': 'lingala',  # Added - Not supported
        'lt': 'lithuanian',
        'lg': 'luganda',  # Added - Not supported
        'lb': 'luxembourgish',
        'mk': 'macedonian',
        'mai': 'maithili',  # Added - Not supported
        'mg': 'malagasy',
        'ms': 'malay',
        'ml': 'malayalam',
        'mt': 'maltese',
        'mi': 'maori',
        'mr': 'marathi',
        'mni-Mtei': 'meiteilon (manipuri)',  # Added - Not supported
        'lus': 'mizo',  # Added - Not supported
        'mn': 'mongolian',
        'ne': 'nepali',
        'no': 'norwegian',
        'or': 'odia',
        'om': 'oromo',  # Added - Not supported
        'ps': 'pashto',
        'fa': 'persian',
        'pl': 'polish',
        'pt': 'portuguese',
        'pa': 'punjabi',
        'qu': 'quechua',  # Added - Supported
        'ro': 'romanian',
        'ru': 'russian',
        'sm': 'samoan',
        'sa': 'sanskrit',  # Added - Not supported
        'gd': 'scots gaelic',
        'nso': 'sepedi',  # Added - Not supported
        'sr': 'serbian',
        'st': 'southern sotho',
        'sn': 'shona',
        'sd': 'sindhi',
        'si': 'sinhala',
        'sk': 'slovak',
        'sl': 'slovenian',
        'so': 'somali',
        'es': 'spanish',
        'su': 'sundanese',
        'sw': 'swahili',
        'sv': 'swedish',
        'tg': 'tajik',
        'ta': 'tamil',
        'tt': 'tatar',  # Added - Not supported
        'te': 'telugu',
        'th': 'thai',
        'ti': 'tigrinya',  # Added - Not supported
        'tr': 'turkish',
        'tk': 'turkmen',  # Added - Not supported
        'ak': 'twi',  # Added - Not supported
        'uk': 'ukrainian',
        'ur': 'urdu',
        'ug': 'uyghur',
        'uz': 'uzbek',
        'vi': 'vietnamese',
        'cy': 'welsh',
        'fy': 'western frisian',  # Added (Changed from 'frisian' to 'western frisian')
        'xh': 'xhosa',
        'yi': 'yiddish',
        'yo': 'yoruba',
        'zu': 'zulu'
    }


def translate_text(extracted_text, configuration):
    config = configuration
    googletrans_languages_dict = googletrans_languages()
    tesseract_languages_dict = tesseract_languages()

    source_language_code = None
    source_language_name = None
    # Identify a single language
    # Evaluate the OCR language and retrieve the corresponding language
    # For example, if the language is 'eng', match it with the googletrans_languages dictionary and identify the key that corresponds to 'English'
    # Extract the first part of the language string, for instance, extract 'korean' from 'korean (vertical)'
    language = tesseract_languages_dict.get(config['ocr']['language'])
    if language:
        for gcode, gname in googletrans_languages_dict.items():
            #  If the googletrans language name matches the first part of the OCR language, print it and set the source language code and name
            if gname == language.split(' ')[0].lower():
                source_language_code = gcode
                source_language_name = gname
    else:
        # ValueError indicates that the user selected multiple OCR language or the language in the config not found
        raise ValueError(f"Source language ({config['ocr']['language']}) not found in translate language list")

    # Find the position of the language in the Tesseract dictionary
    # Then get the destination code from the config based on the 'counter' number
    counter = 0
    destination_language_code = None
    destination_language_name = None
    # Filter out languages from Tesseract that are in the skip list
    save_tesseract_languages = [lang for lang in tesseract_languages().values() if lang not in tesseract_skip_languages()]
    for tess_language_name in save_tesseract_languages:
        # If the current language is the one we're looking for, get its corresponding destination code
        if tess_language_name == language:
            # Get the destination language code from the config file at the index specified by 'counter'
            destination_language_code = config['translate']['languages'][counter]
            # Using the destination language code as a key, get the corresponding destination language name (value)
            destination_language_name = googletrans_languages_dict.get(destination_language_code)
        # Increment the counter for the next iteration
        counter += 1
    if destination_language_code is None:
        raise ValueError(f"Destination language not found in the language list.")

    try:
        translated_text = translator.translate(extracted_text, src=source_language_code, dest=destination_language_code)
        translated_text_result = translated_text.text
    except Exception as e:
        raise ValueError(f"Translating error: {e}")
    # The destination_language_code is used for the translate_in_default_browser function when translating the OCR text
    return translated_text_result, source_language_name, destination_language_name, destination_language_code
