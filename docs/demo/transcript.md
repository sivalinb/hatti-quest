# Hatti Quest — Siva Babu’s story

Five-minute demo with a third-person synthetic English presenter. The voice does not impersonate Siva Babu.

Spoken pronunciation cues: Badaga → “baduuugaa”; Nilgiris → “neel-giri-s”. Standard spellings are retained below.

## 00:00 — A little closer to home

In southern India, the Nilgiri Hills are known as the Blue Mountains. They are home to communities including the Toda, Kota, Kurumba, Irula, Paniya and Kattunayaka, each with its own language and traditions. Badaga life is also rooted in these hills, with distinctive food, close-knit villages, and a connection to farming and nature. Here, a language carries the sounds of home.

## 00:23 — Badaga: a language, a community, a connection

Badaga is a Dravidian language. India's twenty eleven Census recorded one hundred thirty-three thousand five hundred fifty Badaga mother-tongue speakers. This is a dated count in India, not a current worldwide estimate. Siva Babu is Badaga. He moved abroad for growth and opportunity, while staying deeply connected to his roots. He wants children growing up far from the hills to know the language and culture that connect them to home.

## 00:46 — An oral tradition deserves a living future

Badaga has a strong oral tradition, without a single broadly standardised native writing system. People use Roman, Tamil and Kannada writing, and dedicated scripts have been proposed. Spellings and family usage can differ. A written word cannot carry every sound or memory. Keeping the language present means making room for fluent speakers, familiar voices, and everyday conversations. That is the challenge Siva wants to help address.

## 01:12 — What happens when home is far away?

Families leave the hills for education, work, and new opportunities. For children overseas, daily life may happen mostly in English or another local language. There may be few people nearby who speak Badaga. A child can love their grandparents and still struggle to understand their stories. Siva wants to bridge that gap. Hatti Quest is his attempt to bring the language into small, playful moments that families can share.

## 01:38 — A playful beginning

The adventure begins on an illustrated trail inspired by the hills. Every stop is open, and a lesson takes about three minutes. Children meet everyday words about family, conversation, nature, counting, and life at home. They play gentle recognition games, collect badges, and revisit words through spaced practice. There are fifty source-documented words and phrases in this starter. The aim is a confident little beginning that can continue after the screen is put away.

## 02:05 — Home has a voice

Family corner lets a grown-up record a word in a familiar voice. A parent or grandparent can say it slowly, then the child can hear that recording during a lesson. These short recordings stay in the browser on this device. They are never uploaded to the AI services. There is no automatic accent score. Families can keep their own way of saying a word alongside the published source form, and download a recording as a keepsake.

## 02:28 — Your imagination. Our words.

Story Studio brings the AI into the experience. A child chooses a moon mission, an animal adventure, a magical sketchbook, or a little mystery. They choose a word topic too. The system retrieves relevant vocabulary and creates three short English scenes around those word references. Python supplies the Badaga forms and the word games from the documented collection. A small family activity carries the story back into everyday life. An authored adventure remains available if live AI cannot finish.

## 02:56 — Follow the words. Inspect the AI.

The builder's dashboard makes the system visible. Nebius runs the embedding and story models. Pinecone searches a dedicated vocabulary namespace, and Python combines those results with lexical search using reciprocal rank fusion. The model returns structured English fiction, then Python validates the referenced word identifiers. The run ledger shows the sources, retrieval ranks, latency, and provider-reported tokens. A cached adventure reports zero new tokens. Braintrust traces follow each stage, so a builder can inspect what happened.

## 03:27 — Measure the engineering. Invite the community.

The project measured retrieval on twenty-four curated English queries. Hybrid search found the expected words within its top five results in every case. The original lexical search achieved fifty-four percent recall. Eight generated adventures used valid source word references, and all six grounding checks passed. These are small engineering checks, not proof of language accuracy or learning effectiveness. Community speaker review is still pending. Fluent speakers and families can validate pronunciation, preferred usage, and the learning experience.

## 03:57 — A running system, with evidence

Prometheus scrapes the running Python application, and Grafana displays the live metrics: service health, reported tokens, request modes, stage latency, and evaluation scores. Braintrust holds the traces and the experiment record. Failures, fallbacks, and cache behaviour are inspectable. Siva used Codex to build this working Python prototype, its tests, and the demo. The public GitHub repository includes the application, evaluation dataset, and monitoring configuration, so other builders can reproduce and improve the work.

## 04:29 — One language at a time. One community at the centre.

The next step is community review: more family voices, corrected word forms, and activities shaped by the people who use the language. The approach could support other languages with small digital collections or strong oral traditions. Each needs its own sources, permissions, writing choices, speaker review, and evaluation cases. For Siva, preserving Badaga means creating opportunities to speak it. His hope is that the voices of elders become part of children's everyday lives and their future, wherever they grow up.
