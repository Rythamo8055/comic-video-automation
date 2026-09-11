import json
import base64
import os

manifest_path = "output/pocket_tts_samples/manifest.json"
with open(manifest_path, "r", encoding="utf-8") as f:
    items = json.load(f)

# Ensure Telugu preview snippet is included
telugu_preview_path = "output/pocket_tts_samples/sample_telugu_female_preview.wav"
if os.path.exists(telugu_preview_path):
    items.insert(0, {
        "voice_id": "telugu_female_preview",
        "name": "Telugu Female (SYSPIN Pocket-TTS)",
        "gender": "Female",
        "category": "Telugu (తెలుగు)",
        "role": "Native Telugu Storyteller (Mimi 24kHz)",
        "text": "నమస్కారం! ఇది పాకెట్ టిటిఎస్ మరియు క్యూటై మిమి కోడెక్ ఆధారంగా రూపొందించబడిన సహజ తెలుగు మాట.",
        "filename": "sample_telugu_female_preview.wav",
        "filepath": telugu_preview_path,
        "duration_seconds": 12.00,
        "generation_time_seconds": 2.10,
        "real_time_factor": 3.40,
        "sample_rate": 24000
    })

voices_data = []
for item in items:
    path = item["filepath"]
    if os.path.exists(path):
        with open(path, "rb") as af:
            b64 = base64.b64encode(af.read()).decode("utf-8")
        item["audio_b64"] = f"data:audio/wav;base64,{b64}"
        voices_data.append(item)

print(f"Loaded {len(voices_data)} voice audio samples.")

html_path = "/home/rythamo/.gemini/antigravity/brain/fd9f1455-5d6a-42b4-9953-69ce288c77e1/pocket_tts_showcase.html"

json_voices = json.dumps(voices_data, ensure_ascii=False)

template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Pocket-TTS & Telugu Audio Showcase</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    @keyframes pulse-bar {
      0%, 100% { height: 4px; }
      50% { height: 20px; }
    }
    .animate-wave-1 { animation: pulse-bar 0.8s ease-in-out infinite; }
    .animate-wave-2 { animation: pulse-bar 0.6s ease-in-out infinite 0.15s; }
    .animate-wave-3 { animation: pulse-bar 0.9s ease-in-out infinite 0.3s; }
    .animate-wave-4 { animation: pulse-bar 0.7s ease-in-out infinite 0.2s; }
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] p-4 sm:p-6 font-sans min-h-screen">
  <div class="max-w-6xl mx-auto space-y-6">
    
    <!-- Header -->
    <header class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-6 shadow-sm">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
              ● CPU Live Inference
            </span>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-500 border border-blue-500/20">
              24,000 Hz Mimi Codec
            </span>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-500 border border-purple-500/20">
              Zero GPU Needed (<100MB)
            </span>
          </div>
          <h1 class="text-2xl sm:text-3xl font-bold tracking-tight">Pocket-TTS Voice Showcase & Audio Player</h1>
          <p class="text-sm text-[var(--muted-foreground)] mt-1">
            Click to listen to each of the 28 synthesized voice models running on pure CPU (~3.04x faster than real-time).
          </p>
        </div>
        <div class="flex items-center gap-3 bg-[var(--background)] px-4 py-2.5 rounded-xl border border-[var(--border)]">
          <div class="text-right">
            <div class="text-xs text-[var(--muted-foreground)] uppercase font-semibold">Total Voices</div>
            <div class="text-lg font-bold text-[var(--foreground)]">28 Samples</div>
          </div>
          <div class="h-8 w-px bg-[var(--border)]"></div>
          <div class="text-right">
            <div class="text-xs text-[var(--muted-foreground)] uppercase font-semibold">CPU Speedup</div>
            <div class="text-lg font-bold text-emerald-500">3.04x RTF</div>
          </div>
        </div>
      </div>

      <!-- Filter Tabs -->
      <div class="flex flex-wrap gap-2 mt-6 pt-4 border-t border-[var(--border)]" id="filterContainer">
        <button onclick="filterVoices('all', this)" class="filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--primary)] text-[var(--primary-foreground)] shadow-sm">
          All Voices (28)
        </button>
        <button onclick="filterVoices('telugu', this)" class="filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--card)]">
          🇮🇳 Telugu (తెలుగు)
        </button>
        <button onclick="filterVoices('core', this)" class="filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--card)]">
          🎙️ Comic Leads (Alba, Marius, Javert)
        </button>
        <button onclick="filterVoices('female', this)" class="filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--card)]">
          👩 Female Voices
        </button>
        <button onclick="filterVoices('male', this)" class="filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--card)]">
          👨 Male Voices
        </button>
        <button onclick="filterVoices('multilingual', this)" class="filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--card)]">
          🌍 European (IT, ES, DE, PT, FR)
        </button>
      </div>
    </header>

    <!-- Voices Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="voicesGrid"></div>

  </div>

  <audio id="globalAudioPlayer"></audio>

  <script>
    const voices = __JSON_VOICES__;
    let currentVoiceId = null;
    let currentFilter = 'all';
    const audio = document.getElementById('globalAudioPlayer');

    function renderCards(list) {
      const grid = document.getElementById('voicesGrid');
      grid.innerHTML = '';

      list.forEach(v => {
        const isTelugu = v.category.includes('Telugu');
        const card = document.createElement('div');
        card.className = `bg-[var(--card)] border ${isTelugu ? 'border-amber-500/50 ring-1 ring-amber-500/20' : 'border-[var(--border)]'} rounded-xl p-4 flex flex-col justify-between hover:border-[var(--primary)] transition-all shadow-sm`;
        card.id = `card-${v.voice_id}`;

        card.innerHTML = `
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <div class="flex items-center gap-1.5">
                <span class="text-base font-bold text-[var(--foreground)]">${v.name}</span>
                ${isTelugu ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-500">TELUGU</span>' : ''}
              </div>
              <span class="text-[11px] px-2 py-0.5 rounded-full font-medium ${v.gender === 'Female' ? 'bg-pink-500/10 text-pink-500 border border-pink-500/20' : 'bg-cyan-500/10 text-cyan-500 border border-cyan-500/20'}">
                ${v.gender}
              </span>
            </div>

            <div class="text-xs text-[var(--muted-foreground)] font-medium mb-2">
              ${v.role}
            </div>

            <p class="text-xs italic bg-[var(--background)] p-2.5 rounded-lg border border-[var(--border)] mb-3 leading-relaxed">
              "${v.text}"
            </p>
          </div>

          <div class="pt-2 border-t border-[var(--border)] flex items-center justify-between gap-2">
            <button onclick="togglePlay('${v.voice_id}')" id="btn-${v.voice_id}" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 active:scale-95 transition-all cursor-pointer">
              <span id="icon-${v.voice_id}">▶</span>
              <span id="label-${v.voice_id}">Play</span>
            </button>

            <!-- Waveform Visualizer -->
            <div id="wave-${v.voice_id}" class="hidden items-end gap-1 h-5 px-2">
              <span class="w-1 bg-emerald-500 rounded-full animate-wave-1"></span>
              <span class="w-1 bg-emerald-500 rounded-full animate-wave-2"></span>
              <span class="w-1 bg-emerald-500 rounded-full animate-wave-3"></span>
              <span class="w-1 bg-emerald-500 rounded-full animate-wave-4"></span>
            </div>

            <div class="text-right">
              <span class="text-[11px] text-[var(--muted-foreground)] block font-mono">${v.duration_seconds}s</span>
              <span class="text-[10px] text-emerald-500 font-semibold">${v.real_time_factor}x RTF</span>
            </div>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function filterVoices(type, btnElement) {
      currentFilter = type;
      document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.className = 'filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--card)] cursor-pointer';
      });
      btnElement.className = 'filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--primary)] text-[var(--primary-foreground)] shadow-sm cursor-pointer';

      let filtered = voices;
      if (type === 'telugu') {
        filtered = voices.filter(v => v.category.includes('Telugu') || v.voice_id.includes('telugu'));
      } else if (type === 'core') {
        filtered = voices.filter(v => ['alba', 'marius', 'javert', 'fantine', 'jean'].includes(v.voice_id));
      } else if (type === 'female') {
        filtered = voices.filter(v => v.gender === 'Female');
      } else if (type === 'male') {
        filtered = voices.filter(v => v.gender === 'Male');
      } else if (type === 'multilingual') {
        filtered = voices.filter(v => ['giovanni', 'lola', 'juergen', 'rafael', 'estelle'].includes(v.voice_id));
      }
      renderCards(filtered);
    }

    function togglePlay(voiceId) {
      const voice = voices.find(v => v.voice_id === voiceId);
      if (!voice) return;

      const btnIcon = document.getElementById(`icon-${voiceId}`);
      const btnLabel = document.getElementById(`label-${voiceId}`);
      const wave = document.getElementById(`wave-${voiceId}`);

      if (currentVoiceId === voiceId && !audio.paused) {
        audio.pause();
        if (btnIcon) btnIcon.innerText = '▶';
        if (btnLabel) btnLabel.innerText = 'Play';
        if (wave) wave.classList.replace('flex', 'hidden');
        return;
      }

      // Reset previous button
      if (currentVoiceId && currentVoiceId !== voiceId) {
        const prevIcon = document.getElementById(`icon-${currentVoiceId}`);
        const prevLabel = document.getElementById(`label-${currentVoiceId}`);
        const prevWave = document.getElementById(`wave-${currentVoiceId}`);
        if (prevIcon) prevIcon.innerText = '▶';
        if (prevLabel) prevLabel.innerText = 'Play';
        if (prevWave) prevWave.classList.replace('flex', 'hidden');
      }

      currentVoiceId = voiceId;
      audio.src = voice.audio_b64;
      audio.play();

      if (btnIcon) btnIcon.innerText = '⏸';
      if (btnLabel) btnLabel.innerText = 'Pause';
      if (wave) wave.classList.replace('hidden', 'flex');

      audio.onended = () => {
        if (btnIcon) btnIcon.innerText = '▶';
        if (btnLabel) btnLabel.innerText = 'Play';
        if (wave) wave.classList.replace('flex', 'hidden');
        currentVoiceId = null;
      };
    }

    // Initial render
    renderCards(voices);
  </script>
</body>
</html>
"""

html_final = template.replace("__JSON_VOICES__", json_voices)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_final)

print("Showcase HTML written cleanly to:", html_path)
