import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import SupplierSearchPage from './components/SupplierSearchPage'; // Importa el componente de búsqueda

function App() {
    return (
        <Router>
            <div className="min-h-screen bg-gray-100">
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/supplier-search" element={<SupplierSearchPage />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
