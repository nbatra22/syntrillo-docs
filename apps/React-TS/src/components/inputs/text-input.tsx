import React from "react"

interface TextInputProps {
    label: string
    required?: boolean
    id: string
    name: string
    value: string
    placeholder: string
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
}

const TextInput: React.FC<TextInputProps> = ({ label, required, id, name, value, placeholder, onChange }) => {
    return (
        <div className="w-full flex flex-col">
            <label htmlFor={id} className="block mb-1 font-bold text-black">
                {label}{required && <span className="text-red-500">*</span>}
            </label>
            <input
                type="text"
                id={id}
                name={name}
                value={value}
                placeholder={placeholder}
                onChange={onChange}
                className="w-full bg-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required={required}
            />
        </div>
    )
}

export default TextInput
