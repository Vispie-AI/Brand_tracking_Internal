import { useState, useRef, useEffect } from 'react'
import { Upload, FileText, Download, BarChart3, TrendingUp, Users, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import axios from 'axios'

interface AnalysisResults {
  total_count: number
  brand_related_count: number
  non_brand_count: number
  brand_count: number
  matrix_count: number
  ugc_count: number
  brand_in_related: number
  matrix_in_related: number
  ugc_in_related: number
  brand_file: string
  non_brand_file: string
}

interface LogEntry {
  timestamp: string
  level: string
  message: string
}

interface TaskStatus {
  status: 'pending' | 'running' | 'completed' | 'error'
  progress: string
  results?: AnalysisResults
  logs: LogEntry[]
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const droppedFiles = e.dataTransfer.files
    if (droppedFiles.length > 0) {
      const droppedFile = droppedFiles[0]
      if (droppedFile.type === 'application/json' || droppedFile.name.endsWith('.json')) {
        setFile(droppedFile)
      } else {
        alert('请选择JSON文件')
      }
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const uploadFile = async () => {
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      const { task_id } = response.data
      setTaskId(task_id)
      setTaskStatus({ status: 'pending', progress: '文件上传成功，准备开始分析...', logs: [] })
      
      // 开始轮询状态
      pollTaskStatus(task_id)
    } catch (error) {
      console.error('Upload error:', error)
      alert('上传失败，请重试')
    }
  }

  const pollTaskStatus = async (id: string) => {
    try {
      const response = await axios.get(`/api/status/${id}`)
      const status = response.data
      setTaskStatus(status)

      if (status.status === 'running' || status.status === 'pending') {
        setTimeout(() => pollTaskStatus(id), 2000) // 每2秒轮询一次
      }
    } catch (error) {
      console.error('Status polling error:', error)
    }
  }

  const downloadFile = async (fileType: 'brand' | 'non_brand') => {
    if (!taskId) return

    try {
      const response = await axios.get(`/api/download/${taskId}/${fileType}`, {
        responseType: 'blob',
      })
      
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${fileType}_results.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download error:', error)
      alert('下载失败，请重试')
    }
  }

  const resetAnalysis = () => {
    setFile(null)
    setTaskId(null)
    setTaskStatus(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold gradient-text mb-4">
            品牌创作者分析器
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            AI驱动的创作者品牌关联性分析工具，精准识别官方品牌账号、矩阵账号和UGC创作者
          </p>
        </div>

        {/* Upload Section */}
        {!taskId && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <div
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
                isDragging
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <Upload className="mx-auto h-16 w-16 text-gray-400 mb-4" />
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                上传JSON数据文件
              </h3>
              <p className="text-gray-500 mb-6">
                拖拽文件到此处或点击选择文件
              </p>
              
              {file ? (
                <div className="flex items-center justify-center space-x-3 mb-6">
                  <FileText className="h-5 w-5 text-green-500" />
                  <span className="text-sm font-medium text-green-700">{file.name}</span>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                </div>
              ) : null}

              <div className="flex space-x-4 justify-center">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  选择文件
                </button>
                {file && (
                  <button
                    onClick={uploadFile}
                    className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center space-x-2"
                  >
                    <Upload className="h-4 w-4" />
                    <span>开始分析</span>
                  </button>
                )}
              </div>
              
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>
          </div>
        )}

        {/* Analysis Progress */}
        {taskStatus && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-800">分析进度</h2>
              {taskStatus.status === 'completed' && (
                <button
                  onClick={resetAnalysis}
                  className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  新建分析
                </button>
              )}
            </div>

            {/* Status */}
            <div className="flex items-center space-x-3 mb-4">
              {taskStatus.status === 'running' && (
                <Loader2 className="h-6 w-6 text-blue-500 animate-spin" />
              )}
              {taskStatus.status === 'completed' && (
                <CheckCircle className="h-6 w-6 text-green-500" />
              )}
              {taskStatus.status === 'error' && (
                <AlertCircle className="h-6 w-6 text-red-500" />
              )}
              <span className="text-lg font-medium text-gray-700">
                {taskStatus.progress}
              </span>
            </div>

            {/* Progress Bar */}
            {(taskStatus.status === 'running' || taskStatus.status === 'pending') && (
              <div className="w-full bg-gray-200 rounded-full h-3 mb-6">
                <div className="bg-blue-500 h-3 rounded-full progress-bar animate-pulse w-1/2"></div>
              </div>
            )}

            {/* Logs */}
            {taskStatus.logs && taskStatus.logs.length > 0 && (
              <div className="bg-gray-50 rounded-lg p-4 max-h-60 overflow-y-auto mb-6">
                <h3 className="font-medium text-gray-700 mb-3">实时日志</h3>
                <div className="space-y-1 text-sm">
                  {taskStatus.logs.map((log, index) => (
                    <div key={index} className="flex space-x-2">
                      <span className="text-gray-400">{log.timestamp}</span>
                      <span className={`${
                        log.level === 'ERROR' ? 'text-red-600' : 
                        log.level === 'WARNING' ? 'text-yellow-600' : 
                        'text-gray-600'
                      }`}>
                        {log.message}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Results */}
            {taskStatus.status === 'completed' && taskStatus.results && (
              <div>
                <h3 className="text-xl font-bold text-gray-800 mb-6">分析结果</h3>
                
                {/* Statistics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                  <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-blue-100">总数据量</p>
                        <p className="text-3xl font-bold">{taskStatus.results.total_count}</p>
                      </div>
                      <Users className="h-12 w-12 text-blue-200" />
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-green-100">品牌相关</p>
                        <p className="text-3xl font-bold">{taskStatus.results.brand_related_count}</p>
                        <p className="text-sm text-green-100">
                          {((taskStatus.results.brand_related_count / taskStatus.results.total_count) * 100).toFixed(1)}%
                        </p>
                      </div>
                      <TrendingUp className="h-12 w-12 text-green-200" />
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-purple-100">非品牌相关</p>
                        <p className="text-3xl font-bold">{taskStatus.results.non_brand_count}</p>
                        <p className="text-sm text-purple-100">
                          {((taskStatus.results.non_brand_count / taskStatus.results.total_count) * 100).toFixed(1)}%
                        </p>
                      </div>
                      <BarChart3 className="h-12 w-12 text-purple-200" />
                    </div>
                  </div>
                </div>

                {/* Detailed Breakdown */}
                <div className="bg-gray-50 rounded-xl p-6 mb-8">
                  <h4 className="text-lg font-semibold text-gray-800 mb-4">品牌相关账号分类</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{taskStatus.results.brand_in_related}</div>
                      <div className="text-sm text-gray-600">官方品牌账号</div>
                      <div className="text-xs text-gray-500">
                        {taskStatus.results.brand_related_count > 0 
                          ? ((taskStatus.results.brand_in_related / taskStatus.results.brand_related_count) * 100).toFixed(1)
                          : 0}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{taskStatus.results.matrix_in_related}</div>
                      <div className="text-sm text-gray-600">矩阵账号</div>
                      <div className="text-xs text-gray-500">
                        {taskStatus.results.brand_related_count > 0 
                          ? ((taskStatus.results.matrix_in_related / taskStatus.results.brand_related_count) * 100).toFixed(1)
                          : 0}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">{taskStatus.results.ugc_in_related}</div>
                      <div className="text-sm text-gray-600">UGC创作者</div>
                      <div className="text-xs text-gray-500">
                        {taskStatus.results.brand_related_count > 0 
                          ? ((taskStatus.results.ugc_in_related / taskStatus.results.brand_related_count) * 100).toFixed(1)
                          : 0}%
                      </div>
                    </div>
                  </div>
                </div>

                {/* Download Buttons */}
                <div className="flex space-x-4 justify-center">
                  <button
                    onClick={() => downloadFile('brand')}
                    className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center space-x-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>下载品牌相关数据</span>
                  </button>
                  <button
                    onClick={() => downloadFile('non_brand')}
                    className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors flex items-center space-x-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>下载非品牌数据</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
} 