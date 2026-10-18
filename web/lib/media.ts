import type { MediaInfo, Frame } from './types';

export const MAX_FILE_BYTES = 150 * 1024 * 1024;
export const MAX_DURATION = 300;
export function validateVideoFile(file: Pick<File, 'size' | 'type' | 'name'>) {
  if (!file.size) throw new Error('This file is empty. Choose a video with content.');
  if (file.size > MAX_FILE_BYTES) throw new Error('Choose a clip under 150 MB. Trim a longer Reel before importing.');
  if (!['video/mp4', 'video/webm', 'video/quicktime'].includes(file.type)) throw new Error('Use an MP4, WebM, or MOV video. Playback support depends on your browser and codec.');
}
function eventOnce(target: HTMLVideoElement, event: string, timeout = 20000) {
  return new Promise<void>((resolve, reject) => {
    const timer = setTimeout(() => { cleanup(); reject(new Error('Video decoding timed out. Try an H.264 MP4 or a shorter clip.')); }, timeout);
    const good = () => { cleanup(); resolve(); };
    const bad = () => { cleanup(); reject(new Error('Your browser could not decode this video. Try an H.264 MP4, or analyze a transcript.')); };
    function cleanup() { clearTimeout(timer); target.removeEventListener(event, good); target.removeEventListener('error', bad); }
    target.addEventListener(event, good, { once: true }); target.addEventListener('error', bad, { once: true });
  });
}
export async function inspectVideo(file: File): Promise<MediaInfo> {
  validateVideoFile(file);
  const url = URL.createObjectURL(file);
  const video = document.createElement('video'); video.muted = true; video.preload = 'auto'; video.playsInline = true;
  try {
    const loaded = eventOnce(video, 'loadeddata'); video.src = url; video.load(); await loaded;
    if (!Number.isFinite(video.duration) || video.duration <= 0 || !video.videoWidth || !video.videoHeight) throw new Error('Video metadata is unavailable. Re-export the clip as MP4.');
    if (video.duration > MAX_DURATION) throw new Error('This first version supports clips up to 5 minutes. Trim the clip or analyze its transcript.');
    const canvas = document.createElement('canvas');
    const scale = Math.min(1, 360 / Math.max(video.videoWidth, video.videoHeight));
    canvas.width = Math.max(1, Math.round(video.videoWidth * scale)); canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) throw new Error('Frame sampling is not supported in this browser.');
    const frames: Frame[] = [];
    const moments = [Math.min(.15, video.duration * .05), .2, .4, .6, .8, .95].map((p, i) => i === 0 ? p : video.duration * p);
    for (const time of moments) {
      const ready = eventOnce(video, 'seeked'); video.currentTime = Math.min(time, video.duration - .001); await ready;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
      let luminance = 0;
      for (let i = 0; i < pixels.length; i += 4) luminance += .2126 * pixels[i] + .7152 * pixels[i + 1] + .0722 * pixels[i + 2];
      frames.push({ time, image: canvas.toDataURL('image/jpeg', .68), brightness: Math.round(luminance / (pixels.length / 4)) });
    }
    return { name: file.name, size: file.size, type: file.type, duration: video.duration, width: video.videoWidth, height: video.videoHeight, frames };
  } finally { video.removeAttribute('src'); video.load(); URL.revokeObjectURL(url); }
}

export async function decodeAudio(file: File): Promise<Float32Array> {
  const context = new AudioContext();
  try {
    const original = await context.decodeAudioData(await file.arrayBuffer());
    if (original.duration > MAX_DURATION) throw new Error('Local transcription supports clips up to 5 minutes.');
    const offline = new OfflineAudioContext(1, Math.ceil(original.duration * 16000), 16000);
    const source = offline.createBufferSource(); source.buffer = original; source.connect(offline.destination); source.start();
    const mono = await offline.startRendering();
    return new Float32Array(mono.getChannelData(0));
  } catch (error) {
    throw new Error(error instanceof Error && error.message.includes('5 minutes') ? error.message : 'Audio could not be decoded. The video may be silent or use an unsupported codec. Paste a transcript to continue.');
  } finally { await context.close(); }
}
