import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Upload, AlertCircle, CheckCircle, Download, BarChart, Users, Target, Eye, Settings } from 'lucide-react';

// API 配置
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

const BrandAnalyzerDashboard = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState('');
  const [logs, setLogs] = useState([]);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [useMockData, setUseMockData] = useState(false);
  const logsContainerRef = useRef(null);

  // 模拟数据 - 基于实际数据结构
  const mockResults = {
    total_processed: 397,
    brand_related_count: 346,
    non_brand_count: 51,
    // 各类型在总创作者中的数量和百分比
    official_account_count: 35,
    matrix_account_count: 50,
    ugc_creator_count: 216,
    non_branded_creator_count: 51,
    official_account_percentage: Math.round((35 / 397) * 100), // 9%
    matrix_account_percentage: Math.round((50 / 397) * 100), // 13%
    ugc_creator_percentage: Math.round((216 / 397) * 100), // 54%
    non_branded_creator_percentage: Math.round((51 / 397) * 100), // 13%
    // Brand Related Breakdown - 在品牌相关账号中的数量和百分比
    brand_in_related: 35,
    matrix_in_related: 50,
    ugc_in_related: 216,
    brand_in_related_percentage: Math.round((35 / 346) * 100), // 10%
    matrix_in_related_percentage: Math.round((50 / 346) * 100), // 14%
    ugc_in_related_percentage: Math.round((216 / 346) * 100), // 62%
    brand_file: 'brand_related_creators.csv',
    non_brand_file: 'non_brand_creators.csv'
  };

  const mockLogs = [
    'File uploaded successfully',
    'Starting creator data analysis...',
    'Loading 438 creators from JSON file...',
    'Processing creator profiles (batch 1/13)...',
    'Analyzing brand associations with Gemini AI...',
    'Processing creator profiles (batch 5/13)...',
    'Classifying creators by type...',
    'Processing creator profiles (batch 10/13)...',
    'Found 182 brand-related accounts (50 official, 22 matrix, 110 UGC)...',
    'Processing creator profiles (batch 13/13)...',
    'Generating CSV reports...',
    'Analysis completed successfully! Total processed: 438'
  ];
  const [useMockData, setUseMockData] = useState(false);
  const logsContainerRef = useRef(null);

  // 模拟数据 - 基于实际数据结构
  const mockResults = {
    total_processed: 397,
    brand_related_count: 346,
    non_brand_count: 51,
    // 各类型在总创作者中的数量和百分比
    official_account_count: 35,
    matrix_account_count: 50,
    ugc_creator_count: 216,
    non_branded_creator_count: 51,
    official_account_percentage: Math.round((35 / 397) * 100), // 9%
    matrix_account_percentage: Math.round((50 / 397) * 100), // 13%
    ugc_creator_percentage: Math.round((216 / 397) * 100), // 54%
    non_branded_creator_percentage: Math.round((51 / 397) * 100), // 13%
    // Brand Related Breakdown - 在品牌相关账号中的数量和百分比
    brand_in_related: 35,
    matrix_in_related: 50,
    ugc_in_related: 216,
    brand_in_related_percentage: Math.round((35 / 346) * 100), // 10%
    matrix_in_related_percentage: Math.round((50 / 346) * 100), // 14%
    ugc_in_related_percentage: Math.round((216 / 346) * 100), // 62%
    brand_file: 'brand_related_creators.csv',
    non_brand_file: 'non_brand_creators.csv'
  };

  const mockLogs = [
    'File uploaded successfully',
    'Starting creator data analysis...',
    'Loading 438 creators from JSON file...',
    'Processing creator profiles (batch 1/13)...',
    'Analyzing brand associations with Gemini AI...',
    'Processing creator profiles (batch 5/13)...',
    'Classifying creators by type...',
    'Processing creator profiles (batch 10/13)...',
    'Found 182 brand-related accounts (50 official, 22 matrix, 110 UGC)...',
    'Processing creator profiles (batch 13/13)...',
    'Generating CSV reports...',
    'Analysis completed successfully! Total processed: 438'
  ];

  // 拖放处理
  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file && file.name.endsWith('.json')) {
      setFile(file);
      setError(null);
    } else {
      setError('Please select a JSON file');
      setError('Please select a JSON file');
    }
  }, []);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && (selectedFile.name.endsWith('.json') || selectedFile.name.endsWith('.csv'))) {
    if (selectedFile && (selectedFile.name.endsWith('.json') || selectedFile.name.endsWith('.csv'))) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a JSON or CSV file');
      setError('Please select a JSON or CSV file');
    }
  };



  // 模拟文件上传处理
  const simulateUpload = async () => {
    setUploading(true);
    setError(null);
    
    // 模拟上传延迟
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const mockTaskId = 'mock_task_' + Date.now();
    setTaskId(mockTaskId);
    setStatus('processing');
    setUploading(false);

    // 模拟处理过程
    let logIndex = 0;
    const interval = setInterval(() => {
      if (logIndex < mockLogs.length) {
        const logMessage = mockLogs[logIndex];
        if (logMessage) { // 确保日志消息存在
          setLogs(prev => [...prev, logMessage]);
        }
        logIndex++;
      } else {
        clearInterval(interval);
        setStatus('completed');
        setResults(mockResults);
      }
    }, 800);
  };

  // 真实文件上传处理
  const handleRealUpload = async () => {


  // 模拟文件上传处理
  const simulateUpload = async () => {
    setUploading(true);
    setError(null);
    
    // 模拟上传延迟
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const mockTaskId = 'mock_task_' + Date.now();
    setTaskId(mockTaskId);
    setStatus('processing');
    setUploading(false);

    // 模拟处理过程
    let logIndex = 0;
    const interval = setInterval(() => {
      if (logIndex < mockLogs.length) {
        const logMessage = mockLogs[logIndex];
        if (logMessage) { // 确保日志消息存在
          setLogs(prev => [...prev, logMessage]);
        }
        logIndex++;
      } else {
        clearInterval(interval);
        setStatus('completed');
        setResults(mockResults);
      }
    }, 800);
  };

  // 真实文件上传处理
  const handleRealUpload = async () => {
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setTaskId(data.task_id);
        setStatus('processing');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Upload failed');
        setError(errorData.error || 'Upload failed');
      }
    } catch (error) {
      setError('Network error: ' + error.message);
      setError('Network error: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  // 文件上传
  const handleUpload = async () => {
    if (!file) return;

    if (useMockData) {
      // 演示模式使用模拟数据
      await simulateUpload();
    } else {
      // 真实分析模式
      await handleRealUpload();
    }
  };

  // 轮询状态（仅在真实分析模式下）
  // 文件上传
  const handleUpload = async () => {
    if (!file) return;

    if (useMockData) {
      // 演示模式使用模拟数据
      await simulateUpload();
    } else {
      // 真实分析模式
      await handleRealUpload();
    }
  };

  // 轮询状态（仅在真实分析模式下）
  useEffect(() => {
    if (useMockData || !taskId || status === 'completed' || status === 'error') return;
    if (useMockData || !taskId || status === 'completed' || status === 'error') return;

    const pollStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/status?task_id=${taskId}`);
        
        if (response.status === 404) {
          // 任务不存在，可能已经被清理，停止轮询
          console.warn('Task not found, stopping polling');
          setStatus('error');
          setError('分析任务已过期或被清理，请重新上传文件');
          return;
        }
        
        const data = await response.json();
        
        setStatus(data.status);
        setProgress(data.progress || '');
        
        if (data.status === 'completed') {
          // 映射后端数据结构到前端期望的格式
          const backendResults = data.results;
          if (backendResults) {
            const mappedResults = {
              total_processed: backendResults.total_processed || 0,
              brand_related_count: backendResults.brand_related_count || 0,
              non_brand_count: backendResults.non_brand_count || 0,
              // 各类型在总创作者中的数量
              official_account_count: backendResults.official_account_count || 0,
              matrix_account_count: backendResults.matrix_account_count || 0,
              ugc_creator_count: backendResults.ugc_creator_count || 0,
              non_branded_creator_count: backendResults.non_branded_creator_count || 0,
              // 各类型在总创作者中的百分比
              official_account_percentage: backendResults.official_account_percentage || 0,
              matrix_account_percentage: backendResults.matrix_account_percentage || 0,
              ugc_creator_percentage: backendResults.ugc_creator_percentage || 0,
              non_branded_creator_percentage: backendResults.non_branded_creator_percentage || 0,
              // Brand Related Breakdown - 在品牌相关账号中的数量和百分比
              brand_in_related: backendResults.brand_in_related || 0,
              matrix_in_related: backendResults.matrix_in_related || 0,
              ugc_in_related: backendResults.ugc_in_related || 0,
              brand_in_related_percentage: backendResults.brand_in_related_percentage || 0,
              matrix_in_related_percentage: backendResults.matrix_in_related_percentage || 0,
              ugc_in_related_percentage: backendResults.ugc_in_related_percentage || 0,
              brand_file: backendResults.brand_file,
              non_brand_file: backendResults.non_brand_file
            };
            setResults(mappedResults);
          }
          // 映射后端数据结构到前端期望的格式
          const backendResults = data.results;
          if (backendResults) {
            const mappedResults = {
              total_processed: backendResults.total_processed || 0,
              brand_related_count: backendResults.brand_related_count || 0,
              non_brand_count: backendResults.non_brand_count || 0,
              // 各类型在总创作者中的数量
              official_account_count: backendResults.official_account_count || 0,
              matrix_account_count: backendResults.matrix_account_count || 0,
              ugc_creator_count: backendResults.ugc_creator_count || 0,
              non_branded_creator_count: backendResults.non_branded_creator_count || 0,
              // 各类型在总创作者中的百分比
              official_account_percentage: backendResults.official_account_percentage || 0,
              matrix_account_percentage: backendResults.matrix_account_percentage || 0,
              ugc_creator_percentage: backendResults.ugc_creator_percentage || 0,
              non_branded_creator_percentage: backendResults.non_branded_creator_percentage || 0,
              // Brand Related Breakdown - 在品牌相关账号中的数量和百分比
              brand_in_related: backendResults.brand_in_related || 0,
              matrix_in_related: backendResults.matrix_in_related || 0,
              ugc_in_related: backendResults.ugc_in_related || 0,
              brand_in_related_percentage: backendResults.brand_in_related_percentage || 0,
              matrix_in_related_percentage: backendResults.matrix_in_related_percentage || 0,
              ugc_in_related_percentage: backendResults.ugc_in_related_percentage || 0,
              brand_file: backendResults.brand_file,
              non_brand_file: backendResults.non_brand_file
            };
            setResults(mappedResults);
          }
        } else if (data.status === 'error') {
          setError(data.progress || data.error || '分析过程中发生错误');
          setError(data.progress || data.error || '分析过程中发生错误');
        }
      } catch (error) {
        console.error('Status polling error:', error);
        // 如果轮询出错多次，停止轮询
        setError('无法获取分析状态，请刷新页面重试');
        console.error('Status polling error:', error);
        // 如果轮询出错多次，停止轮询
        setError('无法获取分析状态，请刷新页面重试');
      }
    };

    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, [taskId, status, useMockData]);
  }, [taskId, status, useMockData]);

  // 获取日志（仅在真实分析模式下）
  // 获取日志（仅在真实分析模式下）
  useEffect(() => {
    if (useMockData || !taskId || status === 'completed' || status === 'error') return;
    if (useMockData || !taskId || status === 'completed' || status === 'error') return;

    const fetchLogs = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/logs?task_id=${taskId}`);
        
        if (response.status === 404) {
          // 任务不存在，停止获取日志
          console.warn('Task not found for logs, stopping log fetching');
          return;
        }
        
        const data = await response.json();
        if (data.logs) {
          // 处理不同格式的日志
          const processedLogs = data.logs.map(log => {
            if (typeof log === 'string') return log;
            if (log && typeof log === 'object' && log.message) return log.message;
            return log ? JSON.stringify(log) : '';
          }).filter(log => log.trim());
          
          setLogs(processedLogs);
        }
        if (data.logs) {
          // 处理不同格式的日志
          const processedLogs = data.logs.map(log => {
            if (typeof log === 'string') return log;
            if (log && typeof log === 'object' && log.message) return log.message;
            return log ? JSON.stringify(log) : '';
          }).filter(log => log.trim());
          
          setLogs(processedLogs);
        }
      } catch (error) {
        console.error('Fetch logs error:', error);
        console.error('Fetch logs error:', error);
      }
    };

    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, [taskId, useMockData, status]);

  // 自动滚动日志到底部（分析进行中时滚动）
  useEffect(() => {
    if (logsContainerRef.current && logs.length > 0 && status && status !== 'completed' && status !== 'error') {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [logs, status]);
  }, [taskId, useMockData, status]);

  // 自动滚动日志到底部（分析进行中时滚动）
  useEffect(() => {
    if (logsContainerRef.current && logs.length > 0 && status && status !== 'completed' && status !== 'error') {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [logs, status]);

  // 下载文件
  const handleDownload = async (fileType) => {
    if (!taskId) return;

    if (useMockData) {
      // 演示模式下模拟下载
      const filename = fileType === 'brand_related' ? 'brand_related_creators.csv' : 'non_brand_creators.csv';
      const csvContent = `author_unique_id,signature,is_brand,brand_name,author_followers_count
test_creator_1,AI Tools Reviewer,false,,100000
test_creator_2,Official Brand Account,true,Test Brand,50000
test_creator_3,Tech Enthusiast,false,,25000`;
      
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/download?task_id=${taskId}&file_type=${fileType}`);
      
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
        setError('Download failed');
        setError('Download failed');
      }
    } catch (error) {
      setError('Download error: ' + error.message);
      setError('Download error: ' + error.message);
    }
  };

  const resetAnalysis = () => {
    setFile(null);
    setTaskId(null);
    setStatus(null);
    setProgress('');
    setLogs([]);
    setResults(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="w-full max-w-full mx-auto">
        {/* 头部 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            TikTok Creator Brand Analysis Tool
            TikTok Creator Brand Analysis Tool
          </h1>
          <p className="text-lg text-gray-600">
            Upload creator data, intelligently analyze brand associations and classify creators
            Upload creator data, intelligently analyze brand associations and classify creators
          </p>
        </div>

        {/* 分析模式选择 */}
        {!taskId && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              Analysis Mode
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div 
                className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  !useMockData ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                }`}
                onClick={() => setUseMockData(false)}
              >
                <div className="flex items-center mb-2">
                  <input
                    type="radio"
                    checked={!useMockData}
                    onChange={() => setUseMockData(false)}
                    className="mr-3"
                  />
                  <h3 className="text-lg font-medium text-gray-900">Real Analysis</h3>
                </div>
                <p className="text-sm text-gray-600">
                  Upload your JSON file for actual AI-powered brand analysis. 
                  This will use Gemini AI to analyze creator profiles and classify them.
                  <span className="block mt-1 font-medium text-green-600">
                    ✓ Real results ✓ AI analysis ✓ Downloadable reports
                  </span>
                </p>
              </div>

              <div 
                className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  useMockData ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                }`}
                onClick={() => setUseMockData(true)}
              >
                <div className="flex items-center mb-2">
                  <input
                    type="radio"
                    checked={useMockData}
                    onChange={() => setUseMockData(true)}
                    className="mr-3"
                  />
                  <h3 className="text-lg font-medium text-gray-900">Demo Mode</h3>
                </div>
                <p className="text-sm text-gray-600">
                  Quick demonstration with sample data. 
                  See how the interface works without running actual analysis.
                  <span className="block mt-1 font-medium text-orange-600">
                    ⚡ Fast demo ⚡ Sample data ⚡ UI preview
                  </span>
                </p>
              </div>
            </div>

            {!useMockData && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-sm text-yellow-700">
                  <strong>Note:</strong> Real analysis mode requires Python environment and may take several minutes to complete. 
                  The system will use Gemini AI to analyze each creator profile.
                </p>
              </div>
            )}
          </div>
        )}

        {/* 分析模式选择 */}
        {!taskId && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              Analysis Mode
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div 
                className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  !useMockData ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                }`}
                onClick={() => setUseMockData(false)}
              >
                <div className="flex items-center mb-2">
                  <input
                    type="radio"
                    checked={!useMockData}
                    onChange={() => setUseMockData(false)}
                    className="mr-3"
                  />
                  <h3 className="text-lg font-medium text-gray-900">Real Analysis</h3>
                </div>
                <p className="text-sm text-gray-600">
                  Upload your JSON file for actual AI-powered brand analysis. 
                  This will use Gemini AI to analyze creator profiles and classify them.
                  <span className="block mt-1 font-medium text-green-600">
                    ✓ Real results ✓ AI analysis ✓ Downloadable reports
                  </span>
                </p>
              </div>

              <div 
                className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  useMockData ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                }`}
                onClick={() => setUseMockData(true)}
              >
                <div className="flex items-center mb-2">
                  <input
                    type="radio"
                    checked={useMockData}
                    onChange={() => setUseMockData(true)}
                    className="mr-3"
                  />
                  <h3 className="text-lg font-medium text-gray-900">Demo Mode</h3>
                </div>
                <p className="text-sm text-gray-600">
                  Quick demonstration with sample data. 
                  See how the interface works without running actual analysis.
                  <span className="block mt-1 font-medium text-orange-600">
                    ⚡ Fast demo ⚡ Sample data ⚡ UI preview
                  </span>
                </p>
              </div>
            </div>

            {!useMockData && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-sm text-yellow-700">
                  <strong>Note:</strong> Real analysis mode requires Python environment and may take several minutes to complete. 
                  The system will use Gemini AI to analyze each creator profile.
                </p>
              </div>
            )}
          </div>
        )}

        {/* 文件上传区域 */}
        {!taskId && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Upload Data File</h2>
            <h2 className="text-xl font-semibold mb-4">Upload Data File</h2>
            
            <div 
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors cursor-pointer"
              onClick={() => document.getElementById('file-input').click()}
            >
              <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              {file ? (
                <div className="text-green-600">
                  <CheckCircle className="inline h-5 w-5 mr-2" />
                  Selected file: {file.name}
                  Selected file: {file.name}
                </div>
              ) : (
                <div>
                  <p className="text-gray-600 mb-2">Click to select or drag and drop JSON or CSV file here</p>
                  <p className="text-sm text-gray-500">
                    Supported formats: .json, .csv (e.g., creator_list.json, backsheet.csv)
                  </p>
                  <p className="text-xs text-gray-400 mt-2">
                    JSON: author_unique_id, signature, video_description, author_follower_count<br/>
                    CSV: video link, creator handler (TikTok URL format)
                  </p>
                  <p className="text-gray-600 mb-2">Click to select or drag and drop JSON or CSV file here</p>
                  <p className="text-sm text-gray-500">
                    Supported formats: .json, .csv (e.g., creator_list.json, backsheet.csv)
                  </p>
                  <p className="text-xs text-gray-400 mt-2">
                    JSON: author_unique_id, signature, video_description, author_follower_count<br/>
                    CSV: video link, creator handler (TikTok URL format)
                  </p>
                </div>
              )}
            </div>

            <input
              id="file-input"
              type="file"
              accept=".json,.csv"
              accept=".json,.csv"
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
                {uploading ? 'Uploading...' : useMockData ? 'Start Demo Analysis' : 'Start Real Analysis'}
                {uploading ? 'Uploading...' : useMockData ? 'Start Demo Analysis' : 'Start Real Analysis'}
              </button>
            </div>
          </div>
        )}

        {/* Analysis Progress */}
        {taskId && (
        {/* Analysis Progress */}
        {taskId && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Analysis Progress</h2>
              <div className="flex items-center space-x-4">
              <h2 className="text-xl font-semibold">Analysis Progress</h2>
              <div className="flex items-center space-x-4">
              <span className={`px-3 py-1 rounded-full text-sm ${
                  useMockData ? 'bg-orange-100 text-orange-800' : 'bg-green-100 text-green-800'
                  useMockData ? 'bg-orange-100 text-orange-800' : 'bg-green-100 text-green-800'
              }`}>
                  {useMockData ? 'Demo Mode' : 'Real Analysis'}
                  {useMockData ? 'Demo Mode' : 'Real Analysis'}
              </span>
                {status === 'completed' && (
                  <button
                    onClick={resetAnalysis}
                    className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    New Analysis
                  </button>
                )}
              </div>
                {status === 'completed' && (
                  <button
                    onClick={resetAnalysis}
                    className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    New Analysis
                  </button>
                )}
              </div>
            </div>

            {/* Processing Status */}
            <div className="mb-4">
              <div className="flex items-center">
            {/* Processing Status */}
            <div className="mb-4">
              <div className="flex items-center">
            {status === 'processing' && (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
                )}
                {status === 'completed' && (
                  <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
                )}
                {status === 'error' && (
                  <AlertCircle className="h-5 w-5 text-red-600 mr-3" />
                )}
                <span className="text-gray-800">
                  Status: {status === 'processing' && 'Processing...'}
                  {status === 'completed' && 'Analysis Completed'}
                  {status === 'error' && 'Analysis Failed'}
                  {status === 'running' && 'Analysis Running...'}
                  {status === 'pending' && 'Pending...'}
                </span>
              </div>
              
              {/* 显示错误信息 */}
              {error && (
                <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex">
                    <AlertCircle className="h-5 w-5 text-red-400 mr-2 mt-0.5" />
                    <div>
                      <p className="text-sm text-red-800">{error}</p>
                      <button
                        onClick={resetAnalysis}
                        className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                      >
                        重新开始分析
                      </button>
                    </div>
                  </div>
              </div>
            )}
            </div>
            </div>

            {/* Processing Logs */}
            {/* Processing Logs */}
            {logs.length > 0 && (
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Processing Logs:</h3>
                <div 
                  ref={logsContainerRef}
                  className="max-h-40 overflow-y-auto scroll-smooth"
                >
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Processing Logs:</h3>
                <div 
                  ref={logsContainerRef}
                  className="max-h-40 overflow-y-auto scroll-smooth"
                >
                  {logs.map((log, index) => (
                    <div key={index} className="text-xs text-gray-600 font-mono mb-1">
                      {typeof log === 'string' ? log : 
                       (log && typeof log === 'object' && log.message) ? log.message : 
                       log ? JSON.stringify(log) : ''}
                    <div key={index} className="text-xs text-gray-600 font-mono mb-1">
                      {typeof log === 'string' ? log : 
                       (log && typeof log === 'object' && log.message) ? log.message : 
                       log ? JSON.stringify(log) : ''}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Analysis Results */}
        {/* Analysis Results */}
        {results && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-6">Analysis Results</h2>
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-6">Analysis Results</h2>
              
            {/* Statistics Cards - 两排显示，每排3个 */}
            <div className="space-y-4 mb-6">
              {/* 第一排 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Statistics Cards - 两排显示，每排3个 */}
            <div className="space-y-4 mb-6">
              {/* 第一排 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Users className="h-8 w-8 text-blue-600 mr-3" />
                    <Users className="h-8 w-8 text-blue-600 mr-3" />
                    <div>
                      <p className="text-sm text-gray-600">Total Creators</p>
                      <p className="text-2xl font-bold text-blue-600">{results.total_processed}</p>
                      <p className="text-sm text-gray-600">Total Creators</p>
                      <p className="text-2xl font-bold text-blue-600">{results.total_processed}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Target className="h-8 w-8 text-green-600 mr-3" />
                    <div>
                      <p className="text-sm text-gray-600">Brand Related</p>
                      <p className="text-2xl font-bold text-green-600">
                        {results.brand_related_count} ({Math.round((results.brand_related_count / results.total_processed) * 100)}%)
                      </p>
                      <p className="text-sm text-gray-600">Brand Related</p>
                      <p className="text-2xl font-bold text-green-600">
                        {results.brand_related_count} ({Math.round((results.brand_related_count / results.total_processed) * 100)}%)
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <BarChart className="h-8 w-8 text-purple-600 mr-3" />
                    <div>
                      <p className="text-sm text-gray-600">Official Account</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {results.official_account_count} ({results.official_account_percentage}%)
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* 第二排 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-red-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Settings className="h-8 w-8 text-red-600 mr-3" />
                    <BarChart className="h-8 w-8 text-purple-600 mr-3" />
                    <div>
                      <p className="text-sm text-gray-600">Official Account</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {results.official_account_count} ({results.official_account_percentage}%)
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* 第二排 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-red-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Settings className="h-8 w-8 text-red-600 mr-3" />
                    <div>
                      <p className="text-sm text-gray-600">Matrix Account</p>
                      <p className="text-2xl font-bold text-red-600">
                        {results.matrix_account_count} ({results.matrix_account_percentage}%)
                      </p>
                      <p className="text-sm text-gray-600">Matrix Account</p>
                      <p className="text-2xl font-bold text-red-600">
                        {results.matrix_account_count} ({results.matrix_account_percentage}%)
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-orange-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Eye className="h-8 w-8 text-orange-600 mr-3" />
                    <div>
                      <p className="text-sm text-gray-600">UGC Creators</p>
                      <p className="text-2xl font-bold text-orange-600">
                        {results.ugc_creator_count} ({results.ugc_creator_percentage}%)
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Users className="h-8 w-8 text-gray-600 mr-3" />
                    <div>
                      <p className="text-sm text-gray-600">Non-branded Creator</p>
                      <p className="text-2xl font-bold text-gray-600">
                        {results.non_branded_creator_count} ({results.non_branded_creator_percentage}%)
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
                      <p className="text-sm text-gray-600">UGC Creators</p>
                      <p className="text-2xl font-bold text-orange-600">
                        {results.ugc_creator_count} ({results.ugc_creator_percentage}%)
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Users className="h-8 w-8 text-gray-600 mr-3" />
                    <div>
                      <p className="text-sm text-gray-600">Non-branded Creator</p>
                      <p className="text-2xl font-bold text-gray-600">
                        {results.non_branded_creator_count} ({results.non_branded_creator_percentage}%)
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Brand Related Breakdown */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <h3 className="text-lg font-medium mb-3">Brand Related Breakdown</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-sm text-gray-600">Official Account</p>
                  <p className="text-lg font-bold text-purple-600">{results.brand_in_related}</p>
                  <p className="text-xs text-gray-500">({results.brand_in_related_percentage}% of brand related)</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Matrix Account</p>
                  <p className="text-lg font-bold text-red-600">{results.matrix_in_related}</p>
                  <p className="text-xs text-gray-500">({results.matrix_in_related_percentage}% of brand related)</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">UGC Creator</p>
                  <p className="text-lg font-bold text-orange-600">{results.ugc_in_related}</p>
                  <p className="text-xs text-gray-500">({results.ugc_in_related_percentage}% of brand related)</p>
                </div>
              </div>
            {/* Brand Related Breakdown */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <h3 className="text-lg font-medium mb-3">Brand Related Breakdown</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-sm text-gray-600">Official Account</p>
                  <p className="text-lg font-bold text-purple-600">{results.brand_in_related}</p>
                  <p className="text-xs text-gray-500">({results.brand_in_related_percentage}% of brand related)</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Matrix Account</p>
                  <p className="text-lg font-bold text-red-600">{results.matrix_in_related}</p>
                  <p className="text-xs text-gray-500">({results.matrix_in_related_percentage}% of brand related)</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">UGC Creator</p>
                  <p className="text-lg font-bold text-orange-600">{results.ugc_in_related}</p>
                  <p className="text-xs text-gray-500">({results.ugc_in_related_percentage}% of brand related)</p>
                </div>
              </div>
                    </div>

            {/* Distribution */}
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-3">Category Distribution</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Brand Related Accounts</p>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className="bg-green-600 h-3 rounded-full" 
                      style={{width: `${(results.brand_related_count / results.total_processed) * 100}%`}}
                    ></div>

            {/* Distribution */}
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-3">Category Distribution</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Brand Related Accounts</p>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className="bg-green-600 h-3 rounded-full" 
                      style={{width: `${(results.brand_related_count / results.total_processed) * 100}%`}}
                    ></div>
                    </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {results.brand_related_count} / {results.total_processed} 
                    ({Math.round((results.brand_related_count / results.total_processed) * 100)}%)
                  <p className="text-xs text-gray-500 mt-1">
                    {results.brand_related_count} / {results.total_processed} 
                    ({Math.round((results.brand_related_count / results.total_processed) * 100)}%)
                      </p>
                    </div>

                <div>
                  <p className="text-sm text-gray-600 mb-1">Non-Brand Accounts</p>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className="bg-gray-600 h-3 rounded-full" 
                      style={{width: `${(results.non_brand_count / results.total_processed) * 100}%`}}
                    ></div>

                <div>
                  <p className="text-sm text-gray-600 mb-1">Non-Brand Accounts</p>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className="bg-gray-600 h-3 rounded-full" 
                      style={{width: `${(results.non_brand_count / results.total_processed) * 100}%`}}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {results.non_brand_count} / {results.total_processed} 
                    ({Math.round((results.non_brand_count / results.total_processed) * 100)}%)
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {results.non_brand_count} / {results.total_processed} 
                    ({Math.round((results.non_brand_count / results.total_processed) * 100)}%)
                  </p>
                </div>
              </div>
              </div>
            </div>

            {/* Download Buttons */}
            <div className="flex flex-wrap gap-4">
            {/* Download Buttons */}
            <div className="flex flex-wrap gap-4">
                <button
                  onClick={() => handleDownload('brand_related')}
                className="flex items-center bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                className="flex items-center bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                <Download className="h-4 w-4 mr-2" />
                Download Brand Related Data
                <Download className="h-4 w-4 mr-2" />
                Download Brand Related Data
                </button>
                
                <button
                  onClick={() => handleDownload('non_brand')}
                className="flex items-center bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                className="flex items-center bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                <Download className="h-4 w-4 mr-2" />
                Download Non-Brand Data
                <Download className="h-4 w-4 mr-2" />
                Download Non-Brand Data
                </button>
                
                {results.merged_file && (
                  <button
                    onClick={() => handleDownload('merged')}
                    className="flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download Merged Results
                  </button>
                )}
                
                {results.merged_file && (
                  <button
                    onClick={() => handleDownload('merged')}
                    className="flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download Merged Results
                  </button>
                )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BrandAnalyzerDashboard; 