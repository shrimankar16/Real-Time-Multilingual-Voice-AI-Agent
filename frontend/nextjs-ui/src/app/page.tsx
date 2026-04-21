'use client'

import { useState } from 'react'

export default function Home() {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState<Array<{role: string, text: string}>>([])

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Voice AI Agent
          </h1>
          <p className="text-gray-600">
            Clinical Appointment Booking System
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Voice Panel */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Voice Conversation</h2>
            <div className="flex flex-col items-center justify-center space-y-4">
              <button
                onClick={() => setIsRecording(!isRecording)}
                className={`w-32 h-32 rounded-full flex items-center justify-center text-white text-xl font-semibold transition-all ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                    : 'bg-blue-500 hover:bg-blue-600'
                }`}
              >
                {isRecording ? '🎤 Stop' : '🎤 Start'}
              </button>
              <p className="text-gray-600 text-center">
                {isRecording
                  ? 'Listening... Click to stop'
                  : 'Click to start voice conversation'}
              </p>
            </div>

            {/* Transcript Log */}
            <div className="mt-8">
              <h3 className="text-lg font-semibold mb-3">Transcript</h3>
              <div className="bg-gray-50 rounded-lg p-4 h-64 overflow-y-auto space-y-2">
                {transcript.length === 0 ? (
                  <p className="text-gray-400 text-center">
                    No conversation yet. Start speaking!
                  </p>
                ) : (
                  transcript.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded ${
                        msg.role === 'user'
                          ? 'bg-blue-100 ml-8'
                          : 'bg-green-100 mr-8'
                      }`}
                    >
                      <span className="font-semibold">
                        {msg.role === 'user' ? 'You' : 'Agent'}:
                      </span>{' '}
                      {msg.text}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Dashboard */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Dashboard</h2>
            <div className="space-y-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">
                  Available Doctors
                </h3>
                <p className="text-gray-600">Loading...</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="font-semibold text-green-900 mb-2">
                  Recent Appointments
                </h3>
                <p className="text-gray-600">Loading...</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <h3 className="font-semibold text-purple-900 mb-2">
                  System Status
                </h3>
                <p className="text-gray-600">✅ All systems operational</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
