"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { 
  Upload, FileSpreadsheet, CheckCircle2, AlertCircle, 
  BarChart3, Download, Sparkles, X, Info
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { DashboardHeader } from "@/components/dashboard-header"
import { DataPreviewTable } from "@/components/data-preview-table"
import { DataQualityScore } from "@/components/data-quality-score"
import { AnalysisSelector } from "@/components/analysis-selector"
import { AnalysisResultsViz } from "@/components/analysis-results-viz"
import { 
  uploadDatasetEnhanced, 
  getGroupedStats,
  getCrosstab,
  trainMLModel,
  getTopN,
  getComparison,
  downloadDataset,
  saveAnalysis
} from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

export default function DataUploadPage() {
  const { toast } = useToast()
  
  // Upload state
  const [file, setFile] = useState<File | null>(null)
  const [datasetName, setDatasetName] = useState("")
  const [description, setDescription] = useState("")
  const [autoClean, setAutoClean] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  
  // Dataset state
  const [datasetId, setDatasetId] = useState<number | null>(null)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  
  // Analysis state
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResults, setAnalysisResults] = useState<any[]>([])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      setFile(selectedFile)
      
      // Auto-set dataset name from filename
      if (!datasetName) {
        const name = selectedFile.name.replace(/\.[^/.]+$/, "")
        setDatasetName(name)
      }
      
      // Reset state
      setError(null)
      setUploadResult(null)
      setDatasetId(null)
      setAnalysisResults([])
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setUploadProgress(0)
    setError(null)

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      // Upload with enhanced endpoint
      const result = await uploadDatasetEnhanced(
        file,
        datasetName || file.name,
        description,
        autoClean
      )

      clearInterval(progressInterval)
      setUploadProgress(100)
      
      setDatasetId(result.dataset_id)
      setUploadResult(result)
      
      toast({
        title: " Upload Successful!",
        description: `Dataset processed with quality grade: ${result.quality_score?.grade}`,
      })
      
    } catch (err: any) {
      console.error("Upload failed:", err)
      setError(err.message || "Failed to upload dataset")
      
      toast({
        title: " Upload Failed",
        description: err.message || "Please check your file and try again",
        variant: "destructive",
      })
    } finally {
      setUploading(false)
    }
  }

  const handleAnalysis = async (type: string, config: any) => {
    if (!datasetId) return

    setAnalyzing(true)
    const startTime = Date.now()
    
    try {
      let result: any = null
      let title = ""

      switch (type) {
        case 'grouped-stats':
          result = await getGroupedStats(
            datasetId,
            config.groupBy,
            config.valueCol,
            config.aggregation
          )
          title = `${config.aggregation.toUpperCase()} of ${config.valueCol} by ${config.groupBy}`
          break
          
        case 'crosstab':
          result = await getCrosstab(
            datasetId,
            config.rowCol,
            config.colCol,
            config.valueCol || undefined,
            config.aggfunc,
            config.normalize
          )
          title = `Cross-tabulation: ${config.rowCol} × ${config.colCol}`
          break
          
        case 'top-n':
          result = await getTopN(
            datasetId,
            config.groupCol,
            config.valueCol,
            config.n,
            config.ascending
          )
          title = `Top ${config.n} ${config.groupCol} by ${config.valueCol}`
          break
          
        case 'comparison':
          result = await getComparison(
            datasetId,
            config.categoryCol,
            config.valueCol,
            config.categories
          )
          title = `Comparison: ${config.valueCol} across ${config.categoryCol}`
          break
          
        case 'ml-model':
          result = await trainMLModel(
            datasetId,
            config.target,
            config.features,
            config.testSize,
            config.nEstimators,
            config.maxDepth
          )
          title = `ML Model: Predict ${config.target}`
          break
      }

      const executionTime = Date.now() - startTime

      // Save analysis to history
      try {
        await saveAnalysis({
          dataset_id: datasetId,
          analysis_type: type,
          title: title,
          parameters: config,
          results: result,
          visualization_data: { type, config },
          execution_time_ms: executionTime
        })
      } catch (saveErr) {
        console.error("Failed to save analysis to history:", saveErr)
        // Don't fail the whole analysis if save fails
      }

      // Add to results
      setAnalysisResults(prev => [
        ...prev,
        { type, data: result, title, timestamp: new Date() }
      ])

      toast({
        title: " Analysis Complete!",
        description: title,
      })

    } catch (err: any) {
      console.error("Analysis failed:", err)
      
      toast({
        title: " Analysis Failed",
        description: err.message || "Please check your configuration",
        variant: "destructive",
      })
    } finally {
      setAnalyzing(false)
    }
  }

  const handleDownload = async (format: 'csv' | 'excel' | 'json') => {
    if (!datasetId) return

    try {
      await downloadDataset(datasetId, format)
      
      toast({
        title: " Download Started",
        description: `Downloading cleaned dataset as ${format.toUpperCase()}`,
      })
    } catch (err: any) {
      toast({
        title: " Download Failed",
        description: err.message,
        variant: "destructive",
      })
    }
  }

  const resetUpload = () => {
    setFile(null)
    setDatasetName("")
    setDescription("")
    setUploadResult(null)
    setDatasetId(null)
    setAnalysisResults([])
    setError(null)
    setUploadProgress(0)
  }

  return (
    <div className="space-y-6">
      <DashboardHeader 
        title="Universal Analytics Workbench" 
        description="Upload any dataset and perform advanced analytics with AI-powered insights"
      />

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Upload Section */}
      {!uploadResult && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-2 border-dashed border-primary/20 hover:border-primary/40 transition-colors">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Upload Dataset
              </CardTitle>
              <CardDescription>
                Supports CSV, Excel (.xlsx, .xls), and Stata (.dta) files up to 500MB
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* File Upload */}
              {!file ? (
                <div
                  className="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => document.getElementById("dataset-file")?.click()}
                >
                  <div className="flex flex-col items-center gap-2">
                    <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                      <FileSpreadsheet className="h-8 w-8 text-primary" />
                    </div>
                    <p className="text-lg font-medium mt-2">Click to upload or drag and drop</p>
                    <p className="text-sm text-muted-foreground">
                      CSV, Excel, or Stata files (max 500MB)
                    </p>
                  </div>
                  <Input
                    id="dataset-file"
                    type="file"
                    accept=".csv,.xls,.xlsx,.dta"
                    className="hidden"
                    onChange={handleFileChange}
                    disabled={uploading}
                  />
                </div>
              ) : (
                <div className="space-y-4">
                  {/* File Info */}
                  <div className="border rounded-lg p-4 bg-muted/50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                          <FileSpreadsheet className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{file.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {(file.size / (1024 * 1024)).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" onClick={resetUpload} disabled={uploading}>
                        <X className="h-4 w-4" />
                      </Button>
                    </div>

                    {uploading && (
                      <div className="mt-4 space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Processing...</span>
                          <span>{uploadProgress}%</span>
                        </div>
                        <Progress value={uploadProgress} />
                        <p className="text-xs text-muted-foreground">
                          {autoClean ? "Cleaning and analyzing your data..." : "Analyzing your data..."}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Dataset Metadata */}
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="dataset-name">Dataset Name</Label>
                      <Input
                        id="dataset-name"
                        value={datasetName}
                        onChange={(e) => setDatasetName(e.target.value)}
                        placeholder="e.g., Sales Data Q1 2024"
                        disabled={uploading}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Auto-Clean Data</Label>
                      <div className="flex items-center space-x-2 h-10">
                        <Switch
                          checked={autoClean}
                          onCheckedChange={setAutoClean}
                          disabled={uploading}
                        />
                        <span className="text-sm text-muted-foreground">
                          {autoClean ? "Enabled" : "Disabled"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="dataset-description">Description (Optional)</Label>
                    <Textarea
                      id="dataset-description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Brief description of the dataset"
                      disabled={uploading}
                      rows={2}
                    />
                  </div>

                  {autoClean && (
                    <Alert>
                      <Sparkles className="h-4 w-4" />
                      <AlertTitle>Auto-Clean Features</AlertTitle>
                      <AlertDescription>
                        <ul className="text-sm list-disc list-inside mt-2 space-y-1">
                          <li>Automatic type detection (numbers, dates, categories)</li>
                          <li>Column name standardization</li>
                          <li>Missing value imputation</li>
                          <li>Duplicate removal</li>
                          <li>Outlier detection</li>
                        </ul>
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              {/* Actions */}
              {file && (
                <div className="flex gap-2">
                  <Button 
                    onClick={handleUpload} 
                    disabled={!file || uploading}
                    className="flex-1"
                    size="lg"
                  >
                    {uploading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload and Analyze
                      </>
                    )}
                  </Button>
                  <Button variant="outline" onClick={resetUpload} disabled={uploading}>
                    Cancel
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Results Section */}
      {uploadResult && (
        <AnimatePresence mode="wait">
          <div className="space-y-6">
            {/* Success Banner */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <Alert className="bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300 border-green-200 dark:border-green-800">
                <CheckCircle2 className="h-4 w-4" />
                <AlertTitle>Dataset Processed Successfully!</AlertTitle>
                <AlertDescription className="flex items-center justify-between">
                  <span>Your data is ready for analysis</span>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => handleDownload('csv')}>
                      <Download className="h-3 w-3 mr-1" />
                      CSV
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleDownload('excel')}>
                      <Download className="h-3 w-3 mr-1" />
                      Excel
                    </Button>
                    <Button size="sm" variant="outline" onClick={resetUpload}>
                      <Upload className="h-3 w-3 mr-1" />
                      New Upload
                    </Button>
                  </div>
                </AlertDescription>
              </Alert>
            </motion.div>

            {/* Data Quality Score */}
            {uploadResult.quality_score && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <DataQualityScore score={uploadResult.quality_score} />
              </motion.div>
            )}

            {/* Dataset Overview */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle>Dataset Overview</CardTitle>
                  <CardDescription>Summary statistics and data preview</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold">{uploadResult.basic_info.rows.toLocaleString()}</div>
                      <p className="text-xs text-muted-foreground">Rows</p>
                    </div>
                    <div className="p-4 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold">{uploadResult.basic_info.columns}</div>
                      <p className="text-xs text-muted-foreground">Columns</p>
                    </div>
                    <div className="p-4 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold">{uploadResult.basic_info.memory_mb.toFixed(1)} MB</div>
                      <p className="text-xs text-muted-foreground">Memory</p>
                    </div>
                    <div className="p-4 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold">{uploadResult.basic_info.missing_percentage.toFixed(1)}%</div>
                      <p className="text-xs text-muted-foreground">Missing</p>
                    </div>
                  </div>

                  <Separator />

                  {/* Data Preview */}
                  {uploadResult.sample_data && uploadResult.sample_data.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-3">Data Preview (First 10 rows)</h4>
                      <DataPreviewTable
                        columns={Object.keys(uploadResult.columns).map(name => ({
                          name,
                          type: uploadResult.columns[name].dtype
                        }))}
                        data={uploadResult.sample_data}
                      />
                    </div>
                  )}

                  {/* Insights */}
                  {uploadResult.insights && uploadResult.insights.length > 0 && (
                    <div className="p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg">
                      <div className="flex items-start gap-2">
                        <Info className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5" />
                        <div className="flex-1">
                          <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                            Automated Insights
                          </h4>
                          <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
                            {uploadResult.insights.map((insight: string, index: number) => (
                              <li key={index} className="flex items-start gap-2">
                                <span className="text-blue-500">•</span>
                                <span>{insight}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* Analysis Selector */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <AnalysisSelector
                columns={uploadResult.columns}
                datasetId={datasetId!}
                onAnalyze={handleAnalysis}
                loading={analyzing}
              />
            </motion.div>

            {/* Analysis Results */}
            {analysisResults.length > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    <BarChart3 className="h-6 w-6" />
                    Analysis Results
                  </h2>
                  <Badge variant="secondary">
                    {analysisResults.length} {analysisResults.length === 1 ? 'Analysis' : 'Analyses'}
                  </Badge>
                </div>

                {analysisResults.map((result, index) => (
                  <AnalysisResultsViz
                    key={index}
                    type={result.type}
                    data={result.data}
                    title={result.title}
                  />
                ))}
              </motion.div>
            )}
          </div>
        </AnimatePresence>
      )}
    </div>
  )
}
