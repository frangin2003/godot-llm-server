import { useEffect, useState, useRef } from 'react';

function App() {
  const [promptPairs, setPromptPairs] = useState([]); // Will store [{prompt: string, output: string}]
  const [currentPrompt, setCurrentPrompt] = useState('');
  const [output, setOutput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const promptRef = useRef('');

  useEffect(() => {
    promptRef.current = currentPrompt;
  }, [currentPrompt]);

  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:7500');
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to the WebSocket server');
      setIsConnected(true);

      // Send identification message
      const identificationMessage = JSON.stringify({ client: "monitor" });
      ws.send(identificationMessage);
    };

    ws.onmessage = (event) => {
      if (event.data === null) {
        return;
      }

      try {
        if (event.data.startsWith("<|begin_of_text|>")) {
          setCurrentPrompt(event.data);
          setOutput('');
        } else {
          setOutput((prevOutput) => {
            const newOutput = prevOutput + event.data;
            if (event.data.endsWith("}")) {
              setPromptPairs(prev => [...prev, {
                prompt: promptRef.current,
                output: newOutput
              }]);
            }
            return newOutput;
          });
        }
      } catch (error) {
        console.error('Error processing message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed, attempting to reconnect...');
      setIsConnected(false);
      // Attempt to reconnect after a delay
      setTimeout(connectWebSocket, 5000); // Attempt to reconnect after 5 seconds
    };
  };

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handlePromptClick = (pair) => {
    setCurrentPrompt(pair.prompt);
    setOutput(pair.output);
  };

  const handleSendPrompt = async () => {
    if (!currentPrompt.trim()) return;
    
    setOutput(''); // Clear previous output
    
    try {
      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: "llama3.1",
          prompt: currentPrompt,
          stream: true
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.trim() === '') continue;
          
          try {
            const parsedChunk = JSON.parse(line);
            if (parsedChunk.response) {
              setOutput(prev => prev + parsedChunk.response);
            }
          } catch (e) {
            console.error('Error parsing chunk:', e);
          }
        }
      }
    } catch (error) {
      console.error('Error calling Ollama API:', error);
      setOutput('Error: Failed to get response from Ollama');
    }
  };

  return (
    <div className="flex flex-col h-screen p-4 text-xs">
      <div className="flex flex-1 gap-4">
        {/* Left Panel - Prompts List */}
        <div className="w-1/5 flex flex-col">
          <div className="text-white mb-2">Saved Conversations</div>
          <div className="flex-1 border-white border-5 overflow-y-auto">
            {promptPairs.map((pair, index) => (
              <div
                key={index}
                onClick={() => handlePromptClick(pair)}
                className="p-2 hover:bg-gray-800 cursor-pointer"
              >
                {pair.prompt.slice(0, 50)}...
              </div>
            ))}
          </div>
        </div>

        {/* Center Panel - Current Prompt */}
        <div className="w-1/2 flex flex-col">
          <div className="text-[#FF69B4] mb-2">Prompt</div>
          <div className="flex flex-col h-full">
            <textarea
              value={currentPrompt}
              onChange={(e) => setCurrentPrompt(e.target.value)}
              className="flex-1 bg-black border-[#FF69B4] border-5 p-2 resize-none focus:outline-none text-white mb-2"
            />
            <button
              onClick={handleSendPrompt}
              className="bg-black text-[#FF69B4] border-[#FF69B4] border-5 p-2 hover:bg-[#FF69B4] hover:text-black transition-colors"
            >
              SEND
            </button>
          </div>
        </div>

        {/* Right Panel - Output */}
        <div className="w-1/2 flex flex-col">
          <div className="text-[#00FFFF] mb-2">LLM Output</div>
          <textarea
            value={output}
            onChange={(e) => setOutput(e.target.value)}
            className="flex-1 bg-black border-[#00FFFF] border-5 p-2 overflow-y-auto resize-none focus:outline-none text-white"
          />
        </div>
      </div>

      {/* Connection Indicator */}
      <div className="mt-2 text-left">
        {isConnected ? (
          <span className="text-green-500">🟢 Connected</span>
        ) : (
          <span className="text-red-500">🔴 Disconnected</span>
        )}
      </div>
    </div>
  );
}

export default App; 