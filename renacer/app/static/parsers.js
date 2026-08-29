/**
 * Beatstar Community Rhythm Parsers, Remapper & IndexedDB Storage
 * Supports: osu! Mania (.osu / .osz), Quaver (.qua / .qp), Clone Hero (.chart / .zip)
 * Fixed 3-Lane deterministic remapping with strict 2-finger limit & anti-crowding.
 */

// ==========================================
// 1. DETERMINISTIC 3-LANE REMAPPER & STRICT 2-FINGER COLLISION RESOLVER
// ==========================================

class LaneRemapper {
  /**
   * Remapea un carril de origen (4K, 5K, 6K, 7K) a 3 carriles fijos (0, 1, 2)
   */
  static mapTo3K(originalLane, totalLanes = 4) {
    if (totalLanes <= 3) {
      return Math.min(2, Math.max(0, originalLane));
    }
    if (totalLanes === 4) {
      if (originalLane === 0) return 0; // Izquierda
      if (originalLane === 1 || originalLane === 2) return 1; // Centro
      return 2; // Derecha
    }
    if (totalLanes === 5) {
      if (originalLane === 0) return 0;
      if (originalLane === 1 || originalLane === 2 || originalLane === 3) return 1;
      return 2;
    }
    if (totalLanes === 6) {
      if (originalLane <= 1) return 0;
      if (originalLane <= 3) return 1;
      return 2;
    }
    // 7K y superiores
    const ratio = (originalLane + 0.5) / totalLanes;
    if (ratio <= 0.334) return 0;
    if (ratio <= 0.667) return 1;
    return 2;
  }

  /**
   * Downsampler Rítmico Inteligente para Mapas de 4 a 8+ Carriles (osu! 7K, Quaver 7K, Clone Hero 5F)
   * Filtra las micro-subdivisiones innecesarias (notas 24th/32nd) y acordes masivos de teclado
   * para conservar una rítmica musical limpia y jugable con 2 pulgares.
   */
  static thinMultiLaneChart(rawNotes, totalLanes = 4, bpm = 120, stars = 3.0) {
    if (!rawNotes || rawNotes.length === 0) return [];

    const beatDurationMs = 60000 / (bpm || 120);
    const s = Math.max(1.0, Math.min(10.0, parseFloat(stars) || 3.0));

    // Límite ergonómico de distancia temporal mínima entre eventos de golpeo (ms):
    // 1-3★: ~140ms
    // 4-6★: ~110ms
    // 7-10★: ~85ms
    let minEventGap = 140 - (s - 1.0) * 6.5; // 1★: 140ms, 10★: 81.5ms
    if (totalLanes >= 6) {
      minEventGap = Math.max(minEventGap, 90);
    }

    const sorted = [...rawNotes].sort((a, b) => a.timestamp_ms - b.timestamp_ms);
    const thinned = [];
    let lastEventTimestamp = -Infinity;

    for (let i = 0; i < sorted.length; i++) {
      const n = sorted[i];
      const t = n.timestamp_ms;

      // 1. Manejo de acordes simultáneos (|t - lastEvent| <= 40ms)
      if (Math.abs(t - lastEventTimestamp) <= 40) {
        const sameEventNotes = thinned.filter(prev => Math.abs(prev.timestamp_ms - t) <= 40);
        // Permitir como máximo 2 notas en el acorde si están en carriles distintos
        if (sameEventNotes.length < 2) {
          thinned.push(n);
        }
        continue;
      }

      // 2. Comprobación de distancia rítmica mínima
      const gap = t - lastEventTimestamp;
      if (gap < minEventGap) {
        const isHold = n.type === 'hold';
        const beatOffset = ((t % beatDurationMs) + beatDurationMs) % beatDurationMs;
        const isOnBeat = beatOffset < 40 || beatOffset > (beatDurationMs - 40);
        const halfBeat = beatDurationMs / 2;
        const halfOffset = ((t % halfBeat) + halfBeat) % halfBeat;
        const isOnHalfBeat = halfOffset < 35 || halfOffset > (halfBeat - 35);

        // Si no es nota sostenida ni cae en un golpe de compás claro, podar micro-relleno de teclado
        if (!isHold && !isOnBeat && (!isOnHalfBeat || gap < minEventGap * 0.75)) {
          continue;
        }
      }

      lastEventTimestamp = t;
      thinned.push(n);
    }

    return thinned;
  }

  /**
   * Sanitizador Universal para 2 Dedos (2 Pulgares en Móvil)
   * Garantiza al 100% que NUNCA aparezcan 3 notas simultáneas ni en el mismo instante
   * ni dentro de una ventana de juicio de 75ms a lo largo de los 3 carriles.
   */
  static sanitizeForTwoFingers(notes, bpm = 120, stars = 3.0) {
    if (!notes || notes.length === 0) return [];

    // Paso 0: Poda de densidad en mapas masivos
    const preThinned = this.thinMultiLaneChart(notes, 3, bpm, stars);

    // Ordenar cronológicamente
    const sorted = [...preThinned].sort((a, b) => a.timestamp_ms - b.timestamp_ms);

    // 1. Agrupar en acordes instantáneos (|t_a - t_b| <= 45ms)
    const chordGroups = [];
    let currentGroup = [sorted[0]];

    for (let i = 1; i < sorted.length; i++) {
      const curr = sorted[i];
      const anchor = currentGroup[0];

      if (Math.abs(curr.timestamp_ms - anchor.timestamp_ms) <= 45) {
        currentGroup.push(curr);
      } else {
        chordGroups.push(currentGroup);
        currentGroup = [curr];
      }
    }
    if (currentGroup.length > 0) chordGroups.push(currentGroup);

    // 2. En cada acorde: MÁXIMO 2 notas, cada una en un carril distinto
    const pass1Notes = [];
    for (const group of chordGroups) {
      const usedLanes = new Set();
      const kept = [];

      for (const n of group) {
        if (kept.length >= 2) break; // Límite estricto de 2 dedos

        let targetLane = Math.max(0, Math.min(2, n.lane ?? 1));
        if (usedLanes.has(targetLane)) {
          const candidates = targetLane === 1 ? [0, 2] : (targetLane === 0 ? [1, 2] : [1, 0]);
          const free = candidates.find(l => !usedLanes.has(l));
          if (free !== undefined) {
            targetLane = free;
          } else {
            continue;
          }
        }

        usedLanes.add(targetLane);
        n.lane = targetLane;
        kept.push(n);
      }
      pass1Notes.push(...kept);
    }

    // 3. Ventana deslizante de 80ms: Máximo 2 carriles activos concurrentes & Límite de Densidad
    const pass2Notes = [];
    const laneLastHitTime = [-Infinity, -Infinity, -Infinity];

    for (let i = 0; i < pass1Notes.length; i++) {
      const n = pass1Notes[i];
      const t = n.timestamp_ms;

      // A. Anti-Jackhammer: mínimo 80ms entre golpes sucesivos en el MISMO carril
      const lastSameLaneTime = laneLastHitTime[n.lane];
      if (t - lastSameLaneTime < 80 && n.type === 'tap') {
        // Intentar alternar a un carril libre adyacente
        const candidates = n.lane === 1 ? [0, 2] : (n.lane === 0 ? [1, 2] : [1, 0]);
        let alternated = false;
        for (const alt of candidates) {
          if (t - laneLastHitTime[alt] >= 80) {
            const recentAroundT = pass2Notes.filter(prev => Math.abs(prev.timestamp_ms - t) <= 75);
            const usedLanesAroundT = new Set(recentAroundT.map(r => r.lane));
            if (!usedLanesAroundT.has(alt) && usedLanesAroundT.size < 2) {
              n.lane = alt;
              alternated = true;
              break;
            }
          }
        }
        if (!alternated) {
          // Descartar nota redundante de micro-trino imposible para un solo pulgar
          continue;
        }
      }

      // B. Ventana de 3 carriles: en cualquier ventana de 75ms, máximo 2 carriles activos
      const recent = pass2Notes.filter(prev => Math.abs(prev.timestamp_ms - t) <= 75);
      const recentLanes = new Set(recent.map(r => r.lane));

      if (!recentLanes.has(n.lane) && recentLanes.size >= 2) {
        // Un tercer carril dentro de 75ms requeriría 3 dedos: descartar
        continue;
      }

      // C. Límite de densidad por ráfaga: máximo 2 notas por intervalo de 90ms
      const in90ms = pass2Notes.filter(prev => Math.abs(prev.timestamp_ms - t) <= 90);
      if (in90ms.length >= 2 && !recentLanes.has(n.lane)) {
        continue;
      }

      laneLastHitTime[n.lane] = t;
      pass2Notes.push(n);
    }

    // 4. Protección de Notas Sostenidas (Holds)
    const holdIntervals = [];
    for (const n of pass2Notes) {
      if (n.type === 'hold' && (n.end_timestamp_ms || n.duration_ms)) {
        const endT = n.end_timestamp_ms || (n.timestamp_ms + n.duration_ms);
        holdIntervals.push({
          start: n.timestamp_ms,
          end: endT,
          lane: n.lane
        });
      }
    }

    const finalNotes = [];
    for (let i = 0; i < pass2Notes.length; i++) {
      const n = pass2Notes[i];
      const t = n.timestamp_ms;

      const activeHolds = holdIntervals.filter(h => t > h.start + 45 && t < h.end - 45);
      const activeHoldsCount = activeHolds.length;

      if (activeHoldsCount >= 2) {
        // 2 dedos ocupados sosteniendo
        continue;
      }

      if (activeHolds.some(h => h.lane === n.lane)) {
        // No se puede pulsar una nota en un carril que se está sosteniendo
        continue;
      }

      if (activeHoldsCount === 1) {
        const concurrent = finalNotes.filter(prev => Math.abs(prev.timestamp_ms - t) <= 45);
        if (concurrent.length >= 1) {
          continue; // Sólo 1 tap libre mientras 1 dedo sostiene
        }
      }

      finalNotes.push(n);
    }

    // 5. Asignar IDs limpios y swipes ocasionales en golpes de acento
    finalNotes.forEach((n, idx) => {
      n.id = idx + 1;
      if (n.type === 'tap' && idx % 18 === 17) {
        n.type = 'swipe';
        if (n.lane === 0) n.direction = 'left';
        else if (n.lane === 2) n.direction = 'right';
        else n.direction = (idx % 2 === 0) ? 'up' : 'down';
      }
    });

    return finalNotes;
  }

  /**
   * Resuelve colisiones iniciales y sanitiza para 2 dedos
   */
  static resolveCollisions(rawNotes, totalLanes = 4, bpm = 120, stars = 3.0) {
    if (!rawNotes || rawNotes.length === 0) return [];

    // Paso 1: Poda de canales múltiples en 4K/6K/7K
    const thinned = this.thinMultiLaneChart(rawNotes, totalLanes, bpm, stars);

    // Paso 2: Mapear carriles a 3K
    const mapped = thinned.map(n => ({
      ...n,
      lane: this.mapTo3K(n.originalLane ?? n.lane, totalLanes)
    }));

    // Paso 3: Sanitización universal a 2 dedos
    return this.sanitizeForTwoFingers(mapped, bpm, stars);
  }
}

// ==========================================
// 2. PARSER: OSU! MANIA (.osu)
// ==========================================

class OsuManiaParser {
  static parse(osuText) {
    const lines = osuText.split(/\r?\n/);
    let currentSection = '';
    
    let audioFilename = 'audio.mp3';
    let audioLeadIn = 0;
    let title = 'Canción';
    let artist = 'Artista';
    let creator = 'osu! Mapper';
    let version = 'Normal';
    let circleSize = 4; // Columns / Keys
    let overallDifficulty = 5;

    const timingPoints = [];
    const hitObjectsRaw = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line || line.startsWith('//')) continue;

      if (line.startsWith('[') && line.endsWith(']')) {
        currentSection = line.slice(1, -1);
        continue;
      }

      if (currentSection === 'General') {
        const [k, ...v] = line.split(':');
        const key = k.trim();
        const val = v.join(':').trim();
        if (key === 'AudioFilename') audioFilename = val;
        if (key === 'AudioLeadIn') audioLeadIn = parseInt(val, 10) || 0;
      } else if (currentSection === 'Metadata') {
        const [k, ...v] = line.split(':');
        const key = k.trim();
        const val = v.join(':').trim();
        if (key === 'Title') title = val;
        if (key === 'Artist') artist = val;
        if (key === 'Creator') creator = val;
        if (key === 'Version') version = val;
      } else if (currentSection === 'Difficulty') {
        const [k, ...v] = line.split(':');
        const key = k.trim();
        const val = v.join(':').trim();
        if (key === 'CircleSize') circleSize = Math.max(1, parseInt(val, 10) || 4);
        if (key === 'OverallDifficulty') overallDifficulty = parseFloat(val) || 5;
      } else if (currentSection === 'TimingPoints') {
        const parts = line.split(',');
        if (parts.length >= 2) {
          const time = parseFloat(parts[0]);
          const beatLength = parseFloat(parts[1]);
          const uninherited = parts.length > 6 ? parseInt(parts[6], 10) : 1;
          if (uninherited === 1 && beatLength > 0) {
            timingPoints.push({ time, bpm: 60000 / beatLength });
          }
        }
      } else if (currentSection === 'HitObjects') {
        const parts = line.split(',');
        if (parts.length >= 4) {
          const x = parseInt(parts[0], 10);
          const time = parseInt(parts[2], 10);
          const type = parseInt(parts[3], 10);
          
          const originalLane = Math.max(0, Math.min(circleSize - 1, Math.floor((x * circleSize) / 512)));
          const isHold = (type & 128) !== 0;
          let endTime = time;

          if (isHold && parts.length >= 6) {
            const endPart = parts[5].split(':')[0];
            endTime = parseInt(endPart, 10) || (time + 400);
          }

          const duration = Math.max(0, endTime - time);

          hitObjectsRaw.push({
            originalLane: originalLane,
            timestamp_ms: time,
            type: (isHold && duration >= 80) ? 'hold' : 'tap',
            duration_ms: (isHold && duration >= 80) ? duration : null,
            end_timestamp_ms: (isHold && duration >= 80) ? endTime : null
          });
        }
      }
    }

    const bpm = timingPoints.length > 0 ? timingPoints[0].bpm : 120;
    const finalNotes = LaneRemapper.resolveCollisions(hitObjectsRaw, circleSize, Math.round(bpm), overallDifficulty);

    return {
      audioFilename,
      audioLeadIn,
      title,
      artist,
      creator,
      difficultyName: version,
      stars: Math.max(1.0, Math.min(10.0, overallDifficulty)),
      bpm: Math.round(bpm),
      keys: circleSize,
      notes: finalNotes
    };
  }
}

// ==========================================
// 3. PARSER: QUAVER (.qua)
// ==========================================

class QuaverParser {
  static parse(quaText) {
    const lines = quaText.split(/\r?\n/);
    
    let audioFilename = 'audio.mp3';
    let title = 'Canción Quaver';
    let artist = 'Artista';
    let creator = 'Quaver Charter';
    let difficultyName = 'Normal';
    let keys = 4;
    let bpm = 120;

    let inHitObjects = false;
    let currentHitObject = null;
    const rawNotes = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line || line.startsWith('#')) continue;

      if (line.startsWith('AudioFile:')) {
        audioFilename = line.replace('AudioFile:', '').trim();
      } else if (line.startsWith('Title:')) {
        title = line.replace('Title:', '').trim();
      } else if (line.startsWith('Artist:')) {
        artist = line.replace('Artist:', '').trim();
      } else if (line.startsWith('Creator:')) {
        creator = line.replace('Creator:', '').trim();
      } else if (line.startsWith('DifficultyName:')) {
        difficultyName = line.replace('DifficultyName:', '').trim();
      } else if (line.startsWith('Mode:')) {
        const m = line.replace('Mode:', '').trim();
        keys = m === 'Keys7' ? 7 : 4;
      } else if (line.startsWith('BPM:')) {
        bpm = parseFloat(line.replace('BPM:', '').trim()) || 120;
      } else if (line.startsWith('HitObjects:')) {
        inHitObjects = true;
        continue;
      } else if (inHitObjects) {
        if (line.startsWith('- StartTime:')) {
          if (currentHitObject && currentHitObject.StartTime !== undefined) {
            this._pushQuaverNote(currentHitObject, rawNotes);
          }
          currentHitObject = {
            StartTime: parseInt(line.replace('- StartTime:', '').trim(), 10),
            Lane: 1,
            EndTime: 0
          };
        } else if (currentHitObject && line.startsWith('Lane:')) {
          currentHitObject.Lane = parseInt(line.replace('Lane:', '').trim(), 10) || 1;
        } else if (currentHitObject && line.startsWith('EndTime:')) {
          currentHitObject.EndTime = parseInt(line.replace('EndTime:', '').trim(), 10) || 0;
        } else if (line.startsWith('TimingPoints:') || line.startsWith('SliderVelocities:')) {
          if (currentHitObject) {
            this._pushQuaverNote(currentHitObject, rawNotes);
            currentHitObject = null;
          }
          inHitObjects = false;
        }
      }
    }

    if (currentHitObject && currentHitObject.StartTime !== undefined) {
      this._pushQuaverNote(currentHitObject, rawNotes);
    }

    const finalNotes = LaneRemapper.resolveCollisions(rawNotes, keys, Math.round(bpm), 3.5);

    return {
      audioFilename,
      title,
      artist,
      creator,
      difficultyName,
      stars: 3.5,
      bpm: Math.round(bpm),
      keys,
      notes: finalNotes
    };
  }

  static _pushQuaverNote(obj, outArray) {
    const originalLane = Math.max(0, (obj.Lane || 1) - 1);
    const startT = obj.StartTime || 0;
    const endT = obj.EndTime || 0;
    const isHold = endT > startT + 50;
    const duration = isHold ? (endT - startT) : null;

    outArray.push({
      originalLane,
      timestamp_ms: startT,
      type: isHold ? 'hold' : 'tap',
      duration_ms: duration,
      end_timestamp_ms: isHold ? endT : null
    });
  }
}

// ==========================================
// 4. PARSER: CLONE HERO (.chart)
// ==========================================

class CloneHeroParser {
  static parse(chartText, chosenDiff = 'ExpertSingle') {
    const lines = chartText.split(/\r?\n/);
    let currentSection = '';

    let resolution = 192;
    let offsetSec = 0;
    let title = 'Canción Clone Hero';
    let artist = 'Artista';
    let charter = 'Charter';
    let audioFilename = 'song.ogg';

    const bpms = [];
    const rawEvents = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      if (line.startsWith('[') && line.endsWith(']')) {
        currentSection = line.slice(1, -1);
        continue;
      }

      if (currentSection === 'Song') {
        const [k, ...v] = line.split('=');
        const key = k.trim();
        const val = v.join('=').trim().replace(/^"|"$/g, '');
        if (key === 'Resolution') resolution = parseInt(val, 10) || 192;
        if (key === 'Offset') offsetSec = parseFloat(val) || 0;
        if (key === 'Name') title = val;
        if (key === 'Artist') artist = val;
        if (key === 'Charter') charter = val;
        if (key === 'MusicStream') audioFilename = val;
      } else if (currentSection === 'SyncTrack') {
        const parts = line.split(/\s*=\s*/);
        if (parts.length === 2) {
          const tick = parseInt(parts[0].trim(), 10);
          const evParts = parts[1].trim().split(/\s+/);
          if (evParts[0] === 'B') {
            const rawBpm = parseInt(evParts[1], 10) / 1000;
            bpms.push({ tick, bpm: rawBpm });
          }
        }
      } else if (currentSection === chosenDiff || (!currentSection.includes('Single') && currentSection === 'ExpertSingle')) {
        const parts = line.split(/\s*=\s*/);
        if (parts.length === 2) {
          const tick = parseInt(parts[0].trim(), 10);
          const evParts = parts[1].trim().split(/\s+/);
          if (evParts[0] === 'N') {
            const fret = parseInt(evParts[1], 10);
            const length = parseInt(evParts[2], 10) || 0;
            if (fret <= 4) {
              rawEvents.push({ tick, fret, length });
            }
          }
        }
      }
    }

    if (bpms.length === 0) bpms.push({ tick: 0, bpm: 120 });
    bpms.sort((a, b) => a.tick - b.tick);

    const tickToMs = (targetTick) => {
      let accumulatedMs = offsetSec * 1000;
      let lastTick = 0;
      let currentBpm = bpms[0].bpm;

      for (const bp of bpms) {
        if (targetTick <= bp.tick) break;
        const deltaTicks = bp.tick - lastTick;
        const msPerTick = (60000 / currentBpm) / resolution;
        accumulatedMs += deltaTicks * msPerTick;
        lastTick = bp.tick;
        currentBpm = bp.bpm;
      }

      const remTicks = targetTick - lastTick;
      const msPerTick = (60000 / currentBpm) / resolution;
      accumulatedMs += remTicks * msPerTick;
      return accumulatedMs;
    };

    const rawNotes = [];
    for (const ev of rawEvents) {
      const startMs = tickToMs(ev.tick);
      const isHold = ev.length > resolution / 4;
      const endMs = isHold ? tickToMs(ev.tick + ev.length) : startMs;
      const duration = isHold ? Math.max(0, endMs - startMs) : null;

      rawNotes.push({
        originalLane: ev.fret,
        timestamp_ms: Math.max(0, startMs),
        type: isHold ? 'hold' : 'tap',
        duration_ms: duration,
        end_timestamp_ms: isHold ? endMs : null
      });
    }

    const finalNotes = LaneRemapper.resolveCollisions(rawNotes, 5, Math.round(bpms[0].bpm), 4.5);

    return {
      audioFilename,
      title,
      artist,
      creator: charter,
      difficultyName: chosenDiff,
      stars: 4.5,
      bpm: Math.round(bpms[0].bpm),
      keys: 5,
      notes: finalNotes
    };
  }
}

// ==========================================
// 5. PACKAGE UNPACKER (JSZip Client-Side)
// ==========================================

class PackageUnpacker {
  static async unpack(arrayBuffer, fileType = 'osz', selectedDiffId = null) {
    if (typeof JSZip === 'undefined') {
      throw new Error('La librería JSZip no está cargada en el cliente.');
    }

    const zip = await JSZip.loadAsync(arrayBuffer);
    const files = Object.keys(zip.files);

    let parsedBeatmap = null;
    let audioBlob = null;
    let targetAudioName = '';
    let extractedDiffs = [];

    if (fileType === 'osz' || files.some(f => f.endsWith('.osu'))) {
      const osuFiles = files.filter(f => f.endsWith('.osu'));
      if (osuFiles.length === 0) throw new Error('No se encontraron archivos .osu en el paquete.');

      for (const f of osuFiles) {
        const txt = await zip.file(f).async('text');
        const parsed = OsuManiaParser.parse(txt);
        extractedDiffs.push({
          file: f,
          id: f,
          name: parsed.difficultyName,
          stars: parsed.stars,
          label: `${parsed.difficultyName} (${parsed.stars.toFixed(1)}★)`,
          parsedData: parsed
        });
      }

      extractedDiffs.sort((a, b) => a.stars - b.stars);

      let chosen = extractedDiffs.find(d => d.id === selectedDiffId || d.name === selectedDiffId) || extractedDiffs[0];
      parsedBeatmap = chosen.parsedData;
      targetAudioName = parsedBeatmap.audioFilename;

    } else if (fileType === 'qp' || files.some(f => f.endsWith('.qua'))) {
      const quaFiles = files.filter(f => f.endsWith('.qua'));
      if (quaFiles.length === 0) throw new Error('No se encontraron archivos .qua en el paquete Quaver.');

      for (const f of quaFiles) {
        const txt = await zip.file(f).async('text');
        const parsed = QuaverParser.parse(txt);
        extractedDiffs.push({
          file: f,
          id: f,
          name: parsed.difficultyName,
          stars: parsed.stars,
          label: parsed.difficultyName,
          parsedData: parsed
        });
      }

      let chosen = extractedDiffs.find(d => d.id === selectedDiffId || d.name === selectedDiffId) || extractedDiffs[0];
      parsedBeatmap = chosen.parsedData;
      targetAudioName = parsedBeatmap.audioFilename;

    } else if (files.some(f => f.endsWith('.chart'))) {
      const chartFile = files.find(f => f.endsWith('.chart'));
      const txt = await zip.file(chartFile).async('text');
      parsedBeatmap = CloneHeroParser.parse(txt, selectedDiffId || 'ExpertSingle');
      targetAudioName = parsedBeatmap.audioFilename;
    }

    if (!parsedBeatmap) {
      throw new Error('Formato de mapa de ritmo no reconocido en el paquete.');
    }

    let audioFileEntry = null;
    if (targetAudioName) {
      audioFileEntry = zip.file(targetAudioName) || files.find(f => f.toLowerCase() === targetAudioName.toLowerCase());
    }

    if (!audioFileEntry) {
      const audioPath = files.find(f => {
        const lower = f.toLowerCase();
        return lower.endsWith('.mp3') || lower.endsWith('.ogg') || lower.endsWith('.wav') || lower.endsWith('.m4a');
      });
      if (audioPath) {
        audioFileEntry = zip.file(audioPath);
      }
    }

    if (!audioFileEntry) {
      throw new Error('No se encontró archivo de audio (.mp3, .ogg, .wav) dentro del paquete.');
    }

    const audioArrayBuffer = await audioFileEntry.async('arraybuffer');
    const ext = (audioFileEntry.name || 'audio.mp3').split('.').pop().toLowerCase();
    const mime = ext === 'ogg' ? 'audio/ogg' : (ext === 'wav' ? 'audio/wav' : 'audio/mpeg');
    audioBlob = new Blob([audioArrayBuffer], { type: mime });
    const audioUrl = URL.createObjectURL(audioBlob);

    return {
      metadata: {
        id: parsedBeatmap.title.toLowerCase().replace(/\s+/g, '_'),
        title: parsedBeatmap.title,
        artist: parsedBeatmap.artist,
        creator: parsedBeatmap.creator,
        difficulty_name: parsedBeatmap.difficultyName,
        stars: parsedBeatmap.stars,
        bpm: parsedBeatmap.bpm,
        total_notes: parsedBeatmap.notes.length,
        num_lanes: 3
      },
      notes: parsedBeatmap.notes,
      audioBlob: audioBlob,
      audioUrl: audioUrl,
      availableDifficulties: extractedDiffs
    };
  }
}

// ==========================================
// 6. INDEXEDDB STORAGE (Offline Library, Favorites & Playlists)
// ==========================================

class IndexedDBStorage {
  static DB_NAME = 'BeatstarLibraryDB';
  static STORE_SAVED = 'saved_charts';
  static STORE_FAVORITES = 'favorites';
  static STORE_PLAYLISTS = 'playlists';
  static DB_VERSION = 2;

  static openDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);
      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(this.STORE_SAVED)) {
          db.createObjectStore(this.STORE_SAVED, { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains(this.STORE_FAVORITES)) {
          db.createObjectStore(this.STORE_FAVORITES, { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains(this.STORE_PLAYLISTS)) {
          db.createObjectStore(this.STORE_PLAYLISTS, { keyPath: 'id' });
        }
      };
      request.onsuccess = (e) => resolve(e.target.result);
      request.onerror = (e) => reject(e.target.error);
    });
  }

  // --- Saved Offline Charts ---
  static async saveChart(chartItem, beatmapData, audioBlob) {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE_SAVED, 'readwrite');
      const store = tx.objectStore(this.STORE_SAVED);

      const record = {
        id: chartItem.id,
        title: chartItem.title,
        artist: chartItem.artist,
        creator: chartItem.creator,
        source: chartItem.source,
        source_name: chartItem.source_name,
        thumbnail: chartItem.thumbnail,
        difficulties: chartItem.difficulties,
        metadata: beatmapData.metadata,
        notes: beatmapData.notes,
        audioBlob: audioBlob,
        savedAt: Date.now()
      };

      const req = store.put(record);
      req.onsuccess = () => resolve(true);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  static async getChart(chartId) {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE_SAVED, 'readonly');
      const store = tx.objectStore(this.STORE_SAVED);
      const req = store.get(chartId);
      req.onsuccess = () => resolve(req.result);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  static async getAllCharts() {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE_SAVED, 'readonly');
      const store = tx.objectStore(this.STORE_SAVED);
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  static async deleteChart(chartId) {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE_SAVED, 'readwrite');
      const store = tx.objectStore(this.STORE_SAVED);
      const req = store.delete(chartId);
      req.onsuccess = () => resolve(true);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  // --- Favorites (❤️) ---
  static async toggleFavorite(chartItem) {
    const db = await this.openDB();
    const isFav = await this.isFavorite(chartItem.id);
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE_FAVORITES, 'readwrite');
      const store = tx.objectStore(this.STORE_FAVORITES);

      if (isFav) {
        const req = store.delete(chartItem.id);
        req.onsuccess = () => resolve(false); // Removed
        req.onerror = (e) => reject(e.target.error);
      } else {
        const favRecord = {
          id: chartItem.id,
          title: chartItem.title,
          artist: chartItem.artist,
          creator: chartItem.creator,
          source: chartItem.source,
          source_name: chartItem.source_name,
          thumbnail: chartItem.thumbnail,
          difficulties: chartItem.difficulties,
          download_url: chartItem.download_url,
          direct_download_url: chartItem.direct_download_url,
          fallback_download_url: chartItem.fallback_download_url,
          addedAt: Date.now()
        };
        const req = store.put(favRecord);
        req.onsuccess = () => resolve(true); // Added
        req.onerror = (e) => reject(e.target.error);
      }
    });
  }

  static async isFavorite(chartId) {
    const db = await this.openDB();
    return new Promise((resolve) => {
      const tx = db.transaction(this.STORE_FAVORITES, 'readonly');
      const store = tx.objectStore(this.STORE_FAVORITES);
      const req = store.get(chartId);
      req.onsuccess = () => resolve(!!req.result);
      req.onerror = () => resolve(false);
    });
  }

  static async getAllFavorites() {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE_FAVORITES, 'readonly');
      const store = tx.objectStore(this.STORE_FAVORITES);
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  // --- Playlists (📁) ---
  static async savePlaylist(playlistObj) {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE_PLAYLISTS, 'readwrite');
      const store = tx.objectStore(this.STORE_PLAYLISTS);
      const req = store.put(playlistObj);
      req.onsuccess = () => resolve(playlistObj);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  static async getAllPlaylists() {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE_PLAYLISTS, 'readonly');
      const store = tx.objectStore(this.STORE_PLAYLISTS);
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  static async getPlaylist(playlistId) {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE_PLAYLISTS, 'readonly');
      const store = tx.objectStore(this.STORE_PLAYLISTS);
      const req = store.get(playlistId);
      req.onsuccess = () => resolve(req.result);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  static async deletePlaylist(playlistId) {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE_PLAYLISTS, 'readwrite');
      const store = tx.objectStore(this.STORE_PLAYLISTS);
      const req = store.delete(playlistId);
      req.onsuccess = () => resolve(true);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  static async addTrackToPlaylist(playlistId, trackItem) {
    const playlist = await this.getPlaylist(playlistId);
    if (!playlist) throw new Error('Playlist no encontrada.');
    if (!playlist.tracks) playlist.tracks = [];
    
    // Evitar duplicados
    if (!playlist.tracks.some(t => t.id === trackItem.id)) {
      playlist.tracks.push(trackItem);
      playlist.item_count = playlist.tracks.length;
      await this.savePlaylist(playlist);
    }
    return playlist;
  }

  static async removeTrackFromPlaylist(playlistId, trackId) {
    const playlist = await this.getPlaylist(playlistId);
    if (!playlist) return;
    playlist.tracks = (playlist.tracks || []).filter(t => t.id !== trackId);
    playlist.item_count = playlist.tracks.length;
    await this.savePlaylist(playlist);
    return playlist;
  }
}

// Export to global window scope
window.LaneRemapper = LaneRemapper;
window.OsuManiaParser = OsuManiaParser;
window.QuaverParser = QuaverParser;
window.CloneHeroParser = CloneHeroParser;
window.PackageUnpacker = PackageUnpacker;
window.IndexedDBStorage = IndexedDBStorage;
