import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import { HistoryProvider } from "./context/HistoryContext";
import { DashboardProvider } from "./context/DashboardContext";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <DashboardProvider>
        <HistoryProvider>
          <App />
        </HistoryProvider>
      </DashboardProvider>
    </BrowserRouter>
  </React.StrictMode>
);
