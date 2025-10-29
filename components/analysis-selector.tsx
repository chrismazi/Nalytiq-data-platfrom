"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  BarChart3, 
  TrendingUp, 
  Grid3x3, 
  Award,
  LineChart,
  PieChart,
  Brain,
  Download
} from "lucide-react"
import { motion } from "framer-motion"

interface Column {
  name: string
  type: string
  unique: number
  missing: number
}

interface AnalysisSelectorProps {
  columns: Record<string, any>
  datasetId: number
  onAnalyze: (type: string, config: any) => void
  loading?: boolean
}

export function AnalysisSelector({ columns, datasetId, onAnalyze, loading }: AnalysisSelectorProps) {
  const [selectedAnalysis, setSelectedAnalysis] = useState<string>('')
  
  // Extract column information
  const columnNames = Object.keys(columns)
  const numericColumns = columnNames.filter(col => 
    columns[col].dtype?.includes('int') || 
    columns[col].dtype?.includes('float')
  )
  const categoricalColumns = columnNames.filter(col => 
    columns[col].dtype === 'object' || 
    columns[col].dtype === 'category' ||
    (columns[col].unique && columns[col].unique < 50)
  )
  
  // State for different analysis types
  const [groupedStatsConfig, setGroupedStatsConfig] = useState({
    groupBy: '',
    valueCol: '',
    aggregation: 'mean'
  })
  
  const [crosstabConfig, setCrosstabConfig] = useState({
    rowCol: '',
    colCol: '',
    valueCol: '',
    aggfunc: 'count',
    normalize: false
  })
  
  const [topNConfig, setTopNConfig] = useState({
    groupCol: '',
    valueCol: '',
    n: 10,
    ascending: false
  })
  
  const [comparisonConfig, setComparisonConfig] = useState({
    categoryCol: '',
    valueCol: ''
  })
  
  const [mlConfig, setMLConfig] = useState({
    target: '',
    features: [] as string[],
    testSize: 0.2,
    nEstimators: 100
  })

  const analysisTypes = [
    {
      id: 'grouped-stats',
      name: 'Grouped Statistics',
      description: 'Aggregate data by categories',
      icon: BarChart3,
      color: 'text-blue-600',
      bg: 'bg-blue-50 dark:bg-blue-950/30'
    },
    {
      id: 'crosstab',
      name: 'Cross-Tabulation',
      description: 'Create pivot tables',
      icon: Grid3x3,
      color: 'text-purple-600',
      bg: 'bg-purple-50 dark:bg-purple-950/30'
    },
    {
      id: 'top-n',
      name: 'Top N Analysis',
      description: 'Rank records by value',
      icon: Award,
      color: 'text-yellow-600',
      bg: 'bg-yellow-50 dark:bg-yellow-950/30'
    },
    {
      id: 'comparison',
      name: 'Category Comparison',
      description: 'Compare statistics across groups',
      icon: TrendingUp,
      color: 'text-green-600',
      bg: 'bg-green-50 dark:bg-green-950/30'
    },
    {
      id: 'ml-model',
      name: 'ML Prediction',
      description: 'Train machine learning models',
      icon: Brain,
      color: 'text-red-600',
      bg: 'bg-red-50 dark:bg-red-950/30'
    }
  ]

  const aggregations = ['mean', 'sum', 'count', 'min', 'max', 'median', 'std']

  const handleRunAnalysis = () => {
    if (!selectedAnalysis) return

    switch (selectedAnalysis) {
      case 'grouped-stats':
        if (groupedStatsConfig.groupBy && groupedStatsConfig.valueCol) {
          onAnalyze('grouped-stats', groupedStatsConfig)
        }
        break
      case 'crosstab':
        if (crosstabConfig.rowCol && crosstabConfig.colCol) {
          onAnalyze('crosstab', crosstabConfig)
        }
        break
      case 'top-n':
        if (topNConfig.groupCol && topNConfig.valueCol) {
          onAnalyze('top-n', topNConfig)
        }
        break
      case 'comparison':
        if (comparisonConfig.categoryCol && comparisonConfig.valueCol) {
          onAnalyze('comparison', comparisonConfig)
        }
        break
      case 'ml-model':
        if (mlConfig.target) {
          onAnalyze('ml-model', mlConfig)
        }
        break
    }
  }

  const isConfigValid = () => {
    switch (selectedAnalysis) {
      case 'grouped-stats':
        return groupedStatsConfig.groupBy && groupedStatsConfig.valueCol
      case 'crosstab':
        return crosstabConfig.rowCol && crosstabConfig.colCol
      case 'top-n':
        return topNConfig.groupCol && topNConfig.valueCol
      case 'comparison':
        return comparisonConfig.categoryCol && comparisonConfig.valueCol
      case 'ml-model':
        return mlConfig.target
      default:
        return false
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <LineChart className="h-5 w-5" />
          Advanced Analytics
        </CardTitle>
        <CardDescription>
          Choose an analysis type and configure parameters
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={selectedAnalysis} onValueChange={setSelectedAnalysis} className="space-y-4">
          {/* Analysis Type Selection */}
          <TabsList className="grid grid-cols-5 h-auto p-1">
            {analysisTypes.map(type => (
              <TabsTrigger 
                key={type.id} 
                value={type.id}
                className="flex flex-col items-center gap-1 py-3 data-[state=active]:bg-background"
              >
                <type.icon className={`h-5 w-5 ${type.color}`} />
                <span className="text-xs">{type.name.split(' ')[0]}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          {/* Grouped Statistics Configuration */}
          <TabsContent value="grouped-stats" className="space-y-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg">
              <div className="flex items-start gap-2 mb-4">
                <BarChart3 className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-900 dark:text-blue-100">Grouped Statistics</h4>
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    Aggregate numeric values by categorical groups
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Group By (Categorical)</Label>
                    <Select
                      value={groupedStatsConfig.groupBy}
                      onValueChange={(val) => setGroupedStatsConfig(prev => ({ ...prev, groupBy: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select column" />
                      </SelectTrigger>
                      <SelectContent>
                        {categoricalColumns.map(col => (
                          <SelectItem key={col} value={col}>
                            {col} ({columns[col].unique} unique)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Value Column (Numeric)</Label>
                    <Select
                      value={groupedStatsConfig.valueCol}
                      onValueChange={(val) => setGroupedStatsConfig(prev => ({ ...prev, valueCol: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select column" />
                      </SelectTrigger>
                      <SelectContent>
                        {numericColumns.map(col => (
                          <SelectItem key={col} value={col}>{col}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Aggregation Function</Label>
                    <Select
                      value={groupedStatsConfig.aggregation}
                      onValueChange={(val) => setGroupedStatsConfig(prev => ({ ...prev, aggregation: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {aggregations.map(agg => (
                          <SelectItem key={agg} value={agg} className="capitalize">{agg}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Crosstab Configuration */}
          <TabsContent value="crosstab" className="space-y-4">
            <div className="p-4 bg-purple-50 dark:bg-purple-950/30 rounded-lg">
              <div className="flex items-start gap-2 mb-4">
                <Grid3x3 className="h-5 w-5 text-purple-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-purple-900 dark:text-purple-100">Cross-Tabulation</h4>
                  <p className="text-sm text-purple-700 dark:text-purple-300">
                    Create pivot tables to analyze relationships
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Row Variable</Label>
                    <Select
                      value={crosstabConfig.rowCol}
                      onValueChange={(val) => setCrosstabConfig(prev => ({ ...prev, rowCol: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select column" />
                      </SelectTrigger>
                      <SelectContent>
                        {categoricalColumns.map(col => (
                          <SelectItem key={col} value={col}>{col}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Column Variable</Label>
                    <Select
                      value={crosstabConfig.colCol}
                      onValueChange={(val) => setCrosstabConfig(prev => ({ ...prev, colCol: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select column" />
                      </SelectTrigger>
                      <SelectContent>
                        {categoricalColumns.map(col => (
                          <SelectItem key={col} value={col}>{col}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Value Column (Optional)</Label>
                    <Select
                      value={crosstabConfig.valueCol}
                      onValueChange={(val) => setCrosstabConfig(prev => ({ ...prev, valueCol: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Count if empty" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">Count</SelectItem>
                        {numericColumns.map(col => (
                          <SelectItem key={col} value={col}>{col}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Aggregation</Label>
                    <Select
                      value={crosstabConfig.aggfunc}
                      onValueChange={(val) => setCrosstabConfig(prev => ({ ...prev, aggfunc: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {aggregations.map(agg => (
                          <SelectItem key={agg} value={agg} className="capitalize">{agg}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Top N Configuration */}
          <TabsContent value="top-n" className="space-y-4">
            <div className="p-4 bg-yellow-50 dark:bg-yellow-950/30 rounded-lg">
              <div className="flex items-start gap-2 mb-4">
                <Award className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-yellow-900 dark:text-yellow-100">Top N Analysis</h4>
                  <p className="text-sm text-yellow-700 dark:text-yellow-300">
                    Identify top or bottom performers
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label>Category Column</Label>
                    <Select
                      value={topNConfig.groupCol}
                      onValueChange={(val) => setTopNConfig(prev => ({ ...prev, groupCol: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select column" />
                      </SelectTrigger>
                      <SelectContent>
                        {categoricalColumns.map(col => (
                          <SelectItem key={col} value={col}>{col}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Value Column</Label>
                    <Select
                      value={topNConfig.valueCol}
                      onValueChange={(val) => setTopNConfig(prev => ({ ...prev, valueCol: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select column" />
                      </SelectTrigger>
                      <SelectContent>
                        {numericColumns.map(col => (
                          <SelectItem key={col} value={col}>{col}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Number of Items</Label>
                    <Select
                      value={String(topNConfig.n)}
                      onValueChange={(val) => setTopNConfig(prev => ({ ...prev, n: Number(val) }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[5, 10, 15, 20, 25].map(n => (
                          <SelectItem key={n} value={String(n)}>Top {n}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Comparison Configuration */}
          <TabsContent value="comparison" className="space-y-4">
            <div className="p-4 bg-green-50 dark:bg-green-950/30 rounded-lg">
              <div className="flex items-start gap-2 mb-4">
                <TrendingUp className="h-5 w-5 text-green-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-green-900 dark:text-green-100">Category Comparison</h4>
                  <p className="text-sm text-green-700 dark:text-green-300">
                    Compare statistics across different categories
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Category Column</Label>
                    <Select
                      value={comparisonConfig.categoryCol}
                      onValueChange={(val) => setComparisonConfig(prev => ({ ...prev, categoryCol: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select column" />
                      </SelectTrigger>
                      <SelectContent>
                        {categoricalColumns.map(col => (
                          <SelectItem key={col} value={col}>{col}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Value Column</Label>
                    <Select
                      value={comparisonConfig.valueCol}
                      onValueChange={(val) => setComparisonConfig(prev => ({ ...prev, valueCol: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select column" />
                      </SelectTrigger>
                      <SelectContent>
                        {numericColumns.map(col => (
                          <SelectItem key={col} value={col}>{col}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* ML Model Configuration */}
          <TabsContent value="ml-model" className="space-y-4">
            <div className="p-4 bg-red-50 dark:bg-red-950/30 rounded-lg">
              <div className="flex items-start gap-2 mb-4">
                <Brain className="h-5 w-5 text-red-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-red-900 dark:text-red-100">Machine Learning Model</h4>
                  <p className="text-sm text-red-700 dark:text-red-300">
                    Train predictive models with Random Forest
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid gap-4">
                  <div className="space-y-2">
                    <Label>Target Variable (What to predict)</Label>
                    <Select
                      value={mlConfig.target}
                      onValueChange={(val) => setMLConfig(prev => ({ ...prev, target: val }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select target" />
                      </SelectTrigger>
                      <SelectContent>
                        {columnNames.map(col => (
                          <SelectItem key={col} value={col}>
                            {col} ({columns[col].dtype})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Test Size</Label>
                      <Select
                        value={String(mlConfig.testSize)}
                        onValueChange={(val) => setMLConfig(prev => ({ ...prev, testSize: Number(val) }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0.1">10%</SelectItem>
                          <SelectItem value="0.2">20%</SelectItem>
                          <SelectItem value="0.3">30%</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Number of Trees</Label>
                      <Select
                        value={String(mlConfig.nEstimators)}
                        onValueChange={(val) => setMLConfig(prev => ({ ...prev, nEstimators: Number(val) }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="50">50</SelectItem>
                          <SelectItem value="100">100</SelectItem>
                          <SelectItem value="200">200</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="text-sm text-muted-foreground p-3 bg-background rounded border">
                    <p>Features: All columns except target (automatic)</p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Run Analysis Button */}
        <div className="mt-6 flex gap-2">
          <Button 
            onClick={handleRunAnalysis} 
            disabled={!isConfigValid() || loading}
            className="flex-1"
            size="lg"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Analyzing...
              </>
            ) : (
              <>
                <BarChart3 className="h-4 w-4 mr-2" />
                Run Analysis
              </>
            )}
          </Button>
        </div>

        {!selectedAnalysis && (
          <div className="mt-4 text-center text-sm text-muted-foreground">
            Select an analysis type above to get started
          </div>
        )}
      </CardContent>
    </Card>
  )
}
