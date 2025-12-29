"""
Hebrew to English translation mappings for medical terms.
Precomputed translations for common medical/residency terms.
"""

# Common Hebrew medical terms mapped to English
HEBREW_MEDICAL_TERMS = {
    # Stations
    'התמחות': 'Orientation',
    'לידה': 'Birth',
    'גינקולוגיה': 'Gynecology',
    'מיילדות': 'Maternity',
    'מחלקה': 'Department',
    'רוטציה': 'Rotation',
    'חדר לידה': 'Delivery Room',
    'מיון': 'Emergency Room',
    'יום': 'Day',
    
    # Departments
    'מחלקה א': 'Department A',
    'מחלקה ב': 'Department B',
    
    # Stages
    'שלב א': 'Stage A',
    'שלב ב': 'Stage B',
    
    # Other terms
    'הפריה חוץ גופית': 'IVF',
    'אונקולוגיה גינקולוגית': 'Gyneco-Oncology',
    'פיקוח': 'Supervisor',
    'חופשת לידה': 'Maternity Leave',
    'חופשה ללא תשלום': 'Unpaid Leave',
    
    # Time periods
    'חודש': 'Month',
    'חודשים': 'Months',
    'שנה': 'Year',
    'שנים': 'Years',
}

def get_hebrew_translation(text: str) -> str:
    """Get precomputed translation for common Hebrew terms."""
    return HEBREW_MEDICAL_TERMS.get(text, text)

