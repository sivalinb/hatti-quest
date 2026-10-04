/* The Python server teaches. This browser remembers, and keeps family voices. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const STORAGE_KEY = 'hatti-quest-progress-v1';
  let content, state, activeLesson, step = 0, phase = 'study', reviewWords = [];
  let dueWords = [], searchSequence = 0, voiceSequence = 0, toastTimer;
  let recorder, recordingStream, recordTimer, recordBusy = false;
  let audioPlayer, audioUrl, dbPromise, booted = false;
  const validDate = (value) => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
  function today() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }
  const freshState = () => ({version: 1, learned: [], completed: [], moments: [], recall: {}});
  function element(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function button(text, className, handler) {
    const b = element('button', className, text);
    b.type = 'button';
    b.addEventListener('click', () => run(handler));
    return b;
  }
  function notify(message) {
    $('toast').textContent = message;
    $('toast').hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {$('toast').hidden = true;}, 4500);
  }
  function showError(error) {
    console.error(error);
    $('app-error').textContent = 'Something did not load. Check the Python app is running, then try again.';
    $('app-error').hidden = false;
    notify('That did not finish. Please try again.');
  }
  async function run(fn) {try {await fn();} catch (error) {showError(error);}}
  async function api(path, body) {
    const response = await fetch(path, body === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    if (!response.ok) throw new Error(`Request failed (${response.status}): ${path}`);
    return response.json();
  }
  function validateProgress(input) {
    if (!input || input.version !== 1 || typeof input !== 'object') throw new Error('Unrecognised progress version');
    const wordIds = new Set(content.words.map(w => w.id));
    const lessonIds = new Set(content.lessons.map(l => l.id));
    const result = freshState();
    for (const [key, allowed] of [['learned', wordIds], ['completed', lessonIds], ['moments', lessonIds]]) {
      if (!Array.isArray(input[key]) || input[key].length > 100 || input[key].some(id => typeof id !== 'string' || !allowed.has(id))) throw new Error('Unrecognised learning content');
      result[key] = [...new Set(input[key])];
    }
    if (!input.recall || Array.isArray(input.recall) || typeof input.recall !== 'object' || Object.keys(input.recall).length > 100) throw new Error('Invalid review progress');
    for (const [id, r] of Object.entries(input.recall)) {
      if (!wordIds.has(id) || !r || !Number.isInteger(r.wins) || r.wins < 0 || r.wins > 50 || !Number.isInteger(r.misses) || r.misses < 0 || r.misses > 1000 || !validDate(r.due) || !validDate(r.last)) throw new Error('Invalid review record');
      result.recall[id] = {wins: r.wins, misses: r.misses, due: r.due, last: r.last};
    }
    return result;
  }
  function loadState() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? validateProgress(JSON.parse(saved)) : freshState();
    } catch {notify('Saved progress could not be read. You can still explore.'); return freshState();}
  }
  function saveState() {
    try {localStorage.setItem(STORAGE_KEY, JSON.stringify(state));}
    catch {notify('Browser storage is unavailable. Export progress before leaving.');}
  }
  function go(view, changeHash = true) {
    const allowed = ['adventure', 'basket', 'family', 'story'];
    if (!allowed.includes(view)) view = 'adventure';
    document.querySelectorAll('.view').forEach(el => {el.hidden = el.id !== `view-${view}`;});
    document.querySelectorAll('[data-view]').forEach(el => {
      const active = el.dataset.view === view;
      el.classList.toggle('active', active);
      if (active) el.setAttribute('aria-current', 'page'); else el.removeAttribute('aria-current');
    });
    if (changeHash) history.replaceState(null, '', `#${view}`);
    if (booted && view === 'basket') run(searchWords);
    if (booted && view === 'family') run(renderSavedVoices);
    window.scrollTo({top: 0, behavior: 'instant'});
  }
  function refreshAdventure() {
    const next = content.lessons.find(l => !state.completed.includes(l.id)) || content.lessons[0];
    $('quest-nodes').replaceChildren(...content.lessons.map(l => {
      const complete = state.completed.includes(l.id);
      const b = button('', `quest-node node-${l.id}${complete ? ' done' : ''}${next.id === l.id ? ' current' : ''}`, () => startLesson(l.id));
      b.setAttribute('aria-label', `${l.title}, ${complete ? 'completed, play again' : `${l.minutes} minute adventure`}`);
      const icon = element('span', 'node-icon', l.icon); icon.setAttribute('aria-hidden', 'true');
      if (complete) icon.append(element('span', 'node-check', '✓'));
      b.append(icon, element('span', 'node-label', l.title));
      return b;
    }));
    $('next-icon').textContent = next.icon;
    $('next-title').textContent = next.title;
    $('next-description').textContent = next.intro;
    $('start-quest').dataset.lesson = next.id;
    $('start-quest').textContent = state.completed.length === 5 ? 'Visit again →' : 'Let’s go →';
    $('trail-progress').textContent = `${state.completed.length} / 5 adventures`;
    $('header-count').textContent = $('learned-count').textContent = state.learned.length;
    $('family-count').textContent = state.moments.length;
    $('badge-count').textContent = state.completed.length;
    $('badges').replaceChildren(...content.lessons.filter(l => state.completed.includes(l.id)).map(l => {
      const badge = element('div', 'badge'); badge.append(element('span', '', l.icon), document.createTextNode(l.badge)); return badge;
    }));
    renderMissions();
  }
  async function refreshReviews() {
    const result = await api('/api/review', {today: today(), progress: state.recall});
    dueWords = result.words;
    $('start-review').disabled = dueWords.length === 0;
    $('review-description').textContent = dueWords.length ? `${dueWords.length} ${dueWords.length === 1 ? 'word is' : 'words are'} ready to say hello again.` : Object.keys(state.recall).length ? 'All refreshed for now. Your words will return another day.' : 'Your new words will return for a gentle practice.';
  }
  function sourceLink(w) {
    const a = element('a', 'source-link', 'See the community source ↗');
    a.href = w.source.url; a.target = '_blank'; a.rel = 'noopener noreferrer';
    return a;
  }
  function dialogTop(label, icon, position, total) {
    const top = element('div', 'quest-topline');
    const text = element('div');
    text.append(element('p', 'eyebrow', phase === 'study' ? 'MEET YOUR NEW WORDS' : 'A LITTLE WORD GAME'));
    const heading = element('h2', '', label); heading.id = 'quest-heading';
    text.append(heading); top.append(element('span', 'large-icon', icon), text);
    const progress = element('div', 'quest-progress');
    const bar = document.createElement('progress'); bar.max = total; bar.value = position;
    bar.setAttribute('aria-label', `${position} of ${total} words`);
    progress.append(bar, element('span', '', `${position} / ${total}`));
    return [top, progress];
  }
  async function startLesson(id) {
    activeLesson = await api(`/api/lessons/${encodeURIComponent(id)}`);
    step = 0; phase = 'study'; reviewWords = [];
    $('quest-dialog').showModal();
    await renderStudy();
  }
  async function renderStudy() {
    const w = activeLesson.words[step];
    const body = $('quest-body');
    body.replaceChildren(...dialogTop(activeLesson.title, activeLesson.icon, step + 1, activeLesson.words.length));
    body.append(element('div', 'learning-word', w.badaga), element('p', 'learning-gloss', w.english), element('p', 'learning-note', w.note), sourceLink(w));
    const listen = element('div', 'listen-box');
    listen.append(element('p', '', 'Listen together, then try saying it in your own voice.'));
    const voice = await getVoice(w.id).catch(() => null);
    if (phase !== 'study' || !body.isConnected || activeLesson.words[step].id !== w.id) return;
    if (voice) listen.append(button(`▶ Hear ${voice.speaker || 'a family voice'}`, 'text-button', () => playVoice(voice)));
    else listen.append(element('p', 'muted', 'A grown-up can add a familiar voice in Family corner.'), button('Add a family voice ↗', 'text-button', () => {closeQuest(); selectVoiceWord(w.id); go('family');}));
    body.append(listen);
    const controls = element('div', 'quest-footer');
    const back = button('← Back', 'text-button', async () => {step--; await renderStudy();}); back.disabled = step === 0;
    controls.append(back, button(step + 1 === activeLesson.words.length ? 'Let’s play →' : 'Next word →', 'button primary', async () => {
      if (step + 1 < activeLesson.words.length) {step++; await renderStudy();}
      else {step = 0; phase = 'quiz'; await renderQuiz();}
    }));
    body.append(controls);
  }
  async function renderQuiz() {
    const reviewing = phase === 'review';
    const total = reviewing ? reviewWords.length : activeLesson.challenges.length;
    const challenge = reviewing ? await api(`/api/words/${encodeURIComponent(reviewWords[step].id)}/challenge`) : activeLesson.challenges[step];
    const body = $('quest-body');
    body.replaceChildren(...dialogTop(reviewing ? 'A little refresh' : activeLesson.title, reviewing ? '🌱' : activeLesson.icon, step + 1, total));
    body.append(element('p', 'quiz-prompt', challenge.prompt));
    const choices = element('div', 'quiz-choices');
    for (const c of challenge.choices) {
      const b = button(c.label, 'quiz-choice', async () => {
        choices.querySelectorAll('button').forEach(el => {el.disabled = true;});
        let result;
        try {result = await api('/api/answer', {word_id: challenge.word_id, choice_id: c.id, today: today(), prior: state.recall[challenge.word_id] || null});}
        catch (error) {choices.querySelectorAll('button').forEach(el => {el.disabled = false;}); throw error;}
        state.recall[challenge.word_id] = result.review;
        if (result.correct && !state.learned.includes(challenge.word_id)) state.learned.push(challenge.word_id);
        saveState(); refreshAdventure();
        b.classList.add(result.correct ? 'correct' : 'incorrect');
        choices.querySelectorAll('button').forEach(el => {if (el.dataset.word === challenge.word_id) el.classList.add('correct');});
        const feedback = element('div', 'quiz-feedback'); feedback.setAttribute('role', 'status');
        feedback.append(element('strong', '', result.message), element('p', '', `${result.word.badaga} · ${result.word.english}`), sourceLink(result.word));
        body.append(feedback);
        const controls = element('div', 'quest-footer');
        controls.append(element('span', 'muted', 'Every try helps you learn.'), button(step + 1 < total ? 'Keep going →' : 'Finish →', 'button primary', async () => {
          step++;
          if (step < total) await renderQuiz(); else await finishQuest(reviewing);
        }));
        body.append(controls);
        controls.querySelector('button').focus();
      });
      b.dataset.word = c.id; choices.append(b);
    }
    body.append(choices);
  }
  async function finishQuest(reviewing) {
    if (!reviewing && !state.completed.includes(activeLesson.id)) state.completed.push(activeLesson.id);
    saveState(); refreshAdventure(); await refreshReviews();
    const body = $('quest-body');
    const box = element('div', 'quest-complete');
    const h = element('h2', '', reviewing ? 'A little closer, again.' : 'Look how far you’ve come!'); h.id = 'quest-heading';
    box.append(element('div', 'complete-icon', reviewing ? '🌱' : activeLesson.icon), h, element('p', '', reviewing ? 'Your words are tucked away for another day. Try one in a conversation.' : 'You visited five words. Now let them be part of a little moment at home.'));
    if (!reviewing) {
      box.append(element('div', 'complete-badge', `✦ ${activeLesson.badge}`));
      const task = element('div', 'family-task'); task.append(element('h3', '', 'Take the adventure into your day'), element('p', '', activeLesson.challenge));
      box.append(task);
    }
    const actions = element('div', 'quest-footer');
    actions.append(button('Family corner ↗', 'text-button', () => {closeQuest(); go('family');}), button('Back to the hills →', 'button primary', closeQuest));
    box.append(actions); body.replaceChildren(box);
  }
  function closeQuest() {$('quest-dialog').close(); stopPlayback();}
  async function startReview() {
    await refreshReviews(); if (!dueWords.length) return notify('All refreshed for today.');
    reviewWords = [...dueWords]; phase = 'review'; step = 0;
    $('quest-dialog').showModal(); await renderQuiz();
  }
  async function searchWords() {
    const sequence = ++searchSequence;
    const params = new URLSearchParams({q: $('word-search').value.trim(), category: $('word-category').value});
    const result = await api(`/api/search?${params}`);
    if (sequence !== searchSequence) return;
    $('search-summary').textContent = `${result.words.length} ${result.words.length === 1 ? 'word' : 'words'} to explore${$('word-search').value.trim() ? ' · matches in source words, translations and teaching notes' : ''}`;
    const cards = await Promise.all(result.words.map(wordCard));
    if (sequence !== searchSequence) return;
    $('word-results').replaceChildren(...(cards.length ? cards : [element('p', 'empty-results', 'No words found yet. Try a short word such as “mother”, “milk” or “Ondu”.')]));
  }
  async function wordCard(w) {
    const card = element('article', `word-card${state.learned.includes(w.id) ? ' recognised' : ''}`);
    card.dataset.wordId = w.id;
    const names = {hello: 'Conversations', family: 'Family', kitchen: 'Everyday life', garden: 'Nature', market: 'Numbers'};
    card.append(element('span', 'word-category', names[w.category]), element('h3', '', w.badaga), element('p', 'gloss', w.english), element('p', 'word-note', w.note), sourceLink(w));
    const voice = await getVoice(w.id).catch(() => null);
    card.append(voice ? button(`▶ Hear ${voice.speaker || 'a family voice'}`, 'text-button voice-button', () => playVoice(voice)) : button('＋ Add a familiar voice', 'text-button voice-button', () => {selectVoiceWord(w.id); go('family');}));
    return card;
  }
  function renderMissions() {
    const available = content.lessons.filter(l => state.completed.includes(l.id));
    $('family-missions').replaceChildren(...(available.length ? available.map(l => {
      const el = element('div', 'mission'); el.append(element('h3', '', `${l.icon} ${l.title}`), element('p', '', l.challenge));
      const done = state.moments.includes(l.id);
      const b = button(done ? '✓ A moment shared' : 'We tried this together ✓', 'text-button', () => {
        if (!state.moments.includes(l.id)) {state.moments.push(l.id); saveState(); refreshAdventure(); notify('A little moment worth keeping.');}
      }); b.disabled = done; el.append(b); return el;
    }) : [element('p', 'muted', 'Finish any adventure to discover a small activity you can try with family.')]));
  }
  async function getGuidance(topic) {
    document.querySelectorAll('[data-topic]').forEach(b => {b.disabled = true; b.classList.toggle('active', b.dataset.topic === topic);});
    $('guide-response').replaceChildren(element('p', '', 'Finding a little idea…'));
    try {
      const guide = await api('/api/guide', {topic});
      const chips = element('div', 'guide-words');
      guide.words.forEach(w => chips.append(element('span', '', `${w.badaga} · ${w.english}`)));
      const links = element('div');
      [...new Map(guide.words.map(w => [w.source.id, w])).values()].forEach(w => links.append(sourceLink(w), document.createTextNode(' ')));
      $('guide-response').replaceChildren(element('h3', '', guide.title), element('p', '', guide.text), chips, links, element('p', 'guide-mode', guide.mode === 'live-selection' ? 'AI selected existing source words. The tip is authored.' : guide.mode === 'source-guide-fallback' ? 'Source guide · the live selection was unavailable.' : 'Source guide · authored tips and published words.'));
    } finally {document.querySelectorAll('[data-topic]').forEach(b => {b.disabled = false;});}
  }
  function voiceDB() {
    if (!dbPromise) dbPromise = new Promise((resolve, reject) => {
      if (!window.indexedDB) return reject(new Error('Local audio storage is unavailable'));
      const request = indexedDB.open('hatti-quest-family-voices', 1);
      request.onupgradeneeded = () => request.result.createObjectStore('voices', {keyPath: 'wordId'});
      request.onsuccess = () => {request.result.onversionchange = () => request.result.close(); resolve(request.result);};
      request.onerror = () => {dbPromise = null; reject(request.error);};
      request.onblocked = () => {dbPromise = null; reject(new Error('Close another Hatti Quest tab to update voice storage'));};
    });
    return dbPromise;
  }
  async function voiceTransaction(mode, action) {
    const db = await voiceDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('voices', mode);
      const request = action(tx.objectStore('voices'));
      tx.oncomplete = () => resolve(request.result);
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error || new Error('Voice storage was interrupted'));
    });
  }
  const getVoice = (id) => voiceTransaction('readonly', store => store.get(id));
  const allVoices = () => voiceTransaction('readonly', store => store.getAll());
  function stopPlayback() {
    if (audioPlayer) {audioPlayer.pause(); audioPlayer = null;}
    if (audioUrl) {URL.revokeObjectURL(audioUrl); audioUrl = null;}
  }
  async function playVoice(voice) {
    stopPlayback(); audioUrl = URL.createObjectURL(voice.blob); audioPlayer = new Audio(audioUrl);
    audioPlayer.onended = stopPlayback;
    try {await audioPlayer.play();} catch {stopPlayback(); notify('This recording could not play. Try saving a different audio file.');}
  }
  function selectVoiceWord(id) {$('voice-word').value = id; renderRecordWord();}
  function renderRecordWord() {
    const w = content.words.find(word => word.id === $('voice-word').value);
    $('record-word').replaceChildren(document.createTextNode(w.badaga), element('small', '', w.english));
    $('record-preview').replaceChildren();
  }
  function setRecordingBusy(busy) {
    recordBusy = busy; $('voice-word').disabled = $('speaker-label').disabled = $('audio-upload').disabled = busy;
    $('record-voice').textContent = busy ? '■ Stop & save voice' : '● Record a family voice';
  }
  function releaseMicrophone() {
    clearTimeout(recordTimer);
    if (recordingStream) recordingStream.getTracks().forEach(track => track.stop());
    recordingStream = null;
  }
  async function saveVoice(id, blob, speaker) {
    if (!blob.size || blob.size > 2_000_000 || !blob.type.startsWith('audio/')) throw new Error('Use an audio file smaller than 2 MB.');
    const voice = {wordId: id, blob, speaker: speaker.trim().slice(0, 40), saved: new Date().toISOString()};
    await voiceTransaction('readwrite', store => store.put(voice));
    $('record-status').textContent = 'Saved on this device. You can hear this voice in adventures and your word basket.';
    $('record-preview').replaceChildren(button('▶ Hear the saved voice', 'text-button', () => playVoice(voice)));
    await renderSavedVoices(); notify('A familiar voice, saved here.');
  }
  async function toggleRecording() {
    if (recorder && recorder.state === 'recording') {recorder.stop(); return;}
    if (recordBusy) return;
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      $('record-status').textContent = 'Recording needs a supported browser on localhost or HTTPS. You can choose an audio file instead.'; return;
    }
    const id = $('voice-word').value, speaker = $('speaker-label').value;
    setRecordingBusy(true); $('record-voice').disabled = true;
    $('record-status').textContent = 'Allow microphone access to record a short family voice.';
    try {
      recordingStream = await navigator.mediaDevices.getUserMedia({audio: true, video: false});
      const mime = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus'].find(type => MediaRecorder.isTypeSupported(type));
      recorder = mime ? new MediaRecorder(recordingStream, {mimeType: mime}) : new MediaRecorder(recordingStream);
      const currentRecorder = recorder;
      const chunks = [];
      recorder.ondataavailable = event => {if (event.data.size) chunks.push(event.data);};
      recorder.onstop = async () => {
        releaseMicrophone(); $('record-voice').disabled = true;
        try {await saveVoice(id, new Blob(chunks, {type: currentRecorder.mimeType || 'audio/webm'}), speaker);}
        catch (error) {$('record-status').textContent = `Voice could not be saved. ${error.message}`;}
        finally {recorder = null; setRecordingBusy(false); $('record-voice').disabled = false;}
      };
      recorder.onerror = () => {releaseMicrophone(); setRecordingBusy(false); $('record-status').textContent = 'Recording was interrupted. Please try again.';};
      recorder.start(); $('record-status').textContent = 'Recording… say the word slowly. Stops automatically after 20 seconds.';
      recordTimer = setTimeout(() => {if (recorder?.state === 'recording') recorder.stop();}, 20_000);
    } catch (error) {
      releaseMicrophone(); setRecordingBusy(false);
      $('record-status').textContent = error.name === 'NotAllowedError' ? 'Microphone access was not allowed. You can choose a family audio file instead.' : 'Microphone unavailable. You can choose an audio file instead.';
    } finally {$('record-voice').disabled = false;}
  }
  async function renderSavedVoices() {
    const sequence = ++voiceSequence;
    let voices;
    try {voices = await allVoices();}
    catch {$('saved-voices').replaceChildren(element('p', 'muted', 'Local audio storage is unavailable in this browser. Try a regular browser window.')); return;}
    if (sequence !== voiceSequence) return;
    voices = voices.filter(v => content.words.some(w => w.id === v.wordId));
    $('voice-count').textContent = voices.length;
    $('saved-voices').replaceChildren(...(voices.length ? voices.map(v => {
      const w = content.words.find(w => w.id === v.wordId);
      const el = element('div', 'saved-voice'); el.dataset.wordId = v.wordId;
      el.append(element('h3', '', `${w.badaga} · ${w.english}`), element('p', '', `${v.speaker || 'Family voice'} · on this device`));
      const actions = element('div', 'voice-actions');
      actions.append(button('▶ Play', 'text-button', () => playVoice(v)), button('Download', 'text-button', () => download(v.blob, `${v.wordId}-family-voice.${v.blob.type.includes('mp4') ? 'm4a' : v.blob.type.includes('wav') ? 'wav' : v.blob.type.includes('mpeg') ? 'mp3' : v.blob.type.includes('ogg') ? 'ogg' : 'webm'}`)), button('Remove', 'text-button danger', async () => {
        if (!confirm(`Remove the saved family voice for “${w.badaga}” from this device?`)) return;
        stopPlayback(); await voiceTransaction('readwrite', store => store.delete(v.wordId)); await renderSavedVoices(); notify('Voice removed from this device.');
      }));
      el.append(actions); return el;
    }) : [element('p', 'muted', 'Your first family voice will appear here.')]));
  }
  function download(blob, filename) {
    const url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = filename; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  }
  async function makeStory() {
    const trigger = $('create-story');
    trigger.disabled = true;
    $('studio-status').textContent = 'Packing a few words from home…';
    try {
      const focus = $('story-focus').value;
      const story = await api('/api/ai/story', {focus, theme: $('story-theme').value,
        review_word_ids: dueWords.filter(w => w.category === focus).slice(0, 3).map(w => w.id)});
      const target = $('studio-story');
      target.replaceChildren(element('h3', 'story-title', `${story.icon} ${story.title}`));
      const scenes = element('div', 'story-scenes');
      for (const [index, scene] of story.scenes.entries()) {
        const card = element('article', 'story-scene');
        card.append(element('span', 'story-step', `CHAPTER ${index + 1}`), element('p', 'story-prose', scene.text));
        const word = element('div', 'story-word');
        word.append(element('strong', '', scene.word.badaga), element('span', '', scene.word.english));
        card.append(word, sourceLink(scene.word));
        const voice = await getVoice(scene.word.id).catch(() => null);
        if (voice) card.append(button('▶ A familiar voice', 'text-button', () => playVoice(voice)));
        const challenge = element('details', 'story-challenge');
        challenge.append(element('summary', '', 'Try a little word game'));
        challenge.append(element('p', '', scene.challenge.prompt));
        const choices = element('div', 'story-choices');
        for (const choice of scene.challenge.choices) {
          choices.append(button(choice.label, 'quiz-choice', async () => {
            choices.querySelectorAll('button').forEach(b => {b.disabled = true;});
            try {
              const result = await api('/api/answer', {word_id: scene.word.id, choice_id: choice.id,
                today: today(), prior: state.recall[scene.word.id] || null});
              state.recall[scene.word.id] = result.review;
              if (result.correct && !state.learned.includes(scene.word.id)) state.learned.push(scene.word.id);
              saveState(); refreshAdventure(); await refreshReviews();
              challenge.append(element('p', 'quiz-feedback', `${result.message} ${result.word.badaga} · ${result.word.english}`));
            } catch (error) {choices.querySelectorAll('button').forEach(b => {b.disabled = false;}); throw error;}
          }));
        }
        challenge.append(choices); card.append(challenge); scenes.append(card);
      }
      target.append(scenes);
      const activity = element('div', 'story-activity');
      activity.append(element('strong', '', 'Take the story off the screen'), element('p', '', story.family_activity));
      target.append(activity);
      const live = ['live', 'cached-live'].includes(story.mode);
      $('studio-status').textContent = `${live ? '✦ AI story' : '✧ Authored story'} · source-linked words · ${story.evidence.cached ? 'saved adventure' : 'a fresh little adventure'}`;
      const evidence = element('details', 'story-evidence');
      evidence.append(element('summary', '', 'For grown-ups: see the sources behind this story'));
      evidence.append(element('p', '', `Word cards: ${story.review_status}. ${live ? 'English fiction generated with AI.' : 'English fiction from the authored fallback.'} Retrieval: ${story.evidence.retrieval_mode}. Family recordings stay on this device.`));
      const links = element('div', 'resource-links');
      for (const scene of story.scenes) links.append(sourceLink(scene.word));
      evidence.append(links); target.append(evidence);
      target.scrollIntoView({behavior: 'smooth', block: 'start'});
    } catch (error) {
      $('studio-status').textContent = error.message.includes('429') ? 'The studio is taking a little pause. Try again in a minute.' : 'That adventure could not load. Please try again.';
    } finally {trigger.disabled = false;}
  }
  async function bootstrap() {
    content = await api('/api/content'); state = loadState();
    $('voice-word').replaceChildren(...content.words.map(w => {const option = element('option', '', `${w.badaga} — ${w.english}`); option.value = w.id; return option;}));
    renderRecordWord(); refreshAdventure(); booted = true;
    await refreshReviews(); go(location.hash.slice(1), false);
  }
  document.querySelectorAll('[data-view],[data-go]').forEach(b => b.addEventListener('click', () => go(b.dataset.view || b.dataset.go)));
  $('start-quest').addEventListener('click', () => {if (booted) run(() => startLesson($('start-quest').dataset.lesson));});
  $('create-story').addEventListener('click', () => {if (booted) run(makeStory);});
  $('start-review').addEventListener('click', () => run(startReview));
  $('close-quest').addEventListener('click', closeQuest);
  $('quest-dialog').addEventListener('close', stopPlayback);
  $('map-help').addEventListener('click', () => {go('family'); run(() => getGuidance('start'));});
  let searchTimer;
  $('word-search').addEventListener('input', () => {clearTimeout(searchTimer); searchTimer = setTimeout(() => run(searchWords), 200);});
  $('word-category').addEventListener('change', () => run(searchWords));
  $('voice-word').addEventListener('change', renderRecordWord);
  $('record-voice').addEventListener('click', () => run(toggleRecording));
  $('refresh-voices').addEventListener('click', () => run(renderSavedVoices));
  document.querySelectorAll('[data-topic]').forEach(b => b.addEventListener('click', () => run(() => getGuidance(b.dataset.topic))));
  $('audio-upload').addEventListener('change', async event => {
    const file = event.target.files[0]; if (!file) return;
    try {await saveVoice($('voice-word').value, file, $('speaker-label').value);}
    catch (error) {$('record-status').textContent = `Voice could not be saved. ${error.message}`;}
    event.target.value = '';
  });
  $('export-progress').addEventListener('click', () => {
    download(new Blob([JSON.stringify(state, null, 2)], {type: 'application/json'}), `hatti-quest-progress-${today()}.json`);
    $('backup-status').textContent = 'Progress exported. Family recordings are separate; use Download beside a saved voice to keep one.';
  });
  $('import-progress').addEventListener('change', async event => {
    const file = event.target.files[0]; if (!file) return;
    try {
      if (file.size > 50_000) throw new Error('Progress files must be smaller than 50 KB.');
      const imported = validateProgress(JSON.parse(await file.text()));
      if (!confirm('Replace learning progress in this browser with this file? Family voices will stay here.')) return;
      state = imported; saveState(); refreshAdventure(); await refreshReviews();
      $('backup-status').textContent = 'Progress imported. You can continue your adventures.';
    } catch (error) {$('backup-status').textContent = `No progress changed. ${error.message}`;}
    finally {event.target.value = '';}
  });
  $('reset-progress').addEventListener('click', () => {
    if (!confirm('Reset learning progress in this browser? Export first if you want to keep it. Family voices will stay here.')) return;
    state = freshState(); saveState(); refreshAdventure(); run(refreshReviews); $('backup-status').textContent = 'Learning progress reset. Saved family voices are still here.';
  });
  window.addEventListener('hashchange', () => go(location.hash.slice(1), false));
  window.addEventListener('storage', event => {if (event.key === STORAGE_KEY && booted) {state = loadState(); refreshAdventure(); run(refreshReviews);}});
  window.addEventListener('pageshow', event => {if (event.persisted && booted) run(refreshReviews);});
  document.addEventListener('visibilitychange', () => {if (!document.hidden && booted) run(refreshReviews);});
  window.addEventListener('beforeunload', () => {releaseMicrophone(); stopPlayback();});
  run(bootstrap);
})();
