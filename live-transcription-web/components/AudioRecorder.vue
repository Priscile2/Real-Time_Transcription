<template>
  <div class="space-y-4">
    <!-- Upload Audio Section -->
    <div class="flex flex-col space-y-2">
      <div class="flex items-center space-x-2">
        <input 
          type="file" 
          @change="handleFileUpload" 
          accept="audio/*,.mp3,.mp4,.mov,.wav" 
          class="border p-2 rounded-md w-full"
          id="file-upload"
        />
        <button 
          @click="startTranscription" 
          :disabled="!selectedFile || loading || audioStore.isRecording"
          class="px-4 py-2 text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 flex-shrink-0"
        >
          {{ loading ? 'Processing...' : 'Transcribe' }}
        </button>
      </div>
      
      <div v-if="fileError" class="text-red-500 text-sm">
        {{ fileError }}
      </div>
      
      <div v-if="selectedFile" class="text-sm text-gray-600">
        Selected file: {{ selectedFile.name }} ({{ formatFileSize(selectedFile.size) }})
      </div>
      
      <div v-if="uploadProgress > 0 && uploadProgress < 100" class="w-full">
        <div class="bg-gray-200 rounded-full h-2">
          <div 
            class="bg-blue-600 h-2 rounded-full" 
            :style="`width: ${uploadProgress}%`"
          ></div>
        </div>
        <div class="text-xs text-gray-600 mt-1">{{ uploadProgress }}% uploaded</div>
      </div>
    </div>
   
    <!-- Live Recording Section -->
    <div class="flex items-center space-x-2">
      <button
        @click="handleRecordingToggle"
        :disabled="disabled || audioStore.isStopping || loading"
        :class="[
          'flex items-center justify-center px-4 py-2.5 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-opacity-50 transition-all duration-200 shadow-sm text-white min-h-[40px]',
          audioStore.isRecording ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500' : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
          (disabled || audioStore.isStopping || loading) ? 'opacity-50 cursor-not-allowed' : ''
        ]"
      >
        <svg 
          :class="{'animate-pulse': audioStore.isRecording}" 
          class="h-4 w-4 mr-2 flex-shrink-0" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            stroke-linecap="round" 
            stroke-linejoin="round" 
            stroke-width="2" 
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>
        <span class="whitespace-nowrap">
          {{ buttonText }}
        </span>
      </button>
    </div>
    
    <div v-if="!audioStore.isRecording && audioStore.combinedError" class="p-4 bg-red-50 text-red-600 rounded-md">
      {{ audioStore.combinedError }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useTranscriptionStore } from '~/stores/transcriptionStore';
import { useAudioStore } from '~/stores/audioStore';

const transcriptionStore = useTranscriptionStore();
const audioStore = useAudioStore();
const selectedFile = ref<File | null>(null);
const loading = ref(false);
const fileError = ref('');
const uploadProgress = ref(0);

const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB max file size

const handleFileUpload = (event: Event) => {
  fileError.value = '';
  const target = event.target as HTMLInputElement;
  if (target.files) {
    const file = target.files[0];

    if (file.size > MAX_FILE_SIZE) {
      fileError.value = `File is too large. Maximum size is ${MAX_FILE_SIZE / (1024 * 1024)}MB`;
      target.value = ''; // Clear the input
      selectedFile.value = null;
      return;
    }
    
    selectedFile.value = file;
  }
};

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' bytes';
  else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  else return (bytes / 1048576).toFixed(1) + ' MB';
};

const startTranscription = async () => {
  if (!selectedFile.value) return;
  loading.value = true;
  const formData = new FormData();
  formData.append("file", selectedFile.value);

  try {
    const response = await fetch("http://127.0.0.1:8000/transcribe", {
      method: "POST",
      body: formData
    });
    
    // First, check if the response is valid
    if (!response.ok) {
      throw new Error(`Server returned ${response.status}: ${response.statusText}`);
    }
    
    // Try to get JSON data
    const data = await response.json();
    
    // Check what property contains the transcription
    console.log("Response data:", data);
    
    // Look for known property names
    let transcriptionText = null;
    if (data.transcriptionText) {
      transcriptionText = data.transcriptionText;
    } else if (data.transcritionText) {
      transcriptionText = data.transcritionText;
    } else if (data.transcribed_text) {
      transcriptionText = data.transcribed_text;
    }
    
    if (transcriptionText) {
      // Update the transcription in the store
      transcriptionStore.transcription = transcriptionText;
    } else {
      console.error("No transcription text found in response:", data);
      throw new Error("No transcription text found in response");
    }
  } catch (error) {
    console.error("Error:", error);
  } finally {
    loading.value = false;
  }
};

const handleRecordingToggle = async () => {
  try {
    if (!audioStore.isRecording) {
      await audioStore.startRecording();
    } else {
      await audioStore.stopRecording();
    }
  } catch (error: any) {
    console.error('Recording error:', error);
  }
};

const buttonText = computed(() => {
  if (audioStore.isStopping) return 'Stopping...';
  return audioStore.isRecording ? 'Recording...' : 'Start Recording';
});

const props = defineProps<{ disabled?: boolean }>();
</script>

<style scoped>
.animate-pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
}
</style>