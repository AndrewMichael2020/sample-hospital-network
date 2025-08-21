import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ScenarioBuilder } from '../screens/ScenarioBuilder';
import { ResultsDashboard } from '../screens/ResultsDashboard';
import { ScenarioCompare } from '../screens/ScenarioCompare';
import { NavHeader } from '../components/NavHeader';

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <NavHeader />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/scenario-builder" replace />} />
            <Route path="/scenario-builder" element={<ScenarioBuilder />} />
            <Route path="/results/:scenarioId?" element={<ResultsDashboard />} />
            <Route path="/compare/:scenarioAId/:scenarioBId?" element={<ScenarioCompare />} />
            <Route path="*" element={<Navigate to="/scenario-builder" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};