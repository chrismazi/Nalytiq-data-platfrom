import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";

interface EDAOverviewProps {
  data: File | any;
  columns: string[];
  setColumns: (cols: string[]) => void;
}

const COLORS = ["#8884d8", "#82ca9d", "#ffc658", "#ff8042", "#8dd1e1", "#a4de6c", "#d0ed57", "#ffc0cb"];

const BACKEND_URL = "http://localhost:8000";

const EDAOverview: React.FC<EDAOverviewProps> = ({ data, columns, setColumns }) => {
  const [eda, setEda] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!data) return;
    setLoading(true);
    setError(null);
    let fetchPromise;
    if (data instanceof File) {
      const formData = new FormData();
      formData.append("file", data);
      fetchPromise = fetch(`${BACKEND_URL}/eda/`, {
        method: "POST",
        body: formData,
      });
    } else if (data && data.columns && data.head) {
      fetchPromise = fetch(`${BACKEND_URL}/eda/json/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    } else {
      setError("No valid data for EDA");
      setLoading(false);
      return;
    }
    fetchPromise
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((json) => {
        setEda(json);
        setColumns(json.columns || []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [data, setColumns]);

  if (!data) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-4">Automated EDA & Visualizations</h2>
        <div className="bg-white rounded-lg shadow p-6 animate-fade-in">
          <p className="mb-2">Upload a dataset to see summary statistics and visualizations.</p>
        </div>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-4">Automated EDA & Visualizations</h2>
        <div className="bg-white rounded-lg shadow p-6 animate-fade-in">
          <p>Loading EDA...</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-4">Automated EDA & Visualizations</h2>
        <div className="bg-white rounded-lg shadow p-6 animate-fade-in">
          <p className="text-red-500">{String(error)}</p>
        </div>
      </section>
    );
  }

  if (!eda) return null;

  // Render summary stats and charts
  return (
    <section className="mb-10">
      <h2 className="text-2xl font-semibold mb-4">Automated EDA & Visualizations</h2>
      <div className="bg-white rounded-lg shadow p-6 animate-fade-in">
        <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-gray-500 text-xs">Rows</div>
            <div className="text-xl font-bold">{eda.shape?.[0]}</div>
          </div>
          <div>
            <div className="text-gray-500 text-xs">Columns</div>
            <div className="text-xl font-bold">{eda.shape?.[1]}</div>
          </div>
          <div>
            <div className="text-gray-500 text-xs">Missing Values</div>
            <div className="text-xl font-bold">{Object.values(eda.missing || {}).reduce((a: any, b: any) => a + (b || 0), 0)}</div>
          </div>
        </div>
        <div className="mb-6">
          <h3 className="font-semibold mb-2">Column Types</h3>
          <div className="flex flex-wrap gap-2">
            {eda.columns?.map((col: string, i: number) => (
              <span key={col} className="px-2 py-1 rounded bg-blue-100 text-blue-800 text-xs font-mono animate-fade-in">
                {col}: {eda.dtypes?.[col]}
              </span>
            ))}
          </div>
        </div>
        <h3 className="font-semibold mb-2">Summary Statistics</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr>
                <th className="p-1">Stat</th>
                {(eda.columns || []).filter(
                  (col: string) => col !== 'Sample Data' && col !== 'Sample Data (First 10 rows)' && col !== 'Correlation Matrix'
                ).map((col: string) => (
                  <th key={col} className="p-1">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.keys(eda.describe || {}).filter(
                (stat: string) => stat !== 'Sample Data' && stat !== 'Sample Data (First 10 rows)' && stat !== 'Correlation Matrix'
              ).map((stat: string) => (
                <tr key={stat}>
                  <td className="p-1 font-semibold">{stat}</td>
                  {(eda.columns || []).filter(
                    (col: string) => col !== 'Sample Data' && col !== 'Sample Data (First 10 rows)' && col !== 'Correlation Matrix'
                  ).map((col: string) => (
                    <td key={col} className="p-1">{eda.describe?.[col]?.[stat] ?? "-"}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h3 className="font-semibold mb-2">Suggested Visualizations</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {(eda.visualization_suggestions || [])
            .filter((viz: any) => viz.column !== 'Sample Data' && viz.column !== 'Sample Data (First 10 rows)' && viz.column !== 'Correlation Matrix')
            .map((viz: any, i: number) => {
              const col = viz.column;
              if (viz.type === "histogram" && eda.describe?.[col]) {
                return (
                  <div key={col} className="bg-gray-50 rounded p-4 shadow animate-fade-in">
                    <div className="font-semibold mb-2">{col} (Histogram)</div>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={Object.entries(eda.describe[col] || {}).map(([k, v]) => ({ name: k, value: v }))}>
                        <XAxis dataKey="name" fontSize={10} />
                        <YAxis fontSize={10} />
                        <Tooltip />
                        <Bar dataKey="value" fill={COLORS[i % COLORS.length]} isAnimationActive />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                );
              }
              if (viz.type === "bar" && eda.describe?.[col]) {
                const valueCounts = Object.entries(eda.describe[col] || {})
                  .filter(([k]) => k !== "count" && k !== "unique" && k !== "top" && k !== "freq")
                  .map(([k, v]) => ({ name: k, value: v }));
                return (
                  <div key={col} className="bg-gray-50 rounded p-4 shadow animate-fade-in">
                    <div className="font-semibold mb-2">{col} (Bar)</div>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={valueCounts}>
                        <XAxis dataKey="name" fontSize={10} />
                        <YAxis fontSize={10} />
                        <Tooltip />
                        <Bar dataKey="value" fill={COLORS[i % COLORS.length]} isAnimationActive />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                );
              }
              return null;
            })
            .filter((el: any): el is React.ReactNode => el !== null)
          }
        </div>
      </div>
    </section>
  );
};

export default EDAOverview; 