"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { 
  History, Star, Trash2, Eye, Play, GitCompare, 
  Filter, Search, Calendar, Clock, TrendingUp,
  BarChart3, Table as TableIcon, ListFilter, Activity
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DashboardHeader } from "@/components/dashboard-header"
import { AnalysisResultsViz } from "@/components/analysis-results-viz"
import { useToast } from "@/hooks/use-toast"
import {
  getAnalysisHistory,
  getAnalysisDetail,
  toggleAnalysisFavorite,
  deleteAnalysis,
  getHistoryStats
} from "@/lib/api"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

export default function AnalysisHistoryPage() {
  const { toast } = useToast()
  
  // State
  const [analyses, setAnalyses] = useState<any[]>([])
  const [filteredAnalyses, setFilteredAnalyses] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<any>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [filterType, setFilterType] = useState("all")
  const [selectedAnalysis, setSelectedAnalysis] = useState<any>(null)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)

  // Load data
  useEffect(() => {
    loadHistory()
    loadStats()
  }, [])

  // Filter analyses
  useEffect(() => {
    let filtered = analyses

    // Filter by type
    if (filterType !== "all") {
      if (filterType === "favorites") {
        filtered = filtered.filter(a => a.is_favorite)
      } else {
        filtered = filtered.filter(a => a.analysis_type === filterType)
      }
    }

    // Search
    if (searchQuery) {
      filtered = filtered.filter(a => 
        a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.analysis_type.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    setFilteredAnalyses(filtered)
  }, [analyses, filterType, searchQuery])

  const loadHistory = async () => {
    try {
      setLoading(true)
      const response = await getAnalysisHistory({ limit: 100 })
      setAnalyses(response.analyses || [])
    } catch (error: any) {
      toast({
        title: "Failed to load history",
        description: error.message,
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await getHistoryStats()
      setStats(response.stats)
    } catch (error) {
      console.error("Failed to load stats:", error)
    }
  }

  const handleViewDetails = async (analysisId: number) => {
    try {
      const response = await getAnalysisDetail(analysisId)
      setSelectedAnalysis(response.analysis)
      setDetailDialogOpen(true)
    } catch (error: any) {
      toast({
        title: "Failed to load analysis",
        description: error.message,
        variant: "destructive"
      })
    }
  }

  const handleToggleFavorite = async (analysisId: number) => {
    try {
      await toggleAnalysisFavorite(analysisId)
      
      // Update local state
      setAnalyses(prev => prev.map(a => 
        a.id === analysisId ? { ...a, is_favorite: !a.is_favorite } : a
      ))
      
      toast({
        title: "Success",
        description: "Favorite status updated"
      })
    } catch (error: any) {
      toast({
        title: "Failed to update favorite",
        description: error.message,
        variant: "destructive"
      })
    }
  }

  const handleDelete = async (analysisId: number) => {
    if (!confirm("Are you sure you want to delete this analysis?")) return

    try {
      await deleteAnalysis(analysisId)
      
      // Remove from local state
      setAnalyses(prev => prev.filter(a => a.id !== analysisId))
      
      toast({
        title: "Success",
        description: "Analysis deleted"
      })
    } catch (error: any) {
      toast({
        title: "Failed to delete",
        description: error.message,
        variant: "destructive"
      })
    }
  }

  const getAnalysisTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'grouped-stats': 'bg-blue-500',
      'crosstab': 'bg-purple-500',
      'top-n': 'bg-green-500',
      'comparison': 'bg-orange-500',
      'ml-model': 'bg-pink-500'
    }
    return colors[type] || 'bg-gray-500'
  }

  const getAnalysisTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'grouped-stats': 'Grouped Statistics',
      'crosstab': 'Cross-Tabulation',
      'top-n': 'Top N Analysis',
      'comparison': 'Category Comparison',
      'ml-model': 'ML Prediction'
    }
    return labels[type] || type
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (days === 0) return "Today"
    if (days === 1) return "Yesterday"
    if (days < 7) return `${days} days ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="space-y-6">
      <DashboardHeader
        title="Analysis History"
        description="View, manage, and re-run your past analyses"
      />

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Analyses</p>
                  <p className="text-2xl font-bold">{stats.total_analyses}</p>
                </div>
                <History className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Saved</p>
                  <p className="text-2xl font-bold">{stats.saved_analyses}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Favorites</p>
                  <p className="text-2xl font-bold">{stats.favorite_analyses}</p>
                </div>
                <Star className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">This Week</p>
                  <p className="text-2xl font-bold">
                    {stats.recent_activity?.reduce((sum: number, day: any) => sum + day.count, 0) || 0}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters and Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search analyses..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-full md:w-[200px]">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="favorites">Favorites</SelectItem>
                <SelectItem value="grouped-stats">Grouped Stats</SelectItem>
                <SelectItem value="crosstab">Cross-Tabulation</SelectItem>
                <SelectItem value="top-n">Top N</SelectItem>
                <SelectItem value="comparison">Comparison</SelectItem>
                <SelectItem value="ml-model">ML Models</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Analyses List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Analyses</CardTitle>
          <CardDescription>
            {filteredAnalyses.length} {filteredAnalyses.length === 1 ? 'analysis' : 'analyses'} found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="mt-4 text-muted-foreground">Loading analyses...</p>
            </div>
          ) : filteredAnalyses.length === 0 ? (
            <div className="text-center py-12">
              <History className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-lg font-medium mb-2">No analyses found</p>
              <p className="text-muted-foreground">
                {searchQuery || filterType !== "all" 
                  ? "Try adjusting your filters"
                  : "Start by uploading data and running analyses"
                }
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredAnalyses.map((analysis) => (
                <motion.div
                  key={analysis.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className={getAnalysisTypeColor(analysis.analysis_type)}>
                          {getAnalysisTypeLabel(analysis.analysis_type)}
                        </Badge>
                        {analysis.is_favorite && (
                          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        )}
                      </div>
                      
                      <h3 className="font-semibold text-lg mb-1 truncate">
                        {analysis.title}
                      </h3>
                      
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {formatDate(analysis.created_at)}
                        </div>
                        {analysis.execution_time_ms && (
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {analysis.execution_time_ms}ms
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handleViewDetails(analysis.id)}
                        title="View details"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handleToggleFavorite(analysis.id)}
                        title={analysis.is_favorite ? "Remove from favorites" : "Add to favorites"}
                      >
                        <Star className={`h-4 w-4 ${analysis.is_favorite ? 'fill-yellow-400 text-yellow-400' : ''}`} />
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handleDelete(analysis.id)}
                        title="Delete analysis"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedAnalysis?.title}</DialogTitle>
            <DialogDescription>
              {selectedAnalysis && (
                <div className="flex items-center gap-4 text-sm">
                  <Badge className={getAnalysisTypeColor(selectedAnalysis.analysis_type)}>
                    {getAnalysisTypeLabel(selectedAnalysis.analysis_type)}
                  </Badge>
                  <span>{formatDate(selectedAnalysis.created_at)}</span>
                  {selectedAnalysis.execution_time_ms && (
                    <span>{selectedAnalysis.execution_time_ms}ms</span>
                  )}
                </div>
              )}
            </DialogDescription>
          </DialogHeader>

          {selectedAnalysis && (
            <div className="mt-4">
              <AnalysisResultsViz
                type={selectedAnalysis.analysis_type}
                data={selectedAnalysis.results}
                title={selectedAnalysis.title}
              />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
