import { useState } from 'react';
import { Card } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { DocumentProcessing } from './DocumentProcessing';
import { Settings, FileText, Sliders } from 'lucide-react';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Slider } from './ui/slider';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';

interface Document {
  id: string;
  name: string;
  size: string;
  date: string;
  status: 'processing' | 'completed' | 'error';
}

interface ConfigPanelProps {
  documents: Document[];
  setDocuments: (docs: Document[]) => void;

  temperature: number[];
  setTemperature: (v: number[]) => void;

  topK: number[];
  setTopK: (v: number[]) => void;

  maxTokens: number[];
  setMaxTokens: (v: number[]) => void;

  useDocs: boolean;
  setUseDocs: (v: boolean) => void;

  model: string;
  setModel: (v: string) => void;

  responseStyle: string;
  setResponseStyle: (v: string) => void;

  semanticWeight: number[];
  setSemanticWeight: (v: number[]) => void;

  systemPrompt: string;
  setSystemPrompt: (v: string) => void;
}

export function ConfigPanel({ 
  documents,
  setDocuments,
  topK,
  setTopK,
  temperature,
  model,
  setModel,
  setTemperature,
  maxTokens,
  setMaxTokens,
  useDocs,
  setUseDocs,
  responseStyle,
  setResponseStyle,
  semanticWeight,
  setSemanticWeight,
  systemPrompt,
  setSystemPrompt,
}: ConfigPanelProps) {

  const handleResetPrompt = () => {
    setSystemPrompt(
      `Bạn là một trợ lý pháp lý thân thiện, lịch sự và trung thực của Việt Nam
Nhiệm vụ của bạn:
1. Nếu người dùng CHÀO HỎI → hãy trả lời chào hỏi tự nhiên, thân thiện.
2. Nếu người dùng hỏi VỀ PHÁP LUẬT → bạn chỉ được phép trả lời dựa trên TÀI LIỆU dưới đây (nếu có) và giải thích rõ ràng nếu người dùng cần, không hiểu.
3. Nếu câu hỏi KHÔNG LIÊN QUAN đến pháp luật → hãy lịch sự từ chối và nói rằng bạn chỉ hỗ trợ câu hỏi pháp luật.
4. Nếu không tìm thấy nội dung liên quan trong tài liệu → hãy trả lời:
"Tôi xin lỗi, tôi không có đủ thông tin trong tài liệu hiện tại để trả lời câu hỏi này."
`
    );
  };

  const isGPTModel = model === 'gpt4' || model === 'gpt3.5';

  return (
    <Card className="h-full bg-white shadow-lg border-gray-200 overflow-hidden flex flex-col">
      <div className="p-6 border-b border-gray-200 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-blue-600" />
          <h2 className="text-gray-900">Cấu Hình Chatbot</h2>
        </div>
        <p className="text-sm text-gray-500 mt-1">Tùy chỉnh và quản lý chatbot</p>
      </div>

      <Tabs defaultValue="documents" className="flex-1 flex flex-col min-h-0">
        <TabsList className="mx-6 mt-4 grid w-auto grid-cols-2 bg-gray-100">
          <TabsTrigger value="documents" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Tài liệu
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Sliders className="w-4 h-4" />
            Cài đặt
          </TabsTrigger>
        </TabsList>

        <TabsContent value="documents" className="flex-1 overflow-hidden m-0 mt-4">
          <div className="h-full px-6 pb-6 overflow-y-auto">
            <DocumentProcessing 
              documents={documents}
              setDocuments={setDocuments}
            />
          </div>
        </TabsContent>

        <TabsContent value="settings" className="flex-1 overflow-y-auto m-0 mt-4">
          <div className="px-6 pb-6 space-y-6">
            {/* Model Settings */}
            <div className="space-y-4">
              <h3 className="text-gray-900">Cấu hình mô hình AI</h3>
              
              <div className="space-y-2">
                <Label htmlFor="model">Mô hình ngôn ngữ</Label>
                <Select value={model} onValueChange={setModel} defaultValue="gemini-2.0-flash">
                  <SelectTrigger id="model">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gpt-4o-mini">GPT-4o-mini (Khuyến nghị)</SelectItem>
                    <SelectItem value="gemini-2.0-flash">Gemini 2.0 Flash</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Chỉ hiển thị Temperature khi chọn GPT */}
              {isGPTModel && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="temperature">Độ sáng tạo (Temperature)</Label>
                    <span className="text-sm text-gray-600">{temperature[0]}</span>
                  </div>
                  <Slider
                    id="temperature"
                    min={0}
                    max={1}
                    step={0.1}
                    value={temperature}
                    onValueChange={setTemperature}
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500">
                    Giá trị thấp: Chính xác hơn. Giá trị cao: Sáng tạo hơn
                  </p>
                </div>
              )}

            </div>

            {/* Hybrid Search Settings */}
            <div className="space-y-4 pt-4 border-t border-gray-200">
              <h3 className="text-gray-900">Cấu hình Hybrid Search</h3>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="semanticWeight">Trọng số tìm kiếm</Label>
                  <span className="text-sm text-gray-600">
                    {semanticWeight[0].toFixed(2)}
                  </span>
                </div>
                <Slider
                  id="semanticWeight"
                  min={0}
                  max={1}
                  step={0.05}
                  value={semanticWeight}
                  onValueChange={setSemanticWeight}
                  className="w-full"
                />
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600">
                    Keyword Search ({(1 - semanticWeight[0]).toFixed(2)})
                  </span>
                  <span className="text-gray-600">
                    Semantic Search ({semanticWeight[0].toFixed(2)})
                  </span>
                </div>
                <p className="text-xs text-gray-500">
                  Cân bằng giữa tìm kiếm từ khóa chính xác và tìm kiếm theo ngữ nghĩa
                </p>
              </div>

              <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-xs text-blue-900 mb-2">
                  <strong>Keyword Search:</strong> Tìm kiếm từ khóa chính xác trong tài liệu
                </p>
                <p className="text-xs text-blue-900">
                  <strong>Semantic Search:</strong> Tìm kiếm theo ngữ nghĩa và ý nghĩa
                </p>
              </div>

              <div className="space-y-2">
                <label htmlFor="topK" className="text-sm font-medium">
                  Top K: {topK[0]}
                </label>
                <Slider
                  id="topK"
                  min={1}
                  max={20}
                  step={1}
                  value={topK}
                  onValueChange={(v: number | number[]) =>
                    setTopK(Array.isArray(v) ? v : [v])
                  }
                  className="w-full"
                />
              </div>
            </div>

            {/* Prompt Settings */}
            <div className="space-y-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-gray-900">Cấu hình System Prompt</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleResetPrompt}
                  className="text-xs"
                >
                  Đặt lại mặc định
                </Button>
              </div>

              <div className="space-y-2">
                <Label htmlFor="systemPrompt">System Prompt</Label>
                <Textarea
                  id="systemPrompt"
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  className="min-h-[200px] resize-none text-sm"
                  placeholder="Nhập hướng dẫn cho AI..."
                />
                <p className="text-xs text-gray-500">
                  Định nghĩa vai trò, nhiệm vụ và cách thức trả lời của chatbot
                </p>
              </div>

              <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                <p className="text-xs text-amber-900">
                  <strong>Lưu ý:</strong> System prompt ảnh hưởng trực tiếp đến cách chatbot phản hồi. Hãy mô tả rõ ràng vai trò và yêu cầu.
                </p>
              </div>
            </div>

            {/* Response Settings */}
            <div className="space-y-4 pt-4 border-t border-gray-200">
              <h3 className="text-gray-900">Cấu hình câu trả lời</h3>

              <div className="space-y-2">
                <Label htmlFor="style">Phong cách trả lời</Label>
                <Select value={responseStyle} onValueChange={setResponseStyle}>
                  <SelectTrigger id="style">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="formal">Chính thức - Pháp lý</SelectItem>
                    <SelectItem value="friendly">Thân thiện - Dễ hiểu</SelectItem>
                    <SelectItem value="detailed">Chi tiết - Chuyên sâu</SelectItem>
                    <SelectItem value="concise">Ngắn gọn - Súc tích</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              

              <div className="flex items-center justify-between py-3">
                <div className="space-y-0.5">
                  <Label htmlFor="show-sources">Hiển thị nguồn tham khảo</Label>
                  <p className="text-xs text-gray-500">
                    Hiện điều luật và văn bản liên quan
                  </p>
                </div>
                <Switch id="show-sources" defaultChecked />
              </div>

              <div className="flex items-center justify-between py-3">
                <div className="space-y-0.5">
                  <Label htmlFor="auto-suggest">Câu hỏi gợi ý</Label>
                  <p className="text-xs text-gray-500">
                    Tự động đề xuất câu hỏi liên quan
                  </p>
                </div>
                <Switch id="auto-suggest" defaultChecked />
              </div>
            </div>

            {/* Knowledge Base */}
            <div className="space-y-4 pt-4 border-t border-gray-200">
              <h3 className="text-gray-900">Cơ sở tri thức</h3>

              <div className="space-y-2">
                <Label htmlFor="knowledge">Nguồn pháp luật</Label>
                <Select defaultValue="all">
                  <SelectTrigger id="knowledge">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tất cả lĩnh vực</SelectItem>
                    <SelectItem value="labor">Luật Lao động</SelectItem>
                    <SelectItem value="business">Luật Doanh nghiệp</SelectItem>
                    <SelectItem value="civil">Luật Dân sự</SelectItem>
                    <SelectItem value="criminal">Luật Hình sự</SelectItem>
                    <SelectItem value="administrative">Luật Hành chính</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm text-blue-900 mb-1">
                      {documents.filter(d => d.status === 'completed').length} tài liệu đã xử lý
                    </p>
                    <p className="text-xs text-blue-700">
                      Chatbot sẽ sử dụng các tài liệu này để cung cấp câu trả lời chính xác hơn
                    </p>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
}
