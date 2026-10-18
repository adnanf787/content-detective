import { pipeline, env } from '@huggingface/transformers';
env.allowLocalModels = false;
// Single-threaded WASM works without cross-origin isolation headers.
if (env.backends.onnx.wasm) env.backends.onnx.wasm.numThreads = 1;

let transcriber: ReturnType<typeof pipeline<'automatic-speech-recognition'>> | null = null;
self.onmessage = async (event: MessageEvent<{ audio: Float32Array; language: string }>) => {
  try {
    if (!transcriber) transcriber = pipeline('automatic-speech-recognition', 'Xenova/whisper-tiny', {
      device: 'wasm', dtype: 'q8', progress_callback: (progress) => {
        const entry = progress as { status: string; progress?: number; file?: string };
        self.postMessage({ type: 'progress', status: entry.status, progress: entry.progress, file: entry.file });
      },
    });
    const engine = await transcriber;
    self.postMessage({ type: 'progress', status: 'transcribing' });
    const options = { chunk_length_s: 30, stride_length_s: 5, return_timestamps: true as const,
      task: 'transcribe' as const, ...(event.data.language === 'auto' ? {} : { language: event.data.language }) };
    const output = await engine(event.data.audio, options);
    const result = Array.isArray(output) ? output[0] : output;
    self.postMessage({ type: 'complete', text: result.text });
  } catch (error) {
    transcriber = null;
    self.postMessage({ type: 'error', message: error instanceof Error ? error.message : 'Local speech model failed. Paste a transcript instead.' });
  }
};
