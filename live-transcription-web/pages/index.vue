<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-4">
    <h1 class="text-2xl font-bold mb-4">Audio Transcription</h1>
    
    <AudioRecorder :disabled="false" />
    
    <div class="mt-6 w-full max-w-md bg-white p-4 rounded-md shadow">
      <div class="flex justify-between items-center mb-2">
        <h2 class="text-lg font-medium">Transcription:</h2>
        <span 
          v-if="transcriptionSource" 
          :class="[
            'text-xs px-2 py-1 rounded-full',
            transcriptionSource === 'websocket' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
          ]"
        >
          {{ transcriptionSource === 'websocket' ? 'Live Recording' : 'File Upload' }}
        </span>
      </div>
      
      <p class="text-sm text-gray-500 mb-2">Last updated: {{ lastUpdated }}</p>
      
      <textarea
        v-model="transcription"
        class="w-full h-40 p-2 border rounded-md resize-none focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        placeholder="Transcribed text will appear here..."
        readonly
      ></textarea>
      
      <div class="mt-4 flex space-x-2">
        <button
          @click="downloadText"
          :disabled="!transcription"
          class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Download Transcription
        </button>
        
        <button
          @click="copyToClipboard"
          :disabled="!transcription"
          class="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Copy to Clipboard
        </button>
        
        <button
          @click="clearTranscription"
          :disabled="!transcription"
          class="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Clear
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import AudioRecorder from '~/components/AudioRecorder.vue';
import { useTranscriptionStore } from '~/stores/transcriptionStore';


const transcriptionStore = useTranscriptionStore();
const transcription = ref('');
const lastUpdated = ref('Never');
const transcriptionSource = ref('');
const showConfirmDialog = ref(false);

// Watch for changes in the transcription store
watch(
  [() => transcriptionStore.transcription, () => transcriptionStore.source],
  ([newTranscription, newSource], [oldTranscription, oldSource]) => {
    // Only update if there's a change in transcription
    if (newTranscription !== oldTranscription || newSource !== oldSource) {
      // If we already have a transcription from a different source, confirm before replacing
      if (transcription.value && transcriptionSource.value && 
          newSource && transcriptionSource.value !== newSource) {
        
        const userConfirmed = confirm(
          `You already have a transcription from ${transcriptionSource.value === 'websocket' ? 'Live Recording' : 'File Upload'}. 
           Replace with new transcription from ${newSource === 'websocket' ? 'Live Recording' : 'File Upload'}?`
        );
        
        if (!userConfirmed) return;
      }
      
      // Update our local state
      transcription.value = newTranscription;
      if (newSource) {
        transcriptionSource.value = newSource;
      }
      
      if (newTranscription) {
        lastUpdated.value = new Date().toLocaleTimeString();
      }
    }
  }
);

const downloadText = () => {
  if (!transcription.value) return;
  
  const blob = new Blob([transcription.value], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `transcription_${new Date().toISOString().slice(0,10)}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const copyToClipboard = async () => {
  if (!transcription.value) return;
  
  try {
    await navigator.clipboard.writeText(transcription.value);
    alert('Copied to clipboard!');
  } catch (err) {
    console.error('Failed to copy text:', err);
    alert('Failed to copy to clipboard');
  }
};

const clearTranscription = () => {
  if (!transcription.value) return;
  
  const userConfirmed = confirm('Are you sure you want to clear the transcription?');
  if (userConfirmed) {
    transcription.value = '';
    transcriptionSource.value = '';
    transcriptionStore.resetTranscription();
  }
};
</script>

<style scoped>
textarea {
  font-size: 16px;
  line-height: 1.5;
}
</style>