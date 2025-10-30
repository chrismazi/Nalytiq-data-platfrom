"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { 
  GitCompare, TrendingUp, Award, Zap, Clock,
  BarChart3, Target, CheckCircle2, XCircle, Info
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DashboardHeader } from "@/components/dashboard-header"
import { useToast } from "@/hooks/use-toast"
import { Checkbox } from "@/components/ui/checkbox"
import {
  compareModels,
  getDatasetsList
} from "@/lib/api"
import { Progress } from "@/components/ui/progress"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export default function ModelComparisonPage() {
  const { toast } = useToast()
  
  // State
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState<any>(null)
  const [target, setTarget] = useState("")
  const [selectedAlgorithms, setSelectedAlgorithms] = useState<string[]>(["xgboost", "neural_network"])
  const [comparing, setComparing] = useState(false)
  const [result, setResult] = useState<any>(null)

  const algorithms = [
    {
      id: "xgboost",
      name: "XGBoost",
      icon: Zap,
      color: "text-blue-600",
      description: "Gradient Boosting"
    },
    {
      id: "neural_network",
      name: "Neural Network",
      icon: BarChart3,
      color: "text-purple-600",
      description: "Deep Learning"
    }
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

  const handleDatasetSelect = (datasetId: string) => {
    const dataset = datasets.find(d => d.id === parseInt(datasetId))
    setSelectedDataset(dataset)
    setTarget("")
    setResult(null)
  }

  const handleAlgorithmToggle = (algorithmId: string) => {
    if (selectedAlgorithms.includes(algorithmId)) {
      if (selectedAlgorithms.length > 1) {
        setSelectedAlgorithms(selectedAlgorithms.filter(a => a !== algorithmId))
      }
    } else {
      setSelectedAlgorithms([...selectedAlgorithms, algorithmId])
    }
  }

  const handleCompare = async () => {
    if (!selectedDataset || !target || selectedAlgorithms.length < 2) {
      toast({
        title: "Missing information",
        description: "Please select dataset, target, and at least 2 algorithms",
        variant: "destructive"
      })
      return
    }

    setComparing(true)
    setResult(null)

    try {
      const response = await compareModels({
        dataset_id: selectedDataset.id,
        target,
        algorithms: selectedAlgorithms,
        test_size: 0.2
      })

      setResult(response.result)

      toast({
        title: "✅ Comparison Complete!",
        description: `Trained and compared ${selectedAlgorithms.length} models`
      })

    } catch (error: any) {
      toast({
        title: "Comparison Failed",
        description: error.message,
        variant: "destructive"
      })
    } finally {
      setComparing(false)
    }
  }

  const getAvailableColumns = () => {
    if (!selectedDataset?.columns) return []
    try {
      return JSON.parse(selectedDataset.columns)
    } catch {
      return []
    }
  }

  const getModelByName = (name: string) => {
    return result?.models?.find((m: any) => m.algorithm.toLowerCase().replace(' ', '_') === name)
  }

  const getMetricDisplay = (value: any) => {
    if (typeof value === 'number') {
      return value.toFixed(4)
    }
    return '-'
  }

  const getBestMetricIndex = (metric: string) => {
    if (!result?.models) return -1
    
    const values = result.models.map((m: any) => m.metrics?.[metric] || 0)
    const maxValue = Math.max(...values)
    return values.indexOf(maxValue)
  }

  return (
    <div className="space-y-6">
      <DashboardHeader
        title="Model Comparison"
        description="Train and compare multiple ML algorithms to find the best model"
      />

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
          <CardDescription>
            Select dataset, target variable, and algorithms to compare
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Dataset Selection */}
          <div>
            <Label>Dataset</Label>
            <Select onValueChange={handleDatasetSelect}>
              <SelectTrigger>
                <SelectValue placeholder="Select a dataset" />
              </SelectTrigger>
              <SelectContent>
                {datasets.map((dataset) => (
                  <SelectItem key={dataset.id} value={dataset.id.toString()}>
                    {dataset.name} ({dataset.num_rows} rows, {dataset.num_columns} columns)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Target Selection */}
          {selectedDataset && (
            <div>
              <Label>Target Variable</Label>
              <Select onValueChange={setTarget} value={target}>
                <SelectTrigger>
                  <SelectValue placeholder="Select target variable" />
                </SelectTrigger>
                <SelectContent>
                  {getAvailableColumns().map((col: string) => (
                    <SelectItem key={col} value={col}>
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Algorithm Selection */}
          {target && (
            <div>
              <Label className="mb-3 block">Algorithms to Compare (min 2)</Label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {algorithms.map((algo) => (
                  <div
                    key={algo.id}
                    className={`flex items-center space-x-3 p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedAlgorithms.includes(algo.id)
                        ? 'border-primary bg-primary/5'
                        : 'hover:bg-muted/50'
                    }`}
                    onClick={() => handleAlgorithmToggle(algo.id)}
                  >
                    <Checkbox
                      checked={selectedAlgorithms.includes(algo.id)}
                      onCheckedChange={() => handleAlgorithmToggle(algo.id)}
                    />
                    <algo.icon className={`h-5 w-5 ${algo.color}`} />
                    <div className="flex-1">
                      <p className="font-medium">{algo.name}</p>
                      <p className="text-sm text-muted-foreground">{algo.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compare Button */}
          {target && selectedAlgorithms.length >= 2 && (
            <Button 
              onClick={handleCompare} 
              className="w-full"
              disabled={comparing}
              size="lg"
            >
              {comparing ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Training {selectedAlgorithms.length} Models...
                </>
              ) : (
                <>
                  <GitCompare className="mr-2 h-4 w-4" />
                  Compare {selectedAlgorithms.length} Models
                </>
              )}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Winner Card */}
          <Card className="border-2 border-green-500 bg-green-50/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-green-500 rounded-full">
                    <Award className="h-8 w-8 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Best Model</p>
                    <h2 className="text-2xl font-bold">{result.comparison.best_model}</h2>
                    <p className="text-sm text-muted-foreground mt-1">
                      {result.comparison.comparison_metric}: {result.comparison.best_score?.toFixed(4)}
                    </p>
                  </div>
                </div>
                <Badge className="bg-green-500 text-white text-lg px-4 py-2">
                  Winner
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Problem Type</p>
                    <p className="text-2xl font-bold capitalize">{result.problem_type}</p>
                  </div>
                  <Target className="h-8 w-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Features Used</p>
                    <p className="text-2xl font-bold">{result.n_features}</p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Models Compared</p>
                    <p className="text-2xl font-bold">{result.models.length}</p>
                  </div>
                  <GitCompare className="h-8 w-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Time</p>
                    <p className="text-2xl font-bold">{(result.execution_time_ms / 1000).toFixed(1)}s</p>
                  </div>
                  <Clock className="h-8 w-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Metrics Comparison Table */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>
                Detailed comparison of model performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[200px]">Metric</TableHead>
                      {result.models.map((model: any, i: number) => (
                        <TableHead key={i} className="text-center">
                          {model.algorithm}
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.keys(result.models[0].metrics || {}).map((metric) => {
                      const bestIndex = getBestMetricIndex(metric)
                      return (
                        <TableRow key={metric}>
                          <TableCell className="font-medium capitalize">
                            {metric.replace(/_/g, ' ')}
                          </TableCell>
                          {result.models.map((model: any, i: number) => (
                            <TableCell key={i} className="text-center">
                              <div className="flex items-center justify-center gap-2">
                                {getMetricDisplay(model.metrics?.[metric])}
                                {i === bestIndex && (
                                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                                )}
                              </div>
                            </TableCell>
                          ))}
                        </TableRow>
                      )
                    })}
                    <TableRow>
                      <TableCell className="font-medium">Training Time</TableCell>
                      {result.models.map((model: any, i: number) => (
                        <TableCell key={i} className="text-center">
                          {(model.training_time_seconds).toFixed(2)}s
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Insights */}
          {result.comparison.insights && result.comparison.insights.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Info className="h-5 w-5" />
                  Key Insights
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {result.comparison.insights.map((insight: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                      <span>{insight}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Individual Model Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {result.models.map((model: any, i: number) => (
              <Card key={i}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{model.algorithm}</span>
                    {result.comparison.best_model === model.algorithm && (
                      <Badge className="bg-green-500">Best</Badge>
                    )}
                  </CardTitle>
                  <CardDescription>
                    {model.problem_type} model with {model.n_features} features
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Key Metrics */}
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(model.metrics || {}).slice(0, 4).map(([key, value]: [string, any]) => (
                      <div key={key} className="p-3 bg-muted rounded-lg">
                        <p className="text-xs text-muted-foreground capitalize">
                          {key.replace(/_/g, ' ')}
                        </p>
                        <p className="text-lg font-bold">
                          {typeof value === 'number' ? value.toFixed(4) : '-'}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Feature Importance Preview */}
                  {model.feature_importance && model.feature_importance.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">Top 3 Features</p>
                      <div className="space-y-1">
                        {model.feature_importance.slice(0, 3).map((item: any, j: number) => (
                          <div key={j} className="flex items-center gap-2 text-sm">
                            <span className="font-medium">{j + 1}.</span>
                            <span className="flex-1 truncate">{item.feature}</span>
                            <span className="text-muted-foreground">
                              {item.importance.toFixed(3)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Training Info */}
                  <div className="pt-3 border-t text-sm text-muted-foreground">
                    <p>Training time: {model.training_time_seconds.toFixed(2)}s</p>
                    <p>Samples: {model.n_samples_train} train / {model.n_samples_test} test</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={() => {
                setResult(null)
                setTarget("")
              }}
              className="flex-1"
            >
              New Comparison
            </Button>
            <Button 
              className="flex-1"
              onClick={() => window.location.href = '/history'}
            >
              View in History
            </Button>
          </div>
        </motion.div>
      )}
    </div>
  )
}
