import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import BookEditor from '../components/BookEditor'

const queryClient = new QueryClient()

export default function Home() {
  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ height: '100vh', overflow: 'hidden' }}>
        <BookEditor />
      </div>
    </QueryClientProvider>
  )
}
