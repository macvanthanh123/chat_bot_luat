import { useState, useRef, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { MessageCircle, Send, Bot, User } from 'lucide-react';
import { Badge } from './ui/badge';

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  sources?: string[];
}

interface ChatInterfaceProps {
  uploadedDocuments: Array<{
    id: string;
    name: string;
    status: 'processing' | 'completed' | 'error';
  }>;
  temperature: number;
  maxTokens: number;
  useDocs: boolean;
  responseStyle: string;
  semanticWeight: number;
  systemPrompt: string;
  model: string;
  topK: number;
}

export function ChatInterface({ 
  uploadedDocuments,
  temperature,
  maxTokens,
  useDocs,
  responseStyle,
  semanticWeight,
  model,
  topK,
  systemPrompt, }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: 'Xin chào! Tôi là trợ lý AI chuyên về pháp luật Việt Nam. Tôi có thể giúp bạn:\n\n• Tra cứu văn bản pháp luật\n• Giải thích các điều khoản pháp lý\n• Tư vấn về quy trình pháp lý\n• Phân tích tài liệu đã tải lên\n\nBạn cần hỗ trợ gì?',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sampleResponses = [
    {
      content: 'Căn cứ vào Bộ luật Lao động 2019, thời gian làm việc bình thường không quá 8 giờ trong 1 ngày và 48 giờ trong 1 tuần. Người sử dụng lao động có quyền quy định thời giờ làm việc cụ thể trong ngày, tuần phù hợp với đặc điểm sản xuất, kinh doanh.\n\nThời giờ làm thêm được quy định tại Điều 107:\n• Không quá 50% số giờ làm việc bình thường trong 1 ngày\n• Tổng số giờ làm việc bình thường và làm thêm không quá 12 giờ/ngày\n• Tổng số giờ làm thêm không quá 40 giờ/tháng',
      sources: ['Bộ luật Lao động 2019 - Điều 106, 107'],
    },
    {
      content: 'Theo Luật Doanh nghiệp 2020, có 5 loại hình doanh nghiệp chính tại Việt Nam:\n\n1. Công ty trách nhiệm hữu hạn (TNHH)\n   - Công ty TNHH một thành viên\n   - Công ty TNHH hai thành viên trở lên\n\n2. Công ty cổ phần\n\n3. Công ty hợp danh\n\n4. Doanh nghiệp tư nhân\n\nMỗi loại hình có đặc điểm và yêu cầu pháp lý khác nhau về vốn điều lệ, trách nhiệm pháp lý và cơ cấu quản lý.',
      sources: ['Luật Doanh nghiệp 2020 - Điều 1'],
    },
    {
      content: 'Dựa trên tài liệu bạn đã tải lên, tôi có thể cung cấp phân tích chi tiết về các điều khoản liên quan. Tài liệu của bạn đề cập đến các quy định về hợp đồng và các nghĩa vụ pháp lý.\n\nCác điểm chính cần lưu ý:\n• Điều kiện hiệu lực của hợp đồng\n• Quyền và nghĩa vụ của các bên\n• Các trường hợp đình chỉ hoặc chấm dứt hợp đồng\n\nBạn muốn tôi giải thích chi tiết phần nào?',
      sources: uploadedDocuments.filter(d => d.status === 'completed').map(d => d.name),
    },
  ];

  const handleSend = () => {
  if (!inputValue.trim()) return;

  const userMessage: Message = {
    id: Date.now().toString(),
    type: 'user',
    content: inputValue,
    timestamp: new Date(),
  };

  setMessages((prev) => [...prev, userMessage]);
  setInputValue('');
  setIsTyping(true);

  setTimeout(async () => {
    try {

      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: inputValue, mode: "hybrid", top_k: topK, alpha: semanticWeight, model: model, prompt: systemPrompt})
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      console.log("Response data:", data);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: data.answer || "Không có phản hồi từ server.",
        timestamp: new Date(),
        sources: data.sources?.map((s: any) => s.title || JSON.stringify(s)) || [],
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 2).toString(),
          type: "bot",
          content: "Lỗi khi gọi API backend.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  }, 500);
};
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickQuestions = [
    'Quy định về thời gian làm việc',
    'Các loại hình doanh nghiệp',
    'Điều kiện hợp đồng lao động',
    'Quy trình thành lập công ty',
  ];
  console.log("Temperature:", temperature);
  console.log("Max Tokens:", maxTokens);
  console.log("Use Docs:", useDocs);
  console.log("Response Style:", responseStyle);
  console.log("Semantic Weight:", semanticWeight);
  console.log("System Prompt:", systemPrompt);
  console.log("Model:", model);
  console.log("Top K:", topK);
  return (
    <Card className="h-full flex flex-col bg-white shadow-lg border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-2 mb-2">
          <MessageCircle className="w-5 h-5 text-blue-600" />
          <h2 className="text-gray-900">Tư Vấn Pháp Luật</h2>
        </div>
        <p className="text-sm text-gray-500">Đặt câu hỏi về pháp luật Việt Nam</p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${
              message.type === 'user' ? 'flex-row-reverse' : 'flex-row'
            }`}
          >
            <div
              className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                message.type === 'user'
                  ? 'bg-gradient-to-br from-blue-600 to-indigo-600'
                  : 'bg-gradient-to-br from-emerald-500 to-teal-600'
              }`}
            >
              {message.type === 'user' ? (
                <User className="w-5 h-5 text-white" />
              ) : (
                <Bot className="w-5 h-5 text-white" />
              )}
            </div>
            <div
              className={`flex-1 max-w-[80%] ${
                message.type === 'user' ? 'flex flex-col items-end' : ''
              }`}
            >
              <div
                className={`rounded-lg p-4 ${
                  message.type === 'user'
                    ? 'bg-gradient-to-br from-blue-600 to-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {message.content}
                </p>
              </div>
              {message.sources && message.sources.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {message.sources.map((source, idx) => (
                    <Badge
                      key={idx}
                      variant="outline"
                      className="text-xs bg-blue-50 text-blue-700 border-blue-200"
                    >
                      {source}
                    </Badge>
                  ))}
                </div>
              )}
              <p className="text-xs text-gray-400 mt-1">
                {message.timestamp.toLocaleTimeString('vi-VN', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="bg-gray-100 rounded-lg p-4">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Questions */}
      {messages.length <= 1 && (
        <div className="px-6 py-3 border-t border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-600 mb-2">Câu hỏi gợi ý:</p>
          <div className="flex flex-wrap gap-2">
            {quickQuestions.map((question, idx) => (
              <Button
                key={idx}
                variant="outline"
                size="sm"
                onClick={() => setInputValue(question)}
                className="text-xs hover:bg-white hover:border-blue-400 hover:text-blue-600"
              >
                {question}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-6 border-t border-gray-200">
        <div className="flex gap-3">
          <Textarea
            placeholder="Nhập câu hỏi của bạn về pháp luật..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            className="resize-none min-h-[60px] max-h-[120px]"
            rows={2}
          />
          <Button
            onClick={handleSend}
            disabled={!inputValue.trim() || isTyping}
            className="bg-gradient-to-br from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-6"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Nhấn Enter để gửi, Shift + Enter để xuống dòng
        </p>
      </div>
    </Card>
  );
}
