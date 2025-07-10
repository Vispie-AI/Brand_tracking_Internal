import React, { useState, useCallback, useEffect } from 'react';
import { Upload, AlertCircle, CheckCircle, Download, BarChart, Users, Target, Eye } from 'lucide-react';

const BrandAnalyzerDashboard = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // 拖放处理
  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file && file.name.endsWith('.csv')) {
      setFile(file);
      setError(null);
    } else {
      setError('请选择 CSV 文件');
    }
  }, []);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('请选择 CSV 文件');
    }
  };

  // 文件上传
  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setTaskId(data.task_id);
        setStatus('processing');
      } else {
        const errorData = await response.json();
        setError(errorData.error || '上传失败');
      }
    } catch (error) {
      setError('网络错误：' + error.message);
    } finally {
      setUploading(false);
    }
  };

  // 轮询状态
  useEffect(() => {
    if (!taskId || !status || status === 'completed' || status === 'error') return;

    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/status?task_id=${taskId}`);
        const data = await response.json();
        
        setStatus(data.status);
        
        if (data.status === 'completed') {
          setResults(data.results);
        } else if (data.status === 'error') {
          setError(data.error);
        }
      } catch (error) {
        console.error('轮询状态错误:', error);
      }
    };

    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, [taskId, status]);

  // 获取日志
  useEffect(() => {
    if (!taskId) return;

    const fetchLogs = async () => {
      try {
        const response = await fetch(`/api/logs?task_id=${taskId}`);
        const data = await response.json();
        setLogs(data.logs || []);
      } catch (error) {
        console.error('获取日志错误:', error);
      }
    };

    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, [taskId]);

  // 下载文件
  const handleDownload = async (fileType) => {
    if (!taskId) return;

    try {
      const response = await fetch(`/api/download?task_id=${taskId}&file_type=${fileType}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${fileType}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('下载失败');
      }
    } catch (error) {
      setError('下载错误：' + error.message);
    }
  };

  const resetAnalysis = () => {
    setFile(null);
    setTaskId(null);
    setStatus(null);
    setLogs([]);
    setResults(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* 头部 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            TikTok 创作者品牌分析工具
          </h1>
          <p className="text-lg text-gray-600">
            上传创作者数据，智能分析品牌关联度并进行分类
          </p>
        </div>

        {/* 文件上传区域 */}
        {!taskId && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">上传数据文件</h2>
            
            <div 
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors cursor-pointer"
              onClick={() => document.getElementById('file-input').click()}
            >
              <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              {file ? (
                <div className="text-green-600">
                  <CheckCircle className="inline h-5 w-5 mr-2" />
                  已选择文件: {file.name}
                </div>
              ) : (
                <div>
                  <p className="text-gray-600 mb-2">点击选择或拖拽 CSV 文件到此处</p>
                  <p className="text-sm text-gray-500">支持的格式: .csv</p>
                </div>
              )}
            </div>

            <input
              id="file-input"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex">
                  <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
                  <span className="text-red-700">{error}</span>
                </div>
              </div>
            )}

            <div className="mt-6 flex justify-center">
              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {uploading ? '上传中...' : '开始分析'}
              </button>
            </div>
          </div>
        )}

        {/* 分析进度 */}
        {taskId && status !== 'completed' && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">分析进度</h2>
            
            <div className="flex items-center justify-between mb-4">
              <span className="text-gray-600">任务 ID: {taskId}</span>
              <span className={`px-3 py-1 rounded-full text-sm ${
                status === 'processing' ? 'bg-blue-100 text-blue-800' :
                status === 'error' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {status === 'processing' ? '分析中...' : status}
              </span>
            </div>

            {status === 'processing' && (
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
              </div>
            )}

            {/* 实时日志 */}
            {logs.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">处理日志:</h3>
                <div className="bg-gray-50 rounded border max-h-32 overflow-y-auto p-3">
                  {logs.map((log, index) => (
                    <div key={index} className="text-xs text-gray-600 mb-1">
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 分析结果 */}
        {results && (
          <div className="space-y-6">
            {/* 统计数据 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">分析结果统计</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <BarChart className="h-8 w-8 text-blue-600 mr-3" />
                    <div>
                      <p className="text-sm text-blue-600">总处理数</p>
                      <p className="text-2xl font-bold text-blue-900">{results.total_processed}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Target className="h-8 w-8 text-green-600 mr-3" />
                    <div>
                      <p className="text-sm text-green-600">品牌相关</p>
                      <p className="text-2xl font-bold text-green-900">{results.brand_related_count}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Users className="h-8 w-8 text-purple-600 mr-3" />
                    <div>
                      <p className="text-sm text-purple-600">非品牌账户</p>
                      <p className="text-2xl font-bold text-purple-900">{results.non_brand_count}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-orange-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Eye className="h-8 w-8 text-orange-600 mr-3" />
                    <div>
                      <p className="text-sm text-orange-600">处理成功率</p>
                      <p className="text-2xl font-bold text-orange-900">
                        {((results.total_processed / results.total_processed) * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* 品牌相关账户类型分布 */}
              {results.brand_type_stats && (
                <div className="border-t pt-4">
                  <h3 className="text-lg font-medium mb-3">品牌相关账户类型分布</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-red-50 p-3 rounded">
                      <p className="text-sm text-red-600">官方品牌账户</p>
                      <p className="text-xl font-bold text-red-900">
                        {results.brand_type_stats.is_brand_count} ({results.brand_type_stats.is_brand_percentage}%)
                      </p>
                    </div>
                    <div className="bg-yellow-50 p-3 rounded">
                      <p className="text-sm text-yellow-600">矩阵账户</p>
                      <p className="text-xl font-bold text-yellow-900">
                        {results.brand_type_stats.is_matrix_account_count} ({results.brand_type_stats.is_matrix_account_percentage}%)
                      </p>
                    </div>
                    <div className="bg-indigo-50 p-3 rounded">
                      <p className="text-sm text-indigo-600">UGC 创作者</p>
                      <p className="text-xl font-bold text-indigo-900">
                        {results.brand_type_stats.is_ugc_creator_count} ({results.brand_type_stats.is_ugc_creator_percentage}%)
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 下载区域 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">下载结果文件</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => handleDownload('brand_related')}
                  className="flex items-center justify-center bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Download className="h-5 w-5 mr-2" />
                  下载品牌相关数据
                </button>
                
                <button
                  onClick={() => handleDownload('non_brand')}
                  className="flex items-center justify-center bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Download className="h-5 w-5 mr-2" />
                  下载非品牌数据
                </button>
              </div>

              <div className="mt-6 text-center">
                <button
                  onClick={resetAnalysis}
                  className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  开始新的分析
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BrandAnalyzerDashboard; 