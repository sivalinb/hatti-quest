# Hatti Quest — five-minute demo

Synthetic English narration; conceptual illustrations and actual local application recording.

## 00:00 — A little closer to home

In southern India, the Nilgiri Hills are often called the Blue Mountains. Their landscapes are home to many communities, including the Toda, Kota, Kurumba, Irula, Paniya and Kattunayaka. Each carries its own living language and traditions. This is the setting for Hatti Quest, a small attempt to keep a connection alive.

## 00:21 — Badaga: a language, a community, a connection

I'm Siva Babu, and I'm Badaga. Our community is rooted in the Nilgiri Hills of Tamil Nadu. Badaga is a Dravidian language. India's twenty eleven Census recorded one hundred and thirty-three thousand, five hundred and fifty Badaga mother-tongue speakers. That is a dated census count, not a current worldwide estimate. Behind the number are family conversations, memories, and a sense of belonging.

## 00:46 — An oral tradition deserves a living future

Badaga has a strong oral tradition, without a single broadly standardised native writing system. That does not mean it cannot be written. People use Roman, Tamil and Kannada writing, and dedicated scripts have been proposed. Spellings and family usage can differ. A written word alone cannot carry every sound, relationship or memory. Preserving the language also means making room for fluent speakers and familiar voices.

## 01:11 — What happens when home is far away?

For children growing up outside India, everyday life may happen mostly in English or another local language. There may be fewer neighbours, classmates, and relatives who speak Badaga. A child can love their roots and still struggle to reply to a grandparent. Time zones and busy routines make regular practice harder. Hatti Quest turns that distance into small, playful opportunities to connect with family.

## 01:34 — A playful beginning

The adventure begins on an illustrated trail inspired by the hills. Every stop is open, and a lesson takes about three minutes. Children meet everyday words about family, conversation, nature, counting, and life at home. They play gentle recognition games, collect badges, and revisit words through spaced practice. There are fifty source-documented words and phrases in this starter. The aim is a confident little beginning that can continue after the screen is put away.

## 02:02 — Home has a voice

Family corner lets a grown-up record a word in a familiar voice. A parent or grandparent can say it slowly, then the child can hear that recording during a lesson. These short recordings stay in the browser on this device. They are never uploaded to the AI services. There is no automatic accent score. Families can keep their own way of saying a word alongside the published source form, and download a recording as a keepsake.

## 02:26 — Your imagination. Our words.

Story Studio brings the AI into the experience. A child chooses a moon mission, an animal adventure, a magical sketchbook, or a little mystery. They choose a word topic too. The system retrieves relevant vocabulary and creates three short English scenes around those word references. Python supplies the Badaga forms and the word games from the documented collection. A small family activity carries the story back into everyday life. An authored adventure remains available if live AI cannot finish.

## 02:55 — Follow the words. Inspect the AI.

The builder's dashboard makes the system visible. Nebius runs the embedding and story models. Pinecone searches a dedicated vocabulary namespace, and Python combines those results with lexical search using reciprocal rank fusion. The model returns structured English fiction, then Python validates the referenced word identifiers. The run ledger shows the sources, retrieval ranks, latency, and provider-reported tokens. A cached adventure reports zero new tokens. Braintrust traces follow each stage, so a builder can inspect what happened.

## 03:27 — Measure the engineering. Invite the community.

We measured retrieval on twenty-four curated English queries. Hybrid search found the expected words within its top five results in every case. The original lexical search achieved fifty-four percent recall. Eight generated adventures used valid source word references, and all six grounding checks passed. These are small engineering checks, not proof of language accuracy or learning effectiveness. Community speaker review is still pending. Fluent speakers and families are the people who can validate pronunciation, preferred usage, and the learning experience.

## 03:58 — A running system, with evidence

Prometheus scrapes the running Python application, and Grafana displays the live metrics. We can see service health, reported tokens, request modes, stage latency, and the latest evaluation scores. Braintrust holds the traces and the experiment record. This makes failures, fallbacks, and cache behaviour inspectable. The public GitHub repository includes the Python application, tests, evaluation dataset, and monitoring configuration, so another builder can reproduce and improve the work.

## 04:28 — One language at a time. One community at the centre.

The next step is community review: more family voices, corrected word forms, and learning activities shaped by the people who use the language. The same approach could support other languages with small digital collections or strong oral traditions. Each would need its own source material, permission, speaker review, and evaluation cases. It would also need its own choices about writing and pronunciation. Hatti Quest is my attempt to make technology useful to belonging, one little word and one family conversation at a time.
