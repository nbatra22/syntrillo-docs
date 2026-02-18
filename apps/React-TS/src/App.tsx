import './App.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ProviderSidebarPage from './pages/provider-sidebar/ProviderSidebarPage'
import ProviderTabPage from './pages/provider-tab/ProviderTabPage'
import PatientSidebarPage from './pages/patient-sidebar/PatientSidebarPage'

const HelloWorld = () => {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <h1 className="text-4xl font-bold text-gray-800">Hello World</h1>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/iframe_healthie_provider_sidebar" element={
          <div id='main-container' className='w-full min-h-screen flex flex-col'>
            <div id='header-container' className='h-fit py-8 px-20 flex items-center gap-4 bg-white shadow-sm'>
              <h1 className='text-4xl font-bold text-gray-700'>Syntrillo Clinic</h1>
            </div>
            <div className='flex-1 p-8 bg-gray-50'>
              <ProviderSidebarPage />
            </div>
          </div>
        } />
        <Route path="/iframe_healthie_provider_tab" element={
          <div id='main-container' className='w-full min-h-screen flex flex-col'>
            <div id='header-container' className='h-fit py-8 px-20 flex items-center gap-4 bg-white shadow-sm'>
              <h1 className='text-4xl font-bold text-gray-700'>Syntrillo Clinic</h1>
            </div>
            <div className='flex-1 p-8 bg-gray-50'>
              <ProviderTabPage />
            </div>
          </div>
        } />
        <Route path="/iframe_healthie_client_sidebar" element={
          <div id='main-container' className='w-full min-h-screen flex flex-col'>
            <div id='header-container' className='h-fit py-8 px-20 flex items-center gap-4 bg-white shadow-sm'>
              <h1 className='text-4xl font-bold text-gray-700'>Syntrillo Clinic</h1>
            </div>
            <div className='flex-1 p-8 bg-gray-50'>
              <PatientSidebarPage />
            </div>
          </div>
        } />
        <Route path="/" element={<HelloWorld />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
