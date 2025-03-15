import { useState, useEffect, useRef } from 'react';
import { supabase } from '@/lib/supabaseClient';

// Add type declaration for SpeechRecognition
declare global {
  interface Window {
    SpeechRecognition?: any;
    webkitSpeechRecognition?: any;
  }
}

interface VoiceRecorderProps {
  clientId: string;
  onTranscriptGenerated?: (transcript: string) => void;
}

const VoiceRecorder = ({ clientId, onTranscriptGenerated }: VoiceRecorderProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioURL, setAudioURL] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  
  // Initialize speech recognition
  const speechRecognition = useRef<any>(null);
  
  useEffect(() => {
    // Initialize Web Speech API
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        speechRecognition.current = new SpeechRecognition();
        speechRecognition.current.continuous = true;
        speechRecognition.current.interimResults = true;
        
        speechRecognition.current.onresult = (event: any) => {
          const currentTranscript = Array.from(event.results)
            .map((result: any) => result[0])
            .map((result: any) => result.transcript)
            .join('');
          
          setTranscript(currentTranscript);
        };
        
        speechRecognition.current.onerror = (event: any) => {
          setError(`Speech recognition error: ${event.error}`);
        };
      } else {
        setError('Speech recognition not supported in this browser');
      }
    }
    
    return () => {
      if (speechRecognition.current) {
        speechRecognition.current.stop();
      }
    };
  }, []);
  
  const startRecording = async () => {
    try {
      setError(null);
      audioChunksRef.current = [];
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const url = URL.createObjectURL(audioBlob);
        setAudioURL(url);
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
      
      // Start speech recognition
      if (speechRecognition.current) {
        speechRecognition.current.start();
      }
    } catch (err) {
      setError(`Could not start recording: ${err instanceof Error ? err.message : String(err)}`);
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop all audio tracks
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      
      // Stop speech recognition
      if (speechRecognition.current) {
        speechRecognition.current.stop();
      }
    }
  };
  
  const saveRecording = async () => {
    if (!audioURL || !clientId) return;
    
    try {
      setIsProcessing(true);
      
      // Upload audio file to Supabase Storage
      const audioBlob = await fetch(audioURL).then(r => r.blob());
      const fileName = `voice-notes/${clientId}/${Date.now()}.wav`;
      
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('audio')
        .upload(fileName, audioBlob, {
          cacheControl: '3600',
          contentType: 'audio/wav'
        });
      
      if (uploadError) throw uploadError;
      
      // Get the public URL
      const { data: publicUrlData } = supabase.storage
        .from('audio')
        .getPublicUrl(fileName);
      
      const audioUrl = publicUrlData.publicUrl;
      
      // Save record in the database
      const { data, error } = await supabase.from('voice_notes').insert({
        client_id: clientId,
        audio_url: audioUrl,
        transcript: transcript,
        date: new Date().toISOString()
      });
      
      if (error) throw error;
      
      // Callback with transcript
      if (onTranscriptGenerated) {
        onTranscriptGenerated(transcript);
      }
      
      // Clear state
      setAudioURL(null);
      setTranscript('');
      setIsProcessing(false);
      
    } catch (err) {
      setError(`Error saving recording: ${err instanceof Error ? err.message : String(err)}`);
      setIsProcessing(false);
    }
  };
  
  return (
    <div className="p-4 border rounded-lg bg-white shadow-sm">
      <h3 className="text-lg font-semibold mb-4">Voice Recorder</h3>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="flex flex-col gap-3">
        <div className="flex gap-2">
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`px-4 py-2 rounded-lg ${
              isRecording 
                ? 'bg-red-500 hover:bg-red-600 text-white' 
                : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
            disabled={isProcessing}
          >
            {isRecording ? 'Stop Recording' : 'Start Recording'}
          </button>
          
          {audioURL && (
            <button
              onClick={saveRecording}
              className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg"
              disabled={isProcessing}
            >
              {isProcessing ? 'Saving...' : 'Save Recording'}
            </button>
          )}
        </div>
        
        {audioURL && (
          <div className="mt-4">
            <p className="font-medium mb-2">Preview:</p>
            <audio src={audioURL} controls className="w-full" />
          </div>
        )}
        
        {transcript && (
          <div className="mt-4">
            <p className="font-medium mb-2">Transcript:</p>
            <div className="p-3 bg-gray-100 rounded-lg whitespace-pre-wrap">
              {transcript}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceRecorder; 