import { useState } from 'react'
import syntrilloLogo from './assets/syntrillo-logo.png'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div id='main-container' className='w-full h-full flex flex-col justify-center align-center gap-2'>
      <div id='header-container' className='h-fit py-8 px-20 max-h-20 flex justify-start align-center gap-4'>
        <img src={syntrilloLogo} className='h-16 w-22' alt='logo' />
        <h1 className='text-4xl font-bold text-gray-700'>Syntrillo Clinic</h1>
      </div>
    </div>
  )
}

export default App
