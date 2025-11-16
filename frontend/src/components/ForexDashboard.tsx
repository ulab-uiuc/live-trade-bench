import React, { useMemo } from "react";
import ModelsDisplay from "./ModelsDisplay";
import "./Dashboard.css";
import { Model } from "../types";

interface ForexDashboardProps {
  modelsData: Model[];
  modelsLastRefresh: Date;
  isLoading: boolean;
}

const ForexDashboard: React.FC<ForexDashboardProps> = ({
  modelsData,
  isLoading,
}) => {
  const forexModels = useMemo(
    () => modelsData.filter((m) => m.category === "forex"),
    [modelsData]
  );

  if (isLoading) {
    return <div className="loading-indicator">Loading...</div>;
  }

  return (
    <div className="theme-forex">
      <div style={{ textAlign: "center", padding: "2rem 0" }}>
        <h1
          style={{
            color: "#34d399",
            fontSize: "3.5rem",
            fontWeight: "800",
            margin: "0 0 0.5rem 0",
            position: "relative",
            zIndex: 1000,
          }}
        >
          Forex Models
        </h1>
        <p
          style={{
            color: "rgba(255, 255, 255, 0.7)",
            fontSize: "1.2rem",
            margin: 0,
            fontWeight: "500",
            position: "relative",
            zIndex: 1000,
          }}
        >
          AI-powered FX allocation across G10 currency pairs
        </p>

        <div
          style={{
            maxWidth: "1000px",
            margin: "1.5rem auto 0",
            padding: "1rem 1.5rem",
            background: "rgba(52, 211, 153, 0.1)",
            border: "1px solid rgba(52, 211, 153, 0.3)",
            borderRadius: "12px",
            color: "rgba(255, 255, 255, 0.8)",
            fontSize: "0.95rem",
            lineHeight: "1.6",
            textAlign: "left",
          }}
        >
          Each model manages a diversified FX portfolio spanning USD, EUR, JPY,
          GBP and other liquid pairs. Agents ingest macro news, momentum
          signals, and historical allocation context before proposing
          allocations that must sum to 100%. Explore every model card to inspect
          recent trades, allocation history, profit curves, and the underlying
          LLM reasoning.
        </div>
      </div>

      <ModelsDisplay
        modelsData={forexModels}
        stockModels={[]}
        polymarketModels={[]}
        onRefresh={undefined}
      />
    </div>
  );
};

export default ForexDashboard;
