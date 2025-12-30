"""
Hebrew station name normalization.
Maps common variations/typos to canonical Hebrew station names.
"""

import re

def normalize_text(text: str) -> str:
    """
    Normalize Hebrew text for consistent matching.
    Removes special characters, extra whitespace, and standardizes format.
    """
    if not text:
        return ""
    
    # Convert to string and strip
    normalized = str(text).strip()
    
    # Remove trailing dots and special punctuation
    normalized = re.sub(r'[.\s]+$', '', normalized)
    normalized = re.sub(r'^[.\s]+', '', normalized)
    
    # Replace multiple spaces with single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove common separators that might be inconsistent
    normalized = normalized.replace('_', ' ')
    normalized = normalized.replace('-', ' ')
    
    # Normalize quotes (Hebrew often has different quote styles)
    normalized = normalized.replace('"', '')
    normalized = normalized.replace("'", '')
    normalized = normalized.replace('״', '')
    normalized = normalized.replace('׳', '')
    
    # Trim again
    normalized = normalized.strip()
    
    return normalized

# Hebrew station name variations mapped to canonical names
HEBREW_STATION_ALIASES = {
    # Orientation variations
    'התמחות': 'אוריינטציה',
    'התאמה': 'אוריינטציה',
    'אוריאנטציה': 'אוריינטציה',
    
    # Birth/Delivery variations
    'לידה': 'חדר לידה',
    'חל"י': 'חדר לידה',
    'חדר לידה': 'חדר לידה',
    
    # Maternity intro
    'מיילדות': 'יולדות',
    'מחלקת יולדות': 'יולדות',
    
    # HRP variations
    'הריון בסיכון': 'הריון בסיכון א',  # Default to A if not specified
    'הריונות בסיכון': 'הריון בסיכון א',
    'הריונות בסיכון א': 'הריון בסיכון א',
    'הריונות בסיכון ב': 'הריון בסיכון ב',
    'הב"ס': 'הריון בסיכון א',
    'הב"ס א': 'הריון בסיכון א',
    'הב"ס ב': 'הריון בסיכון ב',
    'הבס': 'הריון בסיכון א',
    'הבס א': 'הריון בסיכון א',
    'הבס ב': 'הריון בסיכון ב',
    'HRP': 'הריון בסיכון א',
    'HRP א': 'הריון בסיכון א',
    'HRP ב': 'הריון בסיכון ב',
    'hrp': 'הריון בסיכון א',
    'hrp א': 'הריון בסיכון א',
    'hrp ב': 'הריון בסיכון ב',
    
    # Gynecology variations
    'גינקולוגיה': 'גינקולוגיה א',  # Default to A if not specified
    'גניקולוגיה': 'גינקולוגיה א',
    'גניקולוגיה א': 'גינקולוגיה א',
    'גניקולוגיה ב': 'גינקולוגיה ב',
    'מחלקת נשים': 'גינקולוגיה א',
    'מחלקת נשים א': 'גינקולוגיה א',
    'מחלקת נשים ב': 'גינקולוגיה ב',
    
    # ER variations
    'מיון': 'מיון יולדות',
    'מיון מיילדות': 'מיון יולדות',
    'מיון נשים': 'מיון נשים',
    'מיון גינקולוגי': 'מיון נשים',
    
    # ER Supervisor
    'אחראי מיון': 'אחראי מיון יולדות',
    'אחראי מיון מיילדות': 'אחראי מיון יולדות',
    'פיקוח מיון': 'אחראי מיון יולדות',
    'אחראי מיון שטח': 'אחראי מיון יולדות',
    'מיון שטח': 'מיון יולדות',
    'מיון נרב': 'מיון נשים',
    
    # Day units
    'יום גינקולוגי': 'א.יום גינקולוגי',
    'גינקולוגיה יום': 'א.יום גינקולוגי',
    'אשפוז יום גינקולוגי': 'א.יום גינקולוגי',
    'א. יום גינקו': 'א.יום גינקולוגי',
    'א יום גינקו': 'א.יום גינקולוגי',
    'יום גינקו': 'א.יום גינקולוגי',
    'יום מיילדותי': 'א.יום מיילדותי',
    'מיילדות יום': 'א.יום מיילדותי',
    'אשפוז יום מיילדותי': 'א.יום מיילדותי',
    'א. יום מיילדותי': 'א.יום מיילדותי',
    'א יום מיילדותי': 'א.יום מיילדותי',
    'א. יום מיילד': 'א. יום מיילד',  # Alternative midwifery day station
    'א יום מיילד': 'א. יום מיילד',
    'יום מיילד': 'א. יום מיילד',
    'אשפוז יום': 'אשפוז יום',  # Generic day hospitalization
    'יום': 'אשפוז יום',
    
    # Stages
    'שלב a': 'שלב א',
    'שלב b': 'שלב ב',
    'שלבא': 'שלב א',
    'שלבב': 'שלב ב',
    
    # Rotations
    'רוטציה a': 'רוטציה א',
    'רוטציה b': 'רוטציה ב',
    
    # Department
    'מחלקה': 'מחלקה',
    'מחלקת נשים ויולדות': 'מחלקה',
    
    # IVF variations
    'הפריה חוץ גופית': 'IVF',
    'הפו"ג': 'IVF',
    'הפוג': 'IVF',
    'ivf': 'IVF',
    
    # Oncology
    'אונקולוגיה': 'גינקואונקולוגיה',
    'גינקו-אונקולוגיה': 'גינקואונקולוגיה',
    'אונקולוגיה גינקולוגית': 'גינקואונקולוגיה',
    
    # Basic sciences
    'מדעים בסיסיים': 'מדעי היסוד',
    'מדעי הבסיס': 'מדעי היסוד',
    'מדעים': 'מדעי היסוד',
    
    # Leave types
    'חופשת לידה': 'חל"ד',
    'חלד': 'חל"ד',
    'חופשה ללא תשלום': 'חל"ת',
    'חלת': 'חל"ת',
    'ימי מחלה': 'מחלה',
    'חופשת מחלה': 'מחלה',
}

def normalize_station_name(raw_name: str) -> str:
    """
    Normalize station name and map variations to canonical Hebrew names.
    Returns the canonical Hebrew station key or the normalized input if no match.
    """
    # First normalize the text
    normalized = normalize_text(raw_name)
    
    # Try exact match in aliases
    if normalized in HEBREW_STATION_ALIASES:
        return HEBREW_STATION_ALIASES[normalized]
    
    # Try case-insensitive match
    normalized_lower = normalized.lower()
    for alias, canonical in HEBREW_STATION_ALIASES.items():
        if alias.lower() == normalized_lower:
            return canonical
    
    # Return normalized text as-is if no alias found
    return normalized

