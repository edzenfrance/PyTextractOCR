# Third-party library
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
        'nld': 'Dutch; Flemish',
        'dzo': 'Dzongkha',
        'eng': 'English',
        'enm': 'English, Middle (1100-1500)',
        'epo': 'Esperanto',
        'est': 'Estonian',
        'fao': 'Faroese',
        'fil': 'Filipino (old - Tagalog)',
        'fin': 'Finnish',
        'fra': 'French',
        'frm': 'French, Middle (ca.1400-1600)',
        'glg': 'Galician',
        'kat': 'Georgian',
        'kat_old': 'Georgian - Old',
        'deu': 'German',
        'frk': 'German - Fraktur',
        'grc': 'Greek, Ancient (to 1453) (contrib)',
        'ell': 'Greek, Modern (1453-)',
        'guj': 'Gujarati',
        'hat': 'Haitian; Haitian Creole',
        'heb': 'Hebrew',
        'hin': 'Hindi',
        'hun': 'Hungarian',
        'isl': 'Icelandic',
        'ind': 'Indonesian',
        'iku': 'Inuktitut',
        'gle': 'Irish',
        'ita': 'Italian',
        'ita_old': 'Italian - Old',
        'jpn': 'Japanese',
        'jav': 'Javanese',
        'kan': 'Kannada',
        'kaz': 'Kazakh',
        'kir': 'Kirghiz; Kyrgyz',
        'kor': 'Korean',
        'kor_vert': 'Korean (vertical)',
        'kmr': 'Kurmanji (Kurdish - Latin Script)',
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
        'equ': 'Math / equation detection module',
        'mon': 'Mongolian',
        'nep': 'Nepali',
        'nor': 'Norwegian',
        'oci': 'Occitan (post 1500)',
        'osd': 'Orientation and script detection module',
        'ori': 'Oriya',
        'pan': 'Panjabi; Punjabi',
        'fas': 'Persian',
        'pol': 'Polish',
        'por': 'Portuguese',
        'pus': 'Pushto; Pashto',
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
        'spa': 'Spanish; Castilian',
        'spa_old': 'Spanish; Castilian - Old',
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
        'uig': 'Uighur; Uyghur',
        'ukr': 'Ukrainian',
        'urd': 'Urdu',
        'uzb': 'Uzbek',
        'uzb_cyrl': 'Uzbek - Cyrilic',
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
        'as': 'assamese',
        'az': 'azerbaijani',
        'eu': 'basque',
        'be': 'belarusian',
        'bn': 'bengali',
        'bs': 'bosnian',
        'bg': 'bulgarian',
        'my': 'burmese',
        'ca': 'catalan',
        'ceb': 'cebuano',
        'ny': 'chichewa',
        'zh-cn': 'chinese (simplified)',
        'zh-tw': 'chinese (traditional)',
        'co': 'corsican',
        'hr': 'croatian',
        'cs': 'czech',
        'da': 'danish',
        'nl': 'dutch',
        'en': 'english',
        'eo': 'esperanto',
        'et': 'estonian',
        'tl': 'filipino',
        'fi': 'finnish',
        'fr': 'french',
        'fy': 'frisian',
        'gl': 'galician',
        'ka': 'georgian',
        'de': 'german',
        'el': 'greek',
        'gu': 'gujarati',
        'ht': 'haitian creole',
        'ha': 'hausa',
        'haw': 'hawaiian',
        'iw': 'hebrew',
        'he': 'hebrew',
        'hi': 'hindi',
        'hmn': 'hmong',
        'hu': 'hungarian',
        'is': 'icelandic',
        'ig': 'igbo',
        'id': 'indonesian',
        'ga': 'irish',
        'it': 'italian',
        'ja': 'japanese',
        'jw': 'javanese',
        'kn': 'kannada',
        'kk': 'kazakh',
        'km': 'khmer',
        'ko': 'korean',
        'ku': 'kurdish (kurmanji)',
        'ky': 'kyrgyz',
        'lo': 'lao',
        'la': 'latin',
        'lv': 'latvian',
        'lt': 'lithuanian',
        'lb': 'luxembourgish',
        'mk': 'macedonian',
        'mg': 'malagasy',
        'ms': 'malay',
        'ml': 'malayalam',
        'mt': 'maltese',
        'mi': 'maori',
        'mr': 'marathi',
        'mn': 'mongolian',
        'ne': 'nepali',
        'no': 'norwegian',
        'or': 'odia',
        'ps': 'pashto',
        'fa': 'persian',
        'pl': 'polish',
        'pt': 'portuguese',
        'pa': 'punjabi',
        'qu': 'quechua',
        'ro': 'romanian',
        'ru': 'russian',
        'sa': 'sanskrit',
        'sm': 'samoan',
        'gd': 'scots gaelic',
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
        'tt': 'tatar',  # ADDED
        'te': 'telugu',
        'th': 'thai',
        'tr': 'turkish',
        'uk': 'ukrainian',
        'ur': 'urdu',
        'ug': 'uyghur',
        'uz': 'uzbek',
        'vi': 'vietnamese',
        'cy': 'welsh',
        'xh': 'xhosa',
        'yi': 'yiddish',
        'yo': 'yoruba',
        'zu': 'zulu'
    }


def translate_text(extracted_text):
    config = load_config()
    googletrans_languages_dict = googletrans_languages()
    tesseract_languages_dict = tesseract_languages()

    language = tesseract_languages_dict.get(config['ocr']['language'])  # Find only one language
    if language:
        source_language = ''.join(k for k, v in googletrans_languages_dict.items() if v == language.lower())
    else:
        raise ValueError(f"Source language '{config['ocr']['language']}' not found in the translate language list.")

    dest_lang = config['translate'][language.lower()]
    destination_language = next((code for code, name in googletrans_languages_dict.items() if code == dest_lang), None)
    if not destination_language:
        raise ValueError(f"Destination language '{dest_lang}' not found in the language list.")

    translated_text = translator.translate(extracted_text, src=source_language, dest=destination_language)
    translated_text_result = translated_text.text
    return translated_text_result
