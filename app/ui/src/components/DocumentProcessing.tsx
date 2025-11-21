import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Upload, File, CheckCircle, AlertCircle, Loader2, Trash2 } from 'lucide-react';

interface Document {
  id: string;
  name: string;
  size: string;
  date: string;
  status: 'processing' | 'completed' | 'error';
}

interface Article {
  id: number;
  title: string;
  created_at: string;
}

interface DocumentProcessingProps {
  documents: Document[];
  setDocuments: (docs: Document[]) => void;
}

export function DocumentProcessing({ documents, setDocuments }: DocumentProcessingProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [existingArticles, setExistingArticles] = useState<Article[]>([]);
  const [searchTermArticles, setSearchTermArticles] = useState(''); // 🔹 thêm state search

  // Filter documents theo searchTerm
  const filteredDocuments = documents.filter(doc =>
    doc.name.toLowerCase().includes(searchTermArticles.toLowerCase())
  );

  // ===============================
  // Fetch existing articles từ DB
  // ===============================
  const fetchExistingArticles = async () => {
    try {
      const res = await fetch('http://localhost:8000/articles');
      const data = await res.json();
      setExistingArticles(data.articles || []);
    } catch (err) {
      console.error('Lỗi khi tải danh sách articles:', err);
    }
  };

  useEffect(() => {
    fetchExistingArticles();
  }, []);

  // ===============================
  // Upload documents
  // ===============================
  const handleProcessDocuments = async () => {
    const fileInput = document.getElementById('file-upload') as HTMLInputElement;
    if (!fileInput?.files || fileInput.files.length === 0) {
      alert('Vui lòng chọn ít nhất một file');
      return;
    }

    setIsProcessing(true);

    let completedCount = 0;
    const totalFiles = fileInput.files.length;

    Array.from(fileInput.files).forEach((file) => {
      const doc = documents.find((d) => d.name === file.name);
      if (!doc) {
        completedCount++;
        if (completedCount === totalFiles) setIsProcessing(false);
        return;
      }

      const formData = new FormData();
      formData.append('file', file);

      fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      })
        .then((response) => {
          if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
          return response.json();
        })
        .then((res) => {
          setDocuments((prev) =>
            prev.map((d) =>
              d.name === file.name ? { ...d, status: 'completed' } : d
            )
          );
          console.log('Upload thành công:', res);
          fetchExistingArticles(); // Reload danh sách articles sau khi upload
        })
        .catch((error) => {
          setDocuments((prev) =>
            prev.map((d) =>
              d.name === file.name ? { ...d, status: 'error' } : d
            )
          );
          console.error('Lỗi upload:', error.message);
        })
        .finally(() => {
          completedCount++;
          if (completedCount === totalFiles) setIsProcessing(false);
        });
    });
  };

  // ===============================
  // Drag & drop
  // ===============================
  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); };
  const handleDrop = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); handleFileUpload(e.dataTransfer.files); };

  const handleFileUpload = (files: FileList | null) => {
    if (!files) return;
    const newDocuments: Document[] = Array.from(files).map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: (file.size / 1024).toFixed(1) + ' KB',
      date: new Date().toLocaleDateString('vi-VN'),
      status: 'processing',
    }));
    setDocuments([...documents, ...newDocuments]);
  };

  const handleDeleteDocument = (id: string) => setDocuments(documents.filter((doc) => doc.id !== id));
  const handleDeleteArticle = async (id: number) => {
    try {
      const res = await fetch(`http://localhost:8000/docs/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      setExistingArticles(existingArticles.filter((art) => art.id !== id));
    } catch (err) { console.error('Lỗi khi xóa article:', err); }
  };

  const getStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'processing': return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-600" />;
    }
  };

  const getStatusText = (status: Document['status']) => {
    switch (status) {
      case 'processing': return 'Đang xử lý...';
      case 'completed': return 'Hoàn thành';
      case 'error': return 'Lỗi';
    }
  };

  return (
    <div className="space-y-6">

      {/* Search Input */}
      {documents.length > 0 && (
        <input
          type="text"
          placeholder="🔍 Tìm kiếm tài liệu..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-lg mb-3"
        />
      )}

      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
      >
        <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
        <p className="text-sm text-gray-700 mb-2">Kéo thả tài liệu vào đây</p>
        <p className="text-xs text-gray-500 mb-3">hoặc</p>
        <Button variant="outline" size="sm" onClick={() => document.getElementById('file-upload')?.click()} className="border-blue-600 text-blue-600 hover:bg-blue-50">
          Chọn tệp
        </Button>
        <input
          id="file-upload"
          type="file"
          multiple
          className="hidden"
          accept=".pdf,.doc,.docx,.txt"
          onChange={(e) => handleFileUpload(e.target.files)}
        />
        <p className="text-xs text-gray-500 mt-3">PDF, DOC, DOCX, TXT</p>
      </div>

      {/* Document List */}
      {filteredDocuments.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm text-gray-700">Tài liệu sắp upload ({filteredDocuments.length})</h3>
          {filteredDocuments.map((doc) => (
            <div key={doc.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
              <File className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900 truncate">{doc.name}</p>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-xs text-gray-500">{doc.size}</span>
                  <span className="text-xs text-gray-500">{doc.date}</span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  {getStatusIcon(doc.status)}
                  <span className="text-xs text-gray-600">{getStatusText(doc.status)}</span>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => handleDeleteDocument(doc.id)} className="text-gray-400 hover:text-red-600 hover:bg-red-50 h-8 w-8 p-0">
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          ))}

          <Button
            onClick={handleProcessDocuments}
            disabled={isProcessing || filteredDocuments.length === 0}
            className={`w-full mt-4 flex items-center justify-center gap-2 px-4 py-2 rounded-xl font-semibold transition-all duration-200 border-2 ${
              isProcessing
                ? 'bg-blue-300 cursor-not-allowed text-gray-700 border-blue-300'
                : 'bg-gradient-to-r from-blue-200 to-blue-400 text-gray-900 border-blue-400 shadow-lg'
            }`}
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin text-gray-700" />
                Đang xử lý...
              </>
            ) : (
              <>🚀 Xử lý tài liệu</>
            )}
          </Button>
        </div>
      )}

      {/*Existing Articles*/}
        {existingArticles.length > 0 && (
          <div className="bg-white border border-gray-300 rounded-xl p-4 shadow-sm">
            <h3 className="text-md font-semibold text-gray-800 mb-3">
              📚 Tài liệu đã có ({existingArticles.length})
            </h3>

            {/*Thanh tìm kiếm nằm trong khối*/}
            <input
              type="text"
              placeholder="🔍 Tìm kiếm tài liệu..."
              value={searchTermArticles}
              onChange={(e) => setSearchTermArticles(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg mb-3"
            />

            <div className="space-y-2">
              {existingArticles
                .filter((art) =>
                  art.title.toLowerCase().includes(searchTermArticles.toLowerCase())
                )
                .map((art) => (
                  <div
                    key={art.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-200 hover:border-gray-300 transition"
                  >
                    <div>
                      <p className="font-medium text-sm text-gray-900">{art.title}</p>
                      <p className="text-xs text-gray-500">
                        ID: {art.id} • {art.created_at ?? 'Không có ngày'}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-red-500 hover:bg-red-50"
                      onClick={() => handleDeleteArticle(art.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
            </div>
          </div>
        )}
    </div>
  );
}
