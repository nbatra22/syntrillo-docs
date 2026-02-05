import './App.css'
import ProviderSidebarPage from './pages/provider-sidebar/ProviderSidebarPage'

function App() {
  return (
    <div id='main-container' className='w-full min-h-screen flex flex-col'>
      <div id='header-container' className='h-fit py-8 px-20 flex items-center gap-4 bg-white shadow-sm'>
        <h1 className='text-4xl font-bold text-gray-700'>Syntrillo Clinic</h1>
      </div>
      <div className='flex-1 p-8 bg-gray-50'>
        <ProviderSidebarPage />
      </div>
    </div>
  )
}

export default App
