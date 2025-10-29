"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, AlertCircle, TrendingUp, TrendingDown } from "lucide-react"
import { motion } from "framer-motion"

interface QualityScoreProps {
  score: {
    completeness: number
    consistency: number
    uniqueness: number
    validity: number
    overall: number
    grade: string
  }
}

export function DataQualityScore({ score }: QualityScoreProps) {
  const getGradeColor = (grade: string) => {
    if (grade.startsWith('A')) return 'bg-green-500'
    if (grade.startsWith('B')) return 'bg-blue-500'
    if (grade.startsWith('C')) return 'bg-yellow-500'
    if (grade.startsWith('D')) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const getScoreColor = (value: number) => {
    if (value >= 90) return 'bg-green-500'
    if (value >= 80) return 'bg-blue-500'
    if (value >= 70) return 'bg-yellow-500'
    if (value >= 60) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const scoreItems = [
    { label: 'Completeness', value: score.completeness, description: 'Non-missing values' },
    { label: 'Consistency', value: score.consistency, description: 'Proper data types' },
    { label: 'Uniqueness', value: score.uniqueness, description: 'No duplicates' },
    { label: 'Validity', value: score.validity, description: 'Within expected range' },
  ]

  return (
    <Card className="border-2">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              Data Quality Assessment
            </CardTitle>
            <CardDescription>Comprehensive quality analysis of your dataset</CardDescription>
          </div>
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 200, damping: 10 }}
            className="relative"
          >
            <div className="h-24 w-24 rounded-full bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 flex items-center justify-center">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {score.overall.toFixed(0)}
                </div>
                <div className="text-xs text-muted-foreground">Overall</div>
              </div>
            </div>
            <div className={`absolute -top-2 -right-2 ${getGradeColor(score.grade)} text-white text-xs font-bold px-2 py-1 rounded-full shadow-lg`}>
              {score.grade.split(' ')[0]}
            </div>
          </motion.div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Overall Grade */}
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
            <div>
              <div className="font-medium">Quality Grade</div>
              <div className="text-sm text-muted-foreground">{score.grade}</div>
            </div>
            <Badge variant="outline" className="text-lg px-4 py-2">
              {score.overall.toFixed(1)}%
            </Badge>
          </div>

          {/* Individual Scores */}
          <div className="space-y-4">
            {scoreItems.map((item, index) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${getScoreColor(item.value)}`} />
                    <div>
                      <div className="font-medium text-sm">{item.label}</div>
                      <div className="text-xs text-muted-foreground">{item.description}</div>
                    </div>
                  </div>
                  <div className="text-sm font-medium">{item.value.toFixed(1)}%</div>
                </div>
                <Progress value={item.value} className="h-2" />
              </motion.div>
            ))}
          </div>

          {/* Recommendations */}
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div className="text-sm">
                <div className="font-medium text-blue-900 dark:text-blue-100 mb-1">
                  Quality Recommendations
                </div>
                <ul className="text-blue-800 dark:text-blue-200 space-y-1">
                  {score.completeness < 95 && (
                    <li>• Consider handling missing values for better analysis</li>
                  )}
                  {score.consistency < 90 && (
                    <li>• Some columns may need type conversion</li>
                  )}
                  {score.uniqueness < 95 && (
                    <li>• Duplicate records detected - consider deduplication</li>
                  )}
                  {score.validity < 90 && (
                    <li>• Outliers detected - review for data quality issues</li>
                  )}
                  {score.overall >= 90 && (
                    <li>• Excellent data quality! Ready for analysis</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
