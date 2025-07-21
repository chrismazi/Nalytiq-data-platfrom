import React, { useState, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, CartesianGrid, LabelList } from "recharts";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { groupedStats } from "@/lib/api";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

const COLORS = ["#2563eb", "#22d3ee", "#f59e42", "#f43f5e", "#10b981", "#eab308", "#a21caf", "#facc15"];

// Utility to group education levels
function groupEducationLevels(data: any[]) {
  const mapping: { [key: string]: string } = {
    'primary': 'Primary',
    'primary school': 'Primary',
    'elementary': 'Primary',
    'secondary': 'Secondary',
    'secondary school': 'Secondary',
    'high school': 'Secondary',
    'post-secondary': 'Tertiary',
    'bachelor': 'Tertiary',
    'bachelors': 'Tertiary',
    'masters': 'Tertiary',
    'phd': 'Tertiary',
    'doctorate': 'Tertiary',
    'tertiary': 'Tertiary',
    'university': 'Tertiary',
    'college': 'Tertiary',
  };
  const grouped: { [key: string]: any } = {};
  data.forEach((row) => {
    let key = (row.education_level || '').toLowerCase().trim();
    let group = mapping[key] || (key === '' ? 'Unknown' : 'Other');
    if (!grouped[group]) grouped[group] = { education_level: group, count: 0, poverty: 0, n: 0 };
    grouped[group].count += row.count || 0;
    if (row.poverty) {
      grouped[group].poverty += row.poverty * (row.count || 1);
      grouped[group].n += row.count || 1;
    }
  });
  // Calculate average poverty rate for each group
  Object.values(grouped).forEach((g) => {
    if (g.n > 0) g.poverty = g.poverty / g.n;
    else delete g.poverty;
    delete g.n;
  });
  return Object.values(grouped);
}

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

  const groupedEducation = useMemo(() => data.education ? groupEducationLevels(data.education) : [], [data.education]);

  // Top 5 districts by consumption, sorted descending
  const topDistrictsSorted = useMemo(() => {
    if (!filteredTopDistricts) return [];
    return [...filteredTopDistricts]
      .sort((a, b) => (b.Consumption || 0) - (a.Consumption || 0))
      .slice(0, 5);
  }, [filteredTopDistricts]);

  // Prepare Urban vs Rural for side-by-side bar chart
  const urbanRuralBarData = useMemo(() => {
    if (!filteredUrbanRural) return [];
    // If data is already in [{ ur2_2012: 'Urban', Consumption: ... }, ...] format, just return
    // Otherwise, map to that format
    return filteredUrbanRural.map((d: any) => ({
      type: d.ur2_2012 || d.type || '',
      Consumption: d.Consumption || 0,
    }));
  }, [filteredUrbanRural]);

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
          {/* Top Districts by Consumption (Top 5, Horizontal Bar) */}
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Top 5 Districts by Consumption</CardTitle></CardHeader>
            <CardContent>
              {topDistrictsSorted && topDistrictsSorted.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={topDistrictsSorted} layout="vertical" barCategoryGap={30}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis type="number" fontSize={14} tickLine={false} axisLine={false} label={{ value: "Avg Consumption", position: "insideBottom", offset: -5 }} />
                    <YAxis dataKey="district" type="category" fontSize={14} width={120} label={{ value: "District", angle: -90, position: "insideLeft", offset: 10 }} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                    <Bar dataKey="Consumption" fill={COLORS[2]} radius={[8, 8, 0, 0]} maxBarSize={40}>
                      <LabelList dataKey="Consumption" position="right" formatter={(v: number|string) => typeof v === 'number' ? v.toLocaleString() : v} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Urban vs Rural Consumption (Side-by-Side Bar) */}
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Urban vs Rural Consumption</CardTitle></CardHeader>
            <CardContent>
              {urbanRuralBarData && urbanRuralBarData.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={urbanRuralBarData} barCategoryGap={30}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis dataKey="type" fontSize={14} tickLine={false} axisLine={false} />
                    <YAxis fontSize={14} tickLine={false} axisLine={false} label={{ value: "Avg Consumption", angle: -90, position: "insideLeft", offset: 10 }} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                    <Bar dataKey="Consumption" fill={COLORS[6]} radius={[8, 8, 0, 0]} maxBarSize={40}>
                      <LabelList dataKey="Consumption" position="top" formatter={(v: number|string) => typeof v === 'number' ? v.toLocaleString() : v} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Education Breakdown (Grouped Donut) */}
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Education Breakdown</CardTitle></CardHeader>
            <CardContent>
              {groupedEducation && groupedEducation.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={groupedEducation}
                      dataKey="count"
                      nameKey="education_level"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {groupedEducation.map((entry, i) => (
                        <Cell key={`cell-edu-${i}`} fill={COLORS[i % COLORS.length]} />
                      ))}
                      <LabelList dataKey="count" position="outside" formatter={(v: number|string) => typeof v === 'number' ? v.toLocaleString() : v} />
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
          {/* Poverty by Education Level (Grouped, Vertical Bar) */}
          <Card className="md:col-span-2 shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Poverty Rate by Education Level</CardTitle></CardHeader>
            <CardContent>
              {groupedEducation && groupedEducation.length > 0 ? (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={groupedEducation} barCategoryGap={30}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis dataKey="education_level" fontSize={14} tickLine={false} axisLine={false} />
                    <YAxis fontSize={14} tickLine={false} axisLine={false} label={{ value: "Poverty Rate (%)", angle: -90, position: "insideLeft", offset: 10 }} domain={[0, 'dataMax']} tickFormatter={(v: number|string) => typeof v === 'number' ? v.toFixed(1) : v} />
                    <Tooltip formatter={(v: number|string) => typeof v === 'number' ? v.toFixed(1) + '%' : v} />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                    <Bar dataKey="poverty" fill={COLORS[4]} radius={[8, 8, 0, 0]} maxBarSize={40}>
                      <LabelList dataKey="poverty" position="top" formatter={(v: number|string) => typeof v === 'number' ? v.toFixed(1) + '%' : v} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-muted-foreground text-center py-8">No data available for this chart.</div>
              )}
            </CardContent>
          </Card>
          {/* Population Count by Education Level (Grouped, Horizontal Bar) */}
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-2"><CardTitle className="text-lg font-semibold">Population by Education Level</CardTitle></CardHeader>
            <CardContent>
              {groupedEducation && groupedEducation.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={groupedEducation} layout="vertical" barCategoryGap={30}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis type="number" fontSize={14} tickLine={false} axisLine={false} label={{ value: "Population", position: "insideBottom", offset: -5 }} />
                    <YAxis dataKey="education_level" type="category" fontSize={14} width={120} label={{ value: "Education Level", angle: -90, position: "insideLeft", offset: 10 }} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                    <Bar dataKey="count" fill={COLORS[5]} radius={[8, 8, 0, 0]} maxBarSize={40}>
                      <LabelList dataKey="count" position="right" formatter={(v: number|string) => typeof v === 'number' ? v.toLocaleString() : v} />
                    </Bar>
                  </BarChart>
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
        </div>
      </div>
    </div>
  );
} 