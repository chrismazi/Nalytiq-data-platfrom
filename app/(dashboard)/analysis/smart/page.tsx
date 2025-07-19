"use client";
import React, { useState } from "react";
import EDAOverview from "@/components/eda/EDAOverview";
import CrosstabSection from "@/components/crosstab/CrosstabSection";
import ModelingSection from "@/components/modeling/ModelingSection";
import ChatbotSection from "@/components/chatbot/ChatbotSection";

interface SmartAnalysisPageProps {
  file: File | null;
  cleanedData: any;
}

const SmartAnalysisPage: React.FC<SmartAnalysisPageProps> = ({ file, cleanedData }) => {
  const [columns, setColumns] = useState<string[]>([]);

  return (
    <div className="p-8 max-w-7xl mx-auto animate-fade-in">
      <h1 className="text-3xl font-bold mb-6">Smart Data Analysis Dashboard</h1>
      {!file ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-6 text-yellow-800">
          No dataset selected. Please upload and clean a dataset first.
        </div>
      ) : null}
      {/* EDA Section */}
      <EDAOverview data={file} columns={columns} setColumns={setColumns} />
      {/* Crosstab Section */}
      <CrosstabSection data={file} columns={columns} />
      {/* Modeling Section */}
      <ModelingSection data={file} columns={columns} />
      {/* Chatbot Section */}
      <ChatbotSection data={file} columns={columns} />
    </div>
  );
};

export default SmartAnalysisPage; 