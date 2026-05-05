"""
qa_lexicon.py — Lexical data for atom-qa.py.

Three structures:
  - ANGLICISM_TABLE: (english, spanish) substitution pairs flagged in non-English atoms.
  - ANGLICISM_WHITELIST: proper nouns / tech terms that survive the anglicism check.
  - ACRONYM_TABLE: (acronym, expansion) pairs. Atoms must define each acronym on first
    use; auto-fix inserts " (expansion)" after the first occurrence if missing.

Edit this file to tune QA behavior — atom-qa.py reads it on every run.
"""


ANGLICISM_TABLE = [
    ("host", "anfitrión"),
    ("hosts", "anfitriones"),
    ("guest", "huésped"),
    ("guests", "huéspedes"),
    ("review", "reseña"),
    ("reviews", "reseñas"),
    ("rating", "calificación"),
    ("amenity", "comodidad"),
    ("amenities", "comodidades"),
    ("booking", "reserva"),
    ("bookings", "reservas"),
    ("listing", "anuncio"),
    ("listings", "anuncios"),
    ("check-in", "entrada"),
    ("check-out", "salida"),
    ("weekend", "fin de semana"),
    ("last-minute", "último momento"),
    ("min-stay", "estancia mínima"),
    ("base price", "precio base"),
    ("funnel", "embudo"),
    ("ranking", "posicionamiento"),
    ("occupancy", "ocupación"),
    ("revenue", "ingresos"),
    ("cleaner", "personal de limpieza"),
    ("cleaners", "personal de limpieza"),
    ("turnover", "rotación"),
    ("pet-friendly", "admite mascotas"),
    ("hot tub", "jacuzzi"),
    ("smart-lock", "cerradura inteligente"),
    ("workspace", "zona de trabajo"),
    ("king bed", "cama king"),
    ("sweet spot", "punto óptimo"),
    ("follow-up", "seguimiento"),
    ("repeat guest", "huésped recurrente"),
    ("social proof", "prueba social"),
    ("take rate", "comisión"),
    ("fee", "tarifa"),
    ("tier", "nivel"),
]

ANGLICISM_WHITELIST = {
    "PriceLabs", "Wheelhouse", "Beyond", "Hostfully", "Hospitable", "Guesty",
    "OwnerRez", "Airbnb", "Booking", "Vrbo", "AllTheRooms", "AirDNA",
    "NoiseAware", "Minut", "Google", "YouTube", "Superhost", "Aircover",
    "Instant Book", "Stays", "Co-Host", "WiFi", "PMS", "API", "URL", "OS",
    "JSON", "YAML", "SEO", "ADR", "BLT", "FPG", "TOS", "GMB", "StayFi",
    "IntelliHost", "check-in",  # operational term allowed in context
}

ACRONYM_TABLE = [
    ("ADR", "Average Daily Rate"),
    ("RevPAR", "Revenue Per Available Rental"),
    ("PMS", "Property Management System"),
    ("OTA", "Online Travel Agency"),
    ("LOS", "Length of Stay"),
    ("DOW", "Day of Week"),
    ("STR", "Short-Term Rental"),
    ("KPI", "Key Performance Indicator"),
    ("ROI", "Return on Investment"),
    ("TOS", "Terms of Service"),
]
