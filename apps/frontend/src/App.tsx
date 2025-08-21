import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppRouter } from './routes/router';
import './App.css';

// Create a query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30 * 1000, // 30 seconds
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="app">
        <AppRouter />
      </div>
    </QueryClientProvider>
  );
}

export default App;
