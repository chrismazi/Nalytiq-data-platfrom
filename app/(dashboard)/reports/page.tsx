"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Download, FileText, Search, SlidersHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DashboardHeader } from "@/components/dashboard-header"
import { Badge } from "@/components/ui/badge"

export default function ReportsPage() {
  const [searchQuery, setSearchQuery] = useState("")

  const reports = [
    {
      id: 1,
      title: "Rwanda Economic Outlook 2023",
      description: "Comprehensive analysis of Rwanda's economic performance and projections",
      date: "May 2, 2023",
      author: "Economic Analysis Team",
      type: "Economic",
      downloads: 245,
    },
    {
      id: 2,
      title: "Population Health Survey Results",
      description: "Key findings from the national health survey",
      date: "April 18, 2023",
      author: "Health Statistics Division",
      type: "Health",
      downloads: 187,
    },
    {
      id: 3,
      title: "Education Statistics Annual Report",
      description: "Analysis of education metrics across all provinces",
      date: "March 30, 2023",
      author: "Education & Social Statistics",
      type: "Education",
      downloads: 203,
    },
    {
      id: 4,
      title: "Agricultural Production Trends",
      description: "Analysis of agricultural output and productivity",
      date: "March 15, 2023",
      author: "Agricultural Statistics Team",
      type: "Agriculture",
      downloads: 156,
    },
    {
      id: 5,
      title: "Labor Market Analysis Q1 2023",
      description: "Employment statistics and labor market trends",
      date: "April 5, 2023",
      author: "Labor Statistics Division",
      type: "Economic",
      downloads: 178,
    },
  ]

  const filteredReports = reports.filter(
    (report) =>
      report.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      report.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      report.type.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <DashboardHeader
        title="Reports & Publications"
        description="Access and download official statistical reports and publications"
      />

      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search reports..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <SlidersHorizontal className="h-4 w-4 mr-2" />
            Filters
          </Button>
          <Button size="sm">
            <Download className="h-4 w-4 mr-2" />
            Download All
          </Button>
        </div>
      </div>

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Reports</TabsTrigger>
          <TabsTrigger value="economic">Economic</TabsTrigger>
          <TabsTrigger value="social">Social</TabsTrigger>
          <TabsTrigger value="demographic">Demographic</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-6 animate-in">
          <div className="grid gap-4">
            {filteredReports.length > 0 ? (
              filteredReports.map((report, index) => (
                <motion.div
                  key={report.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <Card className="overflow-hidden">
                    <div className="flex flex-col md:flex-row">
                      <div className="bg-primary/10 p-6 flex items-center justify-center md:w-24">
                        <FileText className="h-10 w-10 text-primary" />
                      </div>
                      <div className="flex-1 p-6">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-medium text-lg">{report.title}</h3>
                              <Badge variant="outline">{report.type}</Badge>
                            </div>
                            <p className="text-muted-foreground mb-2">{report.description}</p>
                            <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                              <span>Published: {report.date}</span>
                              <span>By: {report.author}</span>
                              <span>{report.downloads} downloads</span>
                            </div>
                          </div>
                          <div className="flex gap-2 mt-4 md:mt-0">
                            <Button variant="outline" size="sm">
                              Preview
                            </Button>
                            <Button size="sm">
                              <Download className="h-4 w-4 mr-2" />
                              Download
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))
            ) : (
              <Card className="p-8 text-center">
                <div className="flex flex-col items-center">
                  <Search className="h-10 w-10 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No reports found</h3>
                  <p className="text-muted-foreground mb-4">
                    We couldn't find any reports matching your search criteria.
                  </p>
                  <Button variant="outline" onClick={() => setSearchQuery("")}>
                    Clear Search
                  </Button>
                </div>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Other tab contents would be similar but filtered by category */}
        <TabsContent value="economic" className="mt-6 animate-in">
          <div className="grid gap-4">
            {filteredReports
              .filter((report) => report.type === "Economic")
              .map((report, index) => (
                <motion.div
                  key={report.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <Card className="overflow-hidden">
                    <div className="flex flex-col md:flex-row">
                      <div className="bg-primary/10 p-6 flex items-center justify-center md:w-24">
                        <FileText className="h-10 w-10 text-primary" />
                      </div>
                      <div className="flex-1 p-6">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-medium text-lg">{report.title}</h3>
                              <Badge variant="outline">{report.type}</Badge>
                            </div>
                            <p className="text-muted-foreground mb-2">{report.description}</p>
                            <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                              <span>Published: {report.date}</span>
                              <span>By: {report.author}</span>
                              <span>{report.downloads} downloads</span>
                            </div>
                          </div>
                          <div className="flex gap-2 mt-4 md:mt-0">
                            <Button variant="outline" size="sm">
                              Preview
                            </Button>
                            <Button size="sm">
                              <Download className="h-4 w-4 mr-2" />
                              Download
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))}
          </div>
        </TabsContent>

        {/* Similar structure for other tabs */}
      </Tabs>
    </div>
  )
}
