import { useState } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { ConfigPanel } from './components/ConfigPanel';
import { Scale, Settings } from 'lucide-react';
import { Button } from './components/ui/button';

export default function App() {
  const [uploadedDocuments, setUploadedDocuments] = useState<Array<{
    id: string;
    name: string;
    size: string;
    date: string;
    status: 'processing' | 'completed' | 'error';
  }>>([]);

  const [isConfigOpen, setIsConfigOpen] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(true); // 🔥 thêm state ẩn/hiện chat

  // ============================
  // 🔥 NÂNG STATE CONFIG LÊN
  // ============================

  const [temperature, setTemperature] = useState([0.7]);
  const [maxTokens, setMaxTokens] = useState([2000]);
  const [useDocs, setUseDocs] = useState(true);
  const [topK, setTopK] = useState([5]);
  const [model, setModel] = useState('gemini-2.0-flash');
  const [responseStyle, setResponseStyle] = useState('formal');
  const [semanticWeight, setSemanticWeight] = useState([0.7]);
  const [systemPrompt, setSystemPrompt] = useState(
    `Bạn là một trợ lý pháp lý thân thiện, lịch sự và trung thực của Việt Nam
Nhiệm vụ của bạn:
1. Nếu người dùng CHÀO HỎI → hãy trả lời chào hỏi tự nhiên, thân thiện.
2. Nếu người dùng hỏi VỀ PHÁP LUẬT → bạn chỉ được phép trả lời dựa trên TÀI LIỆU dưới đây (nếu có) và giải thích rõ ràng nếu người dùng cần, không hiểu.
3. Nếu câu hỏi KHÔNG LIÊN QUAN đến pháp luật → hãy lịch sự từ chối và nói rằng bạn chỉ hỗ trợ câu hỏi pháp luật.
4. Nếu không tìm thấy nội dung liên quan trong tài liệu → hãy trả lời:
"Tôi xin lỗi, tôi không có đủ thông tin trong tài liệu hiện tại để trả lời câu hỏi này."
`
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            
            {/* Logo + Title */}
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-blue-600 to-indigo-600 p-2 rounded-lg">
                <Scale className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-gray-900">Trợ Lý Pháp Luật AI</h1>
                <p className="text-sm text-gray-500">
                  Tư vấn và tra cứu văn bản pháp luật Việt Nam
                </p>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={() => setIsConfigOpen(!isConfigOpen)}
                className="flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                {isConfigOpen ? 'Ẩn cấu hình' : 'Hiện cấu hình'}
              </Button>

              <Button
                variant="outline"
                onClick={() => setIsChatOpen(!isChatOpen)}
                className="flex items-center gap-2"
              >
                {isChatOpen ? 'Ẩn chat' : 'Hiện chat'}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1800px] mx-auto px-6 py-6">
        <div className="flex gap-6 h-[calc(100vh-140px)] transition-all duration-300">

          {/* Config Panel */}
          {isConfigOpen && (
            <div
              className={`${
                isChatOpen ? 'w-[400px]' : 'w-full'
              } flex-shrink-0 transition-all duration-300`}
            >
              <ConfigPanel
                documents={uploadedDocuments}
                setDocuments={setUploadedDocuments}
                model={model}
                setModel={setModel}
                temperature={temperature}
                setTemperature={setTemperature}
                topK={topK}
                setTopK={setTopK}
                maxTokens={maxTokens}
                setMaxTokens={setMaxTokens}
                useDocs={useDocs}
                setUseDocs={setUseDocs}
                responseStyle={responseStyle}
                setResponseStyle={setResponseStyle}
                semanticWeight={semanticWeight}
                setSemanticWeight={setSemanticWeight}
                systemPrompt={systemPrompt}
                setSystemPrompt={setSystemPrompt}
              />
            </div>
          )}

          {/* Chat Interface */}
          {isChatOpen && (
            <div className="flex-1 min-w-0 transition-all duration-300">
              <ChatInterface
                uploadedDocuments={uploadedDocuments}
                model={model}
                topK={topK[0]}
                temperature={temperature[0]}
                maxTokens={maxTokens[0]}
                useDocs={useDocs}
                responseStyle={responseStyle}
                semanticWeight={semanticWeight[0]}
                systemPrompt={systemPrompt}
              />
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
