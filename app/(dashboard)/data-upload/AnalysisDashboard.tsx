import React, { useState, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, CartesianGrid, LabelList } from "recharts";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { groupedStats } from "@/lib/api";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

const COLORS = ["#2563eb", "#22d3ee", "#f59e42", "#f43f5e", "#10b981", "#eab308", "#a21caf", "#facc15"];

export default function AnalysisDashboard({ data, onClose }: { data: any; onClose: () => void }) {
  // Extract unique filter values
  const provinces = useMemo(() => ["All", ...Array.from(new Set((data.province || []).map((d: any) => d.province)))], [data]);
  const genders = useMemo(() => ["All", ...Array.from(new Set((data.gender || []).map((d: any) => d.s1q1)))], [data]);
  const urbanRural = useMemo(() => ["All", ...Array.from(new Set((data.urbanRural || []).map((d: any) => d.ur2_2012)))], [data]);

  // Frequency Table State
  const categoricalVars = useMemo(() => {
    // Guess categorical variables from data keys
    const keys = ["province", "s1q1", "ur2_2012", "district", "education_level"];
    return keys.filter(k => (data[k] && data[k].length > 0)) as string[];
  }, [data]);
  const [selectedFreqVar, setSelectedFreqVar] = useState<string>(categoricalVars[0] || "province");
  const [freqTable, setFreqTable] = useState<any[]>([]);
  const [freqLoading, setFreqLoading] = useState(false);
  const [freqError, setFreqError] = useState<string | null>(null);

  // Filter state
  const [selectedProvince, setSelectedProvince] = useState("All");
  const [selectedGender, setSelectedGender] = useState("All");
  const [selectedUrbanRural, setSelectedUrbanRural] = useState("All");

  // Filtered data
  const filteredProvince = useMemo(() =>
    selectedProvince === "All" ? data.province : data.province.filter((d: any) => d.province === selectedProvince),
    [data, selectedProvince]
  );
  const filteredGender = useMemo(() =>
    selectedGender === "All" ? data.gender : data.gender.filter((d: any) => d.s1q1 === selectedGender),
    [data, selectedGender]
  );
  const filteredUrbanRural = useMemo(() =>
    selectedUrbanRural === "All" ? data.urbanRural : data.urbanRural.filter((d: any) => d.ur2_2012 === selectedUrbanRural),
    [data, selectedUrbanRural]
  );
  const filteredTopDistricts = useMemo(() =>
    selectedProvince === "All" ? data.topDistricts : data.topDistricts.filter((d: any) => d.district === selectedProvince),
    [data, selectedProvince]
  );

  // Fetch frequency table when variable changes
  React.useEffect(() => {
    if (!selectedFreqVar) return;
    setFreqLoading(true);
    setFreqError(null);
    // Use the first available chart's data as a sample to get the file (assume file is available in window.uploadedFile)
    // In production, pass the file or cleaned data context
    const file = (window as any).uploadedFile;
    if (!file) {
      setFreqError("No uploaded file found for frequency table.");
      setFreqLoading(false);
      return;
    }
    groupedStats(file, selectedFreqVar, selectedFreqVar, "count")
      .then(res => {
        if (res.data && Array.isArray(res.data)) {
          setFreqTable(res.data);
        } else {
          setFreqError(res.error || "No data returned.");
        }
        setFreqLoading(false);
      })
      .catch(err => {
        setFreqError(err.message || "Failed to fetch frequency table.");
        setFreqLoading(false);
      });
  }, [selectedFreqVar]);

  return (
    <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center animate-fade-in">
      <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-xl max-w-7xl w-full flex relative overflow-y-auto max-h-[95vh]">
        {/* Sidebar Filters */}
        <div className="w-64 p-6 border-r bg-zinc-50 dark:bg-zinc-800 flex flex-col gap-6">
          <Button onClick={onClose} variant="outline" className="mb-4">Close</Button>
          <div>
            <div className="font-semibold mb-2">Province</div>
            <Select value={selectedProvince} onValueChange={setSelectedProvince}>
              <SelectTrigger><SelectValue placeholder="Select Province" /></SelectTrigger>
              <SelectContent>
                {provinces.map(p => <SelectItem key={String(p)} value={String(p)}>{String(p)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <div className="font-semibold mb-2">Gender</div>
            <Select value={selectedGender} onValueChange={setSelectedGender}>
              <SelectTrigger><SelectValue placeholder="Select Gender" /></SelectTrigger>
              <SelectContent>
                {genders.map(g => <SelectItem key={String(g)} value={String(g)}>{String(g)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <div className="font-semibold mb-2">Urban/Rural</div>
            <Select value={selectedUrbanRural} onValueChange={setSelectedUrbanRural}>
              <SelectTrigger><SelectValue placeholder="Select Type" /></SelectTrigger>
              <SelectContent>
                {urbanRural.map(u => <SelectItem key={String(u)} value={String(u)}>{String(u)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
        {/* Main Dashboard */}
        <div className="flex-1 p-8 grid grid-cols-1 md:grid-cols-2 gap-8 overflow-y-auto bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800">
          {/* Frequency Table */}
          <Card className="md:col-span-2 shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Frequency Table</CardTitle></CardHeader>
            <CardContent>
              <div className="flex items-center gap-4 mb-4">
                <div className="font-medium">Variable:</div>
                <Select value={selectedFreqVar} onValueChange={setSelectedFreqVar}>
                  <SelectTrigger className="w-48"><SelectValue placeholder="Select Variable" /></SelectTrigger>
                  <SelectContent>
                    {categoricalVars.map(v => <SelectItem key={String(v)} value={String(v)}>{String(v)}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              {freqLoading ? (
                <div className="text-muted-foreground text-center py-8">Loading frequency table...</div>
              ) : freqError ? (
                <div className="text-red-500 text-center py-8">{freqError}</div>
              ) : freqTable && freqTable.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-[300px] border rounded bg-white dark:bg-zinc-900">
                    <thead>
                      <tr>
                        <th className="p-2 border-b font-semibold text-gray-700 dark:text-gray-200">{selectedFreqVar}</th>
                        <th className="p-2 border-b font-semibold text-gray-700 dark:text-gray-200">Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {freqTable.map((row, i) => (
                        <tr key={i} className="hover:bg-blue-50 dark:hover:bg-zinc-800">
                          <td className="p-2 border-b">{String(row[selectedFreqVar])}</td>
                          <td className="p-2 border-b font-bold text-blue-700 dark:text-blue-300">{row.count ?? String(row[selectedFreqVar])}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-muted-foreground text-center py-8">No frequency data available.</div>
              )}
            </CardContent>
          </Card>
          {/* Poverty by Province */}
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Poverty by Province</CardTitle></CardHeader>
            <CardContent>
              {filteredProvince && filteredProvince.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={filteredProvince} barCategoryGap={30}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis dataKey="province" fontSize={14} tickLine={false} axisLine={false} dy={8} />
                    <YAxis fontSize={14} tickLine={false} axisLine={false} label={{ value: "Poverty Rate", angle: -90, position: "insideLeft", offset: 10 }} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                    <Bar dataKey="poverty" fill={COLORS[0]} radius={[8, 8, 0, 0]} maxBarSize={40}>
                      <LabelList dataKey="poverty" position="top" formatter={(v: number) => v?.toLocaleString()} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Avg Consumption by Province */}
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Avg Consumption by Province</CardTitle></CardHeader>
            <CardContent>
              {data.avgConsumption && data.avgConsumption.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={data.avgConsumption} barCategoryGap={30}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis dataKey="province" fontSize={14} tickLine={false} axisLine={false} dy={8} />
                    <YAxis fontSize={14} tickLine={false} axisLine={false} label={{ value: "Avg Consumption", angle: -90, position: "insideLeft", offset: 10 }} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                    <Bar dataKey="Consumption" fill={COLORS[1]} radius={[8, 8, 0, 0]} maxBarSize={40}>
                      <LabelList dataKey="Consumption" position="top" formatter={(v: number) => v?.toLocaleString()} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Top Districts by Consumption (Horizontal Bar) */}
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Top Districts by Consumption</CardTitle></CardHeader>
            <CardContent>
              {filteredTopDistricts && filteredTopDistricts.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={filteredTopDistricts} layout="vertical" barCategoryGap={30}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis type="number" fontSize={14} tickLine={false} axisLine={false} label={{ value: "Avg Consumption", position: "insideBottom", offset: -5 }} />
                    <YAxis dataKey="district" type="category" fontSize={14} width={120} label={{ value: "District", angle: -90, position: "insideLeft", offset: 10 }} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                    <Bar dataKey="Consumption" fill={COLORS[2]} radius={[8, 8, 0, 0]} maxBarSize={40}>
                      <LabelList dataKey="Consumption" position="right" formatter={(v: number) => v?.toLocaleString()} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Education Breakdown Pie/Donut (NEW) */}
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Education Breakdown</CardTitle></CardHeader>
            <CardContent>
              {data.education && data.education.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={data.education}
                      dataKey="count"
                      nameKey="education_level"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {data.education.map((entry: any, i: number) => (
                        <Cell key={`cell-edu-${i}`} fill={COLORS[i % COLORS.length]} />
                      ))}
                      <LabelList dataKey="count" position="outside" formatter={(v: number) => v?.toLocaleString()} />
                    </Pie>
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Urban vs Rural Consumption (Donut) */}
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Urban vs Rural Consumption</CardTitle></CardHeader>
            <CardContent>
              {filteredUrbanRural && filteredUrbanRural.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={filteredUrbanRural}
                      dataKey="Consumption"
                      nameKey="ur2_2012"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {filteredUrbanRural.map((entry: any, i: number) => (
                        <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
                      ))}
                      <LabelList dataKey="Consumption" position="outside" formatter={(v: number) => v?.toLocaleString()} />
                    </Pie>
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Poverty by Gender */}
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Poverty by Gender</CardTitle></CardHeader>
            <CardContent>
              {filteredGender && filteredGender.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={filteredGender} layout="vertical" barCategoryGap={30}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis type="number" fontSize={14} tickLine={false} axisLine={false} label={{ value: "Poverty Rate", position: "insideBottom", offset: -5 }} />
                    <YAxis dataKey="s1q1" type="category" fontSize={14} label={{ value: "Gender", angle: -90, position: "insideLeft", offset: 10 }} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                    <Bar dataKey="poverty" fill={COLORS[3]} radius={[8, 8, 0, 0]} maxBarSize={40}>
                      <LabelList dataKey="poverty" position="top" formatter={(v: number) => v?.toLocaleString()} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Poverty by Education Level */}
          <Card className="md:col-span-2 shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Poverty by Education Level</CardTitle></CardHeader>
            <CardContent>
              {data.education && data.education.length > 0 ? (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={data.education} layout="vertical" barCategoryGap={30}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis type="number" fontSize={14} tickLine={false} axisLine={false} label={{ value: "Count", position: "insideBottom", offset: -5 }} />
                    <YAxis dataKey="education_level" type="category" fontSize={14} width={120} label={{ value: "Education Level", angle: -90, position: "insideLeft", offset: 10 }} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                    <Bar dataKey="count" fill={COLORS[4]} radius={[8, 8, 0, 0]} maxBarSize={40}>
                      <LabelList dataKey="count" position="top" formatter={(v: number) => v?.toLocaleString()} />
                    </Bar>
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