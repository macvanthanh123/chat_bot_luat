// ConfigExtractor.jsx
// File React chỉ để lấy toàn bộ cấu hình, KHÔNG có giao diện

import { useState } from 'react';

export default function useChatbotConfig() {
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2000);
  const [useDocs, setUseDocs] = useState(true);
  const [responseStyle, setResponseStyle] = useState('formal');
  const [semanticWeight, setSemanticWeight] = useState(0.7);
  const [model, setModel] = useState('gpt4');
  const [topK, setTopK] = useState(5);
  const [knowledgeSource, setKnowledgeSource] = useState('all');
  const [showSources, setShowSources] = useState(true);
  const [autoSuggest, setAutoSuggest] = useState(true);
  const [systemPrompt, setSystemPrompt] = useState(
    'Bạn là trợ lý AI chuyên về pháp luật Việt Nam. Nhiệm vụ của bạn là:\n\n1. Cung cấp thông tin chính xác về các văn bản pháp luật\n2. Giải thích các điều khoản pháp lý một cách dễ hiểu\n3. Trích dẫn nguồn từ các văn bản pháp luật có liên quan\n4. Tư vấn về quy trình pháp lý cơ bản\n\nLưu ý:\n- Luôn trích dẫn điều, khoản cụ thể\n- Sử dụng ngôn ngữ chuyên nghiệp nhưng dễ hiểu\n- Không đưa ra lời khuyên pháp lý cá nhân\n- Khuyến nghị tham khảo luật sư khi cần thiết'
  );

  // Hàm trả về toàn bộ cấu hình hiện tại
  const getConfig = () => ({
    model,
    temperature,
    maxTokens,
    useDocs,
    responseStyle,
    semanticWeight,
    topK,
    knowledgeSource,
    showSources,
    autoSuggest,
    systemPrompt,
  });

  return {
    // values
    model,
    temperature,
    maxTokens,
    useDocs,
    responseStyle,
    semanticWeight,
    topK,
    knowledgeSource,
    showSources,
    autoSuggest,
    systemPrompt,

    // setters
    setModel,
    setTemperature,
    setMaxTokens,
    setUseDocs,
    setResponseStyle,
    setSemanticWeight,
    setTopK,
    setKnowledgeSource,
    setShowSources,
    setAutoSuggest,
    setSystemPrompt,

    // main function để lấy toàn bộ config
    getConfig,
  };
}
