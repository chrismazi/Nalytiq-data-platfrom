"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Download, Filter, Plus, Table } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DashboardHeader } from "@/components/dashboard-header"
import { DataTable, DataTableProps } from "@/components/data-table"
import { CrossTabBuilder } from "@/components/cross-tab-builder"
import { crosstab } from "@/lib/api"

export default function AnalysisPage() {
  const [activeDataset, setActiveDataset] = useState("eicv6")
  const [freqVar, setFreqVar] = useState("province")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tableData, setTableData] = useState<DataTableProps | null>(null)

  const handleGenerateTable = async () => {
    setLoading(true)
    setError(null)
    setTableData(null)
    try {
      // TODO: Replace with real file selection
      const dummyFile = new File(["dummy"], "dummy.csv")
      const result = await crosstab(dummyFile, [freqVar])
      if (result && result.data && result.data.length > 0) {
        const columns = Object.keys(result.data[0]).map((key) => ({ key, label: key.charAt(0).toUpperCase() + key.slice(1) }))
        setTableData({ data: result.data, columns })
      } else {
        setError("No data returned from backend.")
      }
    } catch (err: any) {
      setError(err.message || "Failed to generate table.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <DashboardHeader
        title="Data Analysis"
        description="Generate tables, cross-tabulations, and statistical analysis"
      />

      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <Select value={activeDataset} onValueChange={setActiveDataset}>
          <SelectTrigger className="w-[280px]">
            <SelectValue placeholder="Select Dataset" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="eicv6">EICV6 Survey Data 2023</SelectItem>
            <SelectItem value="health">Health Indicators 2022</SelectItem>
            <SelectItem value="economic">Economic Census 2023</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Analysis
          </Button>
        </div>
      </div>

      <Tabs defaultValue="frequency">
        <TabsList>
          <TabsTrigger value="frequency">Frequency Tables</TabsTrigger>
          <TabsTrigger value="crosstab">Cross-Tabulations</TabsTrigger>
          <TabsTrigger value="models">Statistical Models</TabsTrigger>
        </TabsList>

        <TabsContent value="frequency" className="mt-6 animate-in">
          <Card>
            <CardHeader>
              <CardTitle>Frequency Tables</CardTitle>
              <CardDescription>Generate frequency distributions for categorical variables</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="flex-1">
                    <label className="text-sm font-medium mb-1 block">Variable</label>
                    <Select defaultValue={freqVar} onValueChange={setFreqVar}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select Variable" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="province">Province</SelectItem>
                        <SelectItem value="gender">Gender</SelectItem>
                        <SelectItem value="age_group">Age Group</SelectItem>
                        <SelectItem value="education">Education Level</SelectItem>
                        <SelectItem value="income">Income Bracket</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex-1">
                    <label className="text-sm font-medium mb-1 block">Weight (Optional)</label>
                    <Select defaultValue="none">
                      <SelectTrigger>
                        <SelectValue placeholder="Select Weight" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="population">Population Weight</SelectItem>
                        <SelectItem value="household">Household Weight</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-end">
                    <Button onClick={handleGenerateTable} disabled={loading}>
                      {loading ? "Generating..." : "Generate Table"}
                    </Button>
                  </div>
                </div>

                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
                  {loading ? (
                    <div className="p-8 text-center">Loading...</div>
                  ) : error ? (
                    <div className="p-8 text-center text-red-500">{error}</div>
                  ) : tableData ? (
                    <Card>
                      <CardHeader className="py-3">
                        <div className="flex justify-between items-center">
                          <CardTitle className="text-lg">{freqVar.charAt(0).toUpperCase() + freqVar.slice(1)} Distribution</CardTitle>
                          <Button variant="outline" size="sm">
                            <Download className="h-4 w-4 mr-2" />
                            Export
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <DataTable data={tableData.data} columns={tableData.columns} />
                      </CardContent>
                    </Card>
                  ) : null}
                </motion.div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="crosstab" className="mt-6 animate-in">
          <Card>
            <CardHeader>
              <CardTitle>Cross-Tabulations</CardTitle>
              <CardDescription>Generate cross-tabulations between two or more variables</CardDescription>
            </CardHeader>
            <CardContent>
              <CrossTabBuilder />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="models" className="mt-6 animate-in">
          <Card>
            <CardHeader>
              <CardTitle>Statistical Models</CardTitle>
              <CardDescription>Run statistical models and regressions on your data</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="rounded-full bg-primary/10 p-4 mb-4">
                  <Table className="h-10 w-10 text-primary" />
                </div>
                <h3 className="text-xl font-medium mb-2">Advanced Statistical Models</h3>
                <p className="text-muted-foreground max-w-md mb-6">
                  Create regression models, cluster analyses, and other advanced statistical techniques.
                </p>
                <Button>Create New Model</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
