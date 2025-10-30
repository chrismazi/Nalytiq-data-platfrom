"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { 
  BarChart3, LineChart, ScatterChart, PieChart, 
  Activity, TrendingUp, Layers, Grid3x3, Download,
  Settings, Sparkles, Eye, Plus
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DashboardHeader } from "@/components/dashboard-header"
import { useToast } from "@/hooks/use-toast"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { PlotlyChartFromAPI } from "@/components/plotly-chart"
import { getDatasetsList } from "@/lib/api"

export default function VisualizationsPage() {
  const { toast } = useToast()
  
  // State
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState<any>(null)
  const [chartType, setChartType] = useState("bar")
  const [columns, setColumns] = useState<any>(null)
  const [chart, setChart] = useState<any>(null)
  const [creating, setCreating] = useState(false)
  
  // Chart configuration
  const [config, setConfig] = useState<any>({})

  const chartTypes = [
    {
      id: "bar",
      name: "Bar Chart",
      icon: BarChart3,
      color: "text-blue-600",
      description: "Compare values across categories"
    },
    {
      id: "line",
      name: "Line Chart",
      icon: LineChart,
      color: "text-green-600",
      description: "Show trends over time"
    },
    {
      id: "scatter",
      name: "Scatter Plot",
      icon: ScatterChart,
      color: "text-purple-600",
      description: "Show relationships"
    },
    {
      id: "pie",
      name: "Pie Chart",
      icon: PieChart,
      color: "text-orange-600",
      description: "Show proportions"
    },
    {
      id: "histogram",
      name: "Histogram",
      icon: Activity,
      color: "text-pink-600",
      description: "Show distribution"
    },
    {
      id: "heatmap",
      name: "Heatmap",
      icon: Grid3x3,
      color: "text-red-600",
      description: "Show correlations"
    },
    {
      id: "box",
      name: "Box Plot",
      icon: Layers,
      color: "text-indigo-600",
      description: "Statistical distribution"
    },
    {
      id: "area",
      name: "Area Chart",
      icon: TrendingUp,
      color: "text-teal-600",
      description: "Cumulative trends"
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

  const handleDatasetSelect = async (datasetId: string) => {
    const dataset = datasets.find(d => d.id === parseInt(datasetId))
    setSelectedDataset(dataset)
    setChart(null)
    setConfig({})
    
    // Load columns
    try {
      const res = await fetch(`http://localhost:8000/api/viz/dataset-columns/${datasetId}`)
      const data = await res.json()
      setColumns(data.columns)
    } catch (error) {
      console.error("Failed to load columns:", error)
    }
  }

  const handleCreateChart = async () => {
    if (!selectedDataset) {
      toast({
        title: "No dataset selected",
        description: "Please select a dataset first",
        variant: "destructive"
      })
      return
    }

    setCreating(true)

    try {
      let endpoint = ""
      let payload: any = {
        dataset_id: selectedDataset.id,
        ...config
      }

      switch (chartType) {
        case "bar":
          endpoint = "/api/viz/bar-chart"
          break
        case "line":
          endpoint = "/api/viz/line-chart"
          payload.y_cols = config.y_cols || [config.y_col]
          break
        case "scatter":
          endpoint = "/api/viz/scatter-plot"
          break
        case "pie":
          endpoint = "/api/viz/pie-chart"
          break
        case "histogram":
          endpoint = "/api/viz/histogram"
          break
        case "heatmap":
          endpoint = "/api/viz/heatmap"
          break
        case "box":
          endpoint = "/api/viz/box-plot"
          break
        case "area":
          endpoint = "/api/viz/area-chart"
          payload.y_cols = config.y_cols || [config.y_col]
          break
        default:
          throw new Error("Unsupported chart type")
      }

      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || "Failed to create chart")
      }

      const data = await res.json()
      setChart(data.chart)

      toast({
        title: "✅ Chart Created!",
        description: `${chartTypes.find(c => c.id === chartType)?.name} generated successfully`
      })

    } catch (error: any) {
      toast({
        title: "Chart creation failed",
        description: error.message,
        variant: "destructive"
      })
    } finally {
      setCreating(false)
    }
  }

  const getChartIcon = (id: string) => {
    const chart = chartTypes.find(c => c.id === id)
    return chart ? <chart.icon className={`h-5 w-5 ${chart.color}`} /> : null
  }

  return (
    <div className="space-y-6">
      <DashboardHeader
        title="Interactive Visualizations"
        description="Create beautiful, interactive charts with Plotly"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Chart Configuration
              </CardTitle>
              <CardDescription>
                Select data and chart type
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Dataset Selection */}
              <div>
                <Label>Dataset</Label>
                <Select onValueChange={handleDatasetSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select dataset" />
                  </SelectTrigger>
                  <SelectContent>
                    {datasets.map((dataset) => (
                      <SelectItem key={dataset.id} value={dataset.id.toString()}>
                        {dataset.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Chart Type Selection */}
              {selectedDataset && (
                <div>
                  <Label className="mb-3 block">Chart Type</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {chartTypes.map((type) => (
                      <button
                        key={type.id}
                        onClick={() => {
                          setChartType(type.id)
                          setConfig({})
                          setChart(null)
                        }}
                        className={`p-3 border rounded-lg text-left transition-all ${
                          chartType === type.id
                            ? 'border-primary bg-primary/5 ring-2 ring-primary'
                            : 'hover:border-primary/50'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <type.icon className={`h-4 w-4 ${type.color}`} />
                          <span className="text-sm font-medium">{type.name}</span>
                        </div>
                        <p className="text-xs text-muted-foreground">{type.description}</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Dynamic Configuration Fields */}
              {selectedDataset && columns && (
                <div className="space-y-3">
                  {chartType === "bar" && (
                    <>
                      <div>
                        <Label>X-Axis (Category)</Label>
                        <Select onValueChange={(v) => setConfig({...config, x_col: v})}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            {columns.all.map((col: string) => (
                              <SelectItem key={col} value={col}>{col}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Y-Axis (Value)</Label>
                        <Select onValueChange={(v) => setConfig({...config, y_col: v})}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            {columns.numeric.map((col: string) => (
                              <SelectItem key={col} value={col}>{col}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </>
                  )}

                  {chartType === "line" && (
                    <>
                      <div>
                        <Label>X-Axis</Label>
                        <Select onValueChange={(v) => setConfig({...config, x_col: v})}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            {columns.all.map((col: string) => (
                              <SelectItem key={col} value={col}>{col}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Y-Axis (Value)</Label>
                        <Select onValueChange={(v) => setConfig({...config, y_col: v})}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            {columns.numeric.map((col: string) => (
                              <SelectItem key={col} value={col}>{col}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </>
                  )}

                  {chartType === "scatter" && (
                    <>
                      <div>
                        <Label>X-Axis</Label>
                        <Select onValueChange={(v) => setConfig({...config, x_col: v})}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            {columns.numeric.map((col: string) => (
                              <SelectItem key={col} value={col}>{col}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Y-Axis</Label>
                        <Select onValueChange={(v) => setConfig({...config, y_col: v})}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            {columns.numeric.map((col: string) => (
                              <SelectItem key={col} value={col}>{col}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </>
                  )}

                  {chartType === "pie" && (
                    <>
                      <div>
                        <Label>Labels</Label>
                        <Select onValueChange={(v) => setConfig({...config, names_col: v})}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            {columns.categorical.map((col: string) => (
                              <SelectItem key={col} value={col}>{col}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Values</Label>
                        <Select onValueChange={(v) => setConfig({...config, values_col: v})}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            {columns.numeric.map((col: string) => (
                              <SelectItem key={col} value={col}>{col}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </>
                  )}

                  {chartType === "histogram" && (
                    <div>
                      <Label>Column</Label>
                      <Select onValueChange={(v) => setConfig({...config, col: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select column" />
                        </SelectTrigger>
                        <SelectContent>
                          {columns.numeric.map((col: string) => (
                            <SelectItem key={col} value={col}>{col}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  {chartType === "box" && (
                    <div>
                      <Label>Value Column</Label>
                      <Select onValueChange={(v) => setConfig({...config, y_col: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select column" />
                        </SelectTrigger>
                        <SelectContent>
                          {columns.numeric.map((col: string) => (
                            <SelectItem key={col} value={col}>{col}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  {/* Title */}
                  <div>
                    <Label>Chart Title (Optional)</Label>
                    <Input
                      placeholder="Enter chart title"
                      onChange={(e) => setConfig({...config, title: e.target.value})}
                    />
                  </div>

                  <Button 
                    onClick={handleCreateChart}
                    disabled={creating || !Object.keys(config).length}
                    className="w-full"
                  >
                    {creating ? (
                      <>
                        <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        Creating Chart...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Create Chart
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Chart Display */}
        <div className="lg:col-span-2">
          <Card className="h-[600px]">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  {getChartIcon(chartType)}
                  {chartTypes.find(c => c.id === chartType)?.name || "Chart"}
                </span>
                {chart && (
                  <Button variant="outline" size="sm">
                    <Download className="mr-2 h-4 w-4" />
                    Export
                  </Button>
                )}
              </CardTitle>
              <CardDescription>
                {chart ? "Interactive visualization" : "Configure and create your chart"}
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[480px]">
              {chart ? (
                <PlotlyChartFromAPI chart={chart} className="h-full" />
              ) : (
                <div className="h-full flex items-center justify-center text-center">
                  <div>
                    <Eye className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                    <p className="text-lg font-medium mb-2">No Chart Yet</p>
                    <p className="text-muted-foreground">
                      Select a dataset and chart type, then click "Create Chart"
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
