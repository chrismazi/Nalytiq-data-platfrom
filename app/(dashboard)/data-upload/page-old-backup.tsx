"use client"

import type React from "react"
import { useState } from "react"
import { motion } from "framer-motion"
import { AlertCircle, Check, FileSpreadsheet, Upload, X, FileType, BarChart3, Bot, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { DashboardHeader } from "@/components/dashboard-header"
import { DataPreviewTable } from "@/components/data-preview-table"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { DocumentChatDialog } from "@/components/document-chat-dialog"
import { uploadDataset, getProfileReport, cleanDataset, povertyByProvince, avgConsumptionByProvince, topDistricts, povertyByGender, urbanRuralConsumption, povertyByEducation } from "@/lib/api"
import { useRouter } from "next/navigation"
import SmartAnalysisPage from "../analysis/smart/page"
import AnalysisDashboard from "./AnalysisDashboard";

export default function DataUploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [processingComplete, setProcessingComplete] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [fileType, setFileType] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const [showChatDialog, setShowChatDialog] = useState(false)
  const [datasetSummary, setDatasetSummary] = useState<any>(null)
  const [profileHtml, setProfileHtml] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cleanedData, setCleanedData] = useState<any>(null)
  const [cleaning, setCleaning] = useState(false)
  const [frequencyCandidates, setFrequencyCandidates] = useState<string[]>([])
  const [selectedFrequencies, setSelectedFrequencies] = useState<string[]>([])
  const router = useRouter();
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [showDashboard, setShowDashboard] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      setFile(selectedFile)

      // Auto-detect file type
      const extension = selectedFile.name.split(".").pop()?.toLowerCase()
      if (extension === "csv") {
        setFileType("csv")
      } else if (extension === "xlsx" || extension === "xls") {
        setFileType("excel")
      } else if (extension === "dta") {
        setFileType("stata")
      } else {
        setFileType("unknown")
      }

      setUploadComplete(false)
      setProcessingComplete(false)
      setShowPreview(false)
      setAnalysisComplete(false)
      setDatasetSummary(null)
      setProfileHtml(null)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setUploadProgress(0)
    setError(null)

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      // Upload to backend
      const summary = await uploadDataset(file)
      if (!summary || !summary.columns || !summary.head) {
        throw new Error("No data returned from backend.")
      }
      setDatasetSummary(summary)
      clearInterval(progressInterval)
      setUploadProgress(100)
      setUploading(false)
      setUploadComplete(true)
      setTimeout(() => {
        setProcessingComplete(true)
        setShowPreview(true)
      }, 1000)
    } catch (err: any) {
      console.error("Upload failed:", err)
      setError("Failed to upload dataset. Backend may be unreachable or returned an error.")
      setUploading(false)
      setUploadProgress(0)
      setDatasetSummary(null)
      setShowPreview(false)
    }
  }

  const startAnalysis = async () => {
    if (!file) return;
    setAnalyzing(true);
    setAnalysisProgress(0);
    setError(null);
    let progressInterval: NodeJS.Timeout | null = null;
    try {
      // Simulate progress updates
      progressInterval = setInterval(() => {
        setAnalysisProgress((prev) => {
          if (prev >= 90) return 90;
          return prev + 5;
        });
      }, 300);
      // Call all analysis endpoints in parallel, with error handling
      const results = await Promise.allSettled([
        povertyByProvince(file),
        avgConsumptionByProvince(file),
        topDistricts(file),
        povertyByGender(file),
        urbanRuralConsumption(file),
        povertyByEducation(file)
      ]);
      if (progressInterval) clearInterval(progressInterval);
      // Log all results for debugging
      console.log('Analysis results (allSettled):', results);
      // Check for errors or empty data
      const errors = results.filter(r => r.status === 'rejected');
      if (errors.length > 0) {
        setError("One or more analysis steps failed. Please check your dataset and try again. Details: " + errors.map(e => e.reason).join('; '));
        setAnalyzing(false);
        setAnalysisProgress(0);
        setShowDashboard(false);
        return;
      }
      const [province, avgCons, topDist, gender, urbanRural, education] = results.map(r => r.status === 'fulfilled' ? r.value : null);
      if (
        !province?.data?.length ||
        !avgCons?.data?.length ||
        !topDist?.data?.length ||
        !gender?.data?.length ||
        !urbanRural?.data?.length ||
        !education?.data?.length
      ) {
        setError("Analysis succeeded but returned no data for one or more charts. Please check your dataset.");
        setAnalyzing(false);
        setAnalysisProgress(0);
        setShowDashboard(false);
        return;
      }
      setDashboardData({
        province: province.data,
        avgConsumption: avgCons.data,
        topDistricts: topDist.data,
        gender: gender.data,
        urbanRural: urbanRural.data,
        education: education.data
      });
      setAnalysisProgress(100);
      setTimeout(() => {
        setAnalyzing(false);
        setShowDashboard(true);
        setAnalysisComplete(true);
      }, 500);
    } catch (err) {
      if (progressInterval) clearInterval(progressInterval);
      let errorMsg = 'Failed to analyze dataset.';
      if (err && typeof err === 'object' && 'message' in err) {
        errorMsg += ' ' + (err as any).message;
      } else if (typeof err === 'string') {
        errorMsg += ' ' + err;
      }
      setError(errorMsg);
      setAnalyzing(false);
      setAnalysisProgress(0);
      setShowDashboard(false);
    }
  };

  const resetUpload = () => {
    setFile(null)
    setUploading(false)
    setUploadProgress(0)
    setUploadComplete(false)
    setProcessingComplete(false)
    setShowPreview(false)
    setFileType(null)
    setAnalyzing(false)
    setAnalysisProgress(0)
    setAnalysisComplete(false)
    setDatasetSummary(null)
    setProfileHtml(null)
    setError(null)
  }

  const handleClean = async () => {
    if (!file) return
    setCleaning(true)
    setError(null)
    try {
      const cleaned = await cleanDataset(file)
      setCleanedData(cleaned)
      setFrequencyCandidates(cleaned.frequency_candidates || [])
      setSelectedFrequencies([])
      setCleaning(false)
    } catch (err: any) {
      setError("Failed to clean dataset. " + (err?.message || ""))
      setCleaning(false)
    }
  }

  return (
    <div className="space-y-6">
      <DashboardHeader title="Data Upload" description="Upload and process statistical datasets for analysis" />

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="upload">
        <TabsList>
          <TabsTrigger value="upload">Upload Dataset</TabsTrigger>
          <TabsTrigger value="history">Upload History</TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-6 mt-6 animate-in">
          <Card>
            <CardHeader>
              <CardTitle>Upload New Dataset</CardTitle>
              <CardDescription>
                Upload CSV, Excel, or Stata files containing statistical data for processing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="grid w-full items-center gap-1.5">
                  <Label htmlFor="dataset-name">Dataset Name</Label>
                  <Input
                    id="dataset-name"
                    placeholder="e.g., EICV6 Survey Data 2023"
                    disabled={uploading || uploadComplete}
                  />
                </div>

                <div className="grid w-full items-center gap-1.5">
                  <Label htmlFor="dataset-description">Description (Optional)</Label>
                  <Textarea
                    id="dataset-description"
                    placeholder="Brief description of the dataset"
                    disabled={uploading || uploadComplete}
                    className="resize-none"
                    rows={3}
                  />
                </div>

                <div className="grid w-full items-center gap-1.5">
                  <Label htmlFor="dataset-file">File</Label>
                  {!file ? (
                    <div
                      className="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={() => document.getElementById("dataset-file")?.click()}
                    >
                      <div className="flex flex-col items-center gap-2">
                        <Upload className="h-8 w-8 text-muted-foreground" />
                        <p className="text-lg font-medium">Click to upload or drag and drop</p>
                        <p className="text-sm text-muted-foreground">
                          CSV, XLS, XLSX, or DTA (Stata) files (max 100MB)
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
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <FileSpreadsheet className="h-8 w-8 text-primary" />
                          <div>
                            <p className="font-medium">{file.name}</p>
                            <p className="text-sm text-muted-foreground">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {fileType && (
                            <Badge variant="outline" className="capitalize">
                              <FileType className="h-3 w-3 mr-1" />
                              {fileType === "csv"
                                ? "CSV"
                                : fileType === "excel"
                                  ? "Excel"
                                  : fileType === "stata"
                                    ? "Stata"
                                    : "Unknown"}
                            </Badge>
                          )}
                          <Button variant="ghost" size="icon" onClick={resetUpload} disabled={uploading}>
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      {uploading && (
                        <div className="mt-4 space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Uploading...</span>
                            <span>{uploadProgress}%</span>
                          </div>
                          <Progress value={uploadProgress} />
                        </div>
                      )}

                      {uploadComplete && !processingComplete && (
                        <div className="mt-4">
                          <Alert>
                            <AlertCircle className="h-4 w-4" />
                            <AlertTitle>Processing</AlertTitle>
                            <AlertDescription>
                              Your file has been uploaded and is now being processed...
                            </AlertDescription>
                          </Alert>
                        </div>
                      )}

                      {processingComplete && (
                        <div className="mt-4">
                          <Alert className="bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300 border-green-200 dark:border-green-800">
                            <Check className="h-4 w-4" />
                            <AlertTitle>Success</AlertTitle>
                            <AlertDescription>
                              Your file has been processed successfully. Preview available below.
                            </AlertDescription>
                          </Alert>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" onClick={resetUpload} disabled={!file || uploading}>
                Cancel
              </Button>
              <Button onClick={handleUpload} disabled={!file || uploading || uploadComplete}>
                {uploading ? "Uploading..." : "Upload and Process"}
              </Button>
            </CardFooter>
          </Card>

          {showPreview && datasetSummary && datasetSummary.columns && datasetSummary.head && datasetSummary.columns.length > 0 && datasetSummary.head.length > 0 ? (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
              <Card>
                <CardHeader>
                  <CardTitle>Data Preview</CardTitle>
                  <CardDescription>Preview of the uploaded dataset with automated schema detection</CardDescription>
                </CardHeader>
                <CardContent>
                  {cleanedData && cleanedData.columns && cleanedData.head && cleanedData.columns.length > 0 && cleanedData.head.length > 0 ? (
                    <>
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline"> Cleaned</Badge>
                        <span className="text-muted-foreground text-xs">Data is now ready for analysis</span>
                      </div>
                      <DataPreviewTable
                        columns={cleanedData.columns.map((col: string) => ({ name: col, type: cleanedData.dtypes[col] }))}
                        data={cleanedData.head}
                      />
                    </>
                  ) : !cleanedData ? (
                    <DataPreviewTable
                      columns={datasetSummary.columns.map((col: string) => ({ name: col, type: datasetSummary.dtypes[col] }))}
                      data={datasetSummary.head}
                    />
                  ) : (
                    <div className="border rounded-md p-4 text-center text-muted-foreground">
                      No cleaned data to preview.
                    </div>
                  )}
                  {!cleanedData && (
                    <Button onClick={handleClean} disabled={cleaning} className="mt-4">
                      {cleaning ? "Cleaning..." : "Clean Data"}
                    </Button>
                  )}
                </CardContent>
                <CardFooter className="flex justify-between">
                  <div className="text-sm text-muted-foreground">
                    <span className="font-medium">Detected:</span> {cleanedData ? cleanedData.shape[1] : datasetSummary.shape[1]} columns, {cleanedData ? cleanedData.shape[0] : datasetSummary.shape[0]} rows
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline">Edit Schema</Button>
                    <Button
                      onClick={startAnalysis}
                      disabled={!cleanedData || analyzing}
                    >
                      {analyzing ? "Analyzing..." : <><BarChart3 className="h-4 w-4 mr-2" />Analyze Data</>}
                    </Button>
                  </div>
                </CardFooter>
              </Card>
            </motion.div>
          ) : showPreview ? (
            <div className="border rounded-md p-4 text-center text-muted-foreground">
              No data to preview. Please upload a valid CSV file.
            </div>
          ) : null}

          {analyzing && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
              <Card>
                <CardHeader>
                  <CardTitle>AI Analysis in Progress</CardTitle>
                  <CardDescription>Our system is analyzing your dataset to uncover patterns and insights.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Analysis Progress</span>
                        <span>{analysisProgress}%</span>
                      </div>
                      <Progress value={analysisProgress} />
                    </div>
                    <div className="border rounded-lg p-4 bg-muted/50">
                      <div className="space-y-3">
                        <div className="flex items-start gap-3">
                          <div className="mt-1 h-2 w-2 rounded-full bg-primary animate-pulse" />
                          <p className="text-sm">
                            {analysisProgress < 20
                              ? "Scanning variables and identifying data types..."
                              : analysisProgress < 40
                                ? "Detecting trends and relationships in your data..."
                                : analysisProgress < 60
                                  ? "Summarizing key statistics and distributions..."
                                  : analysisProgress < 80
                                    ? "Generating visualizations and insights..."
                                    : "Finalizing your smart analysis dashboard..."}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {analysisComplete && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
              <Card>
                <CardHeader>
                  <CardTitle>Analysis Complete</CardTitle>
                  <CardDescription>AI-generated insights from your dataset</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Alert className="bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300 border-green-200 dark:border-green-800">
                      <Check className="h-4 w-4" />
                      <AlertTitle>Analysis Complete</AlertTitle>
                      <AlertDescription>
                        Your data has been analyzed successfully. View the dashboard or chat with your data for
                        insights.
                      </AlertDescription>
                    </Alert>

                    {/* Remove/demote the old HTML profile report iframe and related UI */}
                    {/* {profileHtml && (
                      <div className="border rounded-lg">
                        <div className="p-4 border-b">
                          <h3 className="font-medium">Detailed Analysis Report</h3>
                        </div>
                        <iframe
                          srcDoc={profileHtml
                            // Remove Sample Data section
                            .replace(/<h[1-6][^>]*>Sample Data \(First 10 rows\)<\/h[1-6]>[\s\S]*?(<h[1-6][^>]*>|$)/gi, '$1')
                            // Remove Correlation Matrix section
                            .replace(/<h[1-6][^>]*>Correlation Matrix[^<]*<\/h[1-6]>[\s\S]*?(<h[1-6][^>]*>|$)/gi, '$1')
                          }
                          title="Profile Report"
                          className="w-full h-[600px] border-0"
                        />
                      </div>
                    )} */}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-base">Key Findings</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ul className="space-y-2 text-sm">
                            <li className="flex items-start gap-2">
                              <div className="rounded-full bg-primary/10 p-1 mt-0.5">
                                <Check className="h-3 w-3 text-primary" />
                              </div>
                              <span>Strong correlation (0.78) between education level and income</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <div className="rounded-full bg-primary/10 p-1 mt-0.5">
                                <Check className="h-3 w-3 text-primary" />
                              </div>
                              <span>Significant regional disparities in access to electricity and internet</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <div className="rounded-full bg-primary/10 p-1 mt-0.5">
                                <Check className="h-3 w-3 text-primary" />
                              </div>
                              <span>Gender gap in income narrows with higher education levels</span>
                            </li>
                          </ul>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-base">Recommended Actions</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ul className="space-y-2 text-sm">
                            <li className="flex items-start gap-2">
                              <div className="rounded-full bg-primary/10 p-1 mt-0.5">
                                <BarChart3 className="h-3 w-3 text-primary" />
                              </div>
                              <span>View the auto-generated dashboard for visual insights</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <div className="rounded-full bg-primary/10 p-1 mt-0.5">
                                <Bot className="h-3 w-3 text-primary" />
                              </div>
                              <span>Chat with your data to explore specific questions</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <div className="rounded-full bg-primary/10 p-1 mt-0.5">
                                <FileText className="h-3 w-3 text-primary" />
                              </div>
                              <span>Generate a comprehensive report with all findings</span>
                            </li>
                          </ul>
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="flex justify-between">
                  <Button variant="outline">
                    <FileText className="h-4 w-4 mr-2" />
                    Generate Report
                  </Button>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setShowChatDialog(true)}>
                      <Bot className="h-4 w-4 mr-2" />
                      Chat with Data
                    </Button>
                    <Button
                      onClick={() => setShowDashboard(true)}
                      disabled={!dashboardData}
                    >
                      <BarChart3 className="h-4 w-4 mr-2" />View Dashboard
                    </Button>
                  </div>
                </CardFooter>
              </Card>
            </motion.div>
          )}
        </TabsContent>

        <TabsContent value="history" className="mt-6 animate-in">
          <Card>
            <CardHeader>
              <CardTitle>Upload History</CardTitle>
              <CardDescription>Recent dataset uploads and their processing status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    name: "EICV6 Survey Data 2023",
                    date: "May 1, 2023",
                    status: "Analyzed",
                    type: "CSV",
                    size: "24.5 MB",
                    rows: "12,456",
                  },
                  {
                    name: "Health Indicators 2022",
                    date: "April 15, 2023",
                    status: "Analyzed",
                    type: "Excel",
                    size: "8.2 MB",
                    rows: "5,234",
                  },
                  {
                    name: "Economic Census 2023",
                    date: "March 28, 2023",
                    status: "Processed",
                    type: "Stata",
                    size: "42.1 MB",
                    rows: "28,912",
                  },
                ].map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <FileSpreadsheet className="h-8 w-8 text-primary" />
                      <div>
                        <p className="font-medium">{item.name}</p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span>Uploaded on {item.date}</span>
                          <Badge variant="outline" className="text-xs">
                            {item.type}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-sm text-right">
                        <p>{item.size}</p>
                        <p className="text-muted-foreground">{item.rows} rows</p>
                      </div>
                      <div className="flex items-center gap-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 px-2 py-1 rounded text-xs font-medium">
                        <Check className="h-3 w-3" />
                        {item.status}
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => setShowChatDialog(true)}>
                          <Bot className="h-3 w-3 mr-1" />
                          Chat
                        </Button>
                        <Button variant="ghost" size="sm">
                          View
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <DocumentChatDialog open={showChatDialog} onOpenChange={setShowChatDialog} insights={dashboardData?.insights || datasetSummary?.insights} />
      {/* Move AnalysisDashboard overlay here so it always appears above everything */}
      {showDashboard && dashboardData && (
        <AnalysisDashboard data={dashboardData} onClose={() => setShowDashboard(false)} />
      )}
    </div>
  )
}
