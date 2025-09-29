import { useState } from 'react'

export default function Home() {
  const [text, setText] = useState('')
  return (
    <div style={{ padding: 24 }}>
      <h1>BookEditor (MVP)</h1>
      <textarea value={text} onChange={(e) => setText(e.target.value)} rows={20} cols={80} />
    </div>
  )
}
