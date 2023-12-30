# Third-party library
import webbrowser

from googletrans import Translator

# Custom library
from src.config.config import load_config

translator = Translator()


def tesseract_languages():
    return {
        'afr': 'Afrikaans',
        'sqi': 'Albanian',
        'amh': 'Amharic',
        'ara': 'Arabic',
        'hye': 'Armenian',
        'asm': 'Assamese',
        'aze': 'Azerbaijani',
        'aze_cyrl': 'Azerbaijani - Cyrilic',
        'eus': 'Basque',
        'bel': 'Belarusian',
        'ben': 'Bengali',
        'bos': 'Bosnian',
        'bre': 'Breton',
        'bul': 'Bulgarian',
        'mya': 'Burmese',
        'cat': 'Catalan; Valencian',
        'ceb': 'Cebuano',
        'khm': 'Central Khmer',
        'chr': 'Cherokee',
        'chi_sim': 'Chinese - Simplified',
        'chi_tra': 'Chinese - Traditional',
        'cos': 'Corsican',
        'hrv': 'Croatian',
        'ces': 'Czech',
        'dan': 'Danish',
        'nld': 'Dutch',
        'dzo': 'Dzongkha',
        'eng': 'English',
        'epo': 'Esperanto',
        'est': 'Estonian',
        'fao': 'Faroese',
        'fil': 'Filipino (old - Tagalog)',
        'fin': 'Finnish',
        'fra': 'French',
        'glg': 'Galician',
        'kat': 'Georgian',
        'kat_old': 'Georgian - Old',
        'deu': 'German',
        'frk': 'German - Fraktur',
        'ell': 'Greek',
        'guj': 'Gujarati',
        'hat': 'Haitian Creole',
        'heb': 'Hebrew',
        'hin': 'Hindi',
        'hun': 'Hungarian',
        'isl': 'Icelandic',
        'ind': 'Indonesian',
        'iku': 'Inuktitut',
        'gle': 'Irish',
        'ita': 'Italian',
        'jpn': 'Japanese',
        'jav': 'Javanese',
        'kan': 'Kannada',
        'kaz': 'Kazakh',
        'kor': 'Korean',
        'kor_vert': 'Korean (vertical)',
        'kmr': 'Kurdish (kurmanji)',
        'kir': 'Kyrgyz',
        'lao': 'Lao',
        'lat': 'Latin',
        'lav': 'Latvian',
        'lit': 'Lithuanian',
        'ltz': 'Luxembourgish',
        'mkd': 'Macedonian',
        'msa': 'Malay',
        'mal': 'Malayalam',
        'mlt': 'Maltese',
        'mri': 'Maori',
        'mar': 'Marathi',
        'mon': 'Mongolian',
        'nep': 'Nepali',
        'nor': 'Norwegian',
        'ori': 'Odia',
        'pus': 'Pashto',
        'fas': 'Persian',
        'pol': 'Polish',
        'por': 'Portuguese',
        'pan': 'Punjabi',
        'que': 'Quechua',
        'ron': 'Romanian; Moldavian; Moldovan',
        'rus': 'Russian',
        'san': 'Sanskrit',
        'gla': 'Scottish Gaelic',
        'srp': 'Serbian',
        'srp_latn': 'Serbian - Latin',
        'snd': 'Sindhi',
        'sin': 'Sinhala; Sinhalese',
        'slk': 'Slovak',
        'slv': 'Slovenian',
        'spa': 'Spanish',
        'sun': 'Sundanese',
        'swa': 'Swahili',
        'swe': 'Swedish',
        'syr': 'Syriac',
        'tgk': 'Tajik',
        'tam': 'Tamil',
        'tat': 'Tatar',
        'tel': 'Telugu',
        'tha': 'Thai',
        'bod': 'Tibetan',
        'tir': 'Tigrinya',
        'ton': 'Tonga',
        'tur': 'Turkish',
        'uig': 'Uyghur',
        'ukr': 'Ukrainian',
        'urd': 'Urdu',
        'uzb': 'Uzbek',
        'vie': 'Vietnamese',
        'cym': 'Welsh',
        'fry': 'Western Frisian',
        'yid': 'Yiddish',
        'yor': 'Yoruba'
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
        'doi': 'doghri',  # Added - Not supported ('hi' in detected)
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


def translate_text(extracted_text):
    config = load_config()
    googletrans_languages_dict = googletrans_languages()
    tesseract_languages_dict = tesseract_languages()

    # Identify a single language
    # Evaluate the OCR language and retrieve the corresponding language
    # For instance, if the language is 'eng', compare it with the googletrans dictionary and identify the key which corresponds to 'English'
    language = tesseract_languages_dict.get(config['ocr']['language'])
    if language:
        source_language = ''.join(k for k, v in googletrans_languages_dict.items() if v == language.lower())
    else:
        raise ValueError(f"Source language '{config['ocr']['language']}' not found in the translate language list.")

    dest_lang = config['translate'][language.lower()]
    destination_language = None
    destination_language_name = None
    for code, name in googletrans_languages_dict.items():
        if code == dest_lang:
            destination_language = code
            destination_language_name = name
    if not destination_language:
        raise ValueError(f"Destination language '{dest_lang}' not found in the language list.")

    try:
        translated_text = translator.translate(extracted_text, src=source_language, dest=destination_language)
        translated_text_result = translated_text.text
    except Exception:
        translated_text_result = f"The {destination_language_name} language is not currently supported by googletrans module."
    return translated_text_result
