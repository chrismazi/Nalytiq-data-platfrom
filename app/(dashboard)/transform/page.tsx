"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { 
  Filter, Columns, Trash2, Edit, Plus, Download,
  FileDown, FileSpreadsheet, FileJson, FileText,
  Play, RotateCcw, Eye, Sparkles, Save
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { DashboardHeader } from "@/components/dashboard-header"
import { useToast } from "@/hooks/use-toast"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { getDatasetsList } from "@/lib/api"

export default function TransformPage() {
  const { toast } = useToast()
  
  // State
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState<any>(null)
  const [columns, setColumns] = useState<any>(null)
  const [transformations, setTransformations] = useState<any[]>([])
  const [preview, setPreview] = useState<any>(null)
  const [applying, setApplying] = useState(false)
  
  // Current transformation being built
  const [currentOp, setCurrentOp] = useState("")
  const [opParams, setOpParams] = useState<any>({})

  const operations = [
    { id: "filter_rows", name: "Filter Rows", icon: Filter, category: "filtering" },
    { id: "select_columns", name: "Select Columns", icon: Columns, category: "columns" },
    { id: "drop_columns", name: "Drop Columns", icon: Trash2, category: "columns" },
    { id: "rename_column", name: "Rename Column", icon: Edit, category: "columns" },
    { id: "drop_duplicates", name: "Remove Duplicates", icon: Trash2, category: "cleaning" },
    { id: "fill_missing", name: "Fill Missing", icon: Plus, category: "missing_data" },
    { id: "sort_values", name: "Sort", icon: Filter, category: "sorting" }
  ]

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const response = await getDatasetsList()
      setDatasets(response.datasets || [])
    } catch (error: any) {
      toast({
        title: "Failed to load datasets",
        description: error.message,
        variant: "destructive"
      })
    }
  }

  const handleDatasetSelect = async (datasetId: string) => {
    const dataset = datasets.find(d => d.id === parseInt(datasetId))
    setSelectedDataset(dataset)
    setTransformations([])
    setPreview(null)
    
    // Load columns
    try {
      const res = await fetch(`http://localhost:8000/api/viz/dataset-columns/${datasetId}`)
      const data = await res.json()
      setColumns(data.columns)
    } catch (error) {
      console.error("Failed to load columns:", error)
    }
  }

  const addTransformation = () => {
    if (!currentOp) return

    const newTransform = {
      operation: currentOp,
      params: { ...opParams }
    }

    setTransformations([...transformations, newTransform])
    setCurrentOp("")
    setOpParams({})
  }

  const removeTransformation = (index: number) => {
    setTransformations(transformations.filter((_, i) => i !== index))
  }

  const applyTransformations = async () => {
    if (!selectedDataset || transformations.length === 0) return

    setApplying(true)

    try {
      const res = await fetch('http://localhost:8000/api/export-transform/transformation-pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: selectedDataset.id,
          transformations: transformations
        })
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || 'Failed to apply transformations')
      }

      const data = await res.json()
      setPreview(data.result)

      toast({
        title: "✅ Transformations Applied!",
        description: `${transformations.length} transformation(s) completed successfully`
      })

    } catch (error: any) {
      toast({
        title: "Transformation failed",
        description: error.message,
        variant: "destructive"
      })
    } finally {
      setApplying(false)
    }
  }

  const exportData = async (format: string) => {
    if (!selectedDataset) return

    try {
      const res = await fetch('http://localhost:8000/api/export-transform/export-dataset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: selectedDataset.id,
          format: format
        })
      })

      if (!res.ok) {
        throw new Error('Export failed')
      }

      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `export_${selectedDataset.name}.${format === 'excel' ? 'xlsx' : format}`
      a.click()
      window.URL.revokeObjectURL(url)

      toast({
        title: "✅ Export Complete!",
        description: `Dataset exported as ${format.toUpperCase()}`
      })

    } catch (error: any) {
      toast({
        title: "Export failed",
        description: error.message,
        variant: "destructive"
      })
    }
  }

  const generateReport = async () => {
    if (!selectedDataset) return

    try {
      const res = await fetch('http://localhost:8000/api/export-transform/generate-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: selectedDataset.id,
          title: `Analysis Report: ${selectedDataset.name}`,
          include_data: true,
          include_statistics: true
        })
      })

      if (!res.ok) {
        throw new Error('Report generation failed')
      }

      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report_${selectedDataset.name}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)

      toast({
        title: "✅ Report Generated!",
        description: "PDF report downloaded successfully"
      })

    } catch (error: any) {
      toast({
        title: "Report generation failed",
        description: error.message,
        variant: "destructive"
      })
    }
  }

  return (
    <div className="space-y-6">
      <DashboardHeader
        title="Data Transformation & Export"
        description="Transform your data and export in multiple formats"
      />

      {/* Dataset Selection and Export Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Select Dataset</CardTitle>
          </CardHeader>
          <CardContent>
            <Select onValueChange={handleDatasetSelect}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a dataset" />
              </SelectTrigger>
              <SelectContent>
                {datasets.map((dataset) => (
                  <SelectItem key={dataset.id} value={dataset.id.toString()}>
                    {dataset.name} ({dataset.num_rows} rows)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quick Export</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button 
              onClick={() => exportData('csv')} 
              disabled={!selectedDataset}
              variant="outline"
              className="w-full justify-start"
            >
              <FileText className="mr-2 h-4 w-4" />
              Export CSV
            </Button>
            <Button 
              onClick={() => exportData('excel')} 
              disabled={!selectedDataset}
              variant="outline"
              className="w-full justify-start"
            >
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Export Excel
            </Button>
            <Button 
              onClick={() => exportData('json')} 
              disabled={!selectedDataset}
              variant="outline"
              className="w-full justify-start"
            >
              <FileJson className="mr-2 h-4 w-4" />
              Export JSON
            </Button>
            <Button 
              onClick={generateReport} 
              disabled={!selectedDataset}
              className="w-full justify-start"
            >
              <FileDown className="mr-2 h-4 w-4" />
              Generate PDF Report
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Transformation Builder */}
      {selectedDataset && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Operations Panel */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Add Transformation</CardTitle>
                <CardDescription>Build a transformation pipeline</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Operation</Label>
                  <Select onValueChange={(v) => {
                    setCurrentOp(v)
                    setOpParams({})
                  }} value={currentOp}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select operation" />
                    </SelectTrigger>
                    <SelectContent>
                      {operations.map((op) => (
                        <SelectItem key={op.id} value={op.id}>
                          {op.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Dynamic Parameters */}
                {currentOp === 'filter_rows' && (
                  <>
                    <div>
                      <Label>Column</Label>
                      <Select onValueChange={(v) => setOpParams({...opParams, column: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select column" />
                        </SelectTrigger>
                        <SelectContent>
                          {columns?.all.map((col: string) => (
                            <SelectItem key={col} value={col}>{col}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Operator</Label>
                      <Select onValueChange={(v) => setOpParams({...opParams, operator: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select operator" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="equals">Equals</SelectItem>
                          <SelectItem value="not_equals">Not Equals</SelectItem>
                          <SelectItem value="greater_than">Greater Than</SelectItem>
                          <SelectItem value="less_than">Less Than</SelectItem>
                          <SelectItem value="contains">Contains</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Value</Label>
                      <Input 
                        placeholder="Enter value"
                        onChange={(e) => setOpParams({...opParams, value: e.target.value})}
                      />
                    </div>
                  </>
                )}

                {(currentOp === 'select_columns' || currentOp === 'drop_columns') && (
                  <div>
                    <Label>Columns (comma-separated)</Label>
                    <Input 
                      placeholder="col1, col2, col3"
                      onChange={(e) => setOpParams({...opParams, columns: e.target.value.split(',').map(c => c.trim())})}
                    />
                  </div>
                )}

                {currentOp === 'rename_column' && (
                  <>
                    <div>
                      <Label>Old Name</Label>
                      <Select onValueChange={(v) => setOpParams({...opParams, old_name: v})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {columns?.all.map((col: string) => (
                            <SelectItem key={col} value={col}>{col}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>New Name</Label>
                      <Input 
                        placeholder="New column name"
                        onChange={(e) => setOpParams({...opParams, new_name: e.target.value})}
                      />
                    </div>
                  </>
                )}

                {currentOp === 'fill_missing' && (
                  <>
                    <div>
                      <Label>Column</Label>
                      <Select onValueChange={(v) => setOpParams({...opParams, column: v})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {columns?.numeric.map((col: string) => (
                            <SelectItem key={col} value={col}>{col}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Method</Label>
                      <Select onValueChange={(v) => setOpParams({...opParams, method: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select method" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="mean">Mean</SelectItem>
                          <SelectItem value="median">Median</SelectItem>
                          <SelectItem value="mode">Mode</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                )}

                {currentOp === 'sort_values' && (
                  <div>
                    <Label>Columns (comma-separated)</Label>
                    <Input 
                      placeholder="col1, col2"
                      onChange={(e) => setOpParams({...opParams, columns: e.target.value.split(',').map(c => c.trim())})}
                    />
                  </div>
                )}

                <Button 
                  onClick={addTransformation}
                  disabled={!currentOp || Object.keys(opParams).length === 0}
                  className="w-full"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add to Pipeline
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Pipeline & Preview */}
          <div className="lg:col-span-2 space-y-6">
            {/* Transformation Pipeline */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Transformation Pipeline</span>
                  <Badge variant="secondary">{transformations.length} steps</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {transformations.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No transformations added yet. Add operations from the left panel.
                  </p>
                ) : (
                  <>
                    {transformations.map((transform, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <Badge>{index + 1}</Badge>
                          <div>
                            <p className="font-medium">
                              {operations.find(op => op.id === transform.operation)?.name}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {JSON.stringify(transform.params)}
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeTransformation(index)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}

                    <div className="flex gap-2 pt-4">
                      <Button 
                        onClick={applyTransformations}
                        disabled={applying}
                        className="flex-1"
                      >
                        {applying ? (
                          <>
                            <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                            Applying...
                          </>
                        ) : (
                          <>
                            <Play className="mr-2 h-4 w-4" />
                            Apply Pipeline
                          </>
                        )}
                      </Button>
                      <Button 
                        onClick={() => setTransformations([])}
                        variant="outline"
                      >
                        <RotateCcw className="mr-2 h-4 w-4" />
                        Reset
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Preview */}
            {preview && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Eye className="h-5 w-5" />
                      Preview
                    </span>
                    <Badge variant="secondary">
                      {preview.shape[0]} rows × {preview.shape[1]} cols
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {preview.columns.map((col: string) => (
                            <TableHead key={col}>{col}</TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {preview.preview.slice(0, 10).map((row: any, i: number) => (
                          <TableRow key={i}>
                            {preview.columns.map((col: string) => (
                              <TableCell key={col}>
                                {String(row[col]).substring(0, 50)}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
