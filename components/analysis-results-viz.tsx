"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Download, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { motion } from "framer-motion"

interface AnalysisResultsVizProps {
  type: string
  data: any
  title: string
  onExport?: () => void
}

const COLORS = [
  '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981',
  '#06b6d4', '#6366f1', '#f43f5e', '#84cc16', '#a855f7'
]

export function AnalysisResultsViz({ type, data, title, onExport }: AnalysisResultsVizProps) {
  if (!data) return null

  const renderGroupedStats = () => {
    const chartData = data.data || []
    
    return (
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{data.n_groups}</div>
              <p className="text-xs text-muted-foreground">Groups</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{data.max?.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">Maximum</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{data.min?.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">Minimum</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{data.mean?.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">Average</p>
            </CardContent>
          </Card>
        </div>

        {/* Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {data.aggregation.charAt(0).toUpperCase() + data.aggregation.slice(1)} by {data.group_by}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="category" className="text-xs" />
                <YAxis className="text-xs" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px'
                  }}
                />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Data Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Detailed Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-[400px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-muted">
                  <tr>
                    <th className="text-left p-2">Rank</th>
                    <th className="text-left p-2">{data.group_by}</th>
                    <th className="text-right p-2">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {chartData.map((item: any, index: number) => (
                    <tr key={index} className="border-b">
                      <td className="p-2">#{index + 1}</td>
                      <td className="p-2 font-medium">{item.category}</td>
                      <td className="p-2 text-right">{item.value.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderCrosstab = () => {
    const tableData = data.data || []
    const rowLabels = data.row_labels || []
    const colLabels = data.column_labels || []

    return (
      <div className="space-y-6">
        {/* Summary */}
        <Card className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-950/30 dark:to-blue-950/30">
          <CardContent className="pt-6">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold">{rowLabels.length}</div>
                <p className="text-xs text-muted-foreground">Row Categories</p>
              </div>
              <div>
                <div className="text-2xl font-bold">{colLabels.length}</div>
                <p className="text-xs text-muted-foreground">Column Categories</p>
              </div>
              <div>
                <div className="text-2xl font-bold">{data.grand_total?.toFixed(0)}</div>
                <p className="text-xs text-muted-foreground">Grand Total</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Cross-tabulation Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {data.row_variable} × {data.column_variable}
            </CardTitle>
            <CardDescription>
              {data.normalized ? 'Normalized percentages' : 'Absolute values'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-muted">
                    <th className="p-2 text-left border font-medium">{data.row_variable}</th>
                    {colLabels.map((col: string) => (
                      <th key={col} className="p-2 text-right border font-medium">{col}</th>
                    ))}
                    <th className="p-2 text-right border font-bold bg-muted/50">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {tableData.map((row: any, index: number) => (
                    <tr key={index} className="hover:bg-muted/50">
                      <td className="p-2 border font-medium">{row.category}</td>
                      {colLabels.map((col: string) => (
                        <td key={col} className="p-2 text-right border">
                          {row[col]?.toFixed(data.normalized ? 1 : 0)}
                          {data.normalized && '%'}
                        </td>
                      ))}
                      <td className="p-2 text-right border font-bold bg-muted/20">
                        {data.row_totals?.[row.category]?.toFixed(0)}
                      </td>
                    </tr>
                  ))}
                  <tr className="bg-muted font-bold">
                    <td className="p-2 border">Total</td>
                    {colLabels.map((col: string) => (
                      <td key={col} className="p-2 text-right border">
                        {data.column_totals?.[col]?.toFixed(0)}
                      </td>
                    ))}
                    <td className="p-2 text-right border bg-muted/50">
                      {data.grand_total?.toFixed(0)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderTopN = () => {
    const chartData = data.data || []

    return (
      <div className="space-y-6">
        {/* Horizontal Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Top {data.n} - {data.group_col} by {data.value_col}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {chartData.map((item: any, index: number) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="space-y-2"
                >
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="w-8 text-center">
                        {index + 1}
                      </Badge>
                      <span className="font-medium">{item.name}</span>
                    </div>
                    <span className="font-bold text-blue-600">{item.value.toFixed(2)}</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(item.value / chartData[0].value) * 100}%` }}
                      transition={{ duration: 0.5, delay: index * 0.05 }}
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderComparison = () => {
    const chartData = data.data || []

    return (
      <div className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{data.n_categories}</div>
              <p className="text-xs text-muted-foreground">Categories</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{data.overall_mean?.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">Overall Mean</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{Math.max(...chartData.map((d: any) => d.mean)).toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">Highest Mean</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{Math.min(...chartData.map((d: any) => d.mean)).toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">Lowest Mean</p>
            </CardContent>
          </Card>
        </div>

        {/* Comparison Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Mean Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="mean" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Detailed Comparison Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Statistical Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="p-2 text-left">Category</th>
                    <th className="p-2 text-right">Count</th>
                    <th className="p-2 text-right">Mean</th>
                    <th className="p-2 text-right">Median</th>
                    <th className="p-2 text-right">Std Dev</th>
                    <th className="p-2 text-right">Min</th>
                    <th className="p-2 text-right">Max</th>
                    <th className="p-2 text-center">Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {chartData.map((item: any, index: number) => (
                    <tr key={index} className="border-b hover:bg-muted/50">
                      <td className="p-2 font-medium">{item.category}</td>
                      <td className="p-2 text-right">{item.count}</td>
                      <td className="p-2 text-right font-bold">{item.mean.toFixed(2)}</td>
                      <td className="p-2 text-right">{item.median.toFixed(2)}</td>
                      <td className="p-2 text-right">{item.std.toFixed(2)}</td>
                      <td className="p-2 text-right">{item.min.toFixed(2)}</td>
                      <td className="p-2 text-right">{item.max.toFixed(2)}</td>
                      <td className="p-2 text-center">
                        {item.mean > data.overall_mean ? (
                          <TrendingUp className="h-4 w-4 text-green-500 inline" />
                        ) : item.mean < data.overall_mean ? (
                          <TrendingDown className="h-4 w-4 text-red-500 inline" />
                        ) : (
                          <Minus className="h-4 w-4 text-gray-500 inline" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderMLResults = () => {
    const metrics = data.metrics || {}
    const featureImportance = (data.feature_importance || []).slice(0, 10)
    const isClassification = data.model_type === 'classification'

    return (
      <div className="space-y-6">
        {/* Model Overview */}
        <Card className="bg-gradient-to-br from-red-50 to-pink-50 dark:from-red-950/30 dark:to-pink-950/30">
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-sm text-muted-foreground">Model Type</div>
                <Badge className="mt-1">{data.model_type}</Badge>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Samples</div>
                <div className="text-xl font-bold">{data.n_samples}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Features</div>
                <div className="text-xl font-bold">{data.n_features}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">
                  {isClassification ? 'Accuracy' : 'R² Score'}
                </div>
                <div className="text-xl font-bold">
                  {(isClassification ? metrics.test_accuracy : metrics.test_r2)?.toFixed(3)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Performance Metrics */}
        <div className="grid md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Model Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {isClassification ? (
                  <>
                    <MetricRow label="Test Accuracy" value={metrics.test_accuracy} />
                    <MetricRow label="Precision" value={metrics.precision} />
                    <MetricRow label="Recall" value={metrics.recall} />
                    <MetricRow label="F1 Score" value={metrics.f1_score} />
                  </>
                ) : (
                  <>
                    <MetricRow label="Test R²" value={metrics.test_r2} />
                    <MetricRow label="Test RMSE" value={metrics.test_rmse} decimal={2} />
                    <MetricRow label="Test MAE" value={metrics.test_mae} decimal={2} />
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Cross-Validation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <MetricRow 
                  label={isClassification ? "CV Accuracy" : "CV R²"} 
                  value={isClassification ? metrics.cv_accuracy_mean : metrics.cv_r2_mean} 
                />
                <MetricRow 
                  label="Std Deviation" 
                  value={isClassification ? metrics.cv_accuracy_std : metrics.cv_r2_std} 
                />
                <div className="text-sm text-muted-foreground mt-4">
                  Consistent performance across folds indicates good model stability
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Feature Importance */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top 10 Feature Importance</CardTitle>
            <CardDescription>Most influential features in predictions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {featureImportance.map((item: any, index: number) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="space-y-2"
                >
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{item.feature}</span>
                    <span className="text-blue-600 font-bold">{item.importance_pct.toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${item.importance_pct}%` }}
                      transition={{ duration: 0.5, delay: index * 0.05 }}
                      className="h-full bg-gradient-to-r from-red-500 to-pink-500"
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Insights */}
        {data.insights && data.insights.length > 0 && (
          <Card className="border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20">
            <CardHeader>
              <CardTitle className="text-base">Model Insights</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {data.insights.map((insight: string, index: number) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2" />
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    )
  }

  const renderContent = () => {
    switch (type) {
      case 'grouped-stats':
        return renderGroupedStats()
      case 'crosstab':
        return renderCrosstab()
      case 'top-n':
        return renderTopN()
      case 'comparison':
        return renderComparison()
      case 'ml-model':
        return renderMLResults()
      default:
        return <div>Unknown analysis type</div>
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="border-2">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{title}</CardTitle>
              <CardDescription>Analysis results and visualizations</CardDescription>
            </div>
            {onExport && (
              <Button onClick={onExport} variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {renderContent()}
        </CardContent>
      </Card>
    </motion.div>
  )
}

function MetricRow({ label, value, decimal = 3 }: { label: string; value: number; decimal?: number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm font-bold">{value?.toFixed(decimal)}</span>
        <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
            style={{ width: `${Math.min(value * 100, 100)}%` }}
          />
        </div>
      </div>
    </div>
  )
}
