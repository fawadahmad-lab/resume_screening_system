import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { CandidateDetailPage } from "./pages/CandidateDetailPage";
import { CandidatesPage } from "./pages/CandidatesPage";
import { EvaluationsPage } from "./pages/EvaluationsPage";
import { ScreeningPage } from "./pages/ScreeningPage";
import { SystemPage } from "./pages/SystemPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<CandidatesPage />} />
            <Route path="/screening" element={<ScreeningPage />} />
            <Route path="/candidates/:candidateId" element={<CandidateDetailPage />} />
            <Route path="/evaluations" element={<EvaluationsPage />} />
            <Route path="/system" element={<SystemPage />} />
            <Route path="*" element={<CandidatesPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}