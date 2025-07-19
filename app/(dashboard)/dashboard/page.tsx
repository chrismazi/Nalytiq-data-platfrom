"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Download, Filter, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DashboardHeader } from "@/components/dashboard-header"
import { DateRangePicker } from "@/components/date-range-picker"
import { PopulationChart } from "@/components/charts/population-chart"
import { GDPChart } from "@/components/charts/gdp-chart"
import { InflationChart } from "@/components/charts/inflation-chart"
import { LiteracyChart } from "@/components/charts/literacy-chart"
import { HealthMetricsChart } from "@/components/charts/health-metrics-chart"
import { GenerateReportDialog } from "@/components/generate-report-dialog"

export default function DashboardPage() {
  const [isGeneratingReport, setIsGeneratingReport] = useState(false)
  const [showReportDialog, setShowReportDialog] = useState(false)

  const handleGenerateReport = () => {
    setIsGeneratingReport(true)
    setShowReportDialog(true)

    // Simulate report generation
    setTimeout(() => {
      setIsGeneratingReport(false)
    }, 2000)
  }

  return (
    <div className="space-y-6">
      <DashboardHeader
        title="National Statistics Dashboard"
        description="Real-time analytics and insights from Rwanda's national datasets"
      />

      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-4">
          <DateRangePicker />
          <Select defaultValue="all">
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Data Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              <SelectItem value="economic">Economic</SelectItem>
              <SelectItem value="social">Social</SelectItem>
              <SelectItem value="demographic">Demographic</SelectItem>
              <SelectItem value="health">Health</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm" onClick={handleGenerateReport} disabled={isGeneratingReport}>
            <Download className="h-4 w-4 mr-2" />
            {isGeneratingReport ? "Generating..." : "Generate Report"}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg font-medium">Population</CardTitle>
              <CardDescription>Total population and growth rate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">13.2M</div>
              <div className="text-sm text-muted-foreground mt-1">
                <span className="text-green-500 font-medium">↑ 2.4%</span> from last year
              </div>
              <div className="h-[180px] mt-4">
                <PopulationChart />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg font-medium">GDP Growth</CardTitle>
              <CardDescription>Annual growth percentage</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">7.8%</div>
              <div className="text-sm text-muted-foreground mt-1">
                <span className="text-green-500 font-medium">↑ 0.6%</span> from previous quarter
              </div>
              <div className="h-[180px] mt-4">
                <GDPChart />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg font-medium">Inflation Rate</CardTitle>
              <CardDescription>Consumer price index change</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">4.2%</div>
              <div className="text-sm text-muted-foreground mt-1">
                <span className="text-red-500 font-medium">↑ 0.3%</span> from last month
              </div>
              <div className="h-[180px] mt-4">
                <InflationChart />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg font-medium">Literacy Rate</CardTitle>
              <CardDescription>Population literacy percentage</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">73.2%</div>
              <div className="text-sm text-muted-foreground mt-1">
                <span className="text-green-500 font-medium">↑ 1.8%</span> from last year
              </div>
              <div className="h-[180px] mt-4">
                <LiteracyChart />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.5 }}
        >
          <Card className="col-span-1 md:col-span-2 lg:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg font-medium">Health Metrics</CardTitle>
              <CardDescription>Key health indicators</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Life Expectancy</div>
                  <div className="text-2xl font-bold">69.2 yrs</div>
                  <div className="text-xs text-muted-foreground">
                    <span className="text-green-500">↑ 0.8</span> from 2020
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Infant Mortality</div>
                  <div className="text-2xl font-bold">27.1</div>
                  <div className="text-xs text-muted-foreground">
                    <span className="text-green-500">↓ 3.2</span> from 2020
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Vaccination Rate</div>
                  <div className="text-2xl font-bold">92.4%</div>
                  <div className="text-xs text-muted-foreground">
                    <span className="text-green-500">↑ 2.1%</span> from 2020
                  </div>
                </div>
              </div>
              <div className="h-[220px]">
                <HealthMetricsChart />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="mt-6">
        <Tabs defaultValue="time-series">
          <div className="flex justify-between items-center mb-4">
            <TabsList>
              <TabsTrigger value="time-series">Time Series</TabsTrigger>
              <TabsTrigger value="regional">Regional Comparison</TabsTrigger>
              <TabsTrigger value="demographic">Demographic Breakdown</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="time-series" className="animate-in">
            <Card>
              <CardHeader>
                <CardTitle>Historical Trends</CardTitle>
                <CardDescription>Key indicators over time (2018-2023)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[400px]">
                  <GDPChart height={400} />
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline">Export Data</Button>
                <Select defaultValue="gdp">
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Select Indicator" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gdp">GDP Growth</SelectItem>
                    <SelectItem value="inflation">Inflation</SelectItem>
                    <SelectItem value="population">Population</SelectItem>
                    <SelectItem value="literacy">Literacy Rate</SelectItem>
                  </SelectContent>
                </Select>
              </CardFooter>
            </Card>
          </TabsContent>

          <TabsContent value="regional" className="animate-in">
            <Card>
              <CardHeader>
                <CardTitle>Regional Comparison</CardTitle>
                <CardDescription>Comparing indicators across Rwanda's provinces</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[400px]">
                  <PopulationChart height={400} />
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline">Export Data</Button>
                <Select defaultValue="population">
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Select Indicator" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="population">Population</SelectItem>
                    <SelectItem value="income">Income</SelectItem>
                    <SelectItem value="education">Education</SelectItem>
                    <SelectItem value="health">Health</SelectItem>
                  </SelectContent>
                </Select>
              </CardFooter>
            </Card>
          </TabsContent>

          <TabsContent value="demographic" className="animate-in">
            <Card>
              <CardHeader>
                <CardTitle>Demographic Breakdown</CardTitle>
                <CardDescription>Analysis by age, gender, and other demographic factors</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[400px]">
                  <LiteracyChart height={400} />
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline">Export Data</Button>
                <Select defaultValue="age">
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Select Factor" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="age">Age Groups</SelectItem>
                    <SelectItem value="gender">Gender</SelectItem>
                    <SelectItem value="education">Education Level</SelectItem>
                    <SelectItem value="income">Income Level</SelectItem>
                  </SelectContent>
                </Select>
              </CardFooter>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      <GenerateReportDialog
        open={showReportDialog}
        onOpenChange={setShowReportDialog}
        isGenerating={isGeneratingReport}
      />
    </div>
  )
}
