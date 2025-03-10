"""
LinkedIn CSS selectors and target definitions.
"""

# LinkedIn profile container selectors
PROFILE_CONTAINER_SELECTORS = [
    '.reusable-search__result-container',
    'li.reusable-search__result-container',
    '.entity-result',
    'li.entity-result',
    'li.ember-view',
    'li.search-result',
    '.search-result',
    '[data-test-search-result]',
    'ul.reusable-search__entity-result-list > li',
    'ul.search-results__list > li',
    '.artdeco-list__item',
    '.search-entity'
]

# Selectors for extracting name from profile
NAME_SELECTORS = [
    ".entity-result__title-text a span[aria-hidden='true']",
    ".entity-result__title-text span[aria-hidden='true']",
    ".search-result__info .actor-name",
    ".app-aware-link span[aria-hidden='true']",
    ".entity-result__title-line a span span",
    "span[dir='ltr']",
    ".artdeco-entity-lockup__title span",
    ".linked-area span",
    ".actor-name",
    ".title-text",
    ".artdeco-entity-lockup__title"
]

# Selectors for extracting headline from profile
HEADLINE_SELECTORS = [
    ".entity-result__primary-subtitle",
    ".search-result__info .subline-level-1",
    ".entity-result__summary span",
    ".entity-result__primary-subtitle span",
    ".artdeco-entity-lockup__subtitle",
    ".entity-result__summary",
    ".subline-level-1",
    ".search-result-profile-subtitle",
    ".primary-subtitle",
    ".headline"
]

# Selectors for extracting location from profile
LOCATION_SELECTORS = [
    ".entity-result__secondary-subtitle",
    ".search-result__info .subline-level-2",
    ".entity-result__secondary-subtitle span",
    ".artdeco-entity-lockup__caption",
    ".subline-level-2",
    ".search-result-profile-secondary-subtitle",
    ".secondary-subtitle"
]

# Selectors for next page button
NEXT_BUTTON_SELECTORS = [
    "button[aria-label='Next']",
    ".artdeco-pagination__button--next",
    ".artdeco-pagination__button.artdeco-pagination__button--next",
    "[data-test-pagination-page-btn='next']",
    ".artdeco-pagination__button--next:not(.artdeco-button--disabled)",
    "li.artdeco-pagination__indicator--number.active + li a",
    "button.next",
    ".next-btn",
    ".pagination-next",
    "button.page-next",
    ".pagination-btn[data-control-name='pagination_next']",
    ".artdeco-pagination ul li:last-child a",
    ".artdeco-pagination ul li:last-child button"
]

# Target industries for life coaching
TARGET_INDUSTRIES = [
    "Technology", 
    "Finance", 
    "Healthcare", 
    "Education", 
    "Consulting", 
    "Media",
    "Marketing",
    "Entrepreneurship",
    "Human Resources"
]

# Target roles for life coaching
TARGET_ROLES = [
    "CEO", 
    "CTO", 
    "CFO", 
    "Director", 
    "Manager", 
    "Executive", 
    "VP", 
    "President",
    "Founder",
    "Owner",
    "Leader",
    "Head",
    "Professional"
]

# Target keywords for life coaching
TARGET_KEYWORDS = [
    "career transition",
    "professional development",
    "leadership development",
    "work life balance",
    "burnout",
    "career growth",
    "personal development",
    "executive coaching",
    "leadership coaching",
    "professional coaching",
    "business coaching",
    "transformation"
]

# Title/role-based scoring weights
ROLE_KEYWORD_SCORES = {
    "ceo": 20, 
    "chief executive": 20, 
    "founder": 15, 
    "president": 15,
    "director": 10, 
    "manager": 8, 
    "head": 8, 
    "vp": 10, 
    "vice president": 10,
    "leader": 5, 
    "executive": 10, 
    "officer": 5, 
    "professional": 3,
    "hr": 5, 
    "human resources": 5
}

# Coaching interest keywords
COACHING_KEYWORDS = [
    "development", 
    "growth", 
    "transition", 
    "leadership", 
    "change", 
    "transform", 
    "burnout", 
    "balance", 
    "career"
]

# Target locations for scoring
TARGET_LOCATIONS = [
    "london", 
    "uk", 
    "united kingdom", 
    "england", 
    "manchester", 
    "birmingham", 
    "leeds", 
    "bristol"
]