import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";

const COLORS = ["#6366f1", "#22d3ee", "#f59e42", "#f43f5e", "#10b981", "#eab308", "#a21caf", "#facc15"];

export default function AnalysisDashboard({ data, onClose }: { data: any; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center animate-fade-in">
      <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-xl max-w-5xl w-full p-8 relative overflow-y-auto max-h-[90vh]">
        <Button onClick={onClose} className="absolute top-4 right-4" variant="outline">Close</Button>
        <h2 className="text-2xl font-bold mb-6">Smart Data Analysis Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Poverty by Province */}
          <Card>
            <CardHeader><CardTitle>Poverty by Province</CardTitle></CardHeader>
            <CardContent>
              {data.province && data.province.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={data.province}>
                    <XAxis dataKey="province" fontSize={12} />
                    <YAxis fontSize={12} />
                    <Tooltip />
                    <Bar dataKey="poverty" fill={COLORS[0]} isAnimationActive />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Avg Consumption by Province */}
          <Card>
            <CardHeader><CardTitle>Avg Consumption by Province</CardTitle></CardHeader>
            <CardContent>
              {data.avgConsumption && data.avgConsumption.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={data.avgConsumption}>
                    <XAxis dataKey="province" fontSize={12} />
                    <YAxis fontSize={12} />
                    <Tooltip />
                    <Bar dataKey="Consumption" fill={COLORS[1]} isAnimationActive />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Top Districts by Consumption */}
          <Card>
            <CardHeader><CardTitle>Top Districts by Consumption</CardTitle></CardHeader>
            <CardContent>
              {data.topDistricts && data.topDistricts.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={data.topDistricts}>
                    <XAxis dataKey="district" fontSize={12} />
                    <YAxis fontSize={12} />
                    <Tooltip />
                    <Bar dataKey="Consumption" fill={COLORS[2]} isAnimationActive />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Poverty by Gender */}
          <Card>
            <CardHeader><CardTitle>Poverty by Gender</CardTitle></CardHeader>
            <CardContent>
              {data.gender && data.gender.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={data.gender} layout="vertical">
                    <XAxis type="number" fontSize={12} />
                    <YAxis dataKey="s1q1" type="category" fontSize={12} />
                    <Tooltip />
                    <Bar dataKey="poverty" fill={COLORS[3]} isAnimationActive />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Urban vs Rural Consumption */}
          <Card>
            <CardHeader><CardTitle>Urban vs Rural Consumption</CardTitle></CardHeader>
            <CardContent>
              {data.urbanRural && data.urbanRural.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={data.urbanRural}
                      dataKey="Consumption"
                      nameKey="ur2_2012"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label
                    >
                      {data.urbanRural.map((entry: any, i: number) => (
                        <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Poverty by Education Level */}
          <Card className="md:col-span-2">
            <CardHeader><CardTitle>Poverty by Education Level</CardTitle></CardHeader>
            <CardContent>
              {data.education && data.education.length > 0 ? (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={data.education} layout="vertical">
                    <XAxis type="number" fontSize={12} />
                    <YAxis dataKey="education_level" type="category" fontSize={12} width={120} />
                    <Tooltip />
                    <Bar dataKey="count" fill={COLORS[4]} isAnimationActive />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
} 