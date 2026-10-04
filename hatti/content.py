"""Source-attributed vocabulary facts, not a claim of speaker validation.

Romanisation follows each source. Common words and short translations are
linguistic facts. Editorial teaching text is original to Hatti Quest.
"""
from dataclasses import asdict, dataclass

SOURCE = {
    "id": "jp-learn", "title": "Learn Badaga · Bellie Jayaprakash",
    "url": "https://badaga.co/learn-badaga/", "checked": "2026-10-03",
    "note": "Published community vocabulary; local speaker review is pending."
}
FAMILY_SOURCE = {
    "id": "jp-family", "title": "Family relationships · Bellie Jayaprakash",
    "url": "https://badaga.co/2019/04/28/learn-badaga-5/", "checked": "2026-10-03",
    "note": "Contributor spelling retained; families may use other forms."
}
SOURCES = [SOURCE, FAMILY_SOURCE]

@dataclass(frozen=True)
class Word:
    id: str
    badaga: str
    english: str
    category: str
    note: str
    source_id: str = "jp-learn"
    review_status: str = "source-documented"

def word(id, badaga, english, category, note="", source_id="jp-learn"):
    return Word(id, badaga, english, category, note, source_id)

WORDS = [
    word("how-are-you", "Ollenge iddiya?", "How are you?", "hello", "A conversation starter. Ask your family which form they use with an elder."),
    word("your-name", "Ninna hesaru aena?", "What is your name?", "hello", "Use this in an introduction with a friend."),
    word("my-name", "Enna hesaru Bhoja", "My name is Bhoja", "hello", "Bhoja is the example name in the source; practise with your own name together."),
    word("your-village", "Ninna Hatti edu?", "Which is your village?", "hello", "Ask a relative about the village your family knows."),
    word("badaga-question", "Nee ondu Badagana?", "Are you a Badaga?", "hello", "An identity question documented in the source."),
    word("badaga-answer", "Ha, Na ondu Badaga", "Yes, I am a Badaga", "hello", "A short reply to the identity question."),
    word("mother", "Awway", "Mother", "family", "Ask what your family calls your mother.", "jp-family"),
    word("father", "Appa", "Father", "family", "A familiar family word.", "jp-family"),
    word("sister", "Akka", "Elder sister", "family", "The relationship matters: this means an older sister.", "jp-family"),
    word("brother", "ANNa", "Elder brother", "family", "Capital letters preserve the source's Roman spelling.", "jp-family"),
    word("young-brother", "Thamma", "Younger brother", "family", "Compare with the word for an older brother.", "jp-family"),
    word("grandmother", "Heththey", "Grandmother", "family", "Listen to how a relative says this.", "jp-family"),
    word("grandfather", "Iyya", "Grandfather", "family", "Ask a grandparent about a favourite memory.", "jp-family"),
    word("child", "Koosu", "Child", "family", "A word for a child.", "jp-family"),
    word("children", "Kunavay", "Children", "family", "Notice the source's separate entry for children.", "jp-family"),
    word("elders", "Dhoddavakka", "Elders", "family", "Ask your family how they address older relatives.", "jp-family"),
    word("milk", "Haalu", "Milk", "kitchen", "Compare by listening with Hallu, the source's word for teeth."),
    word("hunger", "Hasu", "Hunger", "kitchen", "Find a moment to use this word at home."),
    word("mouth", "Bae", "Mouth", "kitchen", "Point and name in a word game."),
    word("teeth", "Hallu", "Teeth", "kitchen", "Haalu and Hallu are a useful pair to listen to with a speaker."),
    word("tongue", "Naalenge", "Tongue", "kitchen", "Learn through a point-and-name game."),
    word("hands", "Kai", "Hands", "kitchen", "Try a family game: point to your hands."),
    word("fingers", "Beralu", "Fingers", "kitchen", "Count your fingers using your new number words."),
    word("stomach", "Hotte", "Stomach", "kitchen", "A body word from the source's anatomy list."),
    word("eye", "Kannu", "Eye", "kitchen", "A body word to learn by pointing."),
    word("ear", "Kivi", "Ear", "kitchen", "Listen, then point to your ear."),
    word("dog", "Nei", "Dog", "garden", "Look for a dog in a photograph or a story."),
    word("cat", "Koththi", "Cat", "garden", "Name an animal you might see near home."),
    word("cow", "Dana", "Cow", "garden", "One animal word from the published list."),
    word("buffalo", "Emme", "Buffalo", "garden", "Keep cow and buffalo as separate words."),
    word("rabbit", "Mola", "Rabbit", "garden", "Try finding this animal in a picture book."),
    word("elephant", "Aanay", "Elephant", "garden", "Picture-book vocabulary; this scene is imaginative."),
    word("crow", "Kakke", "Crow", "garden", "Ask someone which birds they remember seeing at home."),
    word("parrot", "Kili", "Parrot", "garden", "A bird from the source's list."),
    word("sparrow", "Gubbachi", "Sparrow", "garden", "Try a little bird-spotting word game."),
    word("fish", "Meenu", "Fish", "garden", "Name this animal in a drawing or photograph."),
    word("one", "Ondu", "One", "market", "Count one object."),
    word("two", "Eradu", "Two", "market", "Count two objects."),
    word("three", "Mooru", "Three", "market", "Count three objects."),
    word("four", "Naakku", "Four", "market", "The source also gives other Roman spellings; ask a speaker."),
    word("five", "Iidu", "Five", "market", "Count five objects; the source includes alternate spellings."),
    word("six", "Aaru", "Six", "market", "Count six objects."),
    word("seven", "eizhu", "Seven", "market", "Ask a relative to record this word so you can hear its sounds."),
    word("eight", "Eattu", "Eight", "market", "Count eight objects."),
    word("nine", "Ombathu", "Nine", "market", "Count nine objects."),
    word("ten", "Hathu", "Ten", "market", "Count all ten fingers."),
    word("head", "Mande", "Head", "kitchen", "Point and name."),
    word("nose", "Mookku", "Nose", "kitchen", "Point and name."),
    word("horse", "Kudire", "Horse", "garden", "Picture-book vocabulary."),
    word("frog", "Kappe", "Frog", "garden", "Picture-book vocabulary."),
]
WORD_BY_ID = {w.id: w for w in WORDS}

LESSONS = [
    {"id": "hello", "title": "Hello, home", "place": "The village doorstep", "icon": "👋", "minutes": 3,
     "intro": "You have arrived for a visit. Learn a few words to begin a conversation.",
     "word_ids": ["how-are-you", "your-name", "my-name", "your-village", "badaga-answer"],
     "challenge": "Ask a relative how they introduce themselves. Listen for a word you recognise.",
     "badge": "Conversation starter", "x": 18, "y": 67},
    {"id": "family", "title": "Our family circle", "place": "A visit with relatives", "icon": "🤗", "minutes": 3,
     "intro": "Every family has stories. Start with the words for people close to you.",
     "word_ids": ["mother", "father", "sister", "grandmother", "grandfather"],
     "challenge": "Look at a family photo together. Name two people using your new relationship words.",
     "badge": "Family storyteller", "x": 38, "y": 51},
    {"id": "kitchen", "title": "Around the kitchen", "place": "Words from everyday life", "icon": "🥛", "minutes": 3,
     "intro": "Small moments at home are chances to use a new word. Try a point-and-name game.",
     "word_ids": ["milk", "hunger", "hands", "fingers", "teeth"],
     "challenge": "Ask a speaker to say Haalu and Hallu. Listen together to what makes them different.",
     "badge": "Everyday explorer", "x": 57, "y": 70},
    {"id": "garden", "title": "A little nature walk", "place": "The garden path", "icon": "🍃", "minutes": 3,
     "intro": "Imagine a walk with someone from home. Learn the names of animals and birds.",
     "word_ids": ["dog", "cat", "cow", "crow", "sparrow"],
     "challenge": "Ask a relative which birds they remember. Learn one more word from their story.",
     "badge": "Nature detective", "x": 74, "y": 43},
    {"id": "market", "title": "Count with me", "place": "A playful market stop", "icon": "🧺", "minutes": 3,
     "intro": "Collect a handful of small objects. You can count them together in Badaga.",
     "word_ids": ["one", "two", "three", "four", "five"],
     "challenge": "Count five things at home in Badaga. Let a family member join in.",
     "badge": "Little number keeper", "x": 85, "y": 72},
]
LESSON_BY_ID = {l["id"]: l for l in LESSONS}

GUIDANCE = {
    "start": {"title": "Start with one small conversation", "text": "Choose Hello, home. Learn one phrase, then try it with someone you know. Recognising a word counts as a beginning; you can take your time finding a reply.", "terms": ["how-are-you", "your-name", "your-village"]},
    "family": {"title": "Let family be part of the lesson", "text": "Open Our family circle, then look at a photograph with a relative. Ask what your own family calls each person. A grown-up can save a recording in Family corner.", "terms": ["mother", "father", "grandmother", "grandfather"]},
    "variants": {"title": "Your family's way of saying it belongs here", "text": "These spellings come from published community resources. If your family says something differently, listen and ask about it. Keep a family recording alongside the source form; a different form does not automatically mean a mistake.", "terms": ["four", "five", "how-are-you"]},
    "numbers": {"title": "Turn counting into a game", "text": "Put five small objects on a table. Count slowly with a family member. Mix them up and count again. Try the market stop when you are ready.", "terms": ["one", "two", "three", "four", "five"]},
    "listening": {"title": "Hear a familiar voice", "text": "A grown-up can record a short word or phrase in Family corner. You can play it during a lesson. Listen first, then try saying it together. The app does not grade anyone's accent.", "terms": ["milk", "teeth", "ear"]},
}

def public_word(w):
    return {**asdict(w), "source": next(s for s in SOURCES if s["id"] == w.source_id)}

def bootstrap():
    return {"lessons": LESSONS, "words": [public_word(w) for w in WORDS], "sources": SOURCES,
            "review_status": "Community speaker review pending", "version": 1}
